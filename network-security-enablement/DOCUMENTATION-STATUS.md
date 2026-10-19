# Document hierarchy and actual writing status

All packets are Draft/unaccepted. A file existing does not mean its content is filled in. Review substantive content one document at a time; the inventory is not a future-state delivery checklist.

## File roles

- **Topic README:** actual explanation or process, unless explicitly labeled an index/scope stub.
- **Cloud/project index README:** short navigation/scope text, not a separate completed handoff explanation.
- **handoff.md:** short acceptance/rejection decision record only. All nine records are scaffolds with no decisions; they are not additional technical explanations.

## Hierarchy

```text
network-security-enablement/
├── README.md / DOCUMENTATION-STATUS.md / templates/handoff.md
├── aws/
│   ├── troubleshooting.md                      general technical checks [DRAFT]
│   └── requests/
│       ├── standard-security-group-requests.md [PLACEHOLDER]
│       └── third-party-standard-requests.md    [PLACEHOLDER]
├── gcp/
│   ├── troubleshooting.md                      general technical checks [DRAFT]
│   └── requests/
│       ├── standard-routable-firewall-rule-requests.md [PLACEHOLDER]
│       └── third-party-standard-requests.md    [PLACEHOLDER]
├── projects/netsec-automation/
│   ├── README.md                               index
│   ├── shared/
│   │   ├── README.md                           overview + expectations [DRAFT]
│   │   ├── cre/                                registration/scaffolding [DRAFT]
│   │   └── risk-findings/                       intake/template [SCAFFOLD]
│   ├── aws/
│   │   ├── README.md                           scope/navigation stub
│   │   ├── qe-defect-handling.md                project decisions [DRAFT]
│   │   ├── intent-driven-sg-egress/             [OUTLINE]
│   │   └── processes/security-group-consolidation-migration/ [OUTLINE]
│   └── gcp/
│       ├── README.md                           scope/navigation stub
│       └── qe-defect-handling.md                project decisions [DRAFT]
└── third-party-environments/
    ├── aws/
    │   ├── resource-gateway-resy/               [OUTLINE]
    │   └── app-id-content-update-remediation/   [OUTLINE]
    └── gcp/
        ├── tock-exception/                     [OUTLINE]
        └── ngfw-poc/                           [OUTLINE]
```

Nine topic packets also have a short decision record. General cloud troubleshooting contains technical checks; project QE workflows link it and select the resolution/escalation path. They do not duplicate the cloud procedure.

## Materially drafted — one-at-a-time review

1. [Automation overview and NSE expectations](projects/netsec-automation/shared/README.md): control model, all in-scope GCP services' IP containers, phased scope, both-cloud/all-pattern assignment and missing-access request boundary.
2. [AWS QE defect handling](projects/netsec-automation/aws/qe-defect-handling.md): defect intake, cloud-guide link, resolve/request/escalate decisions and retest.
3. [GCP QE defect handling](projects/netsec-automation/gcp/qe-defect-handling.md): the same project decision framework with GCP context.
4. [General AWS troubleshooting](aws/troubleshooting.md): cross-platform endpoint and NR/R/NAT intake, NetSec control paths including EWP web egress (EWP externally owned), ENI/SG and module-version/deployed-rule checks, ENI-independent CloudWatch query, SIEM/local logs, scoped Palo Alto PCAP, delta-drop counters, CRE and evidence-based disposition. Vendor references checked; internal links and unlisted paths remain TODOs, and procedures are not live-environment validated.
5. [General GCP troubleshooting](gcp/troubleshooting.md): common application and applicable firewall/tag/service-container checks and findings.

6. [CRE registration and policy-scaffolding explanation](projects/netsec-automation/shared/cre/README.md): proprietary API, AFT/platform triggers, dynamic IP/tag membership, Hydra example, response evidence and registration-versus-policy diagnosis. Resource IP/subnet CIDR registration, source/destination group roles, vending and application-onboarding triggers, data-service/Cloud Run connector examples, explicit API success/error handling, firewall verification and CRE support escalation are filled in. Supporting-reference links and internal contact names remain TODOs.

These are working first passes, not validated command runbooks. Links remain named placeholders. The project-specific guides were split from the original cloud troubleshooting drafts, not created as a new component operations program.

## Not materially filled in — still to author together

These files have headings plus brief context/examples; their actual workflows/details have not yet been supplied or written:

- [AWS intent-driven SG egress](projects/netsec-automation/aws/intent-driven-sg-egress/README.md): the actual request/rule/attachment workflow.
- [AWS SG consolidation/migration](projects/netsec-automation/aws/processes/security-group-consolidation-migration/README.md): the actual migration/consolidation process and AFT/NSE responsibilities.
- [AWS Resource Gateway / Resy](third-party-environments/aws/resource-gateway-resy/README.md): the actual environment risk/acceptance details.
- [AWS App-ID preview/content-update remediation](third-party-environments/aws/app-id-content-update-remediation/README.md): the actual operational procedure.
- [GCP Tock exception](third-party-environments/gcp/tock-exception/README.md): the actual exception details.
- [GCP NGFW POC](third-party-environments/gcp/ngfw-poc/README.md): the actual POC scope, findings and NSE role.

## Explicitly requested new placeholders — author later

After the existing document review and outstanding automation topics:

- [AWS standard security-group requests](aws/requests/standard-security-group-requests.md).
- [GCP standard routable firewall-rule requests](gcp/requests/standard-routable-firewall-rule-requests.md).
- [AWS third-party standard requests](aws/requests/third-party-standard-requests.md).
- [GCP third-party standard requests](gcp/requests/third-party-standard-requests.md).

These are short placeholder files, not completed procedures or extra current-phase acceptance requirements.

## Scaffolding and remaining references

Indexes/cloud scope summaries, nine handoff decision records and templates are scaffolding. [Risk intake](projects/netsec-automation/shared/risk-findings/README.md) is not the authoritative risk document. Spreadsheet, Tech 08.11, policy PR and contact links remain placeholders to insert in place. No verdict/Gatekeeper/platform-operations doc backlog; catalog ownership remains deferred.

## Supporting-document convention

Keep named `TODO:` placeholders for supporting documents, forms and links. These are intended for Max's work agent to find and populate from supplied source material. Standard missing-access request instructions live in the general cloud troubleshooting guides; project QE workflows link to them and retain project-specific resolve/escalate decisions. Gatekeeper is owned by Cloud Security.
