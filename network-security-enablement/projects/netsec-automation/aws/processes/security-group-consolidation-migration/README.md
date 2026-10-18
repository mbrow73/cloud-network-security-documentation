# NetSec Automation — security-group consolidation / migration

**Draft outline — not execution-ready.** [Review and acceptance](handoff.md) · [Parent project](../../README.md).

## 1. Purpose and migration boundaries

TODO: define consolidation versus migration, supported resource types/environments, exclusions, target state, and required parent-project readiness.

## 2. Discovery and dependency mapping

TODO: authoritative SG/rule inventory, attachments, referencing SGs, owners, workloads, existing IaC/state ownership, and connectivity evidence. Identify service-managed/controller-managed resources and exceptions before planning changes.

## 3. Target mapping and equivalence review

TODO: current-to-target SG/rule mapping, approved access intent, allowed differences, rule/attachment quotas, and ownership approval. Similar names or overlapping rules are not evidence of equivalent access; account for combined permissions from all attached SGs.

## 4. Preconditions and change approval

TODO: approved change, application owners, backup/export and state recovery, rollback identifiers, canary population, test plan, communications, and explicit stop/no-go criteria.

## 5. Wave-by-wave execution

TODO: write the exact approved method for creating/selecting targets, synchronizing rules, changing attachments, and handling IaC state. Specify ordering and access implications for the actual resource type; do not assume a universal attach/detach procedure.

## 6. Validation and observation

TODO: required allowed and denied connectivity tests, application health, telemetry, drift checks, observation duration, evidence, and approval before each subsequent wave.

## 7. Failure handling and rollback

TODO: rollback triggers, owner, tested restoration of rules/attachments/state, recovery validation, and escalation when rollback is unsafe or incomplete.

## 8. Retirement and closeout

TODO: confirm no remaining attachments/references and no unmanaged consumers; retire legacy SGs only after the agreed observation and explicit change approval. Update inventory, IaC/state, ownership, and audit evidence.

## 9. Acceptance evidence

TODO: demonstrate an approved canary migration and rollback; document access equivalence, no unintended permission expansion, IaC consistency, and completion/stop criteria. NSE acceptance of this process is separate from approval of any particular migration wave.
