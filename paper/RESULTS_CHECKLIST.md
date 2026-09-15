# Results insertion checklist

Use this only after the frozen non-mock run is complete.

## Integrity checks

- [ ] Maryori's final scenario and ground-truth tests pass.
- [ ] `experiment.mock_mode` is `false` in every submitted run record.
- [ ] Exactly 24 unique trajectory IDs are present.
- [ ] All four conditions have six trajectories each.
- [ ] All three families have eight trajectories each.
- [ ] No tool name or argument appears in the pre-action monitor prefix.
- [ ] One Gemini model ID is used throughout the submitted result set.
- [ ] Missing/failed API calls are counted and explained.
- [ ] Model revision hashes and environment snapshot are recorded.

## Required quantitative reporting

- [ ] PHR and BDR: numerator, denominator, percentage, 95% Wilson interval.
- [ ] EPH and PE for observable, CoT, probe, and NLA.
- [ ] IMV_NLA and IMV_NLA_given_CoT.
- [ ] Probe AUROC and AUPRC under LOTO only.
- [ ] Unique catches by channel.
- [ ] Visible-versus-stealth difference.
- [ ] Rejected-attack false-alert rate.
- [ ] Uniform-versus-adaptive residual harm at identical budget.
- [ ] Latency, tokens, API calls, and GPU-seconds kept separate from assumed cost.
- [ ] Cost sensitivity at -50%, default, and +50%.

## Required qualitative reporting

- [ ] Name and inspect every NLA-only catch.
- [ ] Name and inspect every benign false alarm.
- [ ] Inspect every CoT/NLA disagreement.
- [ ] Inspect cases where probe and NLA disagree on the same activation.
- [ ] Distinguish monitor failure, gate failure, and absent evidence.
- [ ] Include at least one negative or ambiguous case; do not cherry-pick only successes.

## Claim discipline

- [ ] Do not claim causal influence from a decodable probe or NLA phrase.
- [ ] Do not call prefix replay a synchronous real-time deployment.
- [ ] Do not present normalized costs as prices.
- [ ] Do not generalize beyond the 24 synthetic trajectories.
- [ ] Log any post-result change in `DEVIATIONS.md` and label it exploratory.
