# GCP NetSec Automation — initial QE troubleshooting handoff

**Draft for review — operator links, support window and diagnostic details still required.** [Review and acceptance](handoff.md) · [Project index](../README.md).

## 1. Purpose and initial responsibilities

NSE provides IST-hours troubleshooting for QE defects against expected, supported automation patterns. NSE helps identify application/test configuration issues and missing platform prerequisites, coordinates correction with QE/platform operations, and escalates suspected automation architecture or service-catalog defects to **Network Security Architecture and Engineering (NSAE)** with diagnostic evidence.

The [shared support model](../shared/support-model.md) defines responsibility boundaries, exclusions, escalation and acceptance scenarios. Full catalog ownership and component maintenance/release ownership are not transferred in this phase.

## 2. Cloud-specific pattern context

- GKE patterns use developer-authored **Cilium network-policy entries**, not EKS `ServiceEntry` resources, with Gatekeeper guardrails and a separate verdict engine.
- Applicable intra-GCP patterns use source-tagged fleet firewall templates with service-specific IP containers. Sentinel/org-policy implementation PRs are reference placeholders pending Architecture input.

**TODO: authoritative supported-pattern/control-placement spreadsheet**, revision, supported projects, Regions/zones and environments. Third-party environments are not currently included in automation. See the [shared control model](../shared/control-model.md) for the primary/transitive distinction and cross-cloud context.

## 3. Support workflow and evidence

Follow the [QE defect-triage guide](../shared/qe-defect-triage.md): confirm the supported pattern, check application/test and platform prerequisites, inspect declaration/admission/verdict evidence, trace expected control behavior and resolve/route with evidence. Potential coverage gaps go through [risk-findings intake](../shared/risk-findings/README.md).

TODO: component-specific logs/dashboards, operator access, approved diagnostic commands, QE intake and NSAE/platform escalation queues. Gatekeeper guardrails are not the verdict decision, and admission success is not proof of working connectivity.

## 4. Coverage and change boundaries

- Coverage is during agreed India Standard Time (IST) support hours. TODO: exact hours/days, rota, support start and outside-hours routing.
- NSE assists diagnosis and coordination; changes follow the responsible team's approved access/change process.
- No new-pattern approval, automatic access bypass, risk acceptance, or service-catalog ownership is implied.
- TODO: agreed severity/response expectations; none are invented here.

## 5. Reference inputs and dependencies

- [Shared CRE integration](../shared/cre/README.md): TODO: policy-plumbing/lifecycle spreadsheet and actual deployed status.
- TODO: flow spreadsheet, declaration/verdict implementation references and Gatekeeper constraints/namespace limits.
- TODO: platform/Sentinel/organization-policy implementation PRs applicable to this cloud.
- TODO: NSAE-provided risk document, linked from the shared risk intake.

## 6. Support-readiness acceptance

Demonstrate cloud-applicable cases of application/configuration triage, missing platform prerequisite diagnosis, evidence-based NSAE escalation and a potential control-gap report. Verify required access and escalation routes. Record evidence and open blockers in [handoff.md](handoff.md); acceptance is limited to the support scope, not full steady-state project ownership.
