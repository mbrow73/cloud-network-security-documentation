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


### Assumptions to Validate

This option assumes the organization can safely automate Palo Alto URL category updates without making the vulnerability scanner a direct firewall policy authority.

| Assumption | Validation Question | Why It Matters |
|------------|---------------------|----------------|
| A Network Security-owned controller can update Panorama objects safely | Is there an approved API path for adding/removing FQDNs from custom URL categories and committing/pushing changes? | Without this, Option A remains manual or requires brittle automation around firewall operations. |
| The scanner emits trustworthy pass/fail events | Are scan result webhooks signed, tied to a scan ID, and bound to the exact application FQDN/onboarding request? | Scan success becomes a condition for internet exposure; replayed or ambiguous scan events cannot be accepted. |
| A source of truth can map app FQDN to the correct firewall object | Can automation resolve `app FQDN -> cluster/origin -> XNLB forwarding rule -> Palo URL category` deterministically? | Prevents the controller from adding the right app to the wrong cluster/category path. |
| Palo Alto URL category matching is the intended app-level control | Does the policy actually evaluate the hostname/category in the expected traffic leg, and does TLS/SNI/HTTP visibility support that match? | If the firewall cannot reliably evaluate the app identity, URL categories provide false confidence. |
| Panorama commit/push latency is acceptable for onboarding | How long does an object update and commit/push take, and what happens on partial failure? | Each app promotion depends on firewall control-plane timing and failure handling. |
| URL category lifecycle can be managed | Can automation remove entries on app retirement, failed scans, expiration, or revocation? | Otherwise categories become stale allowlists. |
| Post-change validation can prove the public path | Can a synthetic probe confirm `FQDN -> Imperva -> Cequence -> XNLB -> Palo -> GKE ILB` after the category update? | Prevents policy success from being mistaken for end-to-end application reachability. |

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


### Assumptions to Validate

This option assumes the edge/onboarding control plane can become the authoritative application admission point, while Palo Alto policy is simplified to cluster-scoped edge-to-origin enforcement.

| Assumption | Validation Question | Why It Matters |
|------------|---------------------|----------------|
| GTM / Imperva / Cequence can support a staged application route | Can an app hostname exist in `scanner_only` state before being promoted to normal public access? | Without staged route state, scan-before-general-access is difficult or requires temporary firewall exceptions. |
| The scanner can test the real public hostname | Can the scanner target `https://app.example.com` through GTM, Imperva, Cequence, XNLB, Palo Alto, and GKE ILB? | A scan against a private/bypass path does not validate the production internet chain. |
| Scanner-only access can be restricted per app | Can Imperva/Cequence allow only scanner public IPs for one app without opening other apps on the same cluster origin? | Prevents scanner pre-admission access from becoming broad cluster exposure. |
| Cequence can enforce app-level admission reliably | Can Cequence distinguish app hostnames and promote/revoke a single app without impacting other apps on the same origin? | Option B removes Palo URL categories, so app-level admission must move upstream. |
| Origin selection metadata is trusted and non-spoofable | Is the X-Forwarded-Origin/origin-selection value inserted or overwritten only by trusted systems? What happens if a client sends its own value? | If clients can influence origin selection, traffic could be routed to unintended clusters. Current understanding: clients may already be able to set X-Forwarded-Origin to an FQDN or IP, so this assumption is not currently validated and may be false. |
| The onboarding system is a real source of truth | Does an authoritative record exist for `app FQDN -> owner -> environment -> cluster -> origin -> XNLB forwarding rule -> lifecycle state`? | The scanner result only says the app passed; it does not know where the app is allowed to route. Current understanding: no official source of record exists today, so this is a major workstream for Option B. |
| Palo Alto can be safely reduced to cluster-scoped policy | Are Imperva/Cequence NAT pools stable and complete, and are XNLB VIPs reachable only from those approved sources? | Palo becomes the edge-to-cluster boundary instead of per-app admission control. |
| App identity remains visible outside Palo Alto URL categories | Can logs from GTM, Imperva, Cequence, Palo Alto, and GKE be correlated by FQDN/app ID? | Removing URL categories should not create an audit/forensics blind spot. |
| Promotion and rollback are first-class state transitions | Can automation move `scanner_only -> active -> revoked` cleanly and quickly? | Internet exposure must be reversible without emergency manual edits. |

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


## Capability Discovery Required Before Selection

Before selecting either option, the stakeholder teams should validate the following high-ticket capabilities. These are gating assumptions, not implementation details.

| Capability | Owner to Confirm | Option A Dependency | Option B Dependency |
|------------|------------------|---------------------|---------------------|
| Scanner can scan the public application FQDN through the real internet ingress chain | Application Security / Scanner Team | Required for final validation | Required for final admission |
| Scanner results are signed/trustworthy and tied to a specific onboarding request | Application Security / Platform | Required | Required |
| GTM / Imperva / Cequence can create scanner-only pre-admission access per app | Edge / WAF / Bot Teams | Helpful | Required |
| Cequence origin selection is deterministic and protected from client spoofing | Cequence / Edge Team | Required to validate path | Required for admission control; currently suspected false if clients can set X-Forwarded-Origin directly |
| Source-of-truth mapping exists for app FQDN to cluster/origin/XNLB | Platform / DDI / Edge / NetSec | Required for correct category updates | Required for route promotion; currently no official source of record is known |
| Palo Alto API automation can update URL categories and commit/push safely | Network Security | Required | Not required for app admission |
| Palo Alto policy can be safely scoped to edge NAT pools and cluster XNLB VIPs | Network Security | Useful | Required |
| Telemetry can correlate app FQDN across GTM, Imperva, Cequence, Palo Alto, and GKE | SecOps / Observability | Required | Required, especially if URL categories are removed |
| Revocation/expiration can disable public exposure per app | Platform / Edge / NetSec | Required | Required |

If the staged edge route, origin trust, scanner public-path testing, or onboarding source of truth cannot be validated, Option B should not be selected as the immediate target. In that case, Option A is the safer transitional automation pattern because Palo Alto remains an independent application-level enforcement point.


## Current Known Gaps

The following gaps are known or suspected as of this draft and should be treated as primary discussion points with stakeholder teams:

- **Origin header trust is not established.** Current understanding is that clients can set `X-Forwarded-Origin` directly to an FQDN or IP. If true, origin selection cannot be treated as a trusted admission signal unless the edge chain overwrites, strips, signs, or otherwise validates this value before Cequence uses it.
- **No official onboarding source of record is known.** There does not appear to be a single authoritative system that binds app FQDN, owner, environment, cluster, origin, XNLB forwarding rule, Palo Alto policy/category, scan state, and lifecycle state. Without this, either option requires a source-of-truth workstream before safe automation.

These gaps do not automatically eliminate the options, but they materially affect sequencing. Option B should not be selected as the near-term target unless origin trust and source-of-truth ownership are resolved. Option A may still require a source-of-truth layer for safe URL category automation, but it preserves Palo Alto as an independent application-level enforcement point while the upstream control plane matures.


## Recommended Automation Program Approach

This should be treated as a phased ingress automation program, not a single vulnerability-scanner-to-firewall integration. The immediate operational pain is broader than scan-gated admission:

- New backend GKE clusters require manual XNLB forwarding rule / public IP work.
- New applications require cluster-specific CNAME / URL-category policy updates on the internet Palo Alto firewalls.
- The timing of new cluster creation is not always evident to Network Security.
- Vulnerability scan status is only one input into whether an application should be admitted to the public ingress path.
- Several required control-plane capabilities span GTM / DDI, Imperva, Cequence, Palo Alto, GKE platform, AppSec scanning, and observability teams.

The recommended approach is to separate the program into maturity phases.

### Phase 0: Discovery and Ownership Alignment

Goal: define the real systems of record, ownership boundaries, and capability gaps before building automation.

Key outcomes:

- Identify who owns app onboarding metadata.
- Identify who owns cluster/origin/XNLB lifecycle.
- Confirm whether clients can spoof or influence origin-selection headers.
- Confirm whether scanner-only edge access is technically possible.
- Confirm current Palo Alto policy/category behavior and whether URL categories are reliable app-level controls.
- Define required audit fields for app exposure decisions.

Deliverable: capability matrix and owner map.

### Phase 1: Cluster Ingress Registration

Goal: make new cluster ingress capacity explicit and reviewable.

Instead of starting with per-app policy automation, first create a cluster registration workflow for internet-capable GKE clusters.

Example cluster registration record:

```yaml
cluster_id: gke-prod-usw2-01
environment: prod
platform_owner: gke-platform-team
origin_name: cluster-prod-usw2-01.ingress.example.net
xnlb_forwarding_rule: fr-prod-usw2-01
xnlb_vip: 203.0.113.10
gke_backend_ilb: 10.10.20.15
palo_nat_rule: nat-gke-prod-usw2-01
palo_security_rule: allow-edge-to-gke-prod-usw2-01
palo_url_category: gcp-ingress-prod-usw2-01-approved-apps
allowed_edge_sources:
  - imperva_nat_pool_prod
  - cequence_nat_pool_prod
state: proposed | provisioned | active | deprecated | retired
```

This phase does not need to solve app admission yet. It creates visibility into which clusters are internet-capable and which Palo Alto / XNLB objects correspond to each cluster.

### Phase 2: App-to-Cluster Admission Registry

Goal: track application onboarding intent before changing firewall or edge policy.

Example application registration record:

```yaml
app_fqdn: app.example.com
owner: application-team
environment: prod
target_cluster_id: gke-prod-usw2-01
scan_required: true
scan_status: not_started | running | passed | failed | waived
publication_state: requested | scanner_only | approved | active | revoked
created_by: onboarding-api
approved_by: appsec-or-netsec
expires_at: null
```

This phase creates the missing source of truth. It can initially be lightweight, even if final automation is not ready.

### Phase 3: Transitional Palo Alto Automation

Goal: reduce manual Palo Alto work without removing the existing firewall-level app gate.

Recommended near-term automation:

```text
app registration exists
→ scan passes or waiver approved
→ controller validates app-to-cluster mapping
→ controller proposes or applies Palo Alto URL category update
→ Panorama commit/push
→ public-path validation
```

This maps to Option A and is likely the safest transitional pattern while origin trust, scanner-only access, and onboarding source-of-truth maturity are still unresolved.

### Phase 4: Edge-Controlled Admission Pilot

Goal: prove whether Option B is viable for a limited scope.

Pilot only after these capabilities are validated:

- Cequence/Imperva can enforce scanner-only access per app.
- Origin-selection metadata is trusted, overwritten, or validated.
- App-to-cluster mapping is authoritative and auditable.
- Public-path scanner validation is available.
- Revocation works without manual firewall edits.

If successful, Palo Alto can move toward cluster-scoped edge-to-origin rules for selected low-risk clusters/apps.

### Phase 5: Broader Option B Adoption

Goal: make GTM / Imperva / Cequence onboarding the primary app admission control point and remove routine per-app Palo Alto URL category work.

This phase should only proceed after the edge-control pilot proves the model and SecOps telemetry can preserve app-level visibility outside Palo Alto URL categories.

## Near-Term Recommendation

Do not start by wiring vulnerability scanner pass/fail directly to public route activation. The safer near-term program is:

1. Build cluster ingress registration so new XNLB / Palo Alto / GKE ILB mappings are visible.
2. Build app-to-cluster admission records so application onboarding has an owner, target cluster, scan state, and lifecycle state.
3. Automate Palo Alto URL category updates as a transitional control, with human approval where needed.
4. In parallel, run capability discovery for scanner-only edge access and trusted origin selection.
5. Revisit Option B after the onboarding control plane and edge controls can safely replace firewall-level app allowlisting.

This keeps the program grounded in the current pain while still leaving a path to the cleaner target architecture.

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
