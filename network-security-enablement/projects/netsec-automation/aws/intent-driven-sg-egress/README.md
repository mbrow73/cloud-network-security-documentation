# AWS intent-driven security-group egress

**Requested topic outline — fill in the phase being handed over, not the completed target architecture.** [Review and acceptance](handoff.md) · [AWS project](../README.md) · [Current-phase overview](../../shared/README.md).

## Purpose and example

Architecture identifies custom intent-driven SG egress as the primary segmentation control for the Lambda-to-on-premises example. Downstream Palo Alto / Illumio plumbing is described under [shared CRE integration](../../shared/cre/README.md).

## Request and authorization contract

TODO: describe the implemented request/rule workflow and relevant inputs for this phase. Verdicting is not implemented yet; it is future work, not a missing handoff dependency.

## Rendering and runtime enforcement

TODO: intent-to-rule translation, actual SG attachment, rule ownership, combined-SG effects, mutation/attachment permissions, drift detection, and proof that rendered/attached rules match the approved request.

## Operational lifecycle

TODO: checks and issue-routing relevant to NSE support of the implemented SG workflow. Expand only the procedures actually being handed over; full lifecycle/catalog ownership is deferred.

## Phase boundaries

TODO: identify implemented patterns and current support responsibilities, with future items explicitly excluded. The [SG consolidation/migration process](../processes/security-group-consolidation-migration/README.md) remains a separate handoff.
