# AWS intent-driven security-group egress

**Draft outline — exact request, verdict and deployment implementation to confirm.** [Review and acceptance](handoff.md) · [AWS project](../README.md) · [Shared control model](../../shared/control-model.md).

## Purpose and example

Architecture identifies custom intent-driven SG egress as the primary segmentation control for the Lambda-to-on-premises example. Downstream Palo Alto / Illumio plumbing is described under [shared CRE integration](../../shared/cre/README.md).

## Request and authorization contract

TODO: request interface, owner identity, source/resource binding, destination representation, service/port/environment context, verdict authority, and handling of unknown or denied intent.

## Rendering and runtime enforcement

TODO: intent-to-rule translation, actual SG attachment, rule ownership, combined-SG effects, mutation/attachment permissions, drift detection, and proof that rendered/attached rules match the approved request.

## Operational lifecycle

TODO: submit/change/revoke procedures, CI/approval/execution path, propagation checks, failures/retries, rollback, evidence, and escalation.

## Readiness and boundaries

TODO: live versus planned capability inventory, supported resources and exclusions, allowed/denied connectivity tests, and named NSE/Architecture/platform ownership. The [SG consolidation/migration process](../processes/security-group-consolidation-migration/README.md) remains a separate handoff.
