# Panorama address-object tag mismatch: recovery handoff

Incident discussion: 2026-10-26. Cause confirmed by operator: 2026-10-27 (UTC).

## Issue and status

An address appeared tagged in one Panorama context, but the expected tag was missing in the affected device-group view. Push scope listed address objects/tags while Preview Changes appeared empty. Those observations did not establish that the enforcing firewalls had the intended object, DAG membership, or policy behavior.

**Confirmed cause: a device-group object override**, reported by the operator on 2026-10-27. The affected DG's overriding object masked the inherited tag assignment. This is an object-inheritance issue, not an established synchronization or PAN-OS defect. The blank preview is not separately explained by this finding.

The earlier remove-tag/push/re-add/push sequence was considered during troubleshooting; it is **not the confirmed fix and is not the recommended procedure for this cause**. The exact override correction performed and device-side policy/traffic results have not been supplied.

## Corrective procedure for the confirmed cause

For a **static address object's tag assignment**:

1. Compare the exact same object name in Shared/ancestor and the affected child DG. Record Location, address value, full tag list, override status and intended firewall/vsys targets. Preserve the before-state for rollback; the same IP alone does not establish object identity.
2. Determine whether the child override is intentional. If it is not, select the overridden object under **Objects > Addresses** in the child DG and use **Revert** to restore inherited values. Review all fields first: reverting restores the object, not only the missing tag. If the override is required, retain it and correct its tag assignments while preserving intentional values and unrelated tags. Do not change global object precedence to fix one object.
3. Check affected DAG/policy dependencies, review the scoped change, commit to Panorama, then push the affected device-group configuration to the intended firewall/vsys targets. Inspect each device's job result.
4. Complete local verification below. If the change fails, restore the recorded before-state through the owning Panorama scope and escalate with the exact failing job/configuration evidence.

Do not delete the address object or tag definition, cycle parent tags to try to bypass a child override, use Force Template Values, or create same-named local objects as an address-tag repair.

## Required local-firewall verification and monitoring

**The local enforcing firewall is the source of truth for effective policy. A successful Panorama commit/push is not the closure criterion.** Check every intended target/vsys, including relevant peer or load-balanced members; do not infer one device's state from another.

- Inspect the received object and tag assignment with `show config pushed-shared-policy` (use `vsys <name>` where applicable). Confirm the intended running policy with `show running security-policy`.
- If a DAG consumes the tag, confirm the affected IP/subnet's membership locally with `show object dynamic-address-group all`. If runtime registration is involved, also inspect `show object registered-ip all`; static object tags and runtime IP-tag registrations are separate mechanisms.
- Run a local security-policy match test for the actual source, destination, zones, protocol, port, and relevant application. For example, substitute the real values into `test security-policy-match from <src-zone> to <dst-zone> source <src-ip> destination <dst-ip> protocol 6 destination-port <port>`. Select the correct vsys; use CLI help for version-specific arguments. A simulated match is not an end-to-end traffic test.
- Generate representative new application connections. Correlate local Traffic logs/session evidence with the expected rule and action, using the addresses actually visible on that firewall after any NAT or proxy hop. Missing logs alone do not prove a pass.
- Monitor the affected rule and representative traffic during the agreed observation window and recheck after the next normal Panorama push. Record timestamps, device/vsys, object tags, DAG membership, expected/observed rule and action, and any unexpected denies or allows. No fixed observation interval has been supplied.

If unresolved, compare exact object names and Locations across Shared/parent/child scopes, inspect overrides, and collect Panorama/PAN-OS versions and per-device job details for escalation. Do not label this a synchronization bug without evidence.

## References

- [Panorama commit and push semantics](https://docs.paloaltonetworks.com/panorama/administration/administer-panorama/preview-validate-or-commit-configuration-changes)
- [Revert an overridden object to inherited values](https://docs.paloaltonetworks.com/panorama/administration/manage-firewalls/manage-device-groups/revert-to-inherited-object-values)
- [Inherited object precedence](https://docs.paloaltonetworks.com/panorama/administration/manage-firewalls/manage-device-groups/manage-precedence-of-inherited-objects)
- [Firewall CLI: Panorama-pushed configurations](https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000CmAYCA0)
- [Static and dynamic DAG membership](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/address-groups)
- [Policy-match testing](https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClQSCA0)
