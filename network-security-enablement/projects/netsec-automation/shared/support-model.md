# NetSec Automation — initial NSE support handoff

**Draft for review.** Scope supplied by Network Security Architecture and Engineering (NSAE), 2026-10-18. This is a development/quality-engineering support handoff, not transfer of the service catalog or full production operations. [Project index](../README.md).

## Purpose

Network Security Enablement (NSE) will provide troubleshooting support during agreed India Standard Time (IST) support hours for defects raised by Quality Engineering (QE) against supported NetSec Automation patterns. NSE will identify whether a reported failure originates in test/application configuration, missing platform prerequisites, automation execution, or a suspected architecture/service-catalog defect. NSE will help QE and the relevant platform operations teams resolve configuration and provisioning issues, and route suspected automation design or catalog defects to NSAE with actionable diagnostic evidence.

NSE will also record suspected gaps in expected automation-control coverage and assist AFT Operations with planned native-firewall consolidation activities under the separately agreed consolidation/migration process. The required execution authority and change approvals remain explicit in that process.

## Current phase and scope boundary

- Supported patterns are those in the Architecture-provided flow/control-placement spreadsheet, for the versions/environments it identifies. Link and revision: **TODO: supported-pattern/control-placement spreadsheet**.
- Third-party environments are **not currently included in NetSec Automation**. Their separately organized documentation does not imply automation coverage or inclusion in this support handoff.
- On-premises sources in the described automation scope are on-premises cloud Kubernetes workloads, which are also intended to require service entries and verdicts. Do not generalize this to all on-premises sources.
- The current objective is timely defect isolation and feedback while automation architecture continues to develop. Ownership of the service catalog will be handed over later under a separate scope/acceptance decision.
- The boundary between NSE and NSAE is diagnostic support versus remediation of architecture/design/catalog defects, not a requirement for NSE to prove an architectural flaw before requesting engineering help.

## Responsibility boundaries

| Activity | NSE responsibility | Resolution / authority boundary |
| --- | --- | --- |
| QE reports failure in an expected supported pattern | Intake, reproduce/trace where practical, collect evidence, isolate likely failing layer | QE provides test details and confirms retest |
| Incorrect port/protocol, missing workload SG attachment, or destination service not running/listening | Help QE/application owner identify and correct the test/configuration issue through the approved process | QE/application owner corrects its workload/test configuration; privileges are not transferred by this document |
| Required AFT-vended SG or other platform prerequisite missing | Identify the missing prerequisite and coordinate with the responsible platform/AFT operations team | Platform/AFT Operations addresses provisioning within its authority |
| Valid supported intent fails because of suspected automation, service-catalog, or architecture behavior | Supply reproducible evidence, expected-versus-observed behavior, impact and suspected component; escalate promptly | NSAE assesses/remediates architecture/catalog defects and coordinates implementation owners |
| Pattern is unsupported, ambiguous, or not represented in the spreadsheet | Record the gap and ask NSAE to classify it | Do not treat unsupported intent as an approved pattern or open broader access to make the test pass |
| Traffic appears exempt from, or bypasses, an expected automation control | Record a potential control-coverage risk and flag it to NSAE; do not wait for a connectivity failure | Formal assessment, risk treatment and approval follow the authoritative risk process |
| Planned native-firewall consolidation | Assist AFT Operations with pattern/dependency checks, troubleshooting and validation | Follow the [AWS consolidation/migration handoff](../aws/processes/security-group-consolidation-migration/README.md); execution and change authority must be separately assigned |

## NSE does not take over in this phase

- Service-catalog ownership, architecture redesign, or routine maintenance/release ownership of every automation component.
- Approval of new access patterns, risk acceptance, or standing authority to bypass expected controls.
- All platform/application corrective actions simply because NSE identified the cause.
- Third-party environment automation support, unspecified patterns, or 24x7 coverage.

NSE may use approved runbooks and authorized access; additional change/execution responsibilities must be agreed explicitly rather than inferred from troubleshooting ownership.

## Support arrangements to complete

- **Coverage:** India Standard Time (IST). TODO: exact start/end hours, covered weekdays/holidays, support start date and rota.
- **QE intake / queue:** TODO: defect tracker/project, required fields, contact/channel and assignment route.
- **NSAE escalation:** TODO: team handle/queue, engineering contact and urgent escalation route.
- **Platform/AFT contacts:** TODO: operations queues and dependency owners.
- **Response / update expectations:** TODO: agreed targets and severity definitions; none are implied by this draft.
- **Outside coverage / urgent control gaps:** TODO: existing escalation route and owner; do not assume NSE is available outside agreed hours.
- **Diagnostic access / dashboards / training:** TODO: role requests, logs and approved tooling per component.

## Working instructions and evidence

Use the [QE defect-triage guide](qe-defect-triage.md), [shared control model](control-model.md), and [risk-findings intake](risk-findings/README.md). The operator-facing links and product-specific commands are placeholders until supplied and validated.

Acceptance should demonstrate representative application/configuration triage, a missing AFT prerequisite case, an NSAE defect escalation, and a control-gap report. Record cloud-specific evidence and explicit acceptance in the [AWS](../aws/handoff.md) or [GCP](../gcp/handoff.md) handoff records. A successful support walkthrough does not accept the full automation lifecycle or transfer catalog ownership.
