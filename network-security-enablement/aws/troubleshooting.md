# AWS network troubleshooting

**Draft.** Determine whether NetSec controls are blocking the reported flow, identify the blocking control when possible, or provide evidence for a handoff. Finding the application's root cause is not the objective. Project workflows determine remediation/escalation ownership; this guide does not transfer platform ownership.

## 1. Capture the failing flow

Get the following from the requestor:

- Source and destination workload/endpoint IPs, destination port and protocol; source port if known. For each side, record the **non-routable (NR) workload IP, if present**, and the **routable (R) IP used across account/network boundaries**. Mark NR **not applicable** for routable-only workloads; do not require a second IP where none exists. If the requestor only knows the NR IP, AWS account and Region, start with those and look up the routable mapping; do not treat an unknown mapping as not applicable.
- Where each endpoint lives: **AWS account ID/name and Region**, **GCP project ID/name and region where applicable**, or **on-premises/third-party site or network and owning team**. Record production/non-production for each side; an endpoint does not need to be in AWS.
- For zonal AWS workloads, capture the **source subnet and Availability Zone (AZ)** so the corresponding local Palo Alto pair can be selected. For an NR source, also record the NAT gateway and its AZ for the tested path.
- A recent failed-test timestamp with time zone, and a way to reproduce the same flow during investigation.
- For **third-party peering inspection**, where SNI-based controls are enforced, also capture the destination hostname/URL and the IP resolved during the test. Record known NAT/proxy mappings for firewall searches.

Do not require a project pattern/configuration reference before starting these checks.

**Workload versus firewall searches:** use the workload ENI IP for its SG and VPC Flow Logs checks. Beyond the source account, an NR workload is represented by its NAT gateway's routable source; a proxy may originate a separate connection. Enterprise-routable addresses in this environment are `10.x.x.x`; NR workloads use `100.65.x.x` space.

**If only the NR IP, account and Region are known:** find the workload ENI and subnet, then open the subnet's effective route table (its explicit association, or the VPC main table). Follow the route matching the destination to the NAT gateway. Open that gateway under **VPC → NAT gateways** and record its subnet/AZ and assigned private `10.x.x.x` addresses used for SNAT. Record the assigned SNAT addresses, not just the subnet CIDR; confirm the translated source used by the test from traffic evidence when needed. If the route points elsewhere, follow the actual path rather than assuming a NAT gateway. AWS references: [subnet route tables](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-route-tables.html) and [NAT gateway addresses](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-working-with.html).

## 2. Identify the type of flow

Classify each AWS side as an **internet account**, **intranet account**, or **internet egress account**; identify **GCP**, **on-premises**, or **third-party** endpoints explicitly instead of forcing them into an AWS account category. Record the initiating side and production/non-production classification. Internet accounts and internet egress accounts are separate categories, not interchangeable names.

## 3. Find the applicable controls in the path

This is the environment-specific control map. Bidirectional arrows describe endpoint pairings, not permission to initiate connections in both directions.

| Flow | Applicable NetSec controls |
| --- | --- |
| Intranet account ↔ intranet account | Security groups (SGs) only. |
| Internet account ↔ intranet account | SGs and egresscore Palo Altos (non-production) / core Palo Altos (production). |
| Internet account ↔ third party | SGs, egresscore Palo Altos (non-production) / core Palo Altos (production), and third-party Palo Altos. |
| Intranet account ↔ third party | SGs and third-party Palo Altos only. |
| Intranet account ↔ on-premises | SGs and Equinix (production) / TRCWMID2 (non-production). |
| Web egress through an internet egress account, including the return leg | Applicable SGs, **EWP (Enterprise Web Proxy; not NetSec-owned)**, and **egresscore Palo Altos (non-production) / egress Palo Altos (production)**. |

For proxied web egress, check the workload→EWP and EWP→destination connections separately. EWP is not NetSec-owned; coordinate EWP findings with its owner.

Keep the production firewall names distinct: **core** for the internet-account paths above; **egress** for web egress.

**Panorama:** TODO: insert Panorama link. Find local firewalls, source-AZ-to-pair mapping and associated device/management details through Panorama.

Local Palo Altos are deployed as **AZ-based pairs**. For a zonal AWS source, read its subnet/AZ from the source ENI/subnet details and use Panorama to identify and select the corresponding local pair for Traffic-log checks and PCAP; do not guess across all three AZ pairs. Identify the member(s) handling the reproduced flow. Find other applicable firewalls and their details through Panorama as well. If the mapping is missing or the expected pair does not see the flow, record that gap and verify the path with NSAE rather than treating an empty capture as clearance.

## 4. Troubleshoot the controls

Work through applicable controls in order. Skip AWS-side checks for non-AWS endpoints and Palo Alto checks for SG-only paths.

### 4.1 Check source SGs and VPC Flow Logs, then the destination

#### Find the workload ENI and associated SGs

1. For an AWS source, sign in to the **source account provided by the requestor**, select its Region, then open **EC2 → Network & Security → Network Interfaces**. For a non-AWS source, perform the applicable NetSec checks below and continue the ENI/SG procedure at the AWS side; do not search an unrelated AWS account for it.
2. Search/filter by the **workload's local IP**: its NR `100.65.x.x` address when present, otherwise its routable workload IP. Include secondary private IPs. Select the matching network interface (ENI) and verify workload, VPC and subnet. Do **not** use the downstream NAT-gateway R IP to identify the source workload's SG.
3. Open the associated **Security groups** from the ENI details. Check **Outbound rules** for destination address, protocol and port. Evaluate all attached SGs together: their allow rules are combined, not limited to the expected named SG.
4. Record ENI/SG IDs and distinguish **missing SG**, **existing SG not attached**, and **existing/attached SG with stale or missing rules**. NetSec supplies rule changes through SG deployment modules; an existing SG does not mean AFT has applied the newest rules. Compare deployed rules against the **latest applicable version of the NetSec SG deployment module**, including relevant account/environment inputs, and check which version/run AFT actually applied. If expected newer rules are absent, have the **requestor ask AFT Operations to run the account** using the updated module version; this is an informal ask, and NSE can coordinate when needed. Include account/environment, SG ID, expected module version/rules, actual deployed rules and last-run evidence. Recheck deployed state after the run; do not bypass module deployment with an ad hoc rule change.
5. For an AWS destination, repeat in the **destination account/Region**, finding its ENI by the destination workload's local NR/R IP. Confirm SG attachment, check module/rule currency as above, and check **Inbound rules** against the source address visible there—the source workload's R IP, the NAT gateway's R source for an NR workload, or an on-premises/GCP routable IP, as applicable. For a proxied connection, use the proxy's source.

**NetSec SG deployment modules / versions / expected rules:** TODO: insert supporting repository/release link.

**For non-AWS endpoints, NetSec performs the applicable checks:** Illumio and Palo Alto for on-premises; Palo Alto and GCP firewall rules for GCP. Use the routable endpoint addresses visible to those controls.

AWS references: [network interfaces](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) and [security-group rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html).

#### Query CloudWatch for the same test

Open **CloudWatch → Logs → Logs Insights**, choose **Logs Insights QL**, and **select the VPC Flow Logs log group covering the source ENI/VPC/subnet**. An application log group will not show these records. Use the failed-test window, allowing for aggregation/delivery delay. For centralized logging, use the logging account/Region and group containing that workload's flow logs.

Find the configured log destination through the ENI, subnet or VPC **Flow logs** tab. Confirm interface coverage, successful delivery and **ALL** traffic logging before expecting both ACCEPT and REJECT; REJECT-only logging cannot demonstrate acceptance.

Example: workload ENI IP `100.65.1.10` communicating with `10.1.1.1` on TCP/443. Match the workload IP as source for outbound traffic and destination for return traffic. Replace the example addresses, port and protocol; TCP is `6`, UDP is `17`. No ENI ID filter is required.

```sql
fields @timestamp, srcAddr, srcPort, dstAddr, dstPort,
       protocol, action, logStatus, packets, bytes
| filter protocol = 6
| filter (srcAddr = "100.65.1.10" and dstAddr = "10.1.1.1" and dstPort = 443)
      or (srcAddr = "10.1.1.1" and dstAddr = "100.65.1.10" and srcPort = 443)
| sort @timestamp desc
| limit 200
```

This uses discovered fields for standard VPC Flow Logs. See [running a query](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_RunSampleQuery.html). For an AWS destination, repeat the check in its workload flow-log group using its ENI IP and the peer address seen there.

- **Source REJECT for the initiating flow:** recheck source SG egress. A VPC REJECT is not an SG-rule identifier; if the SG permits it, inspect the network ACL or route that evidence to its owner.
- **Destination REJECT for the incoming flow:** check expected SG attachment, then individual ingress rules against the actual source. If SGs permit it, inspect the network ACL; do not equate every REJECT with an SG deny.
- **Source ACCEPT, neither ACCEPT nor REJECT at destination:** suspect loss between resources only after verifying ENI, account/Region, log group, time window, logging health and NAT addresses. Continue to in-path controls; missing records alone do not locate a drop.
- **Destination ACCEPT:** the recorded traffic passed the controls represented by that record. Check return-direction evidence and remaining in-path controls; this is not proof of application success.

SGs are stateful; network ACLs are stateless. Do not request reverse SG openings solely for responses to an allowed tracked connection. AWS references: [record actions/status](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html) and [SG/network-ACL examples](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-records-examples.html).

### 4.2 Query the SIEM

**SIEM:** TODO: insert SIEM link.

Select the **Illumio/Palo Alto** view dropdown and the failed-test time window. Use the **routable source and destination visible to the inspected control**. For an NR workload beyond its source account, use the NAT gateway's R source, not the workload's NR IP; for a proxied leg, use the proxy's source. Example with R source `10.2.1.10` and destination `10.1.1.1`:

```text
source.ip : "10.2.1.10" and destination.ip : "10.1.1.1"
```

Expand matching hits. Filter/search expanded fields for **action** to find the traffic action and **observer** to identify the reporting Palo Alto/Illumio instance. Save action, device, timestamp and rule/policy evidence; confirm the device belongs to the identified path.

Add port/protocol filters using fields actually present in the view. Search reverse and translated tuples where relevant. One observer's permit does not clear other controls. When no explicit block appears, inspect local logs next; no hits are not proof of no drops. For on-premises endpoints, NetSec checks the applicable Illumio and Palo Alto evidence; use Illumio-specific checks for Illumio, not PAN-OS procedures.

### 4.3 Check local firewall logs

If the SIEM and destination SG/flow-log checks do not identify the block, inspect each applicable Palo Alto locally:

1. Select the **local Palo Alto pair corresponding to the zonal source's AZ** through Panorama as described in step 3. Sign in to **Citrix** (TODO: insert Citrix link), select the **Chrome** app, then open `https://<firewall-management-IP>` for the relevant member(s). Find other in-path firewalls and their management details in Panorama.
2. Open **Monitor → Logs → Traffic**. Use the filter builder to match source/destination IPs, port/protocol and test time. Repeat for reverse traffic and NAT-translated addresses.
3. Expand entries and record action, rule, application/App-ID, zones, NAT fields, session ID and session-end reason. Check for denies, drops or resets absent from the SIEM.
4. **URL/content-enforcement log evidence is not currently available in this deployment.** Investigate these drops through the PCAP procedure below, not URL Filtering/Threat-log correlation. A Traffic-log allow alone does not clear URL/content enforcement. Record this logging gap with the findings.

PAN-OS reference: [Traffic-log fields](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/traffic-log-fields).

### 4.4 Take a narrowly filtered Palo Alto PCAP

If source/destination VPC Flow Logs, SIEM and local logs do not explain the failure, or URL/content enforcement is suspected, capture the reproduced flow at the Palo Altos along the path. For the local zonal firewall, open the **source-AZ-corresponding pair** selected in step 3 and capture on the member(s) handling the test, rather than trying all AZ pairs. Record the source AZ and selected firewall names with the capture.

1. Open **Monitor → Packet Capture → Manage Filters**. Match the source/destination/port/protocol **visible at that firewall**: for an NR workload beyond its source account, use its NAT gateway's R source until another translation/proxy changes it. Include reverse traffic and NAT-visible tuples where applicable; do not hard-code an unknown client ephemeral port.
2. Enable filtering and configure four stages with distinct file names: **receive**, **transmit**, **firewall** and **drop**.
3. Start capture, have the requestor reproduce, then stop capture promptly. Download the files for **Wireshark**. Disable capture/filtering after collection.
4. Inspect the **drop file first**, if produced. Match packet tuple and test time, then compare receive/firewall/transmit and return packets to establish what arrived and left each firewall. An empty/missing drop file does not prove forwarding unless the test packets were actually observed.

If expected packets are absent, verify active dataplane/device, filter and capture coverage. Hardware offload can affect visibility; follow the [vendor capture/offload procedure](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/take-packet-captures) rather than treating a blind capture as clearance. Setup reference: [custom packet capture](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/take-packet-captures/take-a-custom-packet-capture).

**Interpretation leads, not automatic diagnoses:**

- A dropped **TLS ClientHello** on third-party peering makes a missing destination hostname in the applicable URL category or an App-ID mismatch worth checking. Use the PCAP (including hostname/SNI where visible), available Traffic-log context and the applicable rule/category/App-ID configuration; URL/Threat-log correlation is not currently available here. The dropped packet alone does not prove either cause.
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

Attach endpoint locations/owners/environment, workload NR/R and NAT/proxy mappings, exact test window, path/devices, ENI/SG IDs and deployed rules/module version, queries/log actions, and relevant PCAP/counter evidence. Record one of:

- **NetSec block identified:** name the control and evidence. Resolve, request access, coordinate with its owner or escalate through the project workflow; retest after correction.
- **Checked NetSec controls passed the reproduced flow:** state exactly which controls and directions were verified, with correlated forwarding/acceptance evidence and no unresolved enforcement block in the tested scope. Hand off the remaining failure without claiming application root cause or clearing unchecked controls.
- **Inconclusive / visibility gap:** name the missing hop, logs, capture or access and the owner needed next. No hits, an unobserved return path or an unmatched capture is not sufficient to clear NetSec.

For SG-only flows, use interface/SG and bidirectional flow-log evidence; do not require Palo Alto evidence where no Palo Alto is in path. NSE does not need to prove application root cause before handing off a documented result.

### Escalate unresolved cases to NSAE

**If the problem cannot be identified through the applicable checks, escalate to NSAE — Network Security Architecture and Engineering — with all supporting evidence collected and checks performed up to that point.** This is a general route, not limited to CRE-backed flows or proven catalog defects. Do not require conclusive root cause or unavailable evidence before escalating.

Include:

- Impact, affected endpoints/owners/environment, failing flow and NR/R/NAT/proxy mappings, test timestamps and reproduction steps.
- Source AZ, selected local Palo Alto pair/member(s), other in-path controls and any uncertainty about the path.
- SG attachment/rule/module-version findings, AFT run status where relevant, and the log groups, time windows and queries used with their results.
- Available SIEM/local Traffic-log extracts, PCAP files/stages and filtered counter samples, with what each check established or did not establish.
- Checks not completed and why (missing access, mapping, logs or ability to reproduce), plus any existing CRE/AFT/EWP-owner case or follow-up.

Keep unresolved visibility gaps explicit rather than clearing NetSec from absent evidence. Preserve the CRE-specific support route for identified registration issues.

**NSAE escalation queue / contacts:** TODO: insert existing queue/contact link.

## Related workflows and request guides

- [NetSec Automation — AWS QE defect handling](../projects/netsec-automation/aws/qe-defect-handling.md).
- [AWS standard security-group requests](requests/standard-security-group-requests.md) — placeholder.
- [AWS third-party standard requests](requests/third-party-standard-requests.md) — placeholder.
- **Diagnostic references / platform contacts:** TODO: insert existing links.
