# Documentation inventory and review queue

Snapshot: 2026-10-18. All documents in this area are Draft and unaccepted; this inventory distinguishes writing maturity, not approval status. Refine one document at a time.

- **Draft:** substantive working text exists; references, review and validation remain.
- **Outline:** file exists, but most implementation/process detail still needs authoring.
- **Template / scaffold:** structure exists to populate during actual submissions/reviews.
- **Not created:** proposed follow-on reference, not an existing file or an adopted requirement for this initial handoff.

## Repository hierarchy

`handoff.md` records exist alongside all nine topic packets (AWS/GCP project support, AWS SG egress, AWS migration, shared CRE, and four third-party topics). They are review scaffolds, not completed acceptance decisions. Shared support/control-model/runbook pages are referenced by cloud handoffs rather than given duplicate acceptance records.

```text
network-security-enablement/
├── README.md                                  [navigation / proposed review workflow]
├── DOCUMENTATION-STATUS.md                    [this inventory]
├── templates/
│   └── handoff.md                             [template]
├── projects/
│   └── netsec-automation/
│       ├── README.md                          [project navigation]
│       ├── shared/
│       │   ├── control-model.md               [draft]
│       │   ├── support-model.md               [draft]
│       │   ├── qe-defect-triage.md             [draft]
│       │   ├── cre/
│       │   │   ├── README.md                  [outline]
│       │   │   └── handoff.md                 [scaffold]
│       │   └── risk-findings/
│       │       ├── README.md                  [draft intake; authoritative risk doc pending]
│       │       └── finding-template.md        [template]
│       ├── aws/
│       │   ├── README.md                      [draft support handoff]
│       │   ├── handoff.md                     [scaffold]
│       │   ├── intent-driven-sg-egress/
│       │   │   ├── README.md                  [outline]
│       │   │   └── handoff.md                 [scaffold]
│       │   └── processes/
│       │       └── security-group-consolidation-migration/
│       │           ├── README.md              [outline]
│       │           └── handoff.md             [scaffold]
│       └── gcp/
│           ├── README.md                      [draft support handoff]
│           └── handoff.md                     [scaffold]
└── third-party-environments/
    ├── aws/
    │   ├── resource-gateway-resy/
    │   │   ├── README.md                      [outline]
    │   │   └── handoff.md                     [scaffold]
    │   └── app-id-content-update-remediation/
    │       ├── README.md                      [outline]
    │       └── handoff.md                     [scaffold]
    └── gcp/
        ├── tock-exception/
        │   ├── README.md                      [outline]
        │   └── handoff.md                     [scaffold]
        └── ngfw-poc/
            ├── README.md                      [outline]
            └── handoff.md                     [scaffold]
```

## Created: substantive drafts to review

1. [Shared control model](projects/netsec-automation/shared/control-model.md): primary/transitive roles, examples, declaration types, Gatekeeper/verdict distinction, flow-sheet and enforcement references.
2. [Initial support scope](projects/netsec-automation/shared/support-model.md): IST-hours QE troubleshooting, NSE/NSAE/platform boundaries, deferred catalog ownership and consolidation assistance.
3. [QE defect triage](projects/netsec-automation/shared/qe-defect-triage.md): diagnostic flow, configuration/platform checks, NSAE escalation and evidence.
4. [AWS support handoff](projects/netsec-automation/aws/README.md) and [GCP support handoff](projects/netsec-automation/gcp/README.md): cloud-specific context, shared support scope and readiness criteria.
5. [Risk-findings intake](projects/netsec-automation/shared/risk-findings/README.md) and [finding template](projects/netsec-automation/shared/risk-findings/finding-template.md): repository PR route; NSAE risk document/review contacts not supplied yet.

## Created: outlines still needing substantive authoring

1. [Shared CRE integration](projects/netsec-automation/shared/cre/README.md).
2. [AWS intent-driven SG egress](projects/netsec-automation/aws/intent-driven-sg-egress/README.md).
3. [AWS SG consolidation/migration](projects/netsec-automation/aws/processes/security-group-consolidation-migration/README.md).
4. [AWS Resource Gateway / Resy risk acceptance](third-party-environments/aws/resource-gateway-resy/README.md).
5. [AWS App-ID preview/content-update remediation](third-party-environments/aws/app-id-content-update-remediation/README.md).
6. [GCP Tock exception](third-party-environments/gcp/tock-exception/README.md).
7. [GCP NGFW POC](third-party-environments/gcp/ngfw-poc/README.md).

## Not yet created: candidate focused references

These are likely follow-on references implied by the described architecture, not new agreed project deliverables. Decide whether each warrants its own file or belongs within an existing guide as authoring proceeds. Do not duplicate authoritative platform/vendor docs.

- **Shared verdict-engine troubleshooting reference:** decision/request/evidence flow, denial versus execution failure, logs and ownership. Gatekeeper is not this engine.
- **AWS EKS declaration / Gatekeeper diagnostics:** ServiceEntry submission, constraints, namespace limits and failure evidence.
- **GCP GKE declaration / Gatekeeper diagnostics:** Cilium network-policy submission, constraints, namespace limits and failure evidence.
- **GCP IP-container and fleet firewall reference:** allocation strategy, source tags, rule/template mapping, Sentinel/org-policy PRs and support checks.
- **Authoritative automation risk document:** Max will supply it; the intake/template is already created. Link or incorporate it rather than inventing a replacement risk policy.

**Deferred:** full service-catalog ownership/maintenance handoff is later work, not required for the current troubleshooting assignment.

## Inputs to attach or link, not necessarily new documents

- Supported-pattern / primary-transitive control-placement spreadsheet (owner and revision).
- CRE policy-plumbing and lifecycle table/spreadsheet.
- Sentinel and organization-policy enforcement PRs for GCP container planning.
- Actual declaration/verdict component references, constraint values, logs and diagnostic links.
- Exact IST hours/days, start date, rota, QE/NSAE/AFT/platform contacts, queues, access and escalation expectations.
- Walkthrough/test evidence and actual decisions in each applicable handoff record.

## Suggested refinement sequence

Start with support scope, then control model and defect triage; populate cloud-specific differences and risk reporting next. Expand SG egress, CRE and consolidation as their procedures/references become available. Review the four third-party packets individually and separately from automation coverage. This is a suggested order, not a commitment that all subjects must be completed before accepting the initial support scope.
