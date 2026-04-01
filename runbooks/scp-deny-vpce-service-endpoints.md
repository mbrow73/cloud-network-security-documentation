# GWLB Endpoint Service Sharing with PCI Isolation — End-to-End Runbook

## Overview

This runbook walks through the full process of sharing GWLB VPC endpoint services across an AWS Organization via RAM, enabling automatic endpoint association for consumer accounts, and enforcing isolation for PCI-scoped accounts using SCPs.

**What we're building:**
1. An SCP that prevents PCI accounts from connecting to general workload GWLB services
2. RAM resource shares that expose endpoint services to the target OU
3. Auto-accept configuration so consumer accounts get zero-touch endpoint association

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  AWS Organization                                       │
│                                                         │
│  ┌──────────────────┐       ┌────────────────────────┐  │
│  │  Networking Acct  │       │  General Workload OU   │  │
│  │  (GWLB owner)    │       │                        │  │
│  │                   │──RAM──│  ✅ Can create VPC-E   │  │
│  │  • gwlb-general   │share  │     to gwlb-general    │  │
│  │  • gwlb-pci       │       │  ✅ Auto-associates    │  │
│  │                   │       └────────────────────────┘  │
│  │                   │                                   │
│  │                   │       ┌────────────────────────┐  │
│  │                   │──RAM──│  PCI OU                │  │
│  │                   │share  │  + SCP applied         │  │
│  │                   │       │                        │  │
│  │                   │       │  ✅ Can create VPC-E   │  │
│  │                   │       │     to gwlb-pci        │  │
│  │                   │       │  ❌ BLOCKED from       │  │
│  │                   │       │     gwlb-general (SCP) │  │
│  └──────────────────┘       └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- [ ] AWS Organizations enabled with SCPs turned on
- [ ] Networking/security account that owns the GWLB and endpoint services
- [ ] OU structure in place (e.g., `General Workload OU`, `PCI OU`)
- [ ] Terraform workspace configured for the management account (for SCP) and networking account (for RAM + endpoint services)
- [ ] Endpoint service IDs for all GWLB services (both general and PCI-dedicated)

---

## Step 1: Create the SCP (Management Account)

**Why first:** The SCP must be in place BEFORE sharing the endpoint services. If you share first, PCI accounts could create non-compliant endpoints in the window before the SCP is applied.

### 1a. Choose Your SCP Strategy

**Option 1: Deny List (recommended when you have a known set of services to block)**

Block specific general workload endpoint services. PCI accounts can still connect to anything not on the list.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonAuthorizedVpceServices",
      "Effect": "Deny",
      "Action": "ec2:CreateVpcEndpoint",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:VpceServiceName": [
            "com.amazonaws.vpce.us-east-1.vpce-svc-aaaaaaa",
            "com.amazonaws.vpce.us-east-1.vpce-svc-bbbbbbb",
            "com.amazonaws.vpce.us-east-1.vpce-svc-ccccccc",
            "com.amazonaws.vpce.us-east-1.vpce-svc-ddddddd",
            "com.amazonaws.vpce.us-east-1.vpce-svc-eeeeeee",
            "com.amazonaws.vpce.us-east-1.vpce-svc-fffffff",
            "com.amazonaws.vpce.us-east-1.vpce-svc-ggggggg",
            "com.amazonaws.vpce.us-east-1.vpce-svc-hhhhhhh",
            "com.amazonaws.vpce.us-east-1.vpce-svc-iiiiiii",
            "com.amazonaws.vpce.us-east-1.vpce-svc-jjjjjjj"
          ]
        }
      }
    }
  ]
}
```

**Option 2: Allow List (recommended for stricter PCI posture)**

Block ALL custom endpoint services except the ones explicitly authorized for PCI. New services are denied by default.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAllCustomVpceExceptAuthorized",
      "Effect": "Deny",
      "Action": "ec2:CreateVpcEndpoint",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "ec2:VpceServiceName": "com.amazonaws.vpce.*.vpce-svc-*"
        },
        "StringNotEquals": {
          "ec2:VpceServiceName": [
            "com.amazonaws.vpce.us-east-1.vpce-svc-pci12345"
          ]
        }
      }
    }
  ]
}
```

> **How the allow list works:** The `StringLike` condition scopes the deny to only custom endpoint services (`vpce-svc-*`). The `StringNotEquals` carves out the PCI service. AWS-managed endpoints (S3, KMS, Lambda, etc.) use the pattern `com.amazonaws.<region>.<service>` and are never affected by either option.

### 1b. Create the SCP in Terraform

```hcl
resource "aws_organizations_policy" "deny_vpce_services" {
  name        = "deny-non-pci-vpce-services"
  description = "Prevents PCI accounts from creating VPC endpoints to non-authorized custom endpoint services"
  type        = "SERVICE_CONTROL_POLICY"
  content     = file("policies/deny-vpce-services.json")
}
```

### 1c. Attach the SCP to the PCI OU

```hcl
resource "aws_organizations_policy_attachment" "pci_ou" {
  policy_id = aws_organizations_policy.deny_vpce_services.id
  target_id = "ou-yyyy-zzzzzzzz"  # PCI OU ID
}
```

### 1d. Verify

```bash
# List SCPs attached to the PCI OU
aws organizations list-policies-for-target \
  --target-id ou-yyyy-zzzzzzzz \
  --filter SERVICE_CONTROL_POLICY

# Confirm the policy content
aws organizations describe-policy \
  --policy-id p-xxxxxxxxxx
```

**⚠️ Do not proceed to Step 2 until the SCP is confirmed attached.**

---

## Step 2: Configure the GWLB Endpoint Service (Networking Account)

### 2a. Ensure the Endpoint Service Exists

```hcl
resource "aws_vpc_endpoint_service" "gwlb_general" {
  acceptance_required        = false  # Enables auto-accept (Step 4)
  gateway_load_balancer_arns = [aws_lb.gwlb_general.arn]

  tags = {
    Name        = "gwlb-general-workload-endpoint-service"
    Environment = "production"
  }
}
```

> **Key setting:** `acceptance_required = false` means consumer accounts don't need manual approval — endpoints auto-associate on creation. If you want manual approval, set this to `true` (see Step 4 notes).

### 2b. Note the Service Name

After applying, grab the service name:

```bash
aws ec2 describe-vpc-endpoint-service-configurations \
  --query 'ServiceConfigurations[*].[ServiceId,ServiceName,ServiceState]' \
  --output table
```

The service name will look like: `com.amazonaws.vpce.us-east-1.vpce-svc-0abc123def456789`

**This is the value you need in your SCP (Step 1) and your RAM share (Step 3).**

---

## Step 3: Share the Endpoint Service via RAM (Networking Account)

### 3a. Create the RAM Resource Share

```hcl
resource "aws_ram_resource_share" "gwlb_general" {
  name                      = "gwlb-general-endpoint-service"
  allow_external_principals = false  # Restrict to org only

  tags = {
    Name = "gwlb-general-endpoint-service-share"
  }
}
```

### 3b. Associate the Endpoint Service with the Share

```hcl
resource "aws_ram_resource_association" "gwlb_general" {
  resource_arn       = aws_vpc_endpoint_service.gwlb_general.arn
  resource_share_arn = aws_ram_resource_share.gwlb_general.arn
}
```

### 3c. Share to the Target OU

```hcl
resource "aws_ram_principal_association" "workload_ou" {
  principal          = "arn:aws:organizations::111111111111:ou/o-xxxxxxxx/ou-aaaa-bbbbbbbb"
  resource_share_arn = aws_ram_resource_share.gwlb_general.arn
}
```

> **Note:** You can share to multiple OUs or individual accounts by adding more `aws_ram_principal_association` resources. Each association grants visibility of the endpoint service to those principals.

### 3d. Verify the Share

```bash
# Confirm the share is active
aws ram get-resource-shares --resource-owner SELF \
  --query 'resourceShares[*].[name,status]' \
  --output table

# Confirm principals
aws ram list-principals --resource-owner SELF \
  --resource-share-arns "arn:aws:ram:us-east-1:111111111111:resource-share/xxxxxxxx"
```

---

## Step 4: Auto-Accept Configuration

### If `acceptance_required = false` (recommended)

No additional steps needed. When a consumer account runs `CreateVpcEndpoint` referencing your service, the endpoint connection is automatically accepted and active.

### If `acceptance_required = true` (manual approval flow)

You'll need to use allowed principals to pre-authorize specific accounts, but connections still require explicit acceptance:

```hcl
resource "aws_vpc_endpoint_service_allowed_principal" "account_a" {
  vpc_endpoint_service_id = aws_vpc_endpoint_service.gwlb_general.id
  principal_arn           = "arn:aws:iam::123456789012:root"
}
```

> **Important:** `allowed_principal` does NOT auto-accept. It only controls who can request a connection. You would still need to accept each connection manually or via automation. For true zero-touch, use `acceptance_required = false`.

---

## Step 5: Consumer Account — Create the VPC Endpoint

This is what your consumer accounts (or their Terraform) will do:

```hcl
resource "aws_vpc_endpoint" "gwlb" {
  service_name      = "com.amazonaws.vpce.us-east-1.vpce-svc-0abc123def456789"
  vpc_endpoint_type = "GatewayLoadBalancer"
  vpc_id            = aws_vpc.main.id
  subnet_ids        = [aws_subnet.gwlb.id]

  tags = {
    Name = "gwlb-endpoint"
  }
}
```

If the SCP allows it and auto-accept is enabled → the endpoint goes active immediately.

If the SCP blocks it (PCI account hitting a general workload service) → `CreateVpcEndpoint` returns an access denied error.

---

## Step 6: Validate the Full Chain

### From a general workload account (should succeed):

```bash
# Should return the endpoint in "available" state
aws ec2 create-vpc-endpoint \
  --vpc-endpoint-type GatewayLoadBalancer \
  --service-name com.amazonaws.vpce.us-east-1.vpce-svc-0abc123def456789 \
  --vpc-id vpc-xxxxxxxx \
  --subnet-ids subnet-xxxxxxxx

# Verify
aws ec2 describe-vpc-endpoints \
  --query 'VpcEndpoints[*].[VpcEndpointId,ServiceName,State]' \
  --output table
```

### From a PCI account targeting a blocked service (should fail):

```bash
# Should return AccessDeniedException due to SCP
aws ec2 create-vpc-endpoint \
  --vpc-endpoint-type GatewayLoadBalancer \
  --service-name com.amazonaws.vpce.us-east-1.vpce-svc-aaaaaaa \
  --vpc-id vpc-xxxxxxxx \
  --subnet-ids subnet-xxxxxxxx
```

### From a PCI account targeting the PCI-authorized service (should succeed):

```bash
aws ec2 create-vpc-endpoint \
  --vpc-endpoint-type GatewayLoadBalancer \
  --service-name com.amazonaws.vpce.us-east-1.vpce-svc-pci12345 \
  --vpc-id vpc-xxxxxxxx \
  --subnet-ids subnet-xxxxxxxx
```

---

## Naming Convention Reference

| Type | Pattern | Example |
|------|---------|---------|
| AWS managed (interface) | `com.amazonaws.<region>.<service>` | `com.amazonaws.us-east-1.kms` |
| AWS managed (gateway) | `com.amazonaws.<region>.<service>` | `com.amazonaws.us-east-1.s3` |
| Custom / GWLB | `com.amazonaws.vpce.<region>.vpce-svc-<id>` | `com.amazonaws.vpce.us-east-1.vpce-svc-abc123` |

> **Why this matters:** SCP Option 2 (allow list) uses `StringLike: com.amazonaws.vpce.*.vpce-svc-*` to scope the deny to only custom services. AWS-managed endpoints never match this pattern, so they're never affected.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| PCI account can still create blocked endpoints | SCP not attached or wrong OU | Verify with `list-policies-for-target` |
| General workload account gets access denied | SCP attached too broadly (parent OU?) | Check SCP attachment target |
| Endpoint stuck in "pendingAcceptance" | `acceptance_required = true` on the service | Set to `false` or manually accept |
| Consumer can't discover the service | RAM share not active or wrong principal | Verify with `ram get-resource-shares` |
| Endpoint created but no traffic flowing | Route table not updated / GWLB target group health | Check routes and target group health |
| Existing non-compliant endpoints still active | SCPs only block new `CreateVpcEndpoint` calls | Audit and delete existing endpoints manually |

---

## Maintenance Notes

- **Adding new GWLB services:** If using Option 1 (deny list), update the SCP to include the new service name. If using Option 2 (allow list), no SCP change needed — new services are blocked by default.
- **New PCI-authorized services:** If using Option 2, add the service name to the `StringNotEquals` array.
- **Terraform management:** Keep the SCP content in a `.json` file referenced by `file()`. Use a Terraform variable for the service name list so changes go through PR review.
- **Auditing:** Periodically run `describe-vpc-endpoints` across PCI accounts to check for pre-existing non-compliant endpoints that were created before the SCP was applied.

---

## Related Documentation

- [AWS RAM Resource Shares](https://docs.aws.amazon.com/ram/latest/userguide/working-with-sharing.html)
- [VPC Endpoint Services (PrivateLink)](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoint-services.html)
- [VPC Endpoint Condition Keys](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-iam.html)
- [SCP Syntax Reference](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_syntax.html)
- [Gateway Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html)
