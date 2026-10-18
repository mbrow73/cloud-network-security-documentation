# NetSec Automation — QE defect-triage guide

**Draft procedure — component-specific links, access and commands still required before execution-ready acceptance.** [Support scope and ownership](support-model.md).

## 1. Establish expected behavior and collect the case

Capture the QE defect ID, affected cloud/environment/pattern, source and destination identities, timestamp/time zone, protocol/port, test method, expected result, observed result, scope/impact, and recent relevant changes. Link the applicable pattern and revision in **TODO: authoritative supported-pattern/control-placement spreadsheet**. If the pattern is absent or unclear, request NSAE classification rather than assuming the requested access should work.

Capture declaration/verdict/admission results and relevant deployment/run IDs. Use approved evidence locations and redact secrets. TODO: defect intake form, log/dashboard links, operator roles and approved diagnostic commands.

## 2. Check application and test prerequisites

With QE/application owners, verify that the test uses the intended endpoint and approved port/protocol; that name resolution points to the expected destination; and that the destination application is running, listening and healthy. Confirm the reported symptom rather than labeling every failure a firewall defect. Record what was observed; do not change a production service without its owner's approved process.

## 3. Check source declaration and platform prerequisites

- **AWS Lambda / SG-based patterns:** identify the required AFT-vended SG and verify the correct group is attached to the intended workload and the expected egress rule exists. A provisioned-but-unattached SG and a missing SG are different failure cases. Route vending failures to AFT Operations and attachment/test configuration issues to the workload owner with NSE assistance.
- **AWS EKS:** inspect the developer-authored `ServiceEntry`, its Gatekeeper result and the separate verdict result.
- **GCP GKE:** inspect the developer-authored Cilium network-policy entry, its Gatekeeper result and the separate verdict result. Do not call it an EKS `ServiceEntry`.
- **On-premises cloud Kubernetes source:** verify the applicable service-entry/verdict prerequisites from the pattern sheet; implementation details and platform ownership remain TODO.

Gatekeeper enforces declaration guardrails (such as per-namespace entry limits and wildcard restrictions); **Gatekeeper is not the verdict engine**. A successful admission check is not proof of a successful verdict or working runtime traffic. TODO: exact policies, limit values, verdict-engine name, evidence locations and runtime enforcement checks for each supported pattern.

## 4. Trace the expected primary and transitive control path

Use the control-placement sheet to identify the actual primary control, its intended effect, downstream Palo Alto/Illumio/other controls, and the identities visible at each relevant point. Compare expected and observed policy/verdict/runtime evidence without assuming that a timeout or admission success proves a particular component's behavior.

For CRE, use **TODO: CRE policy-plumbing/lifecycle spreadsheet** and **TODO: registration status, logs and policy references**. Record missing/stale registration or partial provisioning; do not invent an integration retry or manually open broad access.

For applicable intra-GCP patterns, compare source tags, destination container allocation and expected firewall policy. Consult **TODO: Sentinel/org-policy enforcement PRs** and **TODO: IP-container allocation evidence** for the governed deployment path.

## 5. Resolve or route with evidence

| Finding | Action |
| --- | --- |
| Test/application configuration error | Help QE/application owner correct through the approved process; retain evidence and request retest |
| Missing platform/AFT prerequisite | Coordinate provisioning recovery with the platform/AFT owner; retest after confirmation |
| Suspected automation execution, verdict, catalog or architecture defect | Escalate to NSAE with the evidence below; escalate an unresolved suspicion without waiting for conclusive proof |
| Unexpected allow, missing expected control or suspected coverage gap | Submit a [risk finding](risk-findings/README.md) and flag to NSAE; record urgent impact through the designated escalation route |
| Unsupported/ambiguous pattern or insufficient diagnostic access | Ask NSAE or the responsible component owner for classification/access support; record the blocker |

### NSAE escalation package

Include defect/pattern IDs and revision, source/destination context, expected and observed behavior, timestamp, sanitized reproduction, relevant configuration/admission/verdict/run/log references, checks performed and their results, business/test impact, and current suspected failing layer. State unknowns and whether an application/platform cause has been ruled out or remains possible. TODO: escalation queue/contact and response expectations.

## 6. Retest and close the support loop

Ask QE to rerun the expected pattern after the responsible owner confirms the correction. Record outcome, root cause or current hypothesis, remediation owner, linked engineering/platform tickets and outstanding follow-ups. If connectivity works but expected controls are missing, keep the control-gap finding open independently; a successful traffic test alone does not close it.

TODO: approved case closure criteria and owner, evidence retention and knowledge/runbook update process.
