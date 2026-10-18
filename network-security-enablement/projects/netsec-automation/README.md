# NetSec Automation

A phased, in-progress project. Document the processes and implemented support scope being handed over now, not the completed future architecture.

- [Shared overview and project expectations](shared/README.md): NSE support covers both clouds and all automation patterns, with current/planned behavior distinguished.
- Cloud troubleshooting: [AWS](aws/troubleshooting.md) and [GCP](gcp/troubleshooting.md), linked from the shared project expectations.
- [Continuous Registration Engine (CRE)](shared/cre/README.md) — requested outline; fill in the relevant scope as we work through it.
- [AWS](aws/README.md) — current-phase support, intent-driven SG egress and the separate consolidation/migration process.
- [GCP](gcp/README.md) — current-phase support and cloud-specific pattern notes.
- [Risk-findings PR area](shared/risk-findings/README.md) — placeholder for NSAE's supplied risk document and new findings.

Verdicting is not implemented yet. Gatekeeper is platform context, not NSAE/NSE-owned operations under this handoff. Neither needs a new troubleshooting document or readiness checklist for this phase. Full catalog ownership comes later.
