from src.policy_gate import PolicyGate, as_views


def _verdict(
    action: str = "BLOCK",
    actionable: bool = True,
    score: float = 0.9,
    evidence: str = "protected-data transfer detected",
) -> dict:
    return {
        "recommended_action": action,
        "actionable_alert": actionable,
        "risk_score": score,
        "evidence": evidence,
    }


def test_decide_verdict_blocks_actionable():
    gate = PolicyGate(escalate_threshold=0.5, block_on_alert=True)
    decision, reason = gate.decide_verdict(_verdict())
    assert decision == "block"
    assert "protected-data transfer" in reason


def test_decide_verdict_escalates_inconsistent_high_score_allow():
    gate = PolicyGate(escalate_threshold=0.5, block_on_alert=True)
    payload = _verdict(action="ALLOW", score=0.8)
    payload["actionable_alert"] = False
    decision, _ = gate.decide_verdict(payload)
    assert decision == "escalate"


def test_decide_verdict_allows_clean_verdict():
    gate = PolicyGate(escalate_threshold=0.5, block_on_alert=True)
    decision, _ = gate.decide_verdict(
        _verdict(action="ALLOW", actionable=False, score=0.2, evidence="no conflict")
    )
    assert decision == "allow"


def test_decide_verdict_accepts_pydantic_like_objects():
    class _Dump:
        def __init__(self, payload: dict):
            self._payload = payload

        def model_dump(self):
            return self._payload

    gate = PolicyGate(block_on_alert=True)
    decision, _ = gate.decide_verdict(_Dump(_verdict()))
    assert decision == "block"


def test_as_views_filters_unknown_views():
    assert as_views(["observable", "cot", "probe", "nla", "unknown", ""]) == [
        "observable",
        "cot",
        "probe",
        "nla",
    ]