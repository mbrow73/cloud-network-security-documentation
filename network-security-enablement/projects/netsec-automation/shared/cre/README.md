# Continuous Registration Engine (CRE) — AWS and GCP

**Requested explanatory outline; refine when we reach this topic.** CRE is NetSec's internally developed Continuous Registration Engine. [Project expectations](../README.md) · [Handoff decision](handoff.md).

## What this document should explain

Explain how CRE supports downstream/transitive environment/service-port policy plumbing with Palo Alto/Illumio across AWS and GCP, so NSE can recognize a missing registration/provisioning issue versus a missing automation pattern or catalog definition. Keep implemented behavior and future work separate.

## How the relevant pattern is registered and mapped

- **CRE registration-to-policy flow:** TODO: insert explanation/diagram.
- **Policy-plumbing table:** TODO: insert spreadsheet/document link.
- **Registration/provisioning references:** TODO: insert existing links.

## What NSE checks and where an issue goes

TODO: existing registration/policy references useful for diagnosis and who owns a provisioning correction. Use [AWS QE defect handling](../../aws/qe-defect-handling.md) or [GCP QE defect handling](../../gcp/qe-defect-handling.md) for the request-versus-architecture decision.

A missing pattern/catalog entry that changes inherited automation access goes to **NSAE**: it can have a broad blast radius and is not an ordinary individual access request. NSE can help requestors with compliant, justified one-time access through the normal process, but does not take over service-catalog definition or broad changes.

## Scope limit

This is one explanation for the existing requested CRE topic, not a new document series or full CRE platform operations manual. Full service-catalog ownership is deferred; verdicting is not implemented yet and is not required to explain the existing policy-plumbing model.
