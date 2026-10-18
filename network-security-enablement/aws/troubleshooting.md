# AWS network troubleshooting

**Draft.** Common technical checks for AWS connectivity issues. Project-specific workflows determine who resolves a finding, which request process applies, and when to escalate; this guide does not transfer project or platform ownership.

## 1. Capture the flow and symptom

Record the environment, source/destination, port/protocol, test time, expected outcome, observed result and recent relevant changes. Use the applicable project's pattern/configuration reference.

## 2. Check the application and request

Confirm that the test uses the intended endpoint and port/protocol, and that the destination application is running and listening. Confirm what access is needed and distinguish missing requested access from incorrectly configured application behavior.

## 3. Check applicable cloud controls

For an SG-based flow, check whether the required SG exists, whether it is attached to the intended workload, and whether its egress configuration matches the intended access. Where AFT must vend the SG, distinguish a provisioning failure from a workload attachment/configuration issue and capture the relevant evidence.

For Kubernetes-related flows, use the relevant platform's existing references and owner support. Do not infer a successful authorization decision merely from a declaration being present.

## 4. Record the finding

Record the failing layer or current hypothesis, checks performed, useful configuration/run/log evidence and unknowns. Relevant findings include an application/test configuration issue, missing prerequisite, missing individual access, or a suspected shared policy/automation gap. A suspected cause does not need to be conclusively proven before asking the responsible team for help.

Return to the originating project's workflow to choose remediation, request assistance or architecture escalation. After the responsible owner makes a correction, retest and link unresolved follow-ups.

## Related workflows and request guides

- [NetSec Automation — AWS QE defect handling](../projects/netsec-automation/aws/qe-defect-handling.md).
- [AWS standard security-group requests](requests/standard-security-group-requests.md) — placeholder.
- [AWS third-party standard requests](requests/third-party-standard-requests.md) — placeholder.
- **Diagnostic references / platform contacts:** TODO: insert existing links.
