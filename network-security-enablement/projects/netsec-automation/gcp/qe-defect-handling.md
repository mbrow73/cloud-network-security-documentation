# NetSec Automation — GCP QE defect handling

**Draft.** [Project expectations](../shared/README.md) · [General GCP troubleshooting](../../../gcp/troubleshooting.md).

## 1. Confirm the pattern and expected phase behavior

Capture the QE defect, automation pattern, environment and expected versus observed behavior. Support covers both AWS and GCP and all automation patterns during agreed IST hours. Use the pattern sheet to distinguish implemented functionality from planned work; verdicting is not implemented yet and Gatekeeper is owned by Cloud Security.

**Pattern / control-placement sheet:** TODO: insert link.

## 2. Diagnose with the cloud guide

Use [general GCP network troubleshooting](../../../gcp/troubleshooting.md) for application, request and applicable cloud-control checks. Record the finding and available evidence here rather than duplicate the technical procedure.

## 3. Act on the result

- **Application/test configuration issue:** help QE/requestors resolve it or give the responsible application team guidance, then retest.
- **Missing platform prerequisite:** coordinate with the responsible platform operations team. For example, an unexpected IP allocation or tag/firewall mismatch needs the relevant platform/configuration owner.
- **Missing individual access:** follow the [general GCP missing-access process](../../../gcp/troubleshooting.md#5-provision-missing-individual-access). Confirm this is an individual access requirement, not missing shared automation/catalog coverage.
- **Blocked CRE-backed pattern:** obtain the requesting team's CRE API response and use the [CRE registration/scaffolding checks](../shared/cre/README.md#diagnosing-blocked-cre-backed-traffic). Coordinate registration/integration failures with the responsible owner; a deny alone is not evidence of missing catalog policy.
- **Missing shared automation/catalog access or suspected design flaw:** escalate to **NSAE — Network Security Architecture and Engineering** with the pattern, impact, expected/observed result and available evidence. A CRE/catalog change can affect many resources; do not treat it as a one-time access request or change shared catalog scope under the standard request process.
- **Suspected gap in an expected implemented control:** submit a [risk finding](../shared/risk-findings/README.md) and flag it to NSAE. Keep planned features distinct from current control gaps.

If the scope or blast radius is unclear, ask NSAE to classify the issue. Conclusive root cause is not required before escalation. NSE support does not transfer full catalog ownership or other teams' platform privileges.

## 4. Retest and track follow-up

Ask QE to retest after the responsible owner makes the correction. Link engineering, platform, request and risk follow-ups as applicable.

- **QE / NSAE / platform routing:** TODO: insert existing contact/queue links.
- [Continuous Registration Engine](../shared/cre/README.md) — registration and policy-scaffolding explanation.
