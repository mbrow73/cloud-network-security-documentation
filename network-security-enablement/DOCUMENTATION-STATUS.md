# Document hierarchy and writing status

All packets remain Draft; none is accepted. This is a writing inventory, not a project-completion checklist. The automation project is mid-delivery and phased.

```text
network-security-enablement/
├── README.md                         navigation and review process
├── DOCUMENTATION-STATUS.md           this inventory
├── templates/handoff.md              short decision template
├── troubleshooting/README.md         general AWS/GCP diagnosis + request routing (draft)
├── projects/netsec-automation/
│   ├── README.md                     project index
│   ├── shared/
│   │   ├── README.md                 overview + project support expectations (draft)
│   │   ├── cre/                      Continuous Registration Engine explanation (outline)
│   │   └── risk-findings/            supplied-risk-doc placeholder + PR template
│   ├── aws/
│   │   ├── README.md                 current-phase support (draft)
│   │   ├── intent-driven-sg-egress/   requested outline
│   │   └── processes/security-group-consolidation-migration/
│   │                                 requested outline
│   └── gcp/README.md                 current-phase support (draft)
└── third-party-environments/
    ├── aws/
    │   ├── resource-gateway-resy/     requested outline
    │   └── app-id-content-update-remediation/  requested outline
    └── gcp/
        ├── tock-exception/           requested outline
        └── ngfw-poc/                 requested outline
```

Each of the nine topic packets also has a short `handoff.md` decision record. The shared overview and risk intake support those packets, not separate handoff programs.

## Existing drafts to refine

- [General AWS/GCP troubleshooting](troubleshooting/README.md): shared procedure, Tech 08.11/request boundary and architecture escalation, linked from project expectations.

- [Shared overview and current-phase QE support](projects/netsec-automation/shared/README.md): architecture context, phase boundary and support expectations for both clouds/all patterns; links the root troubleshooting procedure rather than duplicating it.
- [AWS](projects/netsec-automation/aws/README.md) and [GCP](projects/netsec-automation/gcp/README.md): concise cloud support context.
- [Risk-findings intake](projects/netsec-automation/shared/risk-findings/README.md) and [template](projects/netsec-automation/shared/risk-findings/finding-template.md): placeholder for Max's supplied risk document and finding PRs.

## Requested outlines still to fill in, one at a time

- [Continuous Registration Engine (CRE)](projects/netsec-automation/shared/cre/README.md): how policy plumbing works and how to recognize a missing catalog pattern.
- [AWS intent-driven SG egress](projects/netsec-automation/aws/intent-driven-sg-egress/README.md).
- [AWS SG consolidation/migration](projects/netsec-automation/aws/processes/security-group-consolidation-migration/README.md).
- [AWS Resource Gateway / Resy](third-party-environments/aws/resource-gateway-resy/README.md).
- [AWS App-ID preview/content-update remediation](third-party-environments/aws/app-id-content-update-remediation/README.md).
- [GCP Tock exception](third-party-environments/gcp/tock-exception/README.md).
- [GCP NGFW POC](third-party-environments/gcp/ngfw-poc/README.md).

## Inputs, not additional document deliverables

Add the current-phase pattern spreadsheet, CRE table, relevant implementation PRs, risk document and practical existing support details where applicable. Missing future-state material is not automatically a blocker to the current support slice.

**Not a backlog:** no new verdict-engine, Gatekeeper, Cilium platform-operations or IP-container administration documents are requested. Verdicting does not exist yet; Gatekeeper is not managed by NSAE/NSE. Full service-catalog ownership is later work. External component references can be linked if useful without creating ownership or a new handoff requirement.
