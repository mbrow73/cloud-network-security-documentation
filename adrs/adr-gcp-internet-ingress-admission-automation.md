# ADR: GCP Internet Ingress Admission Automation for Public GKE Applications

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-06-30 |
| **Proposed by** | Maximilian Browne |
| **Stakeholders** | Network Security, Cloud Platform Engineering, Application Security, Application Teams, Security Leadership |
| **Supersedes** | N/A |

---

## Context

Public GKE applications use a multi-stage internet ingress chain that includes external edge, bot mitigation, network firewall inspection, and private GKE backend delivery.

The current high-level path is:

```text
Public DNS / GTM application record
→ Imperva
→ Cequence SaaS bot mitigation
→ external network load balancer (XNLB) fronting Palo Alto firewalls
→ Palo Alto DNAT / SNAT
→ backend GKE internal load balancer (ILB)
→ GKE application
```

In the onboarding flow, the GTM payload points the application record at Imperva and includes origin-selection metadata. Cequence uses origin metadata, such as the X-Forwarded-Origin value from the onboarding payload, to select the correct cluster origin. The selected origin is an XNLB forwarding rule dedicated to a backend cluster or cluster group. Palo Alto policy then translates and forwards traffic to the corresponding backend GKE ILB.

Today, internet firewall enablement is not just a NAT and security policy change. The internet Palo Alto firewalls also use custom URL categories to allowlist application CNAMEs one application at a time. These URL categories are referenced in rules that constrain traffic from approved Imperva / Cequence NAT IPs to the appropriate XNLB forwarding rule and backend cluster path.

This creates operational friction because onboarding a new internet-facing application may require coordination across:

- GTM / DNS onboarding
- Imperva routing
- Cequence bot-mitigation origin selection
- XNLB forwarding rule and public IP creation
- Palo Alto NAT and security policy
- Palo Alto custom URL category updates
- Vulnerability scan completion and go-live approval

Security leadership has requested an automated pattern where completion of the internet application vulnerability scan can drive admission of the application into the internet ingress path.

The key design decision is whether Palo Alto custom URL categories should remain the app-level admission control, or whether the edge onboarding / GTM / Cequence control plane should become the authoritative application admission gate after vulnerability scan success.

## Decision

We will document and evaluate two viable patterns:

1. **Option A: Retain Palo Alto custom URL categories as the application-level enforcement point**
2. **Option B: Move application admission to the GTM / Cequence onboarding control plane and remove per-app Palo Alto URL category requirements**

The recommended direction is **Option B**, provided the GTM / Cequence onboarding control plane is made authoritative, auditable, reversible, and protected by clear guardrails.

Option A remains a conservative fallback when Network Security requires independent firewall-level application allowlisting or when upstream admission controls are not yet mature enough to replace the Palo Alto URL-category gate.

## Option A: Palo Alto URL Category as the Application Admission Gate

### Description

In this model, vulnerability scan success triggers an automation workflow that adds the approved application FQDN / CNAME to the correct Palo Alto custom URL category for the target cluster path.

The scanner does not directly own firewall policy. Instead, scan success is treated as an input signal to a Network Security-owned ingress entitlement controller.

```text
GTM onboarding payload
→ application / cluster / origin registry
→ vulnerability scan result
→ ingress entitlement controller
→ Palo Alto custom URL category update
→ Panorama commit / push
→ validation through public ingress chain
```

### Traffic and Control Flow

**Runtime traffic path:**

```text
User or scanner
→ public app hostname
→ GTM / Imperva
→ Cequence
→ XNLB forwarding rule
→ Palo Alto policy with URL category match
→ Palo Alto DNAT / SNAT
→ GKE ILB
→ application
```

**Automation path:**

```text
Vulnerability scan passes
→ controller verifies FQDN, cluster, origin, forwarding rule, and policy mapping
→ controller adds FQDN / CNAME to cluster-specific Palo Alto URL category
→ controller commits and validates
```

### Required Source of Truth

The automation must have a source-of-truth record that binds application identity to the intended ingress path.

Example record:

```yaml
app_fqdn: app.example.com
cluster_id: gke-prod-usw2-01
origin_name: cluster-prod-usw2-01.ingress.example.net
xnlb_forwarding_rule: fr-prod-usw2-01
palo_url_category: gcp-ingress-prod-usw2-01-approved-apps
allowed_edge_sources:
  - imperva_nat_pool_prod
  - cequence_nat_pool_prod
scanner_sources:
  - appsec_scanner_public_ips
state: requested | scanned_pass | approved | active | expired | revoked
```

### Benefits

- Preserves independent firewall-level app allowlisting
- Limits blast radius if upstream GTM / Cequence routing is misconfigured
- Aligns with the current control model and existing Palo Alto policy structure
- Provides an explicit NetSec-owned enforcement object for each approved application
- Allows policy review and rollback at the firewall layer

### Drawbacks

- Duplicates application admission state across GTM / Cequence and Palo Alto
- Adds manual or automated Panorama commit / push operations for each admitted application
- Increases operational coupling between vulnerability scanning and firewall policy lifecycle
- Requires strong naming conventions and lifecycle hygiene for URL categories
- Can become brittle if stale CNAMEs remain in categories after application retirement

### Guardrails

- The vulnerability scanner must provide signed / trusted scan result events.
- The scanner must not directly mutate Palo Alto policy or categories.
- The entitlement controller must validate the FQDN-to-cluster mapping before modifying policy.
- URL category changes must be logged with app owner, scan ID, commit ID, and expiration / review metadata.
- The controller must support revocation and cleanup for retired applications.
- Post-change validation must test the actual public ingress path.

## Option B: GTM / Cequence Admission Gate with Cluster-Scoped Palo Alto Allow Rules

### Description

In this model, Palo Alto no longer performs per-application URL-category enforcement for the internet ingress chain. Instead, the upstream onboarding control plane becomes the application admission point.

Palo Alto policy enforces the network boundary between approved edge NAT sources and cluster-specific XNLB forwarding rule destinations. Application-level admission is enforced by the GTM / Imperva / Cequence onboarding and route activation workflow.

```text
Palo Alto policy:
source = approved Imperva / Cequence NAT pools
destination = cluster-specific XNLB VIP / forwarding rule IP
service = 443
action = allow
```

Application publication is controlled upstream:

```text
GTM / onboarding record exists
→ scanner is allowed to test application through public path
→ vulnerability scan passes
→ GTM / Cequence route is promoted to normal access
→ post-admission validation confirms public ingress path
```

### Traffic and Control Flow

**Pre-admission scanner path:**

```text
Application scanner public IPs
→ public app hostname
→ GTM / Imperva
→ Cequence scanner-only policy or limited route
→ XNLB
→ Palo Alto cluster-scoped allow rule
→ GKE ILB
→ application
```

**Post-admission public path:**

```text
Approved public users
→ public app hostname
→ GTM / Imperva
→ Cequence normal policy
→ XNLB
→ Palo Alto cluster-scoped allow rule
→ GKE ILB
→ application
```

The vulnerability scanner should generally test the same public ingress chain that users will hit. A separate private scanner path can validate application behavior earlier in CI/CD, but it does not prove the internet ingress chain is correctly configured.

### Benefits

- Removes duplicate per-app allowlist state from Palo Alto
- Reduces Panorama policy/category churn during application onboarding
- Makes application admission a responsibility of the onboarding / edge routing control plane
- Keeps Palo Alto focused on the edge-to-cluster network security boundary
- Simplifies operational flow for new public GKE applications
- Better supports a pipeline-driven model where scan success promotes route state rather than firewall object membership

### Drawbacks

- Shifts application-level authorization away from Palo Alto and into the GTM / Cequence onboarding control plane
- Requires strong assurance that XNLB VIPs are reachable only from approved edge NAT sources
- Requires confidence that origin headers / route-selection metadata cannot be spoofed or abused to reach unintended clusters
- Requires authoritative audit, rollback, and lifecycle controls in the onboarding system
- Reduces firewall-layer app identity visibility unless logs from GTM / Imperva / Cequence are integrated into the operational view

### Guardrails

- GTM / Cequence route activation must be blocked until vulnerability scan success is verified.
- Scanner-only access must be time-bounded and source-restricted.
- XNLB forwarding rules must be cluster-scoped and mapped in source of truth.
- Palo Alto rules must only allow approved Imperva / Cequence NAT pools to specific cluster XNLB VIPs.
- Direct internet access to backend GKE ILBs must remain impossible.
- Origin-selection headers and metadata must be generated only by trusted onboarding / edge components.
- The onboarding controller must support revocation, expiration, and full audit history.
- Post-admission synthetic validation must test the public path through GTM, Imperva, Cequence, XNLB, Palo Alto, and GKE ILB.

## Scanner Path Considerations

The scanner path must be explicit because it changes what the scan result proves.

### Public Path Scan

Recommended for final internet admission.

```text
Scanner public IPs
→ public application hostname
→ GTM / Imperva
→ Cequence
→ XNLB
→ Palo Alto
→ GKE ILB
→ application
```

This validates the real exposed service and the real security chain.

### Private or Separate Scanner Path

Useful only for earlier pre-public application validation.

```text
Scanner network
→ private / internal hostname
→ internal ingress path
→ application
```

This validates the application but does not validate the final internet ingress architecture. It should not be the only gate for public exposure.

## Recommendation

Proceed toward **Option B** as the target pattern if the organization is willing to make GTM / Cequence onboarding the authoritative application admission control point.

Under Option B:

- Palo Alto enforces cluster-scoped edge-to-origin access.
- GTM / Cequence / onboarding automation enforces application publication state.
- Vulnerability scan success promotes the application from scanner-only access to normal public access.
- Post-admission validation confirms that the real public chain works.

Use **Option A** when independent Palo Alto app-level allowlisting is required or while the upstream onboarding controller is not yet mature enough to be the system of record for internet application admission.

## Consequences

### Positive

- Establishes a clear decision boundary between scanning, routing, and firewall enforcement
- Reduces manual firewall policy work for internet-facing GKE applications if Option B is adopted
- Preserves a conservative fallback option with Palo Alto URL categories
- Encourages source-of-truth-driven ingress onboarding instead of ad hoc firewall updates

### Negative

- Option B requires stronger governance around the GTM / Cequence onboarding control plane
- Existing Palo Alto URL category controls may need to be retired carefully to avoid visibility or audit gaps
- Scanner-only pre-admission access must be designed carefully to avoid becoming a permanent bypass
- The public chain remains operationally complex even if firewall category management is simplified

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Upstream route activation becomes the only application admission gate without enough auditability | Medium | High | Require signed scan results, source-of-truth records, full audit logs, and reversible state transitions before removing Palo Alto URL categories. |
| Scanner-only access becomes a permanent exception path | Medium | High | Time-bound scanner access, enforce scanner source IPs, and require automatic cleanup after pass/fail. |
| Origin header or route-selection metadata is spoofed | Medium | High | Only trust metadata inserted by controlled edge/onboarding components; validate origin mapping server-side; restrict XNLB VIP access to approved edge NAT pools. |
| Palo Alto loses useful app-level visibility | Medium | Medium | Integrate GTM / Imperva / Cequence logs with firewall logs and preserve app FQDN in centralized telemetry. |
| Stale app records remain active after retirement | Medium | Medium | Require lifecycle state, owner metadata, expiration / review, and automated revocation. |
| Public-path scan passes but backend mapping points to the wrong cluster | Low | High | Validate FQDN, Cequence origin, XNLB forwarding rule, Palo NAT, and GKE ILB mapping before promotion. |

## Recommendation Summary

| Option | Recommendation | Why |
|--------|----------------|-----|
| **Option A: Palo Alto URL category admission** | Conservative fallback | Maintains independent firewall app allowlisting but duplicates state and keeps onboarding operationally heavy. |
| **Option B: GTM / Cequence admission with cluster-scoped Palo Alto rules** | Preferred target | Simplifies firewall operations and places app admission in the onboarding / edge control plane, provided strong audit and rollback controls exist. |

## Open Questions

- Which system is the authoritative source of truth for app FQDN to cluster origin mapping?
- Can Cequence enforce scanner-only pre-admission access and then promote to normal access after scan pass?
- Are Imperva / Cequence NAT pools stable and fully known for Palo Alto source restrictions?
- Can the onboarding API safely generate and preserve the required origin metadata without allowing spoofing?
- What telemetry will replace Palo Alto URL-category visibility if Option B is selected?
- What is the retirement / revocation process for decommissioned public applications?

## References

- Existing GCP egress ADR: `./adr-gcp-internet-egress-architecture.md`
