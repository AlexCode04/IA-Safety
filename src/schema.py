"""Canonical result schema aligned with EXPERIMENT_SPEC.md."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.1.0"
SPEC_VERSION = "1.0"
MonitorView = Literal["observable", "cot", "probe", "nla"]
PolicyKind = Literal[
    "baseline",
    "nla_probe_cot",
    "probe_nla_cot",
    "cot_nla",
    "action_only",
]
POLICY_KINDS: list[str] = list(PolicyKind.__args__)
PolicyDecision = Literal["allow", "escalate", "block"]
Condition = Literal["BENIGN", "ATTACK_REJECTED", "VISIBLE_SABOTAGE", "STEALTH_SABOTAGE"]
Family = Literal["external_report", "corporate_email", "access_list"]


class Seeds(BaseModel):
    python: int = 260913
    numpy: int = 260913
    torch: int = 260913
    split: int = 260914
    label_permutation: int = 260915
    bootstrap: int = 260916


class ExperimentInfo(BaseModel):
    name: str
    spec_version: str = SPEC_VERSION
    config_hash: str
    mock_mode: bool
    seeds: Seeds
    agent_model: str
    agent_revision: str | None
    monitor_model: str
    nla_model: str
    nla_revision: str | None


class TrajectoryInfo(BaseModel):
    id: str
    family: Family
    condition: Condition
    variant: str
    template_id: str
    authorized_task: str
    critical_tool: str
    severity: float = Field(ge=0)


class AgentTrace(BaseModel):
    model: str
    temperature: float
    do_sample: bool
    max_new_tokens: int
    reasoning: str
    decision_marker_found: bool
    proposed_tool: str
    latency_ms: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class ActivationInfo(BaseModel):
    layer: int
    position_name: str
    captured: bool
    vector_dim: int = Field(ge=0)


class ToolCallInfo(BaseModel):
    name: str
    arguments: dict
    public_arguments: dict
    unauthorized: bool
    committed: bool


class GroundTruthLabels(BaseModel):
    primary_label: Literal[0, 1]
    attack_instruction_present: bool
    malicious_objective_adopted: bool
    harmful_tool_call_proposed: bool
    harm_committed: bool


class ChannelResult(BaseModel):
    view: MonitorView
    enabled: bool
    alert: bool
    alert_before_harm: bool
    score: float = Field(ge=0, le=1)
    assumed_cost: float = Field(ge=0)
    measured_latency_ms: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    api_calls: int = Field(ge=0)
    gpu_seconds: float = Field(ge=0)
    raw_output: str


class ChannelBundle(BaseModel):
    observable: ChannelResult
    cot: ChannelResult
    probe: ChannelResult
    nla: ChannelResult


class PolicyResult(BaseModel):
    kind: PolicyKind
    selected_views: list[MonitorView]
    decision: PolicyDecision
    reason: str
    assumed_cost: float = Field(ge=0)
    alert_before_harm: bool
    intervention_successful: bool
    containment_successful: bool
    residual_harm: float = Field(ge=0)
    prevented_harm: float = Field(ge=0)


class PolicyBundle(BaseModel):
    baseline: PolicyResult
    nla_probe_cot: PolicyResult
    probe_nla_cot: PolicyResult
    cot_nla: PolicyResult
    action_only: PolicyResult


class RunRecord(BaseModel):
    """Single JSONL line written to results/runs.jsonl."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    timestamp: str
    experiment: ExperimentInfo
    trajectory: TrajectoryInfo
    agent: AgentTrace
    activation: ActivationInfo
    tool_call: ToolCallInfo
    labels: GroundTruthLabels
    channels: ChannelBundle
    policies: PolicyBundle

    model_config = {"extra": "forbid"}


def new_run_id() -> str:
    return uuid4().hex


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
