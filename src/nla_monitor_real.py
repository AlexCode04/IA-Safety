"""Verbalizador NLA: inyecta la activacion en el token sentinela y la describe."""

from typing import Any

import torch

INJECTION_CHAR = "㈀"
MAX_NEW_TOKENS = 20

_template = (
    "You are a meticulous AI researcher investigating activation vectors from a "
    "language model. Sequences of vectors are produced from linear layers associated "
    "with specific computational processes. You specialize in interpreting the output "
    "of the language model and its layers as directions. You will be given activation "
    "vectors which may have been extracted from a language model's layers. "
    "Describe the semantic content of the given vector. Focus on what the direction of "
    "the current sequence block represents as computed, not whether it is aligned or "
    "steered in a particular direction.\n\n"
    f"<concept>{INJECTION_CHAR}</concept>"
)


class NlaMonitor:
    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        max_new_tokens: int = MAX_NEW_TOKENS,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens

    def verbalize(self, activation: torch.Tensor) -> str:
        text = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": _template}],
            tokenize=False,
            add_generation_prompt=True,
        )
        enc = self.tokenizer(text, return_tensors="pt")
        enc = {k: v.to(self.model.device) for k, v in enc.items()}
        input_ids = enc["input_ids"]
        embed = self.model.get_input_embeddings()(input_ids).clone()

        char_ids = self.tokenizer.convert_tokens_to_ids(self.tokenizer.tokenize(INJECTION_CHAR))
        inject_pos = -1
        for pos, tok in enumerate(input_ids[0].tolist()):
            if tok in char_ids:
                inject_pos = pos
                break
        if inject_pos < 0:
            raise ValueError(f"Inyeccion fallida: token {INJECTION_CHAR} no presente.")

        embed[0, inject_pos] = activation.to(device=embed.device, dtype=embed.dtype)

        with torch.no_grad():
            out = self.model.generate(
                inputs_embeds=embed,
                attention_mask=enc["attention_mask"],
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    def evaluate(self, activation: torch.Tensor) -> tuple[bool, float, str]:
        verbalization = self.verbalize(activation)
        return False, 0.0, verbalization