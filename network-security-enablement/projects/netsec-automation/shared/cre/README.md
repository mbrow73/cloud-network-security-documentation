# Continuous Registration Engine (CRE) — AWS and GCP

**Draft for review.** CRE is a proprietary NetSec application with an API that provisions required downstream access on Palo Alto and Illumio. This document explains the Palo Alto registration and policy-scaffolding path. Illumio-specific behavior remains a supporting-reference placeholder; Palo Alto mechanics must not be assumed to apply to Illumio.

[Project expectations](../README.md) · [Review decision](handoff.md).

## Registration versus policy scaffolding

**Policy scaffolding** is the prebuilt firewall policy for an automated traffic pattern. It allows traffic from a source address group to a destination address group on the required service/port. The [pattern/control-placement sheet](../README.md#references) identifies the automated traffic patterns.

**CRE registration** supplies IP-to-tag mappings to downstream Palo Alto firewalls. Tag-based Dynamic Address Groups (DAGs) populate from those registrations. Existing rules using the matching groups then apply to the newly registered resources. CRE does not need to create or edit an allow rule for every new cluster/resource joining an existing pattern.

The group definitions and policy scaffolding must already be configured and committed. Updating dynamic registered IP/tag membership does **not** require a new firewall commit; changing the rules or group definitions is a different configuration change. See [Palo Alto dynamic registration](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/addresses/register-ip-addresses-and-tags-dynamically) and [address-group behavior](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/address-groups).

## Provisioning flow

1. A new AWS account is vended through AFT, or the platform team provisions a component such as an EKS/GKE cluster.
2. The applicable hook/platform integration calls the CRE API with the relevant addresses and classification context. For example, the AFT hook identifies EKS subnet addresses that need the EKS tag.
3. CRE registers the applicable IP/tag mappings on the required downstream Palo Alto firewalls.
4. The matching DAGs populate from those registrations.
5. Existing policy-scaffolding rules referencing those groups apply to the registered resources.

```text
AFT hook / platform provisioning
  -> CRE API call with address + tag context
  -> registered IP/tag mappings on downstream Palos
  -> matching Dynamic Address Group membership
  -> existing policy-scaffolding rule applies
```

The API caller's response is diagnostic evidence. Whether it confirms request acceptance or completed delivery to every target is still to be documented; do not infer this from an HTTP success status alone.

- **Hook / platform integration references:** TODO: insert document links.
- **CRE request and response example:** TODO: insert sanitized example/document link.
- **Response success / partial-failure meaning and propagation timing:** TODO: insert explanation/supporting link.

## Example: EKS/GKE to on-premises Hydra

The downstream Palos contain policy scaffolding allowing the applicable EKS/GKE source address group to the on-premises Hydra VIP destination address group on port 443.

When a new EKS or GKE cluster is provisioned and the platform integration makes the CRE call, its registered addresses join the applicable source group. The cluster then matches the existing policy, without a new commit for that membership update. The existing allow rule is reused; this is not a new per-cluster firewall rule.

- **Hydra pattern / group and policy names:** TODO: insert pattern/reference link.
- **Applicable environments and downstream firewalls:** TODO: insert scope/reference link.

## Diagnosing blocked CRE-backed traffic

A Palo Alto deny does **not** establish that policy scaffolding is missing. The policy may exist while the CRE call was never made, failed, used incorrect registration context, or did not produce the expected membership on the firewall seeing the flow.

1. **Capture the blocked flow.** Use [AWS troubleshooting](../../../../aws/troubleshooting.md) or [GCP troubleshooting](../../../../gcp/troubleshooting.md) to identify the affected flow, blocking firewall and available rule/log evidence.
2. **Obtain the CRE API call evidence.** QE/the requesting team should have the call response. Establish whether the call occurred, what addresses/classification were submitted and what the response reports. If evidence is missing, coordinate with the requesting/platform team; absence of evidence is not proof of a catalog gap.
3. **Check registration and group membership.** Compare the flow's relevant addresses with the expected registered mappings, tags and group membership on the applicable downstream firewall. Account for the source identity used by the actual traffic path. A successful call response is useful evidence, not a substitute for checking the relevant downstream state when access remains blocked.
4. **Check policy scaffolding separately.** Use the CRE-enabled address-group reference to find the expected source/destination groups and the rules using them. Check the intended pattern's service/port and applicable policy scope. If membership and a candidate allow rule exist but the flow is still blocked, continue investigating the actual rule match/path rather than concluding the catalog is missing.
5. **Route the finding.** Registration/integration failures need coordination with the responsible platform/CRE owner. Suspected missing or incorrect shared scaffolding/catalog coverage goes to NSAE with the evidence. NSE must not convert a broad catalog change into a one-time access request. Return to [AWS QE defect handling](../../aws/qe-defect-handling.md) or [GCP QE defect handling](../../gcp/qe-defect-handling.md) for project-specific routing.

Conclusive root cause is not required before requesting engineering help. The distinction is to report the evidence and suspected failing layer rather than label every deny as missing catalog coverage.

## Supporting references

- **Automated patterns / policy-scaffolding sheet:** TODO: insert spreadsheet/document link.
- **CRE-enabled address-group and policy reference:** TODO: insert document/table link. Include group names, matching tags/filters, source/destination role, relevant pattern, environment/firewall scope and the policy references using each group. This lets operators filter by group name and distinguish existing coverage from missing scaffolding.
- **Registered-IP / DAG membership lookup:** TODO: insert existing operator guide/console/log reference.
- **CRE API response interpretation:** TODO: insert supporting document and sanitized examples.
- **Registration correction / retry ownership:** TODO: insert responsible team and approved process link. Do not assume NSE can replay calls or modify registrations directly.
- **Illumio integration:** TODO: insert applicable mechanism/scope reference; the flow above covers Palo Alto.

## Ownership boundary

NSE diagnoses and coordinates corrections. NSAE owns decisions/remediation coordination for shared automation/catalog changes because of their broad blast radius. Full CRE platform or service-catalog ownership is not transferred by this explanation. Verdicting is future work and is not required for the registration/scaffolding flow above.
