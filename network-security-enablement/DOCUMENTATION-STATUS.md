# Document hierarchy and actual writing status

All packets are Draft/unaccepted. A file existing does not mean its content is filled in. Review substantive content one document at a time; the inventory is not a future-state delivery checklist.

## File roles

- **Topic README:** actual explanation or process, unless explicitly labeled an index/scope stub.
- **Cloud/project index README:** short navigation/scope text, not a separate completed handoff explanation.
- **handoff.md:** short acceptance/rejection decision record only. All nine records are scaffolds with no decisions; they are not additional technical explanations.

## Hierarchy

```text
network-security-enablement/
├── README.md                         navigation + review workflow
├── DOCUMENTATION-STATUS.md           this inventory
├── templates/handoff.md              decision-record template
├── projects/netsec-automation/
│   ├── README.md                     project index
│   ├── shared/
│   │   ├── README.md                 overview + NSE expectations [SUBSTANTIVE DRAFT]
│   │   ├── cre/                      explanation [OUTLINE]
│   │   └── risk-findings/            intake + template [SCAFFOLD]
│   ├── aws/
│   │   ├── README.md                 cloud scope/navigation stub
│   │   ├── troubleshooting.md        procedure [SUBSTANTIVE DRAFT]
│   │   ├── intent-driven-sg-egress/   explanation [OUTLINE]
│   │   └── processes/security-group-consolidation-migration/
│   │                                 process [OUTLINE]
│   └── gcp/
│       ├── README.md                 cloud scope/navigation stub
│       └── troubleshooting.md        procedure [SUBSTANTIVE DRAFT]
└── third-party-environments/
    ├── aws/
    │   ├── resource-gateway-resy/     risk/explanation [OUTLINE]
    │   └── app-id-content-update-remediation/  process [OUTLINE]
    └── gcp/
        ├── tock-exception/           exception/explanation [OUTLINE]
        └── ngfw-poc/                 POC/explanation [OUTLINE]
```

Nine topic packets also have the decision record described above. No troubleshooting document remains at the NSE root.

## Materially drafted — start the one-at-a-time review here

1. [Automation overview and NSE expectations](projects/netsec-automation/shared/README.md): primary/transitive model, current/planned distinction, both-cloud/all-pattern support, IST support expectations, request-versus-architecture boundary and reference placeholders.
2. [AWS troubleshooting](projects/netsec-automation/aws/troubleshooting.md): application/port checks, missing AFT SG versus missing attachment, available current-phase pattern evidence, individual request versus catalog escalation, risk reporting and retest.
3. [GCP troubleshooting](projects/netsec-automation/gcp/troubleshooting.md): application checks, applicable firewall/source-tag/IP-container checks, current-phase evidence, individual request versus catalog escalation, risk reporting and retest.

These are substantive first passes based on the discussion, not fully populated or validated platform command runbooks. Actual standards/spreadsheet/log/contact links remain placeholders. Review item 1 first, then each cloud guide.

## Not materially filled in — still to author together

These files have headings plus brief context/examples; their actual workflows/details have not yet been supplied or written:

- [Continuous Registration Engine](projects/netsec-automation/shared/cre/README.md): how registration maps to downstream policy and how NSE recognizes missing catalog coverage.
- [AWS intent-driven SG egress](projects/netsec-automation/aws/intent-driven-sg-egress/README.md): the actual request/rule/attachment workflow.
- [AWS SG consolidation/migration](projects/netsec-automation/aws/processes/security-group-consolidation-migration/README.md): the actual migration/consolidation process and AFT/NSE responsibilities.
- [AWS Resource Gateway / Resy](third-party-environments/aws/resource-gateway-resy/README.md): the actual environment risk/acceptance details.
- [AWS App-ID preview/content-update remediation](third-party-environments/aws/app-id-content-update-remediation/README.md): the actual operational procedure.
- [GCP Tock exception](third-party-environments/gcp/tock-exception/README.md): the actual exception details.
- [GCP NGFW POC](third-party-environments/gcp/ngfw-poc/README.md): the actual POC scope, findings and NSE role.

## Scaffolding — do not count as completed subject documents

- Root/project/cloud indexes and this inventory: navigation, review workflow and scope summaries.
- `handoff.md` files and reusable template: decision-record structure only; reviewer details/decisions not populated.
- [Risk-findings intake](projects/netsec-automation/shared/risk-findings/README.md) and [finding template](projects/netsec-automation/shared/risk-findings/finding-template.md): submission scaffold, **not** the authoritative risk document Max will supply, and not actual assessed findings.

## Reference placeholders, not new document scope

Pattern sheet (all clouds/patterns; current/planned), CRE table, Tech 08.11 and request-process links, relevant existing implementation PRs, supplied risk document and practical support references. Add them in place as available. No verdict/Gatekeeper/platform-operations doc backlog: verdicting does not exist yet and Gatekeeper is not managed by NSAE/NSE. Full service-catalog ownership is deferred.
