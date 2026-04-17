# ADR: PAN-OS FQDN Policy for GTM-Backed Destinations

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-04-17 |
| **Proposed by** | Maximilian Browne |
| **Stakeholders** | Network Security, Cloud Platform Engineering, Security Leadership |
| **Supersedes** | N/A |

---

## Context

We evaluated whether **PAN-OS security policy using FQDN address objects** is a viable control for egress to **GTM-backed application destinations**.

The intended value of the pattern was straightforward:

- define destination policy in PAN-OS using an FQDN object
- allow workloads to reach approved application endpoints without manually tracking every backend IP
- simplify policy automation for destinations that may change over time

That model only works if the firewall's DNS view is a reliable proxy for the client's DNS view.

In our environment, that assumption does not hold.

Our GTM implementation returns destination IPs based on **client conditions, resolver context, and views**. As a result, the Palo Alto firewall may resolve a different destination IP set than the actual workload receives.

That creates a structural mismatch between:

- the IPs stored in the PAN-OS FQDN object
- the IP the client workload is actually handed by DNS
- the destination IP against which security policy is enforced

This is not a theoretical concern. It was observed during live testing.

## Test Summary

Testing was performed against a real GTM-backed application flow.

### Test setup

- A PAN-OS security rule used an **FQDN address object** as the destination
- The destination hostname was fronted by **GTM**
- A workload in **GCP** initiated traffic to that FQDN
- FQDN object resolution was checked on the firewall
- Policy match behavior was tested on the firewall using the resolved IPs
- Client-side DNS resolution behavior was compared against firewall-side FQDN resolution

### Observed behavior

The firewall successfully resolved the FQDN object to a set of IPs and policy testing succeeded for those resolved addresses.

However, the client workload could receive a **different GTM-selected IP** than the firewall had associated with the FQDN object.

In practical terms, the test demonstrated this failure mode:

- firewall-resolved destination = **IP 1**
- workload-resolved destination = **IP 2**

Because GTM answers were conditional, the firewall and the client were not guaranteed to receive the same answer for the same hostname.

## Decision

We will **not** use **PAN-OS FQDN address objects** as the enforcement primitive for GTM-backed destinations when DNS answers vary by client condition, resolver view, or source context.

## Rationale

### 1. GTM / client-view mismatch is a hard-fail condition

PAN-OS FQDN address objects represent **what the firewall resolved**, not **what the client will connect to**.

When GTM answers vary by source context, that difference becomes operationally significant. A policy can appear correct on the firewall while still failing or behaving inconsistently for the workload.

### 2. The design introduces management-plane dependency and load

FQDN object refreshes consume management-plane cycles on:

- Panorama
- local Palo Alto firewalls

That is undesirable in an environment where management plane capacity is already a concern.

### 3. The approach adds new failure points

Using FQDN objects for this use case introduces dependency on:

- management-plane DNS resolution
- management interface availability and bandwidth
- resolver reachability and correctness
- refresh timing / propagation timing

That is additional operational complexity for an already fragile enforcement path.

### 4. Refresh timing can create intermittent policy mismatches

Even if firewall and client resolution eventually converge, they may not converge at the same time.

This creates windows where:

- the client receives a newly handed-out GTM IP
- the firewall still holds an older answer set
- different firewalls may hold different answer sets at different times

That kind of staggered resolution is exactly how you get weird outages and painful troubleshooting sessions.

## Consequences

### Positive

- avoids building policy automation on an unreliable primitive
- prevents false confidence in FQDN-based allow rules for conditional DNS targets
- keeps focus on deterministic enforcement mechanisms

### Negative

- removes a potentially convenient abstraction for dynamic destinations
- means destination control must come from a more explicit inventory or another deterministic source of truth
- may require more engineering effort for automation design

## Recommendation

Do **not** proceed with FQDN-object-based security policy automation for this flow.

Instead, use a control mechanism based on a **known destination IP inventory** or another **deterministic source of truth** that does not depend on the firewall's independent DNS resolution behavior.

FQDN-based policy may only be reconsidered if all of the following become true:

- GTM behavior is effectively flattened
- all relevant clients receive the same destination answers
- the firewall DNS view is intentionally aligned with the client DNS view
- the management-plane and refresh-timing risks are explicitly accepted

Those conditions are not met today.

## Evidence Summary

Testing demonstrated that:

- PAN-OS FQDN object resolution can succeed on the firewall
- security policy matching can succeed for the firewall-resolved IPs
- the workload can still receive a different GTM-selected destination IP
- therefore, successful firewall-side FQDN resolution does **not** guarantee reliable client traffic enforcement

## Suggested Decision Statement

> Based on live testing, PAN-OS FQDN address objects are not a reliable policy primitive for GTM-backed destinations in our environment. Because DNS answers vary by client context, the firewall's resolved IP set can diverge from the workload's actual destination IP, creating enforcement mismatch risk. We should not use FQDN-based security policy automation for this flow.
