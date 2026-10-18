# NetSec Automation — control-coverage risk findings

This directory is the proposed repository intake for NSE to report patterns that appear exempt from, or not covered by, expected automation controls. A finding is an observation requiring assessment, not proof of a vulnerability or accepted risk.

## Authoritative risk document

**TODO: NSAE-provided risk document / register / reporting instructions.** Add the supplied document or its authoritative link here. This intake must link to that source rather than become a competing approval register.

## Submit a finding through a PR

1. Copy the [finding template](finding-template.md) into this directory as `YYYY-MM-DD-short-title.md`.
2. Record the expected pattern/control and observed gap, evidence, scope/impact, and unknowns. Potential gaps may be submitted without a complete root cause.
3. Open a PR for the finding and request review from **TODO: NSAE risk reviewer/team handle**. Link the QE defect and engineering ticket where applicable.
4. Flag urgent observed exposure through **TODO: existing urgent escalation channel**; a PR is not a substitute for time-sensitive escalation.
5. Link the authoritative risk/engineering decision when assigned. Track follow-up evidence and assessment without implying NSE can approve an exception or accept risk.

The reviewer route and authoritative risk document are not yet populated. Acceptance of the support handoff requires a usable reporting route. This scaffold adds no automatic reviewer routing or risk-approval workflow.
