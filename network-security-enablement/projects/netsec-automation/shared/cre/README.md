# Continuous Registration Engine (CRE) — AWS and GCP

**Draft for review.** CRE is a proprietary NetSec application with an API that provisions required downstream access on Palo Alto and Illumio. This document explains the Palo Alto registration and policy-scaffolding path. Illumio-specific behavior remains a supporting-reference placeholder; Palo Alto mechanics must not be assumed to apply to Illumio.

[Project expectations](../README.md) · [Review decision](handoff.md).

## Registration versus policy scaffolding

**Policy scaffolding** is the prebuilt firewall policy for an automated traffic pattern. It allows traffic from a source address group to a destination address group on the required service/port. The [pattern/control-placement sheet](../README.md#references) identifies the automated traffic patterns.

**CRE IP registration** supplies resource IP addresses or subnet CIDRs and their tags to downstream Palo Alto firewalls. The values depend on the platform component and onboarding pattern: for example, EKS/GKE node subnet CIDRs, NLB subnet CIDRs, a data service's routable IP, or Cloud Run connector addresses. Request the actual values passed to CRE from the requestor when confirming a flow. Tag-based Dynamic Address Groups (DAGs) populate from those registrations. Existing rules using the matching groups then apply to the newly registered resources. CRE does not need to create or edit an allow rule for every new resource joining an existing pattern.

**A registration is not inherently a source or a destination.** The address group's position in each firewall rule determines that role. For example, GKE node subnet registrations can populate the source DAG while NLB subnet registrations populate the destination DAG in the same prebuilt rule. A group can also appear as a source in one rule and a destination in another. Registration populates the applicable groups; the existing policy scaffolding still determines which directions, services and ports are allowed.

The group definitions and policy scaffolding must already be configured and committed. Updating dynamic registered IP/tag membership does **not** require a new firewall commit; changing the rules or group definitions is a different configuration change. See [Palo Alto dynamic registration](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/addresses/register-ip-addresses-and-tags-dynamically) and [address-group behavior](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/address-groups).

## Provisioning flow

Most CRE calls originate from AFT or account/project vending, but registration is also triggered by application onboarding and paved-road platform deployment workflows. It is not limited to account creation or cluster provisioning.

1. Account/project vending, platform provisioning or application onboarding identifies a resource that needs registration.
2. The applicable workflow calls the CRE API with the resource's IP addresses or subnet CIDRs and classification/tag context. For example, an AFT hook identifies EKS subnet CIDRs that need the EKS tag.
3. CRE attempts to register the applicable IP/tag mappings on the required downstream Palo Alto firewalls and returns the operation result. An error response means the registration operation was unsuccessful; inspect its stated reason rather than treating any returned response as success.
4. Following successful registration, the matching DAGs populate from those registrations.
5. Existing policy-scaffolding rules referencing those groups apply to the registered resources on the source side, destination side or both, according to each rule.

```text
Account/project vending / platform deployment / application onboarding
  -> CRE API call with resource IPs or subnet CIDRs + tag context
  -> inspect CRE operation result
     -> success: registered IP/tag mappings on listed downstream Palos
                 -> matching Dynamic Address Group membership
                 -> existing source/destination policy references apply
     -> error: registration unsuccessful; inspect reason and route to CRE support
```

### API result: success versus error

**Receiving an API response is not itself proof of successful registration.** Read the operation result and any error reason returned by CRE.

- **Explicit registration success:** confirms that the address values provided in the API call were registered on every local firewall listed in that successful response. This is evidence of completed registration on those listed firewalls, not merely request acceptance.
- **Registration error:** the operation to add the registered IPs was unsuccessful. Capture the returned reason, submitted values and firewall context for CRE support. Do not record the registration as successful just because the API returned a response.

Compare the firewall blocking the flow with the successful response's explicit list. Success for the listed firewalls does not establish registration on an unlisted firewall. Also confirm that the submitted IPs/CIDRs and tags are correct for the affected resource and its role in the flow; successful registration does not itself prove that the intended traffic matches the policy scaffolding.

- **Hook / platform integration references:** TODO: insert document links.
- **CRE request and success/error response examples:** TODO: insert sanitized examples/document link, including operation-result fields and error reasons.
- **CRE API response reference:** TODO: insert supporting document link.

## Example: EKS/GKE to on-premises Hydra

The downstream Palos contain policy scaffolding allowing the applicable EKS/GKE source address group to the on-premises Hydra VIP destination address group on port 443.

When a new EKS or GKE cluster is provisioned and the platform integration makes the CRE call, its registered source subnet CIDRs populate the applicable source group. The cluster then matches the existing policy, without a new commit for that membership update. The existing allow rule is reused; this is not a new per-cluster firewall rule.

- **Hydra pattern / group and policy names:** TODO: insert pattern/reference link.
- **Applicable environments and downstream firewalls:** TODO: insert scope/reference link.

## Other registration examples

- **GKE nodes to an NLB-backed service:** GKE node subnet CIDRs populate the source DAG, and NLB subnet CIDRs populate the destination DAG. Both registrations support the same existing rule for the approved service/port. The NLB registration is destination-side membership for this flow, not a source-only registration.
- **Routable data-service onboarding:** an application/platform onboarding workflow provisions a data service in routable space and calls CRE with its routable IP and applicable classification context. Registration populates the matching groups referenced by the service's existing policies; it does not require a new account-vending event.
- **Cloud Run connector deployment:** the paved-road workflow deploys the connector used by a Cloud Run function and registers its connector IP addresses through CRE. Existing policies referencing the matching groups then apply. This is another deployment-time trigger, not exclusively an account/project-vending trigger.

- **Onboarding / data-service / Cloud Run connector workflow references:** TODO: insert supporting document links.

## Diagnosing blocked CRE-backed traffic

A Palo Alto deny does **not** establish that policy scaffolding is missing. The policy may exist while the CRE call was never made, failed, used incorrect registration context, or did not produce the expected membership on the firewall seeing the flow.

1. **Capture the blocked flow.** Use [AWS troubleshooting](../../../../aws/troubleshooting.md) or [GCP troubleshooting](../../../../gcp/troubleshooting.md) to identify the affected flow, blocking firewall and available rule/log evidence.
2. **Obtain the CRE API call evidence.** QE/the requesting team should have the call response. Establish which vending, platform or onboarding workflow made the call, the exact IP addresses/subnet CIDRs and classification context submitted, and the operation result, error reason if present, and local firewall list/results in the response. Ask the requestor for the submitted values if necessary. A returned error means registration was unsuccessful; a response alone is not success. If evidence is missing, obtain it from QE/the requesting team; absence of evidence is not proof of a catalog gap.
3. **Check registration and group membership.** Verify registered IPs/subnet CIDRs, tags and group membership **on the applicable firewall** for both sides of the expected rule. Match the flow's source and destination addresses to their respective registrations and DAG references; do not assume that only the source requires registration. For an explicitly successful registration, compare the blocking firewall with the response's firewall list. Direct firewall inspection establishes which registration/group/policy state applies to the blocked flow.
4. **Check policy scaffolding separately.** Use the CRE-enabled address-group reference to find the expected source/destination groups and the rules using them. Check the intended pattern's service/port and applicable policy scope. If membership and a candidate allow rule exist but the flow is still blocked, continue investigating the actual rule match/path rather than concluding the catalog is missing.
5. **Route the finding.** Escalate missing/failed registrations or CRE integration issues to the [CRE support contacts](#cre-support-contacts), with the submitted values, response and firewall evidence. Suspected missing or incorrect shared scaffolding/catalog coverage goes to NSAE with the evidence. NSE must not convert a broad catalog change into a one-time access request. Return to [AWS QE defect handling](../../aws/qe-defect-handling.md) or [GCP QE defect handling](../../gcp/qe-defect-handling.md) for project-specific routing.

Conclusive root cause is not required before requesting engineering help. The distinction is to report the evidence and suspected failing layer rather than label every deny as missing catalog coverage.

## Supporting references

- **Automated patterns / policy-scaffolding sheet:** TODO: insert spreadsheet/document link.
- **CRE-enabled address-group and policy reference:** TODO: insert document/table link. Include group names, matching tags/filters, relevant pattern, environment/firewall scope and each policy reference, including whether the group is used as source or destination in that rule. Role is per rule, not an intrinsic property of the registration. This lets operators filter by group name and distinguish existing coverage from missing scaffolding.
- **Firewall registered-IP / DAG membership lookup:** TODO: insert existing firewall operator guide/reference.
- **CRE API response examples:** TODO: insert supporting document and sanitized success/error examples with operation-result fields and error reasons.
- **CRE support escalation process:** TODO: insert internal process/queue link. CRE support handles registration issues and advises on correction/retry; NSE does not assume direct replay or registration-change authority.
- **Illumio integration:** TODO: insert applicable mechanism/scope reference; the flow above covers Palo Alto.

## CRE support contacts

- **Primary CRE support contact:** TODO: insert internal name/contact.
- **Alternate CRE support contact:** TODO: insert internal name/contact.
- **CRE support queue / escalation channel:** TODO: insert internal queue/channel link.

Contact details remain placeholders for internal completion. Send registration issues to CRE support; send shared policy-scaffolding/catalog changes to NSAE.

## Ownership boundary

NSE diagnoses and coordinates corrections. NSAE owns decisions/remediation coordination for shared automation/catalog changes because of their broad blast radius. Full CRE platform or service-catalog ownership is not transferred by this explanation. Verdicting is future work and is not required for the registration/scaffolding flow above.
