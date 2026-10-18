# NetSec Automation — shared control-placement model

**Working draft from Architecture discussion, 2026-10-18.** Describes the intended model and reported examples, not independently validated deployment coverage, an accepted operational handoff, or executable policy. AWS and GCP acceptance remain separate. [Project index](../README.md).

## Purpose and terminology

NetSec Automation separates **primary** segmentation controls from **secondary / transitive** controls. These are roles in a traffic path, not names of particular products or claims that downstream controls perform no other security functions.

- **Primary:** the main network segmentation control, ideally closest to the source workload, enforcing permitted egress intent.
- **Secondary / transitive:** controls downstream of the primary, provisioned with environment- and service-specific port-level policy plumbing to support the permitted path.
- **Intent and verdict:** a workload/application request and its central authorization decision. Document the runtime mechanism separately from the artifact/decision that configures it.
- **IP container:** in the GCP example, a service/workload-specific address-allocation construct used to place new resources into predictable IP space and make destination-IP firewall templates deterministic. Its implementation and allocation enforcement remain to be documented.

Architecture describes ingress as generally allowed by default because the source-side egress control carries the main segmentation decision. This is a design convention being described, **not a statement of AWS/GCP product defaults**. The exact applicable boundaries and inbound exceptions are unresolved; do not translate this into universal allow-ingress rules.

## Control-placement matrix

TODO: link or upload the authoritative resource/control-placement sheet, its owner, revision, and coverage. This table captures only the examples supplied so far and is not a complete supported-resource inventory.

| Cloud / source | Destination | Primary intent/control described | Downstream provisioning described | Open validation |
| --- | --- | --- | --- | --- |
| AWS Lambda | On-premises service | Custom intent-driven SG egress rule | Planned CRE integration with Palo Alto / Illumio at account-vending scope | Scope, deployed status, source identity, permitted service/port set, lifecycle |
| AWS EKS workload | On-premises service | App-authored service entry with a centralized verdict; actual runtime enforcement to identify | CRE-based downstream plumbing described at vending time | Mesh/product, verdict authority, denied/bypass paths, exact bootstrap event |
| GCP GKE workload | On-premises service | App-authored service entry with a centralized verdict; actual runtime enforcement to identify | CRE-based downstream plumbing described at vending time | Same enforcement questions; identify GCP project/cluster provisioning event rather than assuming AWS account semantics |
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

Application developers write a service entry that receives a centralized verdict. CRE supplies downstream Palo Alto / Illumio plumbing at the applicable vending/bootstrap event. The service-entry implementation, the verdict service's authoritative name, and the actual runtime enforcement/no-bypass mechanism are still to be identified.

**Conditional technical constraint:** if “service entry” means Istio `ServiceEntry`, neither that registry artifact nor `REGISTRY_ONLY` alone establishes an outbound security boundary. Document the deployed enforcement and traffic-capture constraints before describing a verdict as guaranteed segmentation. [Istio security guidance](https://istio.io/latest/docs/ops/best-practices/security/#understand-traffic-capture-limitations).

## GCP example: tags plus service IP containers

Per Architecture, the GCP Platform Services team created service/workload IP containers at NetSec's request. The example describes CARID `600001725` in network tags applied to GKE node pools across the GCP routable network, including:

- `gkeusc1-600001725-e1`
- `gkeuse4-600001725-e1`

The described template allows the tagged central/east E1 GKE clusters to send egress TCP 443 traffic to the GKE internal-NLB IP container. Confirm protocol, exact resource identity, scope and deployed rule references before using this as an implementation specification. The meaning and isolation boundary of `e1` are not yet documented.

The container's purpose is to constrain new NLB deployments to designated address space, enabling predictable/static firewall rules as resources are added. The firewall supplies runtime traffic enforcement; the container supplies address grouping/allocation structure. TODO: identify what actually forces placement into that space, who can change membership or tags, and how out-of-container deployments are blocked/detected.

## Questions required before operational acceptance

1. What enforces each approved/denied verdict at runtime, and which traffic can bypass it (unmeshed/direct-IP/unsupported protocols or resource types)?
2. Which ingress paths rely on this source-egress model, and how are unmanaged sources, third-party sources, internet ingress, and missing primary controls handled?
3. What exact events provision CRE policy in each cloud, what identity does each downstream product see, and how are updates, deletion, drift, retries, and partial failures handled?
4. Who governs IP allocation and source tags, and what stops another resource/environment from inheriting fleet access or a deployment landing outside the expected IP space?
5. Which capabilities are live, planned, or partially deployed, and who owns the normal and failed operation of each component?

For each supported flow, record source identity/scope, destination/port, intent authority, primary runtime enforcement, secondary controls, bootstrap/change/delete triggers, evidence, and responsible teams in or alongside the authoritative placement sheet.
