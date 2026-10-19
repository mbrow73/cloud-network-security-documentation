# AWS network troubleshooting

**Draft.** Determine whether NetSec controls are blocking the reported flow, identify the blocking control when possible, or provide evidence for a handoff. Finding the application's root cause is not the objective. Project workflows determine remediation/escalation ownership; this guide does not transfer platform ownership.

## 1. Capture the failing flow

Get the following from the requestor:

- Source and destination IPs, destination port and protocol; source port if known.
- Source and destination account IDs/names, environment (production/non-production), and AWS Region for each AWS endpoint.
- A recent failed-test timestamp with time zone, and a way to reproduce the same flow during investigation.
- For hostname-based connections, the hostname/URL and IP resolved during the test. Note known NAT, proxy or load-balancer translations so searches use the addresses visible at each hop.

Do not require a project pattern/configuration reference before starting these checks.

## 2. Identify the type of flow

Classify **both source and destination** as an **internet account**, **intranet account**, **internet egress account**, **on-premises**, or **third-party account/environment**. Record the initiating side and production/non-production classification. Internet accounts and internet egress accounts are separate categories, not interchangeable names.

## 3. Find the applicable controls in the path

This is the environment-specific control map. Bidirectional arrows describe endpoint pairings, not permission to initiate connections in both directions.

| Flow | Applicable NetSec controls |
| --- | --- |
| Intranet account ↔ intranet account | Security groups (SGs) only. |
| Internet account ↔ intranet account | SGs and egresscore Palo Altos (non-production) / core Palo Altos (production). |
| Internet account ↔ third party | SGs, egresscore Palo Altos (non-production) / core Palo Altos (production), and third-party Palo Altos. |
| Intranet account ↔ third party | SGs and third-party Palo Altos only. |
| Intranet account ↔ on-premises | SGs and Equinix (production) / TRCWMID2 (non-production). |

**Internet-egress-account paths and other unlisted pairings:** TODO: insert applicable control paths. Do not assume an unlisted path is SG-only; confirm the path before selecting firewalls to inspect.

**Firewall inventory / management IPs / path reference:** TODO: insert supporting document link.

## 4. Troubleshoot the controls

Work through applicable controls in order. Skip AWS-side checks for non-AWS endpoints and Palo Alto checks for SG-only paths.

### 4.1 Check source SGs and VPC Flow Logs, then the destination

#### Find the workload ENI and associated SGs

1. Sign in to the **source account provided by the requestor**, select its Region, then open **EC2 → Network & Security → Network Interfaces**.
2. Search/filter by the source IP, including secondary private IPs. Select the matching network interface (ENI) and verify its workload, VPC and subnet. For translated addresses, identify the workload's private IP first.
3. Open the associated **Security groups** from the ENI details. Check **Outbound rules** for destination address, protocol and port. Evaluate all attached SGs together: their allow rules are combined, not limited to the expected named SG.
4. Record ENI/SG IDs. Distinguish an expected SG that was never provisioned from an existing SG not attached to the workload. Where AFT should vend it, preserve provisioning evidence for AFT Operations.
5. Repeat in the **destination account/Region**, finding the destination ENI by IP. Confirm the expected SG is attached and check **Inbound rules** against the source address visible at that resource, protocol and destination port.

AWS references: [network interfaces](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) and [security-group rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html).

#### Query CloudWatch for the same test

Open **CloudWatch → Logs → Logs Insights**, choose **Logs Insights QL**, and **select the VPC Flow Logs log group covering the source ENI/VPC/subnet**. An application log group will not show these records. Use the failed-test window, allowing for aggregation/delivery delay. For centralized logging, use the logging account/Region and group containing that workload's flow logs.

Find the configured log destination through the ENI, subnet or VPC **Flow logs** tab. Confirm interface coverage, successful delivery and **ALL** traffic logging before expecting both ACCEPT and REJECT; REJECT-only logging cannot demonstrate acceptance.

Example: TCP/443 from `192.168.1.1` to `192.168.1.2`, including return traffic. Replace IPs, port, protocol and ENI ID. TCP is protocol `6`; UDP is `17`.

```sql
fields @timestamp, interfaceId, srcAddr, srcPort, dstAddr, dstPort,
       protocol, action, logStatus, packets, bytes
| filter interfaceId = "eni-0123456789abcdef0"
| filter protocol = 6
| filter (srcAddr = "192.168.1.1" and dstAddr = "192.168.1.2" and dstPort = 443)
      or (srcAddr = "192.168.1.2" and dstAddr = "192.168.1.1" and srcPort = 443)
| sort @timestamp desc
| limit 200
```

This uses discovered fields for standard VPC Flow Logs. For a custom format, inspect a raw record and map/parse its actual fields first. Keep ACCEPT evidence rather than filtering only to REJECT. To inspect `NODATA`/`SKIPDATA`, remove IP/port/protocol filters: those status records may lack a flow tuple. See [discovered fields](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html) and [running a query](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_RunSampleQuery.html).

Query the **source** log group/ENI first, then the **destination** group with its ENI ID and any translated addresses.

- **Source REJECT for the initiating flow:** recheck source SG egress. A VPC REJECT is not an SG-rule identifier; if the SG permits it, inspect the network ACL or route that evidence to its owner.
- **Destination REJECT for the incoming flow:** check expected SG attachment, then individual ingress rules against the actual source. If SGs permit it, inspect the network ACL; do not equate every REJECT with an SG deny.
- **Source ACCEPT, neither ACCEPT nor REJECT at destination:** suspect loss between resources only after verifying ENI, account/Region, log group, time window, logging health and NAT addresses. Continue to in-path controls; missing records alone do not locate a drop.
- **Destination ACCEPT:** the recorded traffic passed the controls represented by that record. Check return-direction evidence and remaining in-path controls; this is not proof of application success.

SGs are stateful; network ACLs are stateless. Do not request reverse SG openings solely for responses to an allowed tracked connection. AWS references: [record actions/status](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html) and [SG/network-ACL examples](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-records-examples.html).

### 4.2 Query the SIEM

**SIEM:** TODO: insert SIEM link.

Select the **Illumio/Palo Alto** view dropdown and the failed-test time window. Start with:

```text
source.ip : "192.168.1.1" and destination.ip : "192.168.1.2"
```

Expand matching hits. Filter/search expanded fields for **action** to find the traffic action and **observer** to identify the reporting Palo Alto/Illumio instance. Save action, device, timestamp and rule/policy evidence; confirm the device belongs to the identified path.

Add port/protocol filters using fields actually present in the view. Search reverse and translated tuples where relevant. One observer's permit does not clear other controls. When no explicit block appears, inspect local logs next; no hits are not proof of no drops. Use the Illumio owner/reference for Illumio-specific follow-up, not PAN-OS procedures.

**Illumio diagnostic reference / support:** TODO: insert existing link/contact.

### 4.3 Check local firewall logs

If the SIEM and destination SG/flow-log checks do not identify the block, inspect each applicable Palo Alto locally:

1. Sign in to **Citrix** (TODO: insert Citrix link), select the **Chrome** app, then open `https://<firewall-management-IP>` using the path inventory.
2. Open **Monitor → Logs → Traffic**. Use the filter builder to match source/destination IPs, port/protocol and test time. Repeat for reverse traffic and NAT-translated addresses.
3. Expand entries and record action, rule, application/App-ID, zones, NAT fields, session ID and session-end reason. Check for denies, drops or resets absent from the SIEM.
4. For URL/content enforcement, correlate **Monitor → Logs → URL Filtering** and **Threat** by session ID and time. An initial Traffic-log allow does not establish that subsequent inspection passed.

PAN-OS references: [log views](https://docs.paloaltonetworks.com/ngfw/help/11-2/monitor/monitor-logs/log-types), [Traffic-log fields](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/traffic-log-fields) and [URL Filtering fields](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/url-filtering-log-fields).

### 4.4 Take a narrowly filtered Palo Alto PCAP

If source/destination VPC Flow Logs, SIEM and local logs do not explain the failure, capture the reproduced flow at the Palo Altos along the path.

1. Open **Monitor → Packet Capture → Manage Filters**. Match the requestor's source IP, destination IP, destination port and protocol. Include reverse traffic and NAT-visible tuples where applicable; do not hard-code an unknown client ephemeral port.
2. Enable filtering and configure four stages with distinct file names: **receive**, **transmit**, **firewall** and **drop**.
3. Start capture, have the requestor reproduce, then stop capture promptly. Download the files for **Wireshark**. Disable capture/filtering after collection.
4. Inspect the **drop file first**, if produced. Match packet tuple and test time, then compare receive/firewall/transmit and return packets to establish what arrived and left each firewall. An empty/missing drop file does not prove forwarding unless the test packets were actually observed.

If expected packets are absent, verify active dataplane/device, filter and capture coverage. Hardware offload can affect visibility; follow the [vendor capture/offload procedure](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/take-packet-captures) rather than treating a blind capture as clearance. Setup reference: [custom packet capture](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/take-packet-captures/take-a-custom-packet-capture).

**Interpretation leads, not automatic diagnoses:**

- A dropped **TLS ClientHello** on third-party peering makes a missing destination hostname in the applicable URL category or an App-ID mismatch worth checking. Correlate hostname/SNI, rule, application and URL/Threat logs; the packet alone does not prove either cause.
- An initial **TCP SYN** drop makes five-tuple/policy matching an early check. Other TCP drops can involve state, routing or inspection; a TCP drop alone is not proof of policy mismatch.
- When PCAP drops have no explanation in Traffic logs, use filtered delta counters for dataplane causes such as spoofing checks, state problems or asymmetric-routing symptoms.

### 4.5 Correlate delta-drop counters with repeated tests

Keep the **narrow packet filter enabled** for the reported flow; packet capture itself can be OFF. Through approved management CLI access, run:

```text
show counter global filter packet-filter yes delta yes severity drop
```

Run once to establish a sampling baseline. Have the requestor trigger repeated connectivity tests, then rerun during/after those tests. `delta yes` reports changes since the preceding delta sample; `packet-filter yes` scopes output to the configured filter. Save counter names/descriptions, intervals and test timestamps; check that increases repeat with the failing tests, not unrelated traffic.

For an individual counter:

```text
show counter global name <counter_name>
```

Correlate its description with the PCAP to distinguish policy denial from underlying dataplane issues. A counter increase alone does not prove this flow's root cause. Disable filtering afterward. References: [filtered drop-counter procedure](https://knowledgebase.paloaltonetworks.com/articles/en_US/Knowledge/How-to-check-global-counters-f-65794) and [global-counter interpretation](https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClaVCAS).

### 4.6 If the blocking rule uses CRE-backed policy

Verify registered IP/tag and dynamic address-group (DAG) membership for **both source and destination rule references** on the blocking firewall. Obtain submitted resource IPs/subnet CIDRs, tag context, triggering workflow and CRE API result. A response is not itself success: explicit success confirms registration on the local firewalls listed in that result; capture errors and reasons for CRE support.

Follow the [CRE registration-versus-scaffolding checks](../projects/netsec-automation/shared/cre/README.md#diagnosing-blocked-cre-backed-traffic). A deny may reflect failed/missing registration or unexpected membership, not missing catalog coverage. Registration issues go to CRE support; shared scaffolding/catalog changes follow the project's NSAE route.

## 5. Provision missing individual access

For a missing individual access requirement, NSE may help the requestor complete a **request form to provision the missing access** and implement it through the normal authorized process when it meets **NetSec Standard Tech 08.11** and has an appropriate business justification. Follow the [AWS standard security-group requests guide](requests/standard-security-group-requests.md) once populated. For a third-party environment, use the [third-party standard request guide](requests/third-party-standard-requests.md) once populated.

- **NetSec Standard Tech 08.11:** TODO: insert supporting document link.
- **Request form / authorized implementation process:** TODO: insert supporting form/process link.

Shared automation/catalog changes follow the project's architecture-escalation route, not individual-access processing. This guide grants no additional change authority.

## 6. Record the NetSec disposition and hand off

Attach flow/accounts/environment, exact test window, path/devices, ENI/SG IDs and rules, queries/log actions, and relevant PCAP/counter evidence. Record one of:

- **NetSec block identified:** name the control and evidence. Resolve, request access, coordinate with its owner or escalate through the project workflow; retest after correction.
- **Checked NetSec controls passed the reproduced flow:** state exactly which controls and directions were verified, with correlated forwarding/acceptance evidence and no unresolved enforcement block in the tested scope. Hand off the remaining failure without claiming application root cause or clearing unchecked controls.
- **Inconclusive / visibility gap:** name the missing hop, logs, capture or access and the owner needed next. No hits, an unobserved return path or an unmatched capture is not sufficient to clear NetSec.

For SG-only flows, use interface/SG and bidirectional flow-log evidence; do not require Palo Alto evidence where no Palo Alto is in path. NSE does not need to prove application root cause before handing off a documented result.

## Related workflows and request guides

- [NetSec Automation — AWS QE defect handling](../projects/netsec-automation/aws/qe-defect-handling.md).
- [AWS standard security-group requests](requests/standard-security-group-requests.md) — placeholder.
- [AWS third-party standard requests](requests/third-party-standard-requests.md) — placeholder.
- **Diagnostic references / platform contacts:** TODO: insert existing links.
