# 001 Environment Resolution Design

This document captures the environment-resolution design that supports ADR-001.

## Problem

The policy engine must determine the environment classification of both source and destination workloads so that cross-environment access policies can be enforced.

## On-Prem Destination Resolution

### Constraints

- DDI (Cygna Labs IPControl) does not reliably provide environment metadata
- ITSM is the system of record for on-prem asset classification and change-management context

### Proposed Resolution Chain

`FQDN -> IP resolution -> ITSM asset lookup by IP/hostname -> environment field -> policy decision`

## Caching Guidance

Live ITSM lookups during request evaluation will add latency. Recommended pattern:

- build a cached lookup table from ITSM
- refresh on a regular interval
- use live query only on cache miss or reconciliation path

## AWS Source Environment Resolution

Two approaches were evaluated.

### Approach A: Programmatic Resolution (Target State)

Resolve environment from AWS account metadata instead of developer self-declaration.

Suggested chain:

`account ID -> AWS Organizations account name -> pattern match -> fallback to VPC tags -> manual classification if unresolved`

Benefits:
- stronger trust model
- lower chance of intentional or accidental misclassification

Tradeoffs:
- requires supporting integrations and data hygiene
- needs fallback handling for accounts with poor metadata

### Approach B: Developer-Declared Environment (POC Path)

The developer declares source and destination environment in the request schema.

Benefits:
- fastest to implement
- no integration dependency for initial POC

Risks:
- misclassification can bypass intended policy checks
- requires periodic reconciliation against actual metadata

## Recommendation

Use **Approach B** for initial POC speed, while building **Approach A** in parallel. Move to Approach A once validated.
