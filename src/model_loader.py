"""Memory-aware loader for Qwen2.5-7B and the NLA PEFT adapter.

The loader supports a CUDA node with CPU offload as well as a CPU-only node
with 64 GiB system RAM. It downloads missing model and adapter snapshots through
the standard Hugging Face APIs instead of assuming a warm cache.
"""

from __future__ import annotations

import os
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


class ModelLoader:
    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-7B-Instruct",
        verbalizer: str = "Kameshr/nla-qwen2.5-7b-L20-av",
        base_revision: str | None = None,
        verbalizer_revision: str | None = None,
        device: str | None = None,
    ) -> None:
        self.base_model = base_model
        self.verbalizer = verbalizer
        self.base_revision = base_revision or None
        self.verbalizer_revision = verbalizer_revision or None
        self.device = (device or os.getenv("BUDGET_NLA_DEVICE", "auto")).lower()

    def _placement(self) -> tuple[Any, dict | None]:
        cuda_allowed = self.device in {"auto", "cuda"} and torch.cuda.is_available()
        if cuda_allowed:
            index = torch.cuda.current_device()
            total_gib = torch.cuda.get_device_properties(index).total_memory // (1024**3)
            reserve_gib = max(2, min(8, total_gib // 8))
            max_memory = {
                index: f"{max(1, total_gib - reserve_gib)}GiB",
                "cpu": os.getenv("BUDGET_NLA_CPU_MEMORY", "52GiB"),
            }
            dtype = (
                torch.bfloat16
                if torch.cuda.is_bf16_supported()
                else torch.float16
            )
            return dtype, max_memory

        if self.device == "cuda":
            raise RuntimeError("BUDGET_NLA_DEVICE=cuda but CUDA is unavailable.")
        return torch.bfloat16, {"cpu": os.getenv("BUDGET_NLA_CPU_MEMORY", "52GiB")}

    def load(self) -> tuple[Any, Any]:
        dtype, max_memory = self._placement()
        offload_dir = os.getenv("BUDGET_NLA_OFFLOAD_DIR", "results/model_offload")
        device_map: Any = "auto" if torch.cuda.is_available() and self.device != "cpu" else {"": "cpu"}

        base = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            revision=self.base_revision,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
            device_map=device_map,
            max_memory=max_memory,
            offload_folder=offload_dir,
            attn_implementation="eager",
        )
        self.model = PeftModel.from_pretrained(
            base,
            self.verbalizer,
            revision=self.verbalizer_revision,
            is_trainable=False,
        )
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            revision=self.base_revision,
        )
        return self.model, self.tokenizer
