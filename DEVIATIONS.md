# Deviations from EXPERIMENT_SPEC.md

## D-001 — Prefix replay instead of generation pause/resume

- **Recorded:** 2026-09-14, before the final result set.
- **Specification affected:** Section 5, which states that generation stops at
  `<DECISION>` and later resumes from the same prefix.
- **Implemented pilot:** Qwen first generates a complete candidate response.
  Before any simulated tool is committed, the runner reconstructs the exact
  serialized prompt plus reasoning prefix ending at `<DECISION>` and performs a
  separate deterministic forward pass to capture the layer-20 activation. The
  tool name and arguments are excluded from this replayed prefix.
- **Reason:** the current runner does not yet implement multi-token stopping and
  KV-cache continuation. Prefix replay gives the activation for the frozen
  informational boundary without exposing future action text to the probe or
  NLA, but it does not demonstrate synchronous end-to-end latency.
- **Reporting rule:** describe containment outcomes as simulated/counterfactual
  and report live pause/resume as future engineering work.

The specification is frozen before data collection. If a technical
change is required after inspecting results:

1. Record the change here.
2. State when and why it was made.
3. Preserve the original result.
4. Mark the new analysis as exploratory.
5. Do not describe exploratory changes as preregistered.
