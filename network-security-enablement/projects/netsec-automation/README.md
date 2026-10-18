# NetSec Automation

Cloud-specific project handoffs and shared control-model documentation for Network Security Enablement.

## Current handoff: QE troubleshooting support

[Initial NSE support scope](shared/support-model.md) · [QE defect-triage guide](shared/qe-defect-triage.md) · [Risk-findings PR intake](shared/risk-findings/README.md).

NSE supports expected automation patterns during agreed IST hours while architecture development continues, helping QE/platform teams resolve configuration and prerequisite issues and escalating suspected design/catalog defects to **NSAE — Network Security Architecture and Engineering**. Catalog ownership comes later. Third-party environments are not currently included in automation. AWS and GCP support decisions remain separately scoped.

## Shared architecture and integrations

- [Primary and secondary/transitive control model](shared/control-model.md): working definitions, example flows, GCP address-container model, and unresolved enforcement/scope questions.
- [CRE integration](shared/cre/README.md): cross-cloud downstream policy-plumbing outline with its own [handoff record](shared/cre/handoff.md).

## Cloud-specific handoffs

- [AWS](aws/README.md): project operational handoff, including the dependent [security-group consolidation / migration process](aws/processes/security-group-consolidation-migration/README.md).
- [GCP](gcp/README.md): scope to expand from the [shared control-model discussion](shared/control-model.md); no AWS procedures are assumed to apply.

Each cloud has its own handoff record. This page is navigation, not a combined acceptance decision. Shared documents also require explicitly scoped acceptance; their location does not accept either cloud deployment. Accepting AWS responsibilities does not accept GCP responsibilities, or vice versa. Shared material can be linked when genuinely common without duplicating cloud-specific procedures.
