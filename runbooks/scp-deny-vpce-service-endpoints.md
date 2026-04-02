# GWLB Endpoint Service Sharing with PCI Isolation

## Overview

This runbook walks through sharing GWLB VPC endpoint services across an AWS Organization via RAM, enabling automatic endpoint association for consumer accounts, and enforcing isolation for PCI-scoped accounts using SCPs.

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
│  │  Inspection Acct  │       │  General Workload OU   │  │
│  │  (GWLB owner)    │       │                        │  │
│  │                   │--RAM--│  ✅ Can create VPC-E   │  │
│  │  • gwlb-general   │share  │     to gwlb-general    │  │
│  │  • gwlb-pci       │       │  ✅ Auto-associates    │  │
│  │                   │       └────────────────────────┘  │
│  │                   │                                   │
│  │                   │       ┌────────────────────────┐  │
│  │                   │--RAM--│  PCI Account            │  │
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
- [ ] Inspection account that owns the GWLB and endpoint services (AWS_ISInspection_600001725)
- [ ] OU structure in place (e.g., General Workload OU) and PCI account identified
- [ ] Endpoint service IDs for all GWLB services (both general and PCI-dedicated)

---

## Step 1: SCP Policy (Management Account)

**Why first:** The SCP must be in place BEFORE sharing the endpoint services. If you share first, PCI accounts could create non-compliant endpoints in the window before the SCP is applied.

Our team does not create SCPs. Provide the following policy to the team that manages SCPs and request it be attached to the PCI account.

### SCP Policy: Deny List

Block specific general workload endpoint services. PCI accounts can still connect to anything not on the list, including their own dedicated services.

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

Replace the placeholder service IDs with the actual endpoint service names from AWS_ISInspection_600001725.

**⚠️ Do not proceed to Step 2 until the SCP is confirmed attached to the PCI account.**

---

## Step 2: Configure the GWLB Endpoint Service (Inspection Account)

### 2a. Locate the Endpoint Services

The endpoint services already exist in the inspection account (AWS_ISInspection_600001725). Navigate to:

**VPC > Endpoint Services** in the AWS Console.

Note the service names for each GWLB endpoint service. They follow the pattern: `com.amazonaws.vpce.us-east-1.vpce-svc-0abc123def456789`

These are the values needed in the SCP (Step 1) and the RAM share (Step 3).

### 2b. Set Auto-Accept

```hcl
resource "aws_vpc_endpoint_service" "gwlb_general" {
  acceptance_required        = false
  gateway_load_balancer_arns = [aws_lb.gwlb_general.arn]

  tags = {
    Name = "gwlb-general-workload-endpoint-service"
  }
}
```

Setting `acceptance_required = false` ensures that when a consumer account creates a VPC endpoint referencing the service, the connection is automatically accepted with no manual approval needed.

---

## Step 3: Share the Endpoint Service via RAM (Inspection Account)

### 3a. Create the RAM Resource Share

```hcl
resource "aws_ram_resource_share" "gwlb_general" {
  name                      = "gwlb-general-endpoint-service"
  allow_external_principals = false

  tags = {
    Name = "gwlb-general-endpoint-service-share"
  }
}

resource "aws_ram_resource_association" "gwlb_general" {
  resource_arn       = aws_vpc_endpoint_service.gwlb_general.arn
  resource_share_arn = aws_ram_resource_share.gwlb_general.arn
}
```

### 3b. Associate Principals

```hcl
resource "aws_ram_principal_association" "workload_ou" {
  principal          = "arn:aws:organizations::111111111111:ou/o-xxxxxxxx/ou-aaaa-bbbbbbbb"
  resource_share_arn = aws_ram_resource_share.gwlb_general.arn
}
```

You can add multiple `aws_ram_principal_association` resources to share with additional OUs or individual account IDs.

### 3c. Verify the Share

After `terraform apply`, confirm the share shows as **Active** in the RAM console and that the correct principals are listed.

---

## Step 4: Auto-Accept Behavior

With `acceptance_required = false` (configured in Step 2b), no additional steps are needed. When a consumer account creates a VPC endpoint referencing the shared service, the endpoint connection is automatically accepted and goes active immediately.

The full flow:
1. SCP is in place, blocking PCI accounts from non-authorized services
2. RAM share gives the target OU visibility into the endpoint service
3. Consumer account creates a VPC endpoint referencing the service
4. Connection auto-accepts, endpoint goes active, traffic flows

---

## Naming Convention Reference

| Type | Pattern | Example |
|------|---------|---------|
| AWS managed (interface) | `com.amazonaws.<region>.<service>` | `com.amazonaws.us-east-1.kms` |
| AWS managed (gateway) | `com.amazonaws.<region>.<service>` | `com.amazonaws.us-east-1.s3` |
| Custom / GWLB | `com.amazonaws.vpce.<region>.vpce-svc-<id>` | `com.amazonaws.vpce.us-east-1.vpce-svc-abc123` |

---

## Maintenance Notes

- **Adding new GWLB services:** Update the SCP to include the new service name.
- **Existing endpoints:** SCPs only block new `CreateVpcEndpoint` calls. Audit PCI accounts for any pre-existing non-compliant endpoints that were created before the SCP was applied and remove them manually.
