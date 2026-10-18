# AWS network troubleshooting

**Draft.** Common technical checks for AWS connectivity issues. Project-specific workflows determine who resolves a finding, which request process applies, and when to escalate; this guide does not transfer project or platform ownership.

## 1. Capture the flow and symptom

Record the environment, source/destination, port/protocol, test time, expected outcome, observed result and recent relevant changes. Use the applicable project's pattern/configuration reference.

## 2. Check the application and request

Confirm that the test uses the intended endpoint and port/protocol, and that the destination application is running and listening. Confirm what access is needed and distinguish missing requested access from incorrectly configured application behavior.

## 3. Check applicable cloud controls

For an SG-based flow, check whether the required SG exists, whether it is attached to the intended workload, and whether its egress configuration matches the intended access. Where AFT must vend the SG, distinguish a provisioning failure from a workload attachment/configuration issue and capture the relevant evidence.

For Kubernetes-related flows, use the relevant platform's existing references and owner support. Do not infer a successful authorization decision merely from a declaration being present.

### CRE-backed Palo Alto paths

For a blocked flow using CRE-enabled policy, capture the blocking firewall/rule evidence and obtain the CRE API call response from QE/the requesting team. A deny may reflect an unmade/failed registration call or unexpected group membership even when the policy scaffolding already exists. Follow the [CRE registration-versus-scaffolding checks](../projects/netsec-automation/shared/cre/README.md#diagnosing-blocked-cre-backed-traffic) before treating the block as missing catalog coverage.

## 4. Record the finding

Record the failing layer or current hypothesis, checks performed, useful configuration/run/log evidence and unknowns. Relevant findings include an application/test configuration issue, missing prerequisite, missing individual access, or a suspected shared policy/automation gap. A suspected cause does not need to be conclusively proven before asking the responsible team for help.

Return to the originating project's workflow to choose remediation, request assistance or architecture escalation. After the responsible owner makes a correction, retest and link unresolved follow-ups.

## 5. Provision missing individual access

For a missing individual access requirement, NSE may help the requestor complete a **request form to provision the missing access** and implement it through the normal authorized process when it meets **NetSec Standard Tech 08.11** and has an appropriate business justification. Follow the [AWS standard security-group requests guide](requests/standard-security-group-requests.md) once populated. For a third-party environment, use the [third-party standard request guide](requests/third-party-standard-requests.md) once populated.

- **NetSec Standard Tech 08.11:** TODO: insert supporting document link.
- **Request form / authorized implementation process:** TODO: insert supporting form/process link.

If the finding instead requires changing shared automation/catalog coverage, follow the originating project's architecture-escalation route rather than treating the change as individual access. This guidance does not grant shared catalog/template change authority or other teams' platform privileges.

## Related workflows and request guides

- [NetSec Automation — AWS QE defect handling](../projects/netsec-automation/aws/qe-defect-handling.md).
- [AWS standard security-group requests](requests/standard-security-group-requests.md) — placeholder.
- [AWS third-party standard requests](requests/third-party-standard-requests.md) — placeholder.
- **Diagnostic references / platform contacts:** TODO: insert existing links.
