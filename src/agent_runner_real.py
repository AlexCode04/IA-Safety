"""Live Qwen2.5-7B-Instruct runner with the frozen tool-call JSON contract."""

import json
from contextlib import nullcontext
from time import perf_counter
from typing import Any

from src.agent_runner import DECISION_MARKER, SYSTEM_PROMPT, AgentOutput, reasoning_before_decision

KNOWN_TOOLS = {"publish_report", "send_email", "update_allowlist"}


def parse_tool_call(text: str) -> tuple[bool, str, dict[str, Any]]:
    start = text.rfind("{")
    while start >= 0:
        depth = 0
        for index in range(start, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : index + 1]
                    try:
                        payload = json.loads(candidate)
                    except json.JSONDecodeError:
                        payload = None
                    break
        if payload is not None:
            tool_name = payload.get("tool_name")
            arguments = payload.get("arguments")
            if isinstance(tool_name, str) and tool_name in KNOWN_TOOLS and isinstance(arguments, dict):
                return True, tool_name, arguments
        start = text.rfind("{", 0, start)
    return False, "", {}


class RealAgentRunner:
    def __init__(
        self,
        model: str,
        temperature: float,
        model_obj: Any = None,
        tokenizer: Any = None,
        max_new_tokens: int = 512,
        system_prompt: str | None = SYSTEM_PROMPT,
        do_sample: bool = False,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.model_obj = model_obj
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.do_sample = do_sample

    def _ensure_model(self) -> None:
        if self.model_obj is None:
            from src.model_loader import ModelLoader

            loader = ModelLoader()
            self.model_obj, self.tokenizer = loader.load()
            self.model = loader.base_model

    def run(self, scenario: dict[str, Any]) -> AgentOutput:
        import torch

        self._ensure_model()
        started_at = perf_counter()
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": scenario["prompt"]},
        ]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        enc = self.tokenizer(text, return_tensors="pt")
        adapter_context = (
            self.model_obj.disable_adapter()
            if hasattr(self.model_obj, "disable_adapter")
            else nullcontext()
        )
        with adapter_context, torch.no_grad():
            out = self.model_obj.generate(
                **enc,
                max_new_tokens=self.max_new_tokens,
                do_sample=self.do_sample,
                temperature=self.temperature if self.do_sample else None,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = self.tokenizer.decode(
            out[0][enc["input_ids"].shape[1] :], skip_special_tokens=True
        ).strip()
        latency_ms = (perf_counter() - started_at) * 1000
        decision_marker_found = DECISION_MARKER.strip() in generated
        parsed, tool_name, arguments = parse_tool_call(generated)
        if not parsed:
            tool_name = scenario.get("critical_tool", "")
            arguments = {}
        return AgentOutput(
            reasoning=reasoning_before_decision(generated),
            tool_name=tool_name,
            arguments=arguments,
            decision_marker_found=decision_marker_found,
            latency_ms=latency_ms,
            input_tokens=int(enc["input_ids"].shape[1]),
            output_tokens=int(out.shape[1] - enc["input_ids"].shape[1]),
            call_parse_failed=not parsed,
            activation_prefix=(
                f"{text}{reasoning_before_decision(generated)}{DECISION_MARKER}"
            ),
        )
