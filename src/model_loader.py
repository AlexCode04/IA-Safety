"""Carga local de Qwen2.5-7B-Instruct cuantizado int4 (CPU) + adapter verbalizador NLA.

Estrategia: construir la arquitectura desde config en device meta (sin pesos
random), volcar los shards del snapshot con safe_open key-a-key, cuantizar cada
linear con Int4OpaqueTensor (grupo 128) al asignarlo, y montar el adapter PEFT
despues de la cuantizacion. Evita la ruta TorchAoConfig (muerta: cuantifica
post-carga y muere de RAM).
"""

import gc
import glob as _glob
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from huggingface_hub.constants import HF_HUB_CACHE
from peft import PeftModel
from safetensors import safe_open
from torchao.prototype.quantization.int4 import Int4OpaqueTensor
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

QUANT_BITS_TO_GROUP_SIZE = {4: 128}


class ModelLoader:
    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-7B-Instruct",
        verbalizer: str = "Kameshr/nla-qwen2.5-7b-L20-av",
        quant_bits: int = 4,
    ) -> None:
        self.base_model = base_model
        self.verbalizer = verbalizer
        self.quant_bits = quant_bits
        self.group_size = QUANT_BITS_TO_GROUP_SIZE[quant_bits]

    def _snapshot(self, repo_id: str) -> str:
        cache_dir = Path(HF_HUB_CACHE) / f"models--{repo_id.replace('/', '--')}"
        commit = (cache_dir / "refs" / "main").read_text().strip()
        return str(cache_dir / "snapshots" / commit)

    def _load_weights(self, model: nn.Module, snapshot: str) -> None:
        shard_files = sorted(_glob.glob(snapshot + "/model-*.safetensors"))
        for shard in shard_files:
            with safe_open(shard, framework="pt", device="cpu") as f:
                for key in f.keys():
                    tensor = f.get_tensor(key)
                    fqn, attr = key.rsplit(".", 1)
                    mod = model.get_submodule(fqn)
                    if attr == "weight" and isinstance(mod, nn.Linear):
                        quantized = Int4OpaqueTensor.from_hp(
                            tensor, [1, self.group_size]
                        )
                        setattr(mod, attr, nn.Parameter(quantized, requires_grad=False))
                    else:
                        setattr(
                            mod,
                            attr,
                            nn.Parameter(tensor.contiguous(), requires_grad=False),
                        )
                    del tensor
                    gc.collect()

    def _materialize_meta_buffers(self, model: nn.Module) -> None:
        for mod in model.modules():
            meta_bufs = [
                name for name, buf in mod._buffers.items()
                if buf is not None and buf.device.type == "meta"
            ]
            if not meta_bufs:
                continue
            if not hasattr(mod, "config"):
                raise RuntimeError(
                    f"Buffers en meta sin forma de reconstruir: {mod.__class__.__name__}.{meta_bufs}"
                )
            with torch.device("cpu"):
                mod.__init__(mod.config)

    def _load_gpu(self) -> tuple[Any, Any]:
        base = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.bfloat16,
            attn_implementation="eager",
        )
        base.to("cuda")
        self.model = PeftModel.from_pretrained(base, self._snapshot(self.verbalizer))
        self.model.to("cuda")
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        return self.model, self.tokenizer

    def load(self) -> tuple[Any, Any]:
        if torch.cuda.is_available():
            return self._load_gpu()
        snapshot = self._snapshot(self.base_model)
        config = AutoConfig.from_pretrained(snapshot, attn_implementation="eager")
        with torch.device("meta"):
            base = AutoModelForCausalLM.from_config(
                config, dtype=torch.bfloat16, attn_implementation="eager"
            )
        self._load_weights(base, snapshot)
        for param in base.parameters():
            if param.device.type == "meta":
                raise RuntimeError(
                    f"Peso sin materializar tras la carga: {param}\n"
                    "El index de shards no cubre todo el state dict."
                )
        self._materialize_meta_buffers(base)
        self.model = PeftModel.from_pretrained(base, self._snapshot(self.verbalizer))
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        return self.model, self.tokenizer