# Network Security Enablement

Operational handoffs from Architecture to Network Security Enablement (NSE).

**Proposed workflow:** this area is a documentation scaffold, not a record that NSE has already agreed to the workflow or accepted support responsibility. All initial packets are **Draft**.

## Handoff catalog

| Packet | Category | Scope | Decision record |
| --- | --- | --- | --- |
| [NetSec Automation](projects/netsec-automation/README.md) | Project | Service ownership, support model, operating procedures | [Handoff](projects/netsec-automation/handoff.md) |
| [Security-group consolidation / migration](projects/netsec-automation/processes/security-group-consolidation-migration/README.md) | Project process | Migration preparation, execution, validation, recovery | [Handoff](projects/netsec-automation/processes/security-group-consolidation-migration/handoff.md) |
| [Resource Gateway / Resy risk acceptance](third-party-environments/resource-gateway-resy/README.md) | Third-party environment | Operational exposure, risk record, compensating controls | [Handoff](third-party-environments/resource-gateway-resy/handoff.md) |
| [App-ID preview changes / content-update remediation](third-party-environments/app-id-content-update-remediation/README.md) | Third-party operational process | Preview assessment, controlled rollout, break/fix | [Handoff](third-party-environments/app-id-content-update-remediation/handoff.md) |

## Directory rules

- Organize by enduring project or environment/process, not by review status. Keep paths stable after acceptance.
- Keep project-dependent procedures under their project. Migration has its own decision because accepting routine support does not automatically accept a migration process.
- Each packet has a `README.md` for content and a `handoff.md` for scope, readiness, and the decision trail.
- Link existing ADRs, diagrams, runbooks, and authoritative risk/change records; do not copy them into a second source of truth.
- Third-party environment naming/ownership and the meaning of “Resy” need confirmation; the directory does not assert a vendor, platform, or production topology.
- Use `TODO: ...` placeholders for unknown facts. Never replace them with invented owners, service levels, technical steps, or approvals.

## Proposed review lifecycle

1. **Draft:** Architecture prepares the packet. List missing information, named owner roles, acceptance criteria, and supporting evidence.
2. **Proposed:** Architecture opens a review PR, identifies the packet/revision and requested support scope, and requests review from the designated NSE reviewers (`TODO: team handle`). No responsibility transfers yet.
3. **Changes requested:** NSE records specific gaps, why they block acceptance, and the evidence needed. Architecture links the corrections and resubmits. Use **Rejected** for an explicit decision not to accept the proposed scope; reasons are mandatory.
4. **Accepted:** An authorized NSE representative records the reviewed revision, accepted scope, effective date, ownership, and evidence. Open blockers must be resolved; any nonblocking follow-ups need an owner and due date.
5. Material scope/procedure changes require renewed review. Append decisions rather than overwriting history. Prior acceptance applies only to its recorded revision and scope.

A PR merge alone is not operational acceptance. Draft outlines can be merged without changing their status. Status fields are manually maintained; this scaffold adds no approval automation or branch-protection enforcement. Confirm reviewer authority and repository controls before adopting the workflow.

## Acceptance boundary

NSE accepts operational responsibilities, not security risk on behalf of the business. Formal risk acceptance requires the separately authorized risk owner and system of record. Link that decision, affected scope, conditions, and expiry; do not imply approval from a documentation review. Likewise, accepting documentation does not authorize a production change.

## Minimum readiness before proposing a packet

- [ ] Named Architecture contact, NSE reviewer, service/process owner, and escalation route.
- [ ] In-scope and out-of-scope responsibilities, dependencies, and support boundaries.
- [ ] Executable procedures, required access, validation evidence, and tested recovery/rollback path where applicable.
- [ ] Monitoring, incident ownership, change controls, and required training/walkthrough.
- [ ] Risks/exceptions linked to authorized decisions, with expiry and re-review obligations.
- [ ] Critical placeholders resolved; noncritical gaps explicitly classified with owners/dates.
- [ ] Measurable packet-specific acceptance criteria and reviewed content revision.

Use the [handoff record template](templates/handoff.md) for additional packets.
