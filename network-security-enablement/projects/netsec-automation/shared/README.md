# NetSec Automation — current-phase overview and QE support

**Draft for review.** The automation project is partway through a phased delivery. This document covers the support slice being handed to Network Security Enablement (NSE), not the completed target architecture. [Project index](../README.md).

## What is being handed over now

NSE will provide troubleshooting support during agreed IST hours for QE-raised defects across **both AWS and GCP and all NetSec Automation patterns**. The pattern spreadsheet distinguishes implemented/current behavior from planned work; coverage for diagnosis does not imply every target-state control is already delivered. NSE helps identify application/test configuration problems, missing platform prerequisites and suspected automation defects. NSE helps QE and the responsible application/platform operations teams resolve their issues, and routes suspected architecture or service-catalog defects to **NSAE — Network Security Architecture and Engineering** with available diagnostic evidence.

NSE also records suspected gaps in expected automation controls and assists AFT Operations with planned native-firewall consolidation under the [separate consolidation/migration process](../aws/processes/security-group-consolidation-migration/README.md).

## Phase and ownership boundaries

- Coverage includes all automation patterns across both clouds. Current-phase status describes what should exist now; a missing or incomplete pattern can be diagnosed/escalated without assuming its future controls already exist.
- **Verdicting has not been implemented yet.** Verdict-engine operation, diagnostic logs, acceptance tests and runbooks are not requirements for this handoff.
- **Gatekeeper is not managed by NSAE/NSE under this handoff.** It is platform context/an external dependency, not a new operations deliverable. When relevant, route platform-owned behavior to its owner; do not create Gatekeeper administration documentation here.
- Service-catalog ownership and the full automation lifecycle are deferred. NSAE continues architecture/catalog remediation during development.
- Third-party environments are not currently included in automation; their separately requested documentation remains separate.
- A later phase can extend the documented support scope. Planned features and other teams' dependencies are not missing deliverables for the current phase.

## Architecture context (current versus intended)

Primary controls are the main source-side egress segmentation controls; secondary/transitive controls provide downstream environment/service-port policy plumbing. For patterns included in the supplied flow sheet, ingress is described as allowed by the relevant SG/GCP firewall configuration because the main segmentation decision is at source egress. This describes the pattern configuration, not universal vendor defaults.

- **Lambda to on-premises:** the described primary control is custom intent-driven SG egress; downstream Palo Alto/Illumio policy plumbing is described through CRE. Exact implemented scope comes from the current-phase sheet, not this conceptual example.
- **Kubernetes declaration model:** EKS uses `ServiceEntry`; GKE uses Cilium network-policy entries. Centralized verdicting is a future part of the model, not an existing support dependency. Gatekeeper declaration constraints (such as namespace limits and wildcard restrictions) are context only; Gatekeeper is not the verdict engine and its operation is not transferred here.
- **GCP intra-cloud example:** GCP Platform Services created service/workload IP containers at NetSec's request to constrain new NLB resources to predictable IP space. Combined with GKE source tags, these support deterministic firewall templates. Example tags are `gkeusc1-600001725-e1` and `gkeuse4-600001725-e1`; the described rule permits the tagged central/east E1 clusters to reach the GKE INLB container on egress port 443. Sentinel and organization policies enforce the container-planning strategy; implementation PR links can be added below. This does not create a separate platform-policy operations handoff.
- In-scope on-premises sources are described as on-premises cloud Kubernetes workloads; service entries/verdicting are part of the intended design, not proof that all future controls are implemented now.

## NSE expectations and troubleshooting route

Use the cloud guides: [AWS troubleshooting](../aws/troubleshooting.md) and [GCP troubleshooting](../gcp/troubleshooting.md). This project page holds the shared expectations; each guide holds the applicable troubleshooting procedure.

NSE diagnoses and coordinates fixes. NSE may also help requestors complete forms and implement individual access through the normal authorized process when the request meets **NetSec Standard Tech 08.11** and has an appropriate business justification. **TODO: standard and existing request-process links.** This does not confer blanket catalog/template change authority.

When access is missing from an automation pattern/service catalog, particularly CRE-based policy plumbing, escalate to NSAE. A catalog change can have broad inherited impact and must not be handled as a one-time request. NSE supplies the pattern context and available evidence; NSAE handles the architectural/catalog decision and remediation coordination. Full service-catalog ownership remains deferred.

## References to add when available

- **TODO: pattern/control-placement spreadsheet covering both clouds and all patterns**, including implemented versus planned status.
- **TODO: CRE policy-plumbing table/spreadsheet** for the applicable scope.
- **TODO: Sentinel / organization-policy implementation PRs** for the GCP container strategy (references, not new runbooks).
- **TODO: NSAE-provided risk document**, linked from the existing risk-findings area.
- **TODO: practical support details** — agreed IST window, QE/NSAE/AFT/platform routing and relevant existing diagnostic links/access for patterns actually handed over.

These are links/fields in this document, not a new document backlog or a global project-completion checklist. Record any material limitation in the applicable handoff decision; future capabilities do not need to exist before a narrower current-phase handoff can be accepted.
