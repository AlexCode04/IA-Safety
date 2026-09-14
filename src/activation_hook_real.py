"""Hook real de la capa 20 del Qwen en el limite PRE_ACTION_DECISION_BOUNDARY."""

from typing import Any

import torch

POSITION_NAME = "PRE_ACTION_DECISION_BOUNDARY"
TARGET_LAYER = 20


class ActivationHook:
    def __init__(self, model: Any, tokenizer: Any, layer: int = TARGET_LAYER) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.layer = layer

    def capture(self, text: str) -> torch.Tensor:
        captured: dict[str, torch.Tensor] = {}

        def hook(_mod: Any, _inp: Any, out: Any) -> None:
            hidden = out[0] if isinstance(out, tuple) else out
            captured["h"] = hidden[0, -1].detach().float()

        enc = self.tokenizer(text, return_tensors="pt")
        base = self.model.get_base_model()
        handle = base.model.layers[self.layer].register_forward_hook(hook)
        try:
            with torch.no_grad():
                self.model.get_base_model()(**enc)
        finally:
            handle.remove()
        return captured["h"]