# NetSec Automation — shared control-placement model

**Working draft from Architecture discussion, 2026-10-18.** Describes the intended model and reported examples, not independently validated deployment coverage, an accepted operational handoff, or executable policy. AWS and GCP acceptance remain separate. [Project index](../README.md).

## Purpose and terminology

NetSec Automation separates **primary** segmentation controls from **secondary / transitive** controls. These are roles in a traffic path, not names of particular products or claims that downstream controls perform no other security functions.

- **Primary:** the main network segmentation control, ideally closest to the source workload, enforcing permitted egress intent.
- **Secondary / transitive:** controls downstream of the primary, provisioned with environment- and service-specific port-level policy plumbing to support the permitted path.
- **Intent and verdict:** a workload/application request and its central authorization decision. Document the runtime mechanism separately from the artifact/decision that configures it.
- **IP container:** in the GCP example, a service/workload-specific address-allocation construct used to place new resources into predictable IP space and make destination-IP firewall templates deterministic. Architecture identifies Sentinel policies and organization policies as enforcement of the container-planning strategy; exact policy scope and implementation PRs are pending.

For the patterns included in the authoritative flow sheet, ingress is allowed by default in the relevant SG/GCP firewall configuration; source-side egress carries the main segmentation decision. This is the described architecture configuration, **not a statement of product defaults or a universal allow-ingress instruction**. Third-party environments are not yet included in automation. In-scope on-premises sources are described as on-premises cloud Kubernetes workloads that will also require service entries and verdicts; other on-premises sources are not implicitly covered.

## Control-placement matrix

TODO: link or upload the authoritative resource/control-placement sheet, its owner, revision, and coverage. This table captures only the examples supplied so far and is not a complete supported-resource inventory.

| Cloud / source | Destination | Primary intent/control described | Downstream provisioning described | Open validation |
| --- | --- | --- | --- | --- |
| AWS Lambda | On-premises service | Custom intent-driven SG egress rule | Planned CRE integration with Palo Alto / Illumio at account-vending scope | Scope, deployed status, source identity, permitted service/port set, lifecycle |
| AWS EKS workload | On-premises service | Developer-authored EKS `ServiceEntry` with a separate centralized verdict; Gatekeeper declaration guardrails | CRE-based downstream plumbing described at vending time | Exact verdict/runtime implementation, applicable constraints and bootstrap references |
| GCP GKE workload | On-premises service | Developer-authored GKE Cilium network-policy entry with a separate centralized verdict; Gatekeeper declaration guardrails | CRE-based downstream plumbing described at vending time | Exact verdict/runtime implementation and GCP-specific bootstrap/lifecycle references |
| GCP GKE nodes / clusters in routable network | GKE internal NLB IP container | Fleet-template firewall egress policy scoped by network tags and destination IP space; relationship to application primary controls to confirm | No separate secondary hop specified for this intra-GCP example | Allocation controls, tag governance, approved consumers/ports and environment boundaries |

## AWS example: Lambda to on-premises

Conceptual control sequence (not a verified packet-level topology):

```text
Lambda source -> intent-driven SG egress -> downstream Palo Alto / Illumio policy -> on-premises service
```

The primary policy is application-intent driven; the downstream policy is described as environmental/service-specific plumbing. CRE integration is described as planned for account-vending-level automation; do not mark it deployed without evidence.

- [Intent-driven SG egress outline](../aws/intent-driven-sg-egress/README.md)
- [Shared CRE integration outline](cre/README.md)

## EKS / GKE example: workload to on-premises

Developers use **`ServiceEntry` in EKS** and **a Cilium network-policy entry in GKE**. Gatekeeper governs aspects of both declarations, including per-namespace entry limits, wildcard restrictions and mandatory access declarations. The exact numeric limit, constraints and implementation links are TODO.

**Gatekeeper is not the verdict engine.** Declaration/admission guardrails, the separate centralized verdict, and runtime packet enforcement must be documented as distinct steps. TODO: verdict service name, decision/evidence interface and platform-specific runtime enforcement checks. Do not use Gatekeeper admission success as evidence of traffic authorization or successful connectivity.

CRE supplies downstream Palo Alto / Illumio plumbing at the applicable vending/bootstrap event. **TODO: Architecture-provided CRE policy-plumbing/lifecycle table or spreadsheet** for exact scope, identities, events and component references.

**Conditional technical constraint:** if “service entry” means Istio `ServiceEntry`, neither that registry artifact nor `REGISTRY_ONLY` alone establishes an outbound security boundary. Document the deployed enforcement and traffic-capture constraints before describing a verdict as guaranteed segmentation. [Istio security guidance](https://istio.io/latest/docs/ops/best-practices/security/#understand-traffic-capture-limitations).

## GCP example: tags plus service IP containers

Per Architecture, the GCP Platform Services team created service/workload IP containers at NetSec's request. The example describes CARID `600001725` in network tags applied to GKE node pools across the GCP routable network, including:

- `gkeusc1-600001725-e1`
- `gkeuse4-600001725-e1`

The described template allows the tagged central/east E1 GKE clusters to send egress TCP 443 traffic to the GKE internal-NLB IP container. Confirm protocol, exact resource identity, scope and deployed rule references before using this as an implementation specification. The meaning and isolation boundary of `e1` are not yet documented.

The container's purpose is to constrain new NLB deployments to designated address space, enabling predictable/static firewall rules as resources are added. The firewall supplies runtime traffic enforcement; the container supplies address grouping/allocation structure. Architecture identifies **Sentinel policies and organization policies** as enforcing the container-planning strategy. **TODO: implementation/enforcement PR links**, including which resources, allocation constraints, identities and deployment paths each policy covers. Document source-tag governance separately unless those same policies demonstrably cover it.

## Operational handoff and remaining reference inputs

The [initial support handoff](support-model.md) covers NSE troubleshooting QE defects during agreed IST support hours, coordination with application/platform/AFT owners, and escalation of suspected design/catalog defects to **Network Security Architecture and Engineering (NSAE)**. It does not transfer the service catalog. NSE also reports potential control gaps and assists planned native-firewall consolidation under its separate process.

The current handoff is support-focused; comprehensive future service ownership is not a prerequisite for drafting it. Complete these operator references before calling the support procedure execution-ready:

- **TODO: authoritative supported-pattern/control-placement spreadsheet**, owner and revision.
- **TODO: CRE policy-plumbing/lifecycle spreadsheet**, including environment/service/port and identity mapping.
- **TODO: Sentinel / organization-policy enforcement PRs** for container planning and any applicable tag governance.
- **TODO: verdict-engine and Gatekeeper constraint/evidence references**, including namespace limit values and runtime checks.
- **TODO: NSAE-provided risk document**, linked from [risk-findings intake](risk-findings/README.md).
- **TODO: exact IST coverage, QE/NSAE/AFT queues, access and diagnostic links**.
