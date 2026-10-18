# NSE troubleshooting — AWS and GCP

**Working draft.** General diagnosis and request-versus-architecture routing for NSE. The [NetSec Automation expectations](../projects/netsec-automation/shared/README.md) link here rather than duplicate this procedure. Reuse by another project does not itself extend that project's support scope.

## 1. Establish the expected pattern

Capture the QE defect/request, cloud/environment, pattern, source/destination, port/protocol, symptom and expected result. Use **TODO: supported-pattern/control-placement spreadsheet**, with implemented versus planned status.

For NetSec Automation, support covers **both AWS and GCP and all automation patterns**. Current-phase status tells the operator what should exist now; it does not exclude a pattern from diagnosis or imply a planned control already exists. Verdicting is not implemented yet, and Gatekeeper administration is outside this handoff.

## 2. Check application and platform prerequisites

Check the intended endpoint/port and whether the destination application is running/listening. Compare the actual deployed configuration with the expected pattern using existing evidence. For AWS, distinguish an SG not vended by AFT from an existing SG not attached by the workload/requestor. For GCP, check the applicable existing firewall/template, source tags and IP-container placement when relevant.

Only investigate controls implemented for that pattern's phase. Route platform-owned component issues to the responsible team rather than taking over its administration.

## 3. Select the right resolution path

- **Configuration or provisioning issue:** help QE/requestors diagnose and coordinate the fix with the application, AFT or platform owner. Retain the useful checks/evidence and request a retest.
- **Individual access request:** NSE may help the requestor complete the request form and implement access through the normal authorized process, provided it meets **NetSec Standard Tech 08.11** and has an appropriate business justification. **TODO: standard link and existing request-form/process link.** This guide references the standard; it does not invent its requirements or transfer platform privileges/approval authority.
- **Missing automation pattern or catalog-level access:** escalate to **NSAE — Network Security Architecture and Engineering**. For example, changing CRE service-catalog coverage can affect many resources/environments; this is not an ordinary one-time request. NSE should identify the gap and provide evidence, not modify shared templates/catalog scope or treat a broad automation change as an individual request. If the impact/scope is unclear, ask NSAE to classify it.
- **Suspected gap in an expected implemented control:** record the observation through the project's [risk-findings PR area](../projects/netsec-automation/shared/risk-findings/README.md) and flag it to NSAE. Distinguish this from an explicitly planned feature not yet delivered.

## 4. Escalate and close the loop

For an architecture/catalog issue, provide pattern/cloud context, expected versus observed behavior, relevant timestamp/configuration/log references, checks performed, impact and unknowns. Conclusive root cause is not required to raise a suspected design defect. Help QE retest after the responsible owner implements a correction and link any remaining engineering/risk follow-up.

**TODO: existing QE/NSAE/AFT/platform request and escalation routes, and useful diagnostic links.** Exact support coverage is recorded at the project expectations level, not invented by this general guide.

## CRE context

See the existing [Continuous Registration Engine explanation](../projects/netsec-automation/shared/cre/README.md) for its role in cross-cloud downstream policy plumbing. It is an explanatory outline to refine, not a transfer of full CRE platform or service-catalog ownership.
