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
| **C. NetSec internet app repo** | **Recommended near-term** | Create a NetSec-owned GitOps repo for cluster/app records and PAN-OS Terraform automation. Builds the missing source of truth incrementally. |

## Recommended Near-Term Pattern: Option C

Create a repository such as:

```text
netsec-internet-apps/
├── clusters/
├── apps/
├── terraform/
└── .github/workflows/
```

### Cluster record example

```yaml
cluster_id: gke-prod-usw2-01
environment: prod
origin_name: cluster-prod-usw2-01.ingress.example.net
xnlb_forwarding_rule: fr-gke-prod-usw2-01
xnlb_vip: 203.0.113.10
gke_backend_ilb: 10.10.20.15
palo_device_group: dg-internet-prod
palo_url_category: gcp-ingress-prod-usw2-01-approved-apps
allowed_edge_sources:
  - imperva_prod_nat
  - cequence_prod_nat
state: active
```

### App record example

```yaml
fqdn: app.example.com
owner: application-team
environment: prod
target_cluster: gke-prod-usw2-01
scan_status: passed
scan_id: scan-12345
state: active
```

### Flow

```text
App onboarding request
→ PR adds/updates app record
→ CI validates target cluster, metadata, scan/waiver, and policy constraints
→ Terraform plan shows PAN-OS URL category / policy changes
→ NetSec review + approval
→ Terraform apply updates Palo Alto
→ post-change validation confirms public path
```

Phase 1 should focus on codifying the current Palo Alto URL category workflow. Later phases can add scanner webhooks, remediation actions, expiration, revocation, and broader edge-control integration.

## Why Not Start With Option B?

Option B is cleaner on paper, but it depends on capabilities that are not currently proven.

Known gaps:

- **Origin selection is not trusted today.** Current understanding is that clients may be able to set `X-Forwarded-Origin` directly to an FQDN or IP.
- **No official onboarding source of record is known today.** There is no clear authoritative system for `app → owner/env → cluster → origin → XNLB → policy/lifecycle`.
- **Scanner-only staged access is not confirmed.** It is unknown whether Imperva/Cequence can make one app reachable only by scanner IPs before general availability.

Until those are solved, Option B would move app admission upstream without enough control-plane maturity.

## Assumptions to Validate

These are the high-ticket items for stakeholder discussion.

| Area | Question | Why It Matters |
|------|----------|----------------|
| **PAN-OS Terraform** | Can the provider safely manage URL categories, NAT/security policy, device groups, and commit/push? | Determines whether Option C can reduce firewall toil. |
| **Existing Palo state** | Can current categories/rules be imported or reconciled without destructive drift? | Prevents Terraform adoption from breaking production policy. |
| **XNLB ownership** | Does NetSec create XNLB forwarding rules, or only reference platform-created cluster records? | Defines repo scope and team ownership. |
| **Cluster registration** | Who creates a cluster record when a new internet-capable GKE cluster is built? | Solves the current visibility gap. |
| **Scan gating** | Can CI require scan pass, scan ID, waiver, or manual approval before app activation? | Adds scan status without making the scanner a firewall admin. |
| **Origin trust** | Can `X-Forwarded-Origin` be stripped, overwritten, signed, or validated before Cequence uses it? | Required before Option B can be considered safe. |
| **Scanner path** | Can the scanner test the real public FQDN through GTM/Imperva/Cequence/XNLB/Palo/GKE? | A private/bypass scan does not validate the internet path. |
| **Approvals** | Who can request, approve, merge, and apply production app exposure changes? | Prevents app teams from self-approving internet access. |
| **Revocation** | Can removing/changing an app record revoke access cleanly? | Onboarding automation must also handle decommissioning. |
| **Secrets/state** | Where do Panorama credentials and Terraform state live, and who can access them? | Avoids creating a new privileged automation risk. |

## Phased Program

| Phase | Goal | Output |
|-------|------|--------|
| **0. Discovery** | Confirm owners and capability gaps | Owner map + capability matrix |
| **1. Cluster registration** | Make internet-capable clusters visible | `clusters/*.yaml` records |
| **2. App registration** | Track app-to-cluster admission intent | `apps/*.yaml` records |
| **3. PAN-OS automation** | Automate current Palo URL category process | Terraform-managed category membership |
| **4. Scanner integration** | Add scan pass/waiver as a repo gate | CI/webhook/remediation workflow |
| **5. Edge admission pilot** | Test Option B for limited scope | Scanner-only → active route promotion |

## Open Questions

- Can existing Palo Alto URL categories and rules be safely imported into Terraform state?
- Should this repo provision XNLB forwarding rules or only reference platform-owned records?
- Who owns cluster registration when new internet-capable GKE clusters are created?
- Can Imperva/Cequence enforce scanner-only pre-admission access per app?
- Can origin-selection headers be made non-client-controllable?
- What telemetry replaces Palo URL-category visibility if Option B is ever adopted?

## Recommendation Summary

Start with **Option C**.

It reduces immediate NetSec toil, creates the missing source-of-truth layer, and keeps the existing Palo Alto enforcement model intact while the broader organization figures out whether GTM/Cequence can eventually own app-level admission.
