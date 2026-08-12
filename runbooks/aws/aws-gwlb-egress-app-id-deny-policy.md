# AWS GWLB Egress Core - App-ID Deny Policy

## Purpose

Add targeted App-ID deny controls above the existing EWP URL-filter-gated internet access rule. These controls apply only to outbound traffic sourced from the approved EWP dataplane addresses.

The existing EWP allow rule remains the primary internet-access rule and retains its URL Filtering profile and Security Profile Group. Because the firewall does not decrypt this traffic, these App-ID denies are supplemental controls and only act when PAN-OS can identify an application beyond generic `ssl`.

## Rule Order

1. `EGRESS-EWP-ALLOW-APP-EXCEPTIONS`
2. `EGRESS-EWP-DENY-PROHIBITED-APPS`
3. `EGRESS-EWP-DENY-EVASIVE-APPS`
4. `EGRESS-EWP-DENY-TUNNELING-APPS`
5. `EGRESS-EWP-DENY-PROXY-APPS`
6. Existing URL-filter-gated EWP allow rule
7. Existing default deny behavior

## Common Deny-Rule Settings

- **From zone:** `EGRESS`
- **To zone:** `EGRESS`
- **Source:** Exact EWP dataplane address object or approved EWP address group
- **Destination:** `any`
- **User:** `any`
- **Service:** Existing custom TCP/443 service object
- **URL category:** `any`
- **Action:** `deny`; use `reset-both` instead if immediate TCP teardown is operationally preferred
- **Logging:** Log at session end
- **Log forwarding:** Approved SIEM/log-forwarding profile

Do not broaden these rules to non-EWP sources.

## Application Objects and Deny Rules

### Static Prohibited-Application Group

Create application group `AG-EGRESS-DENY-PROHIBITED`.

Add only explicitly prohibited App-IDs confirmed in the installed Applications and Threats content, such as:

- Tor, Psiphon, Ultrasurf, and similar circumvention tools
- Unauthorized consumer VPN applications
- Unauthorized remote-control applications
- SSH
- Unapproved encrypted-DNS applications
- Other organization-prohibited proxy or tunneling tools

Do not add sanctioned enterprise VPN, support, administration, or partner-access applications.

Create `EGRESS-EWP-DENY-PROHIBITED-APPS` with this group in the Application field and the common deny-rule settings.

### Evasive Application Filter

Create application filter `AF-EGRESS-DENY-EVASIVE`:

- **Category:** Any
- **Subcategory:** Any
- **Technology:** Any
- **Risk:** Any
- **Characteristic:** `Evasive`

Create `EGRESS-EWP-DENY-EVASIVE-APPS` with this filter and the common deny-rule settings.

### Tunneling Application Filter

Create application filter `AF-EGRESS-DENY-TUNNELING`:

- **Category:** Any
- **Subcategory:** Any
- **Technology:** Any
- **Risk:** Any
- **Characteristic:** `Tunnels Other Applications`

Create `EGRESS-EWP-DENY-TUNNELING-APPS` with this filter and the common deny-rule settings.

### Proxy Application Filter

Create application filter `AF-EGRESS-DENY-PROXY`:

- **Category:** `Networking`
- **Subcategory:** `Proxy`
- **Technology:** Any
- **Risk:** Any
- **Characteristic:** Any

Create `EGRESS-EWP-DENY-PROXY-APPS` with this filter and the common deny-rule settings.

Confirm the exact category and subcategory labels presented by the installed PAN-OS content. Review every application resolved by the filter for sanctioned enterprise services before enforcement.

## Sanctioned Exceptions

Place exceptions above all App-ID deny rules. Each exception must use:

- Exact EWP source addresses
- Required destination or destination group where feasible
- Explicit App-ID
- TCP/443
- Named owner and business justification
- Review or expiration date

Do not create an exception with both Application `any` and Destination `any`.

## Filters Not Approved for Broad Denial

Do not deny applications solely because they match:

- Risk 4 or 5
- `Prone to Misuse`
- `Transfers Files`
- Remote-access subcategory
- Encrypted-tunnel technology

These attributes include legitimate business applications and create excessive outage risk.

## Deployment Validation

1. Record the resolved App-ID membership of every dynamic filter before deployment.
2. Review recent EWP egress logs for applications that would match.
3. Test approved web access, prohibited applications, sanctioned exceptions, and existing URL-category blocks.
4. Monitor deny-rule hits and false positives during the initial observation period.
5. Recheck dynamic-filter membership after Applications and Threats content updates because new App-IDs can join automatically.

## Visibility Limitation

Without firewall TLS decryption, many HTTPS sessions remain classified as generic `ssl`. These deny rules provide defense in depth only when the firewall identifies a functional App-ID from visible metadata, infrastructure, behavior, or signatures. They do not replace EWP enforcement, URL Filtering, the Security Profile Group, or no-bypass routing.

