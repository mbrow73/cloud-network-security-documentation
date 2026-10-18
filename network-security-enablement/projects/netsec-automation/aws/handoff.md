# AWS NetSec Automation — handoff record

- **Status:** Draft
- **Document type:** Draft initial QE troubleshooting support handoff
- **Submitting team:** Network Security Architecture and Engineering (NSAE)
- **Receiving team:** Network Security Enablement
- **Architecture contact:** TODO: name / team handle
- **NSE reviewer / acceptance authority:** TODO: name / team handle and authority
- **Service or process owner:** TODO: name / team
- **Content:** [Packet documentation](README.md)
- **Reviewed revision:** TODO: content commit SHA or immutable review link
- **Review request:** TODO: PR / tracking link
- **Requested support start:** TODO: date; not effective until explicitly accepted
- **Related packets / dependencies:** [SG migration process](processes/security-group-consolidation-migration/handoff.md) — separately reviewed

## Requested operational scope

NSE provides IST-hours QE defect triage for supported patterns, helps QE/application and platform/AFT owners resolve configuration or provisioning prerequisites, and escalates suspected architecture/catalog defects to NSAE with evidence. NSE records potential control-coverage risks. AWS support includes assistance to AFT Operations with planned native-firewall consolidation under the separate process.

[Shared scope and responsibility boundaries](../shared/support-model.md) and [QE triage procedure](../shared/qe-defect-triage.md) define this phase. **Service-catalog ownership, architecture remediation and third-party environment automation support are excluded.** TODO: exact supported-pattern revision, IST hours/days, contacts, access and evidence references for this cloud.

## Acceptance criteria and evidence

- [ ] Scope and responsibility boundaries agreed by the named owners.
- [ ] Required access and training demonstrated for the receiving team.
- [ ] Applicable procedures, success checks, failure paths, and recovery validated; evidence linked.
- [ ] Monitoring and escalation routes verified.
- [ ] Required security/risk/change approvals linked separately; no approvals implied here.
- [ ] NSE demonstrates an application/test configuration triage and missing platform prerequisite diagnosis applicable to this cloud.
- [ ] NSE produces an actionable NSAE escalation without requiring conclusive root cause first.
- [ ] NSE demonstrates the risk-findings PR route with the authoritative risk document/reviewer linked.
- [ ] Supported-pattern sheet, exact IST coverage, intake/escalation contacts and diagnostic references are populated.
- [ ] AWS only: consolidation-assistance responsibilities are reviewed under the separate migration process; no change authority is implied here.

**Evidence:** TODO: immutable test records, walkthrough, tickets, dashboards, or recorded demonstrations.

## Gaps and follow-ups

| Gap | Blocking? | Owner | Due date | Resolution / evidence |
| --- | --- | --- | --- | --- |
| Missing reference sheets, operator links/contacts/hours and unvalidated triage walkthroughs | Yes | TODO: NSAE owner | TODO | Not resolved |

## Decision history (append only)

No decision has been made. For each review, append:

- **Date / reviewer / authority:** TODO
- **Outcome:** Proposed / Changes requested / Rejected / Accepted
- **Reviewed content revision and scope:** TODO
- **Reason:** TODO; required for Changes requested and Rejected, including impact and the correction/evidence needed for reconsideration
- **Correction links / re-review reference:** TODO
- **Accepted scope / exclusions:** TODO; required for Accepted
- **Effective date / operational owner:** TODO; required for Accepted
- **Nonblocking follow-ups:** TODO: owner and due date, or none

Acceptance is revision- and scope-specific. Review history does not grant risk acceptance or authorize production execution. See the [area workflow](../../../README.md).
