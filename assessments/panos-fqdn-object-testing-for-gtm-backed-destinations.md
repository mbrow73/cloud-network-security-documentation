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

This document captures the results of testing PAN-OS FQDN address objects against a GTM-backed application flow.

The goal was simple: figure out whether FQDN objects are a dependable way to control traffic to destinations whose DNS answers may change based on resolver path, client conditions, or GTM policy.

This is a findings document, not a final architecture decision.

## Background

The appeal of FQDN-based policy is obvious:

- define policy in PAN-OS by hostname instead of tracking backend IPs by hand
- let approved workloads reach the right destination even when the backend changes
- simplify automation for destinations that are expected to move over time

That only works if the firewall is resolving the same destination the workload is actually sent to.

For this flow, that assumption did not hold.

## Test Scope

Testing was performed against a real GTM-backed application flow.

The test setup was:

- a PAN-OS security rule using an **FQDN address object** as the destination
- a destination hostname fronted by **GTM**
- a workload in **GCP** initiating traffic to that FQDN
- firewall-side FQDN resolution checks
- policy match testing on the firewall using the resolved IPs
- comparison of firewall-side resolution and client-side DNS behavior

The question being tested was:

> Can PAN-OS FQDN address objects be relied on for policy enforcement when GTM may hand out different answers depending on resolver context, client conditions, or view?

## Findings

### Firewall-side resolution worked

The firewall resolved the FQDN object successfully and associated it with a set of destination IPs.

Policy testing on the firewall also worked for those firewall-resolved IPs.

### Client-side resolution did not reliably match firewall-side resolution

The workload could receive a different GTM-selected IP than the firewall had associated with the same FQDN object.

In practical terms, the failure mode looked like this:

- firewall resolves the destination to **IP 1**
- workload is handed **IP 2**

Because GTM answers were conditional, the firewall and the workload were not guaranteed to receive the same answer for the same hostname.

### That creates an enforcement mismatch

PAN-OS FQDN address objects reflect **what the firewall resolved**. They do not necessarily reflect **what the client will connect to**.

Once those two diverge, the policy can look correct on the firewall and still fail for the workload.

## Risks Identified

### GTM / resolver mismatch is the hard fail

This is the main issue.

If GTM returns different destination IPs to different resolvers or client contexts, the firewall can end up enforcing policy against a destination set that does not match the workload's actual destination.

### FQDN refreshes add management-plane load

FQDN object refreshes consume management-plane cycles on:

- Panorama
- local Palo Alto firewalls

That is not ideal in an environment where management plane capacity is already tight.

### The design adds more moving parts

Using FQDN objects for this flow adds dependency on:

- management-plane DNS resolution
- management interface availability and bandwidth
- resolver reachability and correctness
- refresh timing and propagation timing

That is extra operational fragility for an already sensitive path.

### Resolution timing can drift

Even if firewall and client answers eventually converge, they may not converge at the same time.

That creates windows where:

- the client has already been handed a new GTM-selected IP
- the firewall is still holding an older answer set
- different firewalls may hold different answers at the same time

That is exactly the kind of timing mismatch that produces intermittent failures and ugly troubleshooting.

## Assessment

Based on live testing, **PAN-OS FQDN address objects do not appear to be a reliable enforcement control for this GTM-backed flow when DNS answers vary by resolver path, client condition, or view**.

That should not be read as "FQDN objects are always bad." If a target FQDN returns effectively flat and uniform answers across the relevant resolver paths, FQDN objects may still be workable.

That was not the case here.

## Recommendation for Leadership Review

Based on what was observed during testing, the recommendation is:

- **do not proceed** with FQDN-object-based policy automation for this flow in its current form
- use a control based on a **known destination IP inventory** or another **deterministic source of truth** that does not depend on the firewall's independent DNS resolution behavior

FQDN-based policy could be reconsidered if all of the following become true:

- GTM behavior is effectively flattened for the target destination
- all relevant clients receive the same destination answers
- the firewall DNS view is intentionally aligned with the client DNS view
- the management-plane and refresh-timing risks are accepted

## Evidence Summary

The testing showed that:

- PAN-OS FQDN object resolution can succeed on the firewall
- policy match testing can succeed for the firewall-resolved IPs
- the workload can still receive a different GTM-selected destination IP
- successful firewall-side resolution therefore does **not** guarantee correct client traffic enforcement

## Suggested Leadership Summary

> Live testing showed that PAN-OS FQDN address objects are not a reliable control for this GTM-backed flow because the firewall can resolve a different destination than the workload is actually handed by DNS. That creates a policy enforcement mismatch risk. Based on these findings, the recommendation is not to proceed with FQDN-based policy automation for this use case unless DNS behavior is made uniform across the relevant resolver paths and enforcement path.
