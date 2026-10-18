# NetSec Automation

Cloud-specific project handoffs and shared control-model documentation for Network Security Enablement.

## Shared architecture and integrations

- [Primary and secondary/transitive control model](shared/control-model.md): working definitions, example flows, GCP address-container model, and unresolved enforcement/scope questions.
- [CRE integration](shared/cre/README.md): cross-cloud downstream policy-plumbing outline with its own [handoff record](shared/cre/handoff.md).

## Cloud-specific handoffs

- [AWS](aws/README.md): project operational handoff, including the dependent [security-group consolidation / migration process](aws/processes/security-group-consolidation-migration/README.md).
- [GCP](gcp/README.md): scope to expand from the [shared control-model discussion](shared/control-model.md); no AWS procedures are assumed to apply.

Each cloud has its own handoff record. This page is navigation, not a combined acceptance decision. Shared documents also require explicitly scoped acceptance; their location does not accept either cloud deployment. Accepting AWS responsibilities does not accept GCP responsibilities, or vice versa. Shared material can be linked when genuinely common without duplicating cloud-specific procedures.
