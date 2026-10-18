# AWS NetSec Automation — troubleshooting

**Substantive first-pass draft, not a validated command-by-command runbook.** [Project expectations](../shared/README.md) · [AWS scope](README.md).

## 1. Establish the expected pattern

Capture the QE defect/request, environment, pattern, source/destination, port/protocol, symptom, timestamp and expected result. Use **TODO: pattern/control-placement spreadsheet**, including implemented versus planned status.

NSE supports both clouds and all automation patterns during agreed IST hours. Use phase status to establish what should exist now; a planned control is not a failed implemented control. This guide covers the AWS checks within that assignment.

## 2. Check application and platform prerequisites

Verify the intended endpoint/port and whether the destination application is running/listening. Compare the actual deployed configuration with the expected pattern using available evidence.

For an SG-based pattern, distinguish **a required SG not vended by AFT** from **an existing SG not attached to the intended workload**. Compare its actual egress configuration with the expected pattern. Check available provisioning evidence with AFT Operations when a prerequisite is missing.

For EKS patterns, use the applicable current-phase declaration/configuration references; ServiceEntry is the described declaration model. Gatekeeper is externally owned and verdicting is not implemented yet. Do not invent a verdict diagnostic step.

## 3. Select the resolution path

- **Configuration/provisioning issue:** help QE/requestors diagnose and coordinate the fix with the application or AFT/platform owner. Retain useful evidence and request a retest.
- **Individual access request:** NSE may help complete the request form and implement access through the normal authorized process when it meets **NetSec Standard Tech 08.11** and has an appropriate business justification. **TODO: standard and existing request-process links.** This does not transfer blanket platform privileges or approval authority.
- **Missing automation pattern or shared catalog access:** escalate to **NSAE — Network Security Architecture and Engineering**. A CRE catalog/template change can affect many resources or environments and must not be treated as an individual access request. When scope/impact is unclear, ask NSAE to classify it.
- **Suspected gap in an expected implemented control:** record the observation in the [risk-findings PR area](../shared/risk-findings/README.md) and flag it to NSAE. Distinguish an observed gap from explicitly planned future work.

## 4. Escalate and retest

Provide pattern/environment context, expected versus observed behavior, timestamp, useful configuration/run/log references, checks performed, impact and unknowns. Conclusive root cause is not required before escalation. Help QE retest once the responsible owner makes a correction; link remaining engineering/risk follow-ups.

**TODO: existing QE/NSAE/AFT/platform request/escalation routes and relevant diagnostic links.** These are reference placeholders, not requirements to create new component manuals.

See the [Continuous Registration Engine outline](../shared/cre/README.md) for the planned explanation of policy plumbing and how to recognize a missing catalog pattern.
