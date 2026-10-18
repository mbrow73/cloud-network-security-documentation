# NetSec Automation — overview and NSE expectations

**Draft.** NetSec Automation is being delivered in phases. This handoff covers NSE support while the project is in progress. [Project index](../README.md).

## NSE support expectations

NSE provides troubleshooting support during agreed IST hours for QE-raised defects across **both AWS and GCP and all automation patterns**. The pattern sheet identifies implemented functionality and planned work. NSE helps requestors/application/platform teams resolve configuration or prerequisite issues and escalates suspected architecture or service-catalog defects to **NSAE — Network Security Architecture and Engineering**.

NSE also reports gaps in expected controls and assists AFT Operations with planned native-firewall consolidation under the [separate consolidation/migration process](../aws/processes/security-group-consolidation-migration/README.md).

## Primary and transitive controls

**Primary controls** provide source-side egress segmentation, ideally close to the workload. **Secondary/transitive controls** provide downstream environment- and service-port policy plumbing.

For patterns included in the flow sheet, the relevant SG/GCP firewall configuration allows ingress because the main segmentation decision occurs at source egress. This applies to those patterns, not every cloud flow.

- **Lambda to on-premises:** custom intent-driven SG egress is the primary control. CRE provisions downstream Palo Alto/Illumio policy plumbing. On Palo Alto, CRE registers source subnet CIDR/tag mappings that populate address groups used by existing policy scaffolding; [the CRE explanation](cre/README.md) separates registration failures from missing policy coverage. The pattern sheet identifies the implementation status for each flow.
- **Kubernetes:** EKS uses `ServiceEntry`; GKE uses Cilium network-policy entries. Centralized verdicting is planned but not implemented. Gatekeeper is owned by Cloud Security and provides declaration constraints such as namespace limits and wildcard restrictions; it is not the verdict engine.
- **On-premises sources:** the in-scope sources are on-premises cloud Kubernetes workloads. Service entries/verdicting are part of the intended architecture; implementation status is recorded in the pattern sheet.

## GCP service IP containers

GCP Platform Services created IP containers for **all services included in the GCP scope of Network Automation**, not only NLBs or VIPs. Containers constrain new service deployments to designated IP space so firewall templates can use predictable destination ranges. Sentinel and organization policies enforce this allocation strategy.

GKE source tags, including `gkeusc1-600001725-e1` and `gkeuse4-600001725-e1`, identify the central/east E1 clusters for the fleet template. For example, tagged GKE clusters can reach the GKE internal-NLB container on egress port 443. This is one use of the broader service-container strategy.

- **Service IP-container plan:** TODO: insert spreadsheet/document link.
- **Sentinel enforcement:** TODO: insert policy PR/document link.
- **Organization-policy enforcement:** TODO: insert policy PR/document link.

## Handling QE defects and missing access

Use the project workflows: [AWS QE defect handling](../aws/qe-defect-handling.md) and [GCP QE defect handling](../gcp/qe-defect-handling.md). They link to the cloud-level troubleshooting guides and determine what to resolve, route as a request, or escalate.

NSE may help requestors complete **request forms to provision missing access** and implement that access through the normal authorized process when it meets **NetSec Standard Tech 08.11** and has an appropriate business justification. This does not grant blanket catalog/template change authority.

- [AWS standard SG requests](../../../aws/requests/standard-security-group-requests.md) — placeholder.
- [GCP standard routable firewall-rule requests](../../../gcp/requests/standard-routable-firewall-rule-requests.md) — placeholder.
- **NetSec Standard Tech 08.11:** TODO: insert standard link.

When missing access requires a shared automation/service-catalog change, especially CRE policy plumbing, NSE escalates it to NSAE. Such changes can have a broad blast radius and are not individual access requests. NSAE owns the architecture/catalog decision and remediation coordination.

## Scope boundaries

- Verdicting is future work, not a current operational dependency.
- Gatekeeper is owned by Cloud Security.
- Full service-catalog ownership is deferred.
- Third-party environments are not currently included in automation. Their standard-request guides and other topic documents are separate.
- Later phases can extend responsibilities explicitly; future capabilities are not prerequisites for accepting the current support assignment.

## References

- **AWS/GCP pattern and control-placement sheet (current/planned):** TODO: insert spreadsheet link.
- **CRE policy-plumbing table:** TODO: insert table/document link.
- **Risk document:** TODO: insert document link in the [risk-findings area](risk-findings/README.md).
- **IST support window / QE, NSAE, AFT and platform contacts:** TODO: insert schedule/contact links.
