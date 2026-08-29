# 001 POC Implementation Plan

This document captures the execution checklist for the **Phase 1 POC** approved by ADR-001.

## Scope

- Split Control Plane only
- Non-Illumio routable hosts only
- ISAFE manages Palo Alto gateway policy
- SG Framework manages AWS-side enforcement

## Prerequisites

- Validate FQDN object support on the EQUINIX_DC Palo Alto
- Validate PAN-OS API / Terraform provider connectivity
- Identify candidate POC workloads with stable, known traffic patterns

## Developer Experience

- Standardize developer submission schema for gateway policy requests
- Align with Stephen Bulmer on submission flow, notifications, and error handling
- Keep SG Framework and ISAFE request schemas compatible enough to support future unification

## Policy Engine

- Define zero-touch approval criteria
- Define reject / exception handling path
- Define lifecycle controls: TTL, expiration, review cadence, and orphan cleanup

## Operational Readiness

- Establish logging and monitoring for ISAFE-pushed rules
- Define and test rollback procedure
- Coordinate proposed POC coarse-grain Core/Midrange rules
- Coordinate with Illumio team to confirm workload boundaries
- Finalize measurable success criteria before kickoff
