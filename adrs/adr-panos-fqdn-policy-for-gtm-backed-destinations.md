# PAN-OS FQDN Object Testing for GTM-Backed Destinations

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-04-17 |
| **Prepared by** | Maximilian Browne |
| **Audience** | Network Security Leadership, Cloud Platform Engineering |
| **Document Type** | Test Findings and Recommendation |

---

## Purpose

Document the results of live testing performed to evaluate whether **PAN-OS FQDN address objects** are a viable control for **GTM-backed application destinations**.

This document is intended to present the observed behavior, identified risks, and a recommendation for leadership review. It is not written as a final governance decision.

## Background

The proposed value of FQDN-based policy was straightforward:

- define destination policy in PAN-OS using an FQDN object
- allow workloads to reach approved application endpoints without manually tracking every backend IP
- simplify policy automation for destinations that may change over time

That model depends on one key assumption:

> the firewall's DNS view is a reliable proxy for the client's DNS view

The testing below shows that assumption does not hold for this GTM-backed flow.

## Test Scope and Method

Testing was performed against a real GTM-backed application flow.

### Test setup

- A PAN-OS security rule used an **FQDN address object** as the destination
- The destination hostname was fronted by **GTM**
- A workload in **GCP** initiated traffic to that FQDN
- FQDN object resolution was checked on the firewall
- Policy match behavior was tested on the firewall using the resolved IPs
- Client-side DNS resolution behavior was compared against firewall-side FQDN resolution

### What was being validated

The test was intended to answer a practical question:

> Can PAN-OS FQDN address objects be relied on for policy enforcement when GTM answers may vary by client condition, resolver context, or view?

## Findings

### 1. Firewall-side FQDN resolution succeeded

The firewall successfully resolved the FQDN object to a set of destination IPs.

Policy testing on the firewall also succeeded for those firewall-resolved IPs.

### 2. Client-side DNS resolution was not guaranteed to match firewall-side resolution

The client workload could receive a **different GTM-selected IP** than the firewall had associated with the same FQDN object.

In practical terms, the observed failure mode looked like this:

- firewall-resolved destination = **IP 1**
- workload-resolved destination = **IP 2**

Because GTM answers were conditional, the firewall and the client were not guaranteed to receive the same answer for the same hostname.

### 3. This creates a policy enforcement mismatch risk

PAN-OS FQDN address objects represent **what the firewall resolved**, not necessarily **what the client will connect to**.

When GTM answers vary by source context, that difference becomes operationally significant. A policy can appear correct on the firewall while still failing or behaving inconsistently for the workload.

## Risks Observed During Evaluation

### 1. GTM / client-view mismatch is a hard-fail condition

This is the primary viability issue.

If GTM returns different destination IPs to different clients or resolvers, the firewall may enforce policy based on an IP set that does not match the workload's actual destination.

### 2. FQDN refreshes introduce management-plane load

FQDN object refreshes consume management-plane cycles on:

- Panorama
- local Palo Alto firewalls

That is undesirable in an environment where management plane capacity is already a concern.

### 3. The approach adds additional failure points

Using FQDN objects for this use case introduces dependency on:

- management-plane DNS resolution
- management interface availability and bandwidth
- resolver reachability and correctness
- refresh timing and propagation timing

That adds operational complexity to an already sensitive enforcement path.

### 4. Staggered resolution timing can create intermittent issues

Even if firewall and client resolution eventually converge, they may not converge at the same time.

This creates windows where:

- the client receives a newly handed-out GTM IP
- the firewall still holds an older answer set
- different firewalls may hold different answer sets at different times

That kind of staggered resolution can create intermittent policy mismatches and difficult troubleshooting conditions.

## Assessment

Based on live testing, **PAN-OS FQDN address objects do not appear to be a reliable enforcement primitive for GTM-backed destinations when DNS answers vary by client condition, resolver view, or source context**.

The approach may still be workable in environments where DNS answers are effectively flat and uniform for all clients traversing the policy domain, but that was not true in this test scenario.

## Recommendation for Leadership Review

Based on the observed behavior, the recommended path is:

- **do not proceed** with FQDN-object-based security policy automation for this flow in its current form
- use a control mechanism based on a **known destination IP inventory** or another **deterministic source of truth** that does not depend on the firewall's independent DNS resolution behavior

FQDN-based policy could be reconsidered only if all of the following become true:

- GTM behavior is effectively flattened
- all relevant clients receive the same destination answers
- the firewall DNS view is intentionally aligned with the client DNS view
- the management-plane and refresh-timing risks are explicitly accepted

## Evidence Summary

Testing demonstrated that:

- PAN-OS FQDN object resolution can succeed on the firewall
- security policy matching can succeed for the firewall-resolved IPs
- the workload can still receive a different GTM-selected destination IP
- therefore, successful firewall-side FQDN resolution does **not** guarantee reliable client traffic enforcement

## Suggested Leadership Summary

> Live testing showed that PAN-OS FQDN address objects are not a reliable control for this GTM-backed flow because the firewall's DNS answer can diverge from the workload's DNS answer. That creates a policy enforcement mismatch risk. Based on these findings, the recommendation is not to proceed with FQDN-based policy automation for this use case unless DNS behavior is made uniform across the relevant clients and enforcement path.
