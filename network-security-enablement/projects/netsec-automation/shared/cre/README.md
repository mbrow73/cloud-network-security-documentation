# CRE integration — shared AWS and GCP automation

**Draft outline — intended integration described, deployment state to confirm.** [Review and acceptance](handoff.md) · [Shared control model](../control-model.md).

## Purpose and scope

CRE provides the described downstream/transitive policy-plumbing integration with Palo Alto and Illumio for AWS and GCP. It is shared project material rather than duplicated cloud-specific documentation. TODO: confirm CRE's full authoritative name and which integrations are currently live versus planned.

## Trigger and identity contract

TODO: exact account/project/cluster vending events in each cloud, authoritative inputs and source identities, environment/service/port mapping, NAT effects, and validation/authorization. Do not assume AWS account vending and GCP project/cluster provisioning are interchangeable.

## Policy lifecycle

TODO: create/update/delete behavior, reconciliation, drift, idempotency, stale registrations, partial failures, safe retries, rollback, and audit evidence. Identify when resource/address changes require re-registration.

## Operations and ownership

TODO: operators, access, integration owners, upstream/downstream responsibilities, health checks, alerts, manual recovery, and escalation.

## Acceptance evidence

TODO: cloud- and product-specific tests of supported lifecycle and failure scenarios. Record the precise integrations/cloud scope accepted; a shared record must not imply acceptance of all AWS/GCP capabilities.
