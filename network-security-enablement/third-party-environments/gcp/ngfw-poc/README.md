# GCP third-party environment — NGFW proof of concept

**Draft outline — test scope and platform to confirm; not a production handoff.** [Review and acceptance](handoff.md).

## 1. Objective, hypothesis, and scope

TODO: specify the NGFW product/tier, use case, questions the POC must answer, GCP projects/Regions/zones, test workloads/flows, and explicit exclusions. Do not infer the test design from the directory name.

## 2. Candidate architecture and prerequisites

TODO: approved test design, traffic/inspection paths, required policies and dependencies, access, licensing/cost owner, test-data constraints, and isolated deployment boundaries.

Related design background: [GCP third-party ingress reverse-proxy removal ADR](../../../../adrs/adr-gcp-third-party-ingress-reverse-proxy-removal.md). Confirm applicability; that ADR is not evidence that this POC has been approved, deployed, or passed.

## 3. Test plan and success criteria

TODO: define test cases and measurable pass/fail criteria before execution, covering intended inspection/enforcement, observability, traffic compatibility, performance, failure/recovery, and any required TLS/control parity. Mark untested capabilities explicitly rather than implying equivalence.

## 4. Execution and evidence

TODO: exact supported platform/version procedures, baseline capture, controlled changes, positive/negative tests, evidence locations, observed results, defects, and retest tracking. No real results are asserted in this outline.

## 5. Operational assessment

TODO: policy/certificate ownership where applicable, alerting, triage, update lifecycle, required skills, support boundaries, cost observations, and limitations or control gaps.

## 6. Stop conditions, recovery, and cleanup

TODO: abort criteria, restoration steps and validation, resource removal, access revocation, and billing checks. Specify who owns any resources that remain after the POC.

## 7. Verdict and next decision

TODO: record pass/fail/inconclusive by criterion, findings, risks, and recommendation. Distinguish accepting the POC evidence/support scope from authorizing production adoption; any production handoff needs its own approved scope and readiness evidence.
