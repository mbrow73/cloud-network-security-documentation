# ADR: GCP Internet Egress Architecture for EWP-Based Outbound Inspection

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-04-09 |
| **Proposed by** | Maximilian Browne |
| **Stakeholders** | Network Security, Cloud Platform Engineering, Security Leadership, Application Teams |
| **Supersedes** | N/A |

---

## Context

We need a standardized pattern for **internet-bound outbound traffic inspection in GCP** for workloads that consume an internally published service via **Private Service Connect (PSC)** and egress through an **Egress Workload Proxy (EWP)**.

The design needs to provide:

- Private service consumption from producer / intranet workloads into EWP via PSC
- Outbound inspection for EWP-initiated internet traffic
- Clear routing semantics that can be reviewed and operated by network/security engineers
- A deployable pattern in GCP that respects real platform constraints
- Strong Infrastructure as Code support for repeatable deployment and policy management

During option analysis, several conceptually cleaner architectures were eliminated because of **hard GCP networking limitations**, especially around multi-interface firewall placement patterns. That materially narrowed the practical option set.

The two viable options are:

1. **Option A — Palo Alto appliance-based split-VPC egress design**
2. **Option B — Native GCP Cloud NGFW-based inspection design**

## Decision

We will treat **Option A (Palo Alto split-VPC design)** as the **preferred architecture** and **Option B (Cloud NGFW service)** as a **viable secondary option**.

Option A is preferred because it aligns more closely with the current enterprise security model, preserves the richer feature set of Palo Alto firewall appliances, and is more likely to pass leadership review without introducing a net new enforcement model.

Option B remains viable because it is cloud-native, quick to deploy, and fully manageable through Infrastructure as Code, but it is a newer direction for the organization and does not provide full parity with the capabilities currently expected from Palo Alto-based enforcement.

## Option A — Preferred: Palo Alto Appliance-Based Split-VPC Design

### Description

In this model:

- A client in the **Intranet VPC** reaches EWP over **PSC**
- PSC targets an **EWP service attachment** in the **Egress Workload VPC**
- **EWP** processes the request and initiates outbound internet traffic as needed
- The Egress Workload VPC uses a **default route to a trust-side internal load balancer**
- Traffic is inserted into a **Palo Alto VM-Series** inspection path
- The firewall performs **security policy enforcement and SNAT on untrust egress**
- Traffic exits via an **Untrust interface** in the **Public Egress VPC**
- The Public Egress VPC routes internet-bound traffic to the **default internet gateway**, with **Cloud NAT** in the outbound path
- Return traffic comes back to the SNAT source, re-enters the inspection path, and returns to EWP
- Responses to the original client return over the **PSC service path**, not via custom return routing to the consumer

### Traffic Summary

**Forward path:**

`Intranet VPC client → PSC endpoint → EWP service attachment → EWP → trust-side ILB → Palo Alto trust interface / policy → PAN SNAT on untrust egress → Public Egress VPC untrust interface → default internet gateway / Cloud NAT → Internet`

**Return path:**

`Internet → Cloud NAT / default internet gateway → Public Egress VPC untrust interface → PAN return route to trust interface → EWP → PSC response path → client`

### Why this is preferred

| Reason | Detail |
|--------|--------|
| **Feature completeness** | Palo Alto appliances provide a broader and better-understood feature set than the native NGFW service for likely inspection, control, and future policy requirements. |
| **Closer to existing security operating model** | This option better matches how the organization already reasons about inspection boundaries, policy ownership, and advanced firewall capabilities. |
| **Lower leadership friction** | Palo Alto-based enforcement is more likely to be accepted because it is closer to established patterns and does not require the same level of new-service confidence building. |
| **Clear zone separation** | The split between Egress Workload VPC and Public Egress VPC creates a cleaner security story than a more collapsed design. |
| **Operationally safer with SNAT** | Applying SNAT on the Palo Alto untrust side simplifies return-path behavior and reduces stateful symmetry risk. |

### Pros

- Mature, enterprise-grade inspection model
- Richer security feature set than the native NGFW service
- Easier to align with current security review expectations
- Stronger conceptual separation between workload-side and public egress-side components
- More explicit inspection boundary for ADR and review discussions

### Cons

- More moving parts than a native service design
- More net new routing and appliance insertion complexity in GCP
- Higher operational overhead than a managed cloud-native service
- Requires careful route design and appliance insertion validation

## Option B — Viable Secondary Option: Native GCP Cloud NGFW Design

### Description

In this model:

- A client in the **Intranet VPC** reaches **EWP** over **PSC**
- PSC targets an **EWP service attachment** in the **Egress Workload VPC**
- **EWP** initiates outbound internet traffic
- The Egress Workload VPC uses a route that steers traffic to a **Cloud NGFW firewall endpoint**
- A **regional or global firewall policy** provides inspection and enforcement capabilities
- Traffic then continues to the **default internet gateway**, with **Cloud NAT** in the outbound path
- Return traffic follows the managed service path back to EWP and then returns to the originating client over PSC

### Traffic Summary

**Forward path:**

`Intranet VPC client → PSC endpoint → EWP service attachment → EWP → Cloud NGFW firewall endpoint → default internet gateway / Cloud NAT → Internet`

**Return path:**

`Internet → Cloud NAT / default internet gateway → firewall endpoint path → EWP → PSC response path → client`

### Why this is viable

| Reason | Detail |
|--------|--------|
| **Cloud-native** | Uses managed Google Cloud security constructs rather than self-managed appliance infrastructure. |
| **Fast to deploy** | Eliminates the need to stand up and operate Palo Alto appliance components. |
| **IaC-friendly** | Firewall policies and associated service constructs are well-aligned with repeatable Infrastructure as Code workflows. |
| **Lower operational burden** | Reduces the amount of appliance lifecycle management compared to VM-based firewalls. |

### Pros

- Fastest path to implementation
- Native Google Cloud control plane and service model
- Fully controllable through Infrastructure as Code
- Lower appliance-management overhead
- Cleaner service ownership model from a cloud platform perspective

### Cons

- Net new service direction for the organization
- Does not provide full feature parity with Palo Alto appliances
- Less aligned with current leadership approval posture
- Requires additional confidence-building before it can be treated as the organizational default

## Alternatives Considered

### Alternative 1: Single / Shared VPC Design with EWP and Palo Alto

**Decision:** Rejected.

Conceptually simpler on paper, but GCP interface and routing constraints make it less clean in practice and weaken the security-zone separation story compared with the preferred split-VPC model.

### Alternative 2: Centralized Hub-and-Spoke Inspection with Palo Alto

**Decision:** Rejected.

Potentially useful as a long-term platform pattern, but adds hub/spoke complexity without improving the immediate use case enough to justify the additional overhead.

### Alternative 3: One-Arm Palo Alto Pattern

**Decision:** Rejected.

Operationally less clear, harder to troubleshoot, and less defensible than the preferred explicit trust/untrust split.

## Consequences

### Positive

- Clear preferred design for GCP outbound inspection with EWP
- Credible fallback / comparison option in native Cloud NGFW
- Decision record reflects that option selection is shaped by **hard GCP networking constraints**, not just architectural taste
- Preferred design gives security and leadership a more familiar review target

### Negative

- Preferred design carries more complexity and operational overhead than the native Cloud NGFW option
- Native Cloud NGFW may remain attractive enough to revisit later, so the ADR must explain clearly why it is not preferred today
- Some conceptually simpler alternatives are eliminated by platform limitations rather than by architectural preference alone

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Appliance-based route design becomes operationally brittle | Medium | High | Keep SNAT on Palo Alto untrust egress, separate packet-flow documentation from route annotations, and validate route behavior early in implementation. |
| Native Cloud NGFW option is later favored without enough feature validation | Medium | Medium | Keep it documented as viable, but require explicit feature-gap review and leadership sign-off before selection. |
| Leadership questions why native GCP service was not chosen | High | Medium | Document that the service is viable, but currently less aligned with the approved feature set and leadership posture than Palo Alto. |
| Architecture review focuses on rejected conceptual options | Medium | Low | Explicitly document GCP hard limitations and why they materially reduce the value of those alternatives. |

## Recommendation Summary

| Option | Recommendation | Why |
|--------|----------------|-----|
| **Option A — Palo Alto split-VPC** | **Preferred** | Stronger feature set, more aligned with current enterprise security posture, lower approval risk, cleaner security boundary story |
| **Option B — Cloud NGFW service** | **Viable secondary option** | Fast, cloud-native, IaC-friendly, but net new and not yet as fully approved or feature-complete for this use case |

## References

- Cloud NGFW overview: <https://docs.cloud.google.com/firewall/docs/about-firewalls>
- Option A diagram: `diagrams/gcp-internet-egress-option-a-palo-alto.png`
- Option B diagram: `diagrams/gcp-internet-egress-option-b-cloud-ngfw.png`
