---
title: AWS Firewall Automation Control Plane Architecture
ea_file_type: ADR
status: proposed
date: 2026-04-06
decision-makers: NSAE Leadership
consulted: Cloud Network Security, Cloud Platform Engineering
informed: Enterprise Architecture, Infrastructure Security
---

# AWS Firewall Automation Control Plane Architecture

| Choose One [X] | ADR Type | Description |
|---|---|---|
| X | architecture | Describes the proposed control-plane architecture for AWS firewall automation and establishes the initial implementation direction for the POC. |

## ADR Status History

| Authors | Status | Date | Deciders |
|---|---|---|---|
| NSAE | Proposed | 2026-04-06 | N/A |

## Terms

| Term | Definition |
|---|---|
| ISAFE | Internal Security Automation and Firewall Engine. A standalone automation platform that receives programmatic API calls from developers and pushes granular firewall policy to Palo Alto firewalls via the management interface. |
| EDL | External Dynamic List. A dynamically-updated IP list on Palo Alto firewalls populated by Illumio automation containing enforced VEN agent IPs. |
| EQUINIX_DC Firewalls | Palo Alto firewalls located in the Equinix DC colo functioning as cloud gateway firewalls. The primary ingress/egress point for cloud-to-on-prem traffic via Direct Connect. |
| FQDN Object | A Palo Alto address object that uses a fully qualified domain name instead of an IP address, allowing the firewall to dynamically resolve destinations. |
| VEN | Virtual Enforcement Node. The Illumio agent installed on managed workloads for microsegmentation visibility and enforcement. |
| SG Framework | The AWS Security Group self-service framework providing developer self-service via YAML requests, PR-based approval, Terraform automation, and GHA validation pipelines. |
| Non-Routable Subnets | AWS VPC subnets with private IP ranges that route through a NAT Gateway to reach external destinations. Firewall visibility is limited to the NAT Gateway IP. |
| Routable Subnets | AWS VPC subnets with IPs that are directly visible end-to-end across the network without NAT translation. |

## Context & Problem Statement

The current firewall rule request process for cloud-to-on-prem and on-prem-to-cloud connectivity requires manual ticket submission and review, resulting in a 1-2 week turnaround time per request. This creates a bottleneck for development teams and incentivizes workarounds that weaken the security posture.

The current AWS-to-on-prem traffic path also creates two architectural constraints:

1. **EDL segmentation risk** - An Illumio EDL-based allow rule exists on all firewalls in the path (EQUINIX_DC, Core, and Midrange). Under the current SOP, this is acceptable because Illumio rules remain granular. If the architecture shifted toward broad cloud-summary allowances on VENs, that EDL would effectively remove firewall-layer segmentation for managed workloads.
2. **NAT visibility limitation** - For workloads in non-routable subnets, the firewall sees only the NAT Gateway IP, not the originating workload IP. This makes granular per-workload policy impractical at the firewall layer. Security Groups remain the only enforcement point that sees true source and destination at the instance level.

The NSAE team needs an architecture that enables developer self-service for cloud-to-on-prem access while improving AWS segmentation and avoiding security group leakage across single-tenant accounts.

### Current Traffic Flow

```
AWS Workload → Security Group → NAT GW (non-routable) or direct (routable)
  → Transit Gateway → Direct Connect → EQUINIX_DC Palo Alto
  → Core Palo Alto → Midrange Firewall → On-Prem Workload (Illumio VEN)
```

### Current Firewall Rules (All Firewalls)

| Firewall | Rule | Type | Impact |
|---|---|---|---|
| EQUINIX_DC | EDL: Any to Illumio Agents | Current | Bidirectional allow for all enforced agents |
| EQUINIX_DC | EDL: Illumio Agents to Any | Current | across AWS, GCP, and Azure |
| Core | EDL: Any to Illumio Agents | Current | Same EDL pass-through as EQUINIX_DC |
| Core | EDL: Illumio Agents to Any | Current | |
| Midrange | EDL: Any to Illumio Agents | Current | Same EDL pass-through as EQUINIX_DC |
| Midrange | EDL: Illumio Agents to Any | Current | |
| Core | AWS Summary to Any | Proposed (POC) | Coarse-grain cloud summary rules for POC |
| Core | Any to AWS Summary | Proposed (POC) | |
| Midrange | AWS Summary to Any | Proposed (POC) | Coarse-grain cloud summary rules for POC |
| Midrange | Any to AWS Summary | Proposed (POC) | |

## Decision Drivers

| ID | Criteria |
|---|---|
| 1 | MUST enable zero-touch developer self-service for cloud-to-on-prem firewall rules |
| 2 | MUST reduce firewall rule request turnaround from 1-2 weeks to near-instantaneous |
| 3 | MUST improve segmentation posture for AWS workloads |
| 4 | MUST prevent security group leakage across single-tenant accounts |
| 5 | MUST NOT disrupt existing GCP and Azure traffic flows through the EDL rule |
| 6 | SHOULD support FQDN-based destination objects for firewall policy |
| 7 | SHOULD provide auditability and approval workflow for all rule changes |
| 8 | SHOULD minimize blast radius during POC and phased rollout |

*Table 1. Decision driver criteria used to evaluate the proposed options*

## Options Considered

- **Option 1: Split Control Plane** - ISAFE manages Palo Alto firewall rules at the Equinix DC gateway, SG Framework manages AWS Security Groups. Two systems with separate approval and audit paths.
- **Option 2: Unified Control Plane** - SG Framework is extended to manage both AWS Security Groups and Palo Alto firewall rules via PAN-OS Terraform provider. One request, one PR, two enforcement points.

### Option 1: Split Control Plane (ISAFE + SG Framework)

![Split Control Plane Architecture](diagrams/split-control-plane.png)

ISAFE manages Palo Alto firewall policy at the EQUINIX_DC layer. The SG Framework independently manages AWS Security Group enforcement.

**POC model:**
- Phase 1 scopes ISAFE to non-Illumio routable hosts that already rely on explicit firewall rules.
- SG Framework remains the AWS-side enforcement mechanism.
- For NATted or Illumio-managed traffic where downstream firewall identity is weak or bypassed, Security Groups remain the workload-level control.

**Advantages:**
- Lower blast radius for the initial POC
- Clear ownership boundaries between perimeter and cloud-native controls
- Uses native Palo Alto FQDN objects immediately
- Preserves the existing SG Framework without major extension work

**Disadvantages:**
- Two systems, two approval paths, two audit trails
- No single source of policy intent across AWS and Palo Alto
- Developers must understand which workflow applies
- Drift between PA-side and SG-side intent is possible

### Option 2: Unified Control Plane (SG Framework Extended)

![Unified Control Plane Architecture](diagrams/unified-control-plane.png)

The SG Framework is extended to manage both AWS Security Groups and Palo Alto firewall policy from a single declarative request. The framework resolves FQDNs for SG enforcement and pushes native FQDN objects to Palo Alto.

**Advantages:**
- Single request path and single audit trail
- Policy coherence by design
- Better long-term developer experience
- Maximizes reuse of the SG Framework operating model

**Disadvantages:**
- Larger implementation scope up front
- Requires PAN-OS provider integration and lifecycle management
- SG-side FQDN resolution is point-in-time and needs refresh strategy
- Requires broader organizational alignment across teams

## Decision

NSAE will use **Option 1: Split Control Plane** for the initial POC.

- **ISAFE** will manage Palo Alto gateway policy.
- **SG Framework** will manage AWS Security Group enforcement.
- **Option 2: Unified Control Plane** remains a future-state candidate and is **not** approved for current implementation scope.

### Rationale

Option 1 is the best fit for the POC because it proves the self-service model with the lowest blast radius, avoids immediate consolidation work across tooling and ownership boundaries, and allows AWS Security Groups to remain the primary workload-level enforcement point where NAT and EDL behavior weaken downstream firewall precision.

## Consequences

### Positive

- Self-service firewall automation can be tested without redesigning both platforms at once
- AWS workloads retain workload-level segmentation through Security Groups
- Existing GCP and Azure EDL-dependent flows remain untouched
- The organization can validate developer demand, approval patterns, and operational readiness before committing to unified control plane work

### Negative

- Split control plane introduces coordination overhead between PA-side and SG-side enforcement
- Audit and troubleshooting remain fragmented across two systems
- Policy coherence is procedural rather than enforced by a single source of truth

### Key Risks

| Risk | Impact | Mitigation |
|---|---|---|
| PA and SG intent diverge | Incorrect or partial enforcement | Reconcile request metadata across systems; define clear ownership boundaries |
| NATted workloads still lack firewall-layer identity | Granular PA policy remains limited | Keep SGs as primary workload-level control |
| POC scope drifts into future-state design | Delayed delivery and higher blast radius | Keep unified control plane explicitly out of current implementation scope |

## References

- [POC Implementation Plan](supporting/001-poc-implementation-plan.md)
- [Environment Resolution Design](supporting/001-environment-resolution.md)
- [POC Success Criteria](supporting/001-poc-success-criteria.md)
