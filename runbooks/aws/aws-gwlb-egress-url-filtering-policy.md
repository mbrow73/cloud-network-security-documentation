# AWS GWLB Egress Core - EWP URL Filtering Policy Plan

## Scope

This document defines the Panorama / PAN-OS 10.2.x policy structure for the AWS GWLB egress-core design:

```text
AWS workload -> EWP -> TGW -> EWP in egress VPC -> GWLBe -> inspection -> GWLBe return -> NAT Gateway -> IGW
```

The firewall policy intent is **not** to be a blind `EWP -> any 443` IPS-only path. The EWP/firewall egress rule should allow web egress, while the attached URL Filtering profile applies category-based guardrails and logs URL decisions.

## Panorama Inputs

```text
Device Group: AWS_GWLB_EGRESSCORE_NP
Rulebase: pre-rulebase
From Zone: EGRESS
To Zone: EGRESS
EWP Source Address Object: EWP
URL Filtering Profile: URLF-EGRESS-PROXY-GUARDRAILS
Security Rule Name: EGRESS-EWP-URL-GUARDRAILS
Future Exception Custom URL Category: URLC-EGRESS-APPROVED-EXCEPTIONS
Future Exception Rule Name: EGRESS-EWP-ALLOW-URL-EXCEPTIONS
```


## Design Summary

Initial policy structure:

1. **Single EWP egress allow rule**
   - `from EGRESS`
   - `to EGRESS`
   - source: `EWP`
   - destination: `any`
   - applications: `ssl`, `web-browsing`
   - service: `application-default`
   - action: `allow`
   - log at session end
   - attach URL Filtering profile `URLF-EGRESS-PROXY-GUARDRAILS`

2. **URL Filtering profile handles category allow/block behavior**
   - `alert` categories are allowed and logged to URL Filtering logs
   - `block` categories are blocked and logged to URL Filtering logs
   - default response page exists; HTTPS block-page presentation is only reliable with SSL decryption

3. **No explicit catch-all deny rule required**
   - traffic not matching the allow rule falls to intrazone/interzone defaults

4. **Exception rule/category kept on deck, not built initially**
   - used later when a business-approved operational URL is blocked by category
   - exceptions should be domain/FQDN/URL-list based, not broad IP holes unless absolutely required

## Initial Set Commands

### Enter Configuration Mode

```bash
configure
```

### Create URL Filtering Profile

```bash
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS description "AWS EWP egress URL guardrails"
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS log-container-page-only yes
```

### Allowed-but-Logged Categories

These categories are permitted, but logged to **Monitor > Logs > URL Filtering** because their action is `alert`.

```bash
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS alert business-and-economy
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS alert computer-and-internet-info
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS alert content-delivery-networks
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS alert software-update
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS alert financial-services
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS alert internet-communications-and-telephony
```

### Blocked Categories

These categories are blocked by the URL Filtering profile and logged to **Monitor > Logs > URL Filtering** with a URL action of `block-url` / blocked equivalent depending on log rendering.

```bash
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block malware
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block phishing
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block command-and-control
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block grayware
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block hacking
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block proxy-avoidance-and-anonymizers
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block dynamic-dns
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block newly-registered-domain
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block parked
set device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS block unknown
```

### Create Security Policy Rule

```bash
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS from EGRESS
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS to EGRESS
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS source EWP
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS destination any
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS application ssl
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS application web-browsing
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS service application-default
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS action allow
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS log-end yes
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS profile-setting profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS
```

### Commit / Push

```bash
commit
```

Then push the device group to the target firewalls from Panorama. Exact command may vary by environment/device group scoping, but the operation is a Panorama device-group push/commit-all.

## URL Filtering Logging

### Is URL Filtering Logging Enabled by Default?

URL Filtering logs are generated when all of these are true:

1. Traffic matches an **allow** security rule.
2. That rule has a **URL Filtering profile** attached.
3. The matching URL category action is log-producing, such as:
   - `alert` - allow and log
   - `block` - block and log
   - `continue` / `override` - user interaction actions, also logged

So the script above **does enable URL Filtering logging behavior** by:

- attaching `URLF-EGRESS-PROXY-GUARDRAILS` to `EGRESS-EWP-URL-GUARDRAILS`
- setting allowed categories to `alert`
- setting denied categories to `block`

`log-end yes` on the security rule controls **Traffic logs**, not URL Filtering logs. URL Filtering logs come from the URL Filtering profile actions.

### Where to View URL Filtering Logs

In Panorama or the firewall UI:

```text
Monitor > Logs > URL Filtering
```

Useful fields/filters:

```text
Rule = EGRESS-EWP-URL-GUARDRAILS
URL Category = <category>
Action = block-url / alert / allowed equivalent
Source = EWP source IP
Destination = destination IP
URL / Host = requested domain or URL
Application = ssl or web-browsing
```

Traffic logs remain under:

```text
Monitor > Logs > Traffic
```

Traffic logs show the session matched the allow rule and whether it ended normally. URL category decisions are primarily visible in **URL Filtering logs**, not Traffic logs.

## Block Page Behavior

PAN-OS includes default URL Filtering response pages. A custom response page is optional.

Expected behavior:

- **HTTP blocked by URL profile:** user should receive a visible Palo Alto URL Filtering block page.
- **HTTPS blocked without SSL decryption:** user may see a reset, browser TLS error, or generic connection failure instead of a clean block page.
- **HTTPS blocked with SSL Forward Proxy decryption:** user experience is much more likely to show the Palo Alto block page cleanly.

Reason: without decryption, the firewall can usually only classify based on TLS metadata such as SNI/certificate/destination. It cannot reliably inject an HTTP block page inside an encrypted session where it is not acting as the TLS endpoint.

## Future Exception Process

Create the exception rule/category only when the first approved exception is required.

When a business-approved operational URL is blocked by the guardrails profile:

1. Operations/app team opens an exception request.
2. Request must include:
   - business owner
   - application/workload
   - requested domain/FQDN/URL pattern
   - reason the destination is required
   - evidence of business approval
   - expected traffic type/port, usually HTTPS/443
   - expiration/review date
3. Security/network team validates:
   - domain ownership/reputation
   - URL category and reason for block
   - whether the destination should be allowed by category tuning or specific exception
   - whether raw IP allowlisting is truly required
4. Approved exception is added to a custom URL category or URL EDL.
5. A dedicated exception allow rule is inserted above the general URL guardrails rule.
6. Exception allow rule still receives the same security profile stack. It is a policy exception, not an inspection bypass.

### Future Exception Object

```bash
set device-group AWS_GWLB_EGRESSCORE_NP profiles custom-url-category URLC-EGRESS-APPROVED-EXCEPTIONS type "URL List"
set device-group AWS_GWLB_EGRESSCORE_NP profiles custom-url-category URLC-EGRESS-APPROVED-EXCEPTIONS list vendor.example.com
set device-group AWS_GWLB_EGRESSCORE_NP profiles custom-url-category URLC-EGRESS-APPROVED-EXCEPTIONS list "*.vendor.example.com"
```

### Future Exception Rule

```bash
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS from EGRESS
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS to EGRESS
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS source EWP
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS destination any
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS application ssl
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS application web-browsing
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS service application-default
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS category URLC-EGRESS-APPROVED-EXCEPTIONS
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS action allow
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS log-end yes
set device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-ALLOW-URL-EXCEPTIONS profile-setting profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS
```

Place this rule above `EGRESS-EWP-URL-GUARDRAILS`.

## Verification Commands

```bash
set cli config-output-format set
show device-group AWS_GWLB_EGRESSCORE_NP profiles url-filtering URLF-EGRESS-PROXY-GUARDRAILS
show device-group AWS_GWLB_EGRESSCORE_NP pre-rulebase security rules EGRESS-EWP-URL-GUARDRAILS
```

After testing a blocked URL, verify in:

```text
Monitor > Logs > URL Filtering
```

Filter by:

```text
(rule eq 'EGRESS-EWP-URL-GUARDRAILS')
```

or by the EWP source IP.
