# ADR: GCP Internet Ingress Automation for Public GKE Applications

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-06-30 |
| **Proposed by** | Maximilian Browne |
| **Stakeholders** | Network Security, Cloud Platform, AppSec, Edge/WAF/Bot, App Teams, Security Leadership |

---

## Context

Public GKE application ingress currently follows this chain:

```text
Public DNS / GTM app record
→ Imperva
→ Cequence SaaS bot mitigation
→ external NLB (XNLB) fronting Palo Alto firewalls
→ Palo Alto DNAT / SNAT
→ backend GKE internal load balancer
→ GKE application
```

Current onboarding has two major manual pain points:

1. **New internet-capable GKE clusters require XNLB / public IP / Palo Alto mapping work**, and NetSec may not have a clear signal when that work is needed.
2. **Each new app requires adding the app CNAME/FQDN to the Palo Alto custom URL category for the target cluster path.**

Security leadership also wants vulnerability scan completion to become part of internet app admission.

This is not just a scanner-to-firewall integration. It is an internet ingress lifecycle problem across GTM/DDI, Imperva, Cequence, Palo Alto, GKE platform, AppSec scanning, and observability.

## Decision

Use **Option C: Network Security Internet Application Repository** as the near-term automation path.

Keep Option A as the current enforcement model and Option B as a possible long-term target.

| Option | Recommendation | Summary |
|--------|----------------|---------|
| **A. Automate Palo Alto URL categories** | Current enforcement model | Keep app-level allowlisting on Palo Alto, but automate category membership after scan/approval. |
| **B. Move admission to GTM/Cequence** | Long-term candidate only | Palo allows edge NATs to cluster VIPs; GTM/Cequence controls app publication. Not safe until origin trust and source-of-truth gaps are solved. |
| **C. NetSec internet app repo** | **Recommended near-term** | Create a NetSec-owned GitOps repo for cluster ingress bootstrap, app admission records, XNLB provisioning, and PAN-OS Terraform automation. Builds the missing source of truth incrementally. |

## Recommended Near-Term Pattern: Option C

Create a repository such as:

```text
netsec-internet-apps/
├── clusters/
├── apps/
├── terraform/
└── .github/workflows/
```

### Cluster intent record example

The platform/requestor provides only the backend target and required metadata. NetSec automation derives Palo Alto object names, device group, URL category, NAT/security rule names, and XNLB forwarding-rule names from standards. Requestors should not provide firewall object names.

```yaml
cluster_id: gke-prod-usw2-01
environment: prod
requestor: gke-platform-team
backend:
  gke_ilb_ip: 10.10.20.15
  gke_ilb_name: ilb-gke-prod-usw2-01
  gcp_project: app-prod-host-project
netsec_ingress:
  # derived by automation from cluster_id, environment, region, and naming standards
  xnlb_forwarding_rule: generated_by_pipeline
  xnlb_vip: allocated_by_terraform
  palo_device_group: generated_by_pipeline
  palo_nat_rule: generated_by_pipeline
  palo_security_rule: generated_by_pipeline
  palo_url_category: generated_by_pipeline
allowed_edge_sources:
  - imperva_prod_nat
  - cequence_prod_nat
gtm_onboarding_output:
  origin_ip: terraform_output
  origin_name: optional_generated_name
state: requested | provisioned | active | deprecated | retired
```

### App admission record example

Apps bind to an already-provisioned cluster ingress path by referencing `target_cluster`. The cluster record determines the Palo Alto URL category and other firewall implementation details. App records should not repeat cluster-derived firewall fields, and requestors should not choose scanner behavior. Vulnerability scan status should be produced by CI/AppSec integration as an external check or status, not supplied as app intent. The app record lifecycle represents desired enforcement state after review/merge: `active` means the FQDN should be admitted for the target cluster, while `revoked` means the FQDN should be removed/disabled.

```yaml
fqdn: app.example.com
owner: application-team
environment: prod
target_cluster: gke-prod-usw2-01
lifecycle: active | revoked
```

### Flow

**Cluster bootstrap:**

```text
Platform builds GKE cluster + backend ILB
→ Platform submits cluster intent with backend ILB details and required metadata
→ CI derives XNLB and Palo Alto object names from standards
→ NetSec repo provisions XNLB VIP/forwarding rule
→ NetSec repo provisions Palo NAT/security/category mapping
→ workflow outputs XNLB origin IP/name for GTM onboarding
→ requestor uses that output in GTM onboarding API payload
```

**App onboarding:**

```text
App onboarding request
→ PR adds/updates app record targeting an existing cluster record
→ CI derives target Palo category from the cluster record and validates metadata, required checks/waivers, and policy constraints
→ Terraform plan shows Palo Alto URL category membership change
→ NetSec review + approval
→ Terraform apply updates Palo Alto
→ scanner/validation tests real public path after exposure unless scanner-only pre-admission exists
```

Phase 1 should focus on cluster ingress bootstrap and the current Palo Alto URL category workflow. Later phases can add scanner webhooks, remediation actions, expiration, revocation, and broader edge-control integration.

## Why Not Start With Option B?

Option B is cleaner on paper, but it depends on capabilities that are not currently proven.

Known gaps:

- **Origin selection is not trusted today.** Current understanding is that clients may be able to set `X-Forwarded-Origin` directly to an FQDN or IP.
- **No official onboarding source of record is known today.** There is no clear authoritative system for `app → owner/env → cluster → origin → XNLB → policy/lifecycle`.
- **Scanner-only staged access is not confirmed.** It is unknown whether Imperva/Cequence can make one app reachable only by scanner IPs before general availability.
- **There is a scanner bootstrap problem.** A scan cannot be a prerequisite for opening the same access path if the scanner has no pre-admission path to reach the application. The design must define how scanner traffic is allowed before general access, such as scanner-only edge policy, temporary Palo category membership, a preview/staging hostname, or a manual break-glass approval.

Until those are solved, Option B would move app admission upstream without enough control-plane maturity.

## Assumptions to Validate

These are the high-ticket items for stakeholder discussion.

| Area | Question | Why It Matters |
|------|----------|----------------|
| **PAN-OS Terraform** | Can the provider safely manage URL categories, NAT/security policy, device groups, and commit/push? | Determines whether Option C can reduce firewall toil. |
| **Naming/derivation logic** | Can CI derive Palo device group, NAT/security rule names, URL category, XNLB forwarding-rule name, and origin output from cluster metadata? | Requestors should provide intent/backend data, not firewall implementation details. |
| **Existing Palo state** | Can current categories/rules be imported or reconciled without destructive drift? | Prevents Terraform adoption from breaking production policy. |
| **XNLB ownership** | NetSec creates and owns XNLB forwarding rules, and Option C may provision those GCP resources from the same repo that stores app/cluster intent. Platform should trigger the cluster registration workflow after building a new internet-capable GKE cluster. | Defines repo scope and team handoff. |
| **Cluster registration** | Platform initiates the cluster record after building a new internet-capable GKE cluster; NetSec repo provisions or records the XNLB forwarding rule/public IP and Palo mapping. | Solves the current visibility gap and gives the requestor the origin IP/name required for GTM onboarding. |
| **Scan integration** | Can CI/AppSec publish scan results or waivers as checks/status outside the requester-supplied app YAML? | Adds scan visibility without asking requestors to declare scanner mode/status themselves. |
| **Origin trust** | Can `X-Forwarded-Origin` be stripped, overwritten, signed, or validated before Cequence uses it? | Required before Option B can be considered safe. |
| **Scanner path** | The scanner likely must test the real public FQDN through GTM/Imperva/Cequence/XNLB/Palo/GKE. If no scanner-only pre-admission path exists, scanning cannot be a strict preventative gate before initial exposure. | In that case, scan integration should start as detective/remediation CI: detect failed scans after exposure, notify owners, open remediation PRs/issues, and optionally remove/revoke Palo category membership after policy-defined failure windows. |
| **Approvals** | Who can request, review, merge, and apply production app exposure changes? | The app record is the proposed registration; approval should be represented by PR review/merge controls, not a vague `approval` field in the YAML. |
| **Revocation** | Can changing an app record to `lifecycle: revoked` remove access cleanly? Can scanner findings open revocation PRs automatically? | Onboarding automation must also handle decommissioning and vulnerability-driven access removal. |
| **Secrets/state** | Where do Panorama credentials and Terraform state live, and who can access them? | Avoids creating a new privileged automation risk. |

## Scanner Control Model

If the scanner must use the same public FQDN path that application teams are requesting, and no scanner-only pre-admission path exists, vulnerability scanning should not be represented as a strict preventative control for initial access.

Near-term scan integration should be treated as **detective/remediation CI**:

```text
app access is approved through NetSec repo
→ public path becomes reachable
→ scanner tests real FQDN through the production ingress chain
→ scan result updates PR status / external check / issue
→ failed scan triggers remediation workflow or opens a PR changing lifecycle to `revoked` based on policy
```

This avoids pretending scan pass can be required before the scanner has any route to the application. Preventative scan gating can be revisited later if Imperva/Cequence or another edge layer can provide scanner-only pre-admission access.

## Cluster Onboarding Flow

For new internet-capable GKE clusters, the repository can own the cluster ingress bootstrap instead of only referencing already-created objects.

```text
1. Platform builds GKE cluster and backend GKE ILB.
2. Platform submits a cluster intent record with backend ILB details.
3. NetSec repo provisions the XNLB forwarding rule and reserved public IP.
4. NetSec repo provisions/updates Palo Alto NAT, security policy, and cluster URL category.
5. Workflow outputs the XNLB origin IP/name required for GTM onboarding.
6. Requestor submits GTM onboarding API payload using the NetSec-provided origin/IP details.
7. App records can then add CNAME/FQDN membership for that cluster path.
```

Important boundary: requestors can provide the backend GKE ILB because that is their/platform-owned target, but they should not choose the public XNLB IP, forwarding-rule name, Palo Alto device group, NAT rule, security rule, or URL category directly. Those values should be derived by the NetSec workflow from approved naming and placement standards so the ingress path remains controlled and auditable.

## Phased Program

| Phase | Goal | Output |
|-------|------|--------|
| **0. Discovery** | Confirm owners and capability gaps | Owner map + capability matrix |
| **1. Cluster ingress bootstrap** | Create/register internet-capable cluster ingress path | `clusters/*.yaml`, backend ILB input, XNLB forwarding rule/public IP output, Palo NAT/security/category mapping, GTM onboarding output |
| **2. App registration** | Track app-to-cluster admission intent | `apps/*.yaml` records |
| **3. PAN-OS automation** | Automate current Palo URL category process | Terraform-managed category membership |
| **4. Scanner integration** | Add scan results/waivers as external repo checks | CI/webhook/remediation workflow |
| **5. Edge admission pilot** | Test Option B for limited scope | Scanner-only → active route promotion |

## Open Questions

- Can existing Palo Alto URL categories and rules be safely imported into Terraform state?
- What exact GCP permissions/project boundaries are required for the NetSec repo to provision XNLB forwarding rules and reserve public IPs?
- What output format should the NetSec workflow provide to the requestor for the follow-on GTM onboarding API payload?
- What exact handoff does Platform use to submit the post-build cluster intent record?
- If no scanner-only pre-admission path exists, should scan integration be detective/remediation first rather than preventative, using external CI/AppSec checks instead of requester-supplied fields?
- What SLA/action should occur when a newly exposed app fails scan: notify only, block future changes, open a PR setting `lifecycle: revoked`, remove Palo URL category membership, or require manual exception?
- Can Imperva/Cequence enforce scanner-only pre-admission access per app in the future?
- Can origin-selection headers be made non-client-controllable?
- What telemetry replaces Palo URL-category visibility if Option B is ever adopted?

## Recommendation Summary

Start with **Option C**.

It reduces immediate NetSec toil, creates the missing source-of-truth layer, and keeps the existing Palo Alto enforcement model intact while the broader organization figures out whether GTM/Cequence can eventually own app-level admission.
