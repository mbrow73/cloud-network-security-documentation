# Network Security Enablement

Architecture/NSAE handoff documentation for NSE, organized by project/process and cloud. The project is delivered in phases; accept the documented support slice, not an implied completed future architecture.

## General cloud guides

- [AWS troubleshooting](aws/troubleshooting.md) and [GCP troubleshooting](gcp/troubleshooting.md): reusable technical checks.
- Project-specific QE workflows link those guides and decide how to act on the findings. For automation: [AWS](projects/netsec-automation/aws/qe-defect-handling.md), [GCP](projects/netsec-automation/gcp/qe-defect-handling.md).
- Request-guide placeholders for later authoring: [AWS standard SG](aws/requests/standard-security-group-requests.md), [GCP standard routable firewall rules](gcp/requests/standard-routable-firewall-rule-requests.md), [AWS third-party standard requests](aws/requests/third-party-standard-requests.md), [GCP third-party standard requests](gcp/requests/third-party-standard-requests.md).

## Topics

### NetSec Automation

- [Project index](projects/netsec-automation/README.md).
- [Shared current-phase overview and QE support](projects/netsec-automation/shared/README.md).
- [AWS support](projects/netsec-automation/aws/README.md) · [decision](projects/netsec-automation/aws/handoff.md).
- [GCP support](projects/netsec-automation/gcp/README.md) · [decision](projects/netsec-automation/gcp/handoff.md).
- [Continuous Registration Engine (CRE)](projects/netsec-automation/shared/cre/README.md) · [decision](projects/netsec-automation/shared/cre/handoff.md).
- [AWS intent-driven SG egress](projects/netsec-automation/aws/intent-driven-sg-egress/README.md) · [decision](projects/netsec-automation/aws/intent-driven-sg-egress/handoff.md).
- [AWS SG consolidation/migration](projects/netsec-automation/aws/processes/security-group-consolidation-migration/README.md) · [decision](projects/netsec-automation/aws/processes/security-group-consolidation-migration/handoff.md).
- [Risk-findings PR area](projects/netsec-automation/shared/risk-findings/README.md) — placeholder for the supplied risk document and new findings.

### Third-party environments (separate from automation)

- AWS: [Resource Gateway / Resy risk acceptance](third-party-environments/aws/resource-gateway-resy/README.md), [App-ID preview/content-update remediation](third-party-environments/aws/app-id-content-update-remediation/README.md).
- GCP: [Tock exception](third-party-environments/gcp/tock-exception/README.md), [NGFW POC](third-party-environments/gcp/ngfw-poc/README.md).

## Lightweight handoff review

In topic directories, `README.md` is the actual explanation/process document (some are still outlines). `handoff.md` is only the short acceptance/rejection **decision record**, not another explanation. Cloud/project index READMEs are navigation/scope stubs. Architecture proposes it; NSE accepts the stated scope or requests changes/rejects with reasons for Architecture to address. Keep a short dated decision history with the reviewed revision and responsibility/exclusions. Merging a draft is not acceptance.

Use [the decision template](templates/handoff.md). Review the actual process/phase being handed over. Keep current scope, future work and external dependencies distinct. Do not turn every mentioned component into another document, or require future systems/other teams' runbooks to exist before accepting a narrower task. A future phase extends scope only when explicitly proposed.

Operational acceptance does not accept business/security risk or approve production changes. Maintain cloud-specific topics without mirroring irrelevant AWS/GCP folders. Link existing references and use placeholders without inventing facts.

[Document hierarchy and writing status](DOCUMENTATION-STATUS.md). All packets currently remain Draft; refine one topic at a time.
