# GCP NetSec Automation — project operational handoff

**Draft outline — initial control-model context captured; scope and enforcement not validated; not execution-ready.** [Review and acceptance](handoff.md) · [Project index](../README.md).

## 1. Scope and capability inventory

Initial examples are GKE-to-on-premises service-entry intent/central verdict with CRE-based downstream policy, and intra-GCP fleet firewall templates combining GKE source tags with service-specific destination IP containers. See the [shared control model](../shared/control-model.md) for the supplied examples and unresolved enforcement questions.

TODO: confirm capabilities/release, supported projects/Regions/environments, consumers, exclusions and live versus planned status. Do not copy the AWS service model or SG migration process into this scope.

## 2. Architecture and dependencies

TODO: authoritative design, code repositories, execution platform, inputs/state, identity, approvals, and deployed inventory.

## 3. Ownership, access, and support model

TODO: NSE versus Architecture/platform/application responsibilities, required roles, access lifecycle, support expectations, escalation, and training.

## 4. Operational procedures and monitoring

TODO: enumerate the actual request/change/maintenance operations, alerts, logs, failure modes, safe retry, and evidence requirements before expanding into executable procedures.

## 5. Change, recovery, and readiness

TODO: change gates, rollback/recovery paths, demonstrations, and measurable acceptance criteria for the agreed GCP capabilities. Track missing scope as a blocker in the handoff record.
