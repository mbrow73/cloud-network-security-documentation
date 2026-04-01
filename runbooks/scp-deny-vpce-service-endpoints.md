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
│  │                   │--RAM--│  PCI OU                │  │
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
- [ ] OU structure in place (e.g., General Workload OU, PCI OU)
- [ ] Endpoint service IDs for all GWLB services (both general and PCI-dedicated)

---

## Step 1: SCP Policy (Management Account)

**Why first:** The SCP must be in place BEFORE sharing the endpoint services. If you share first, PCI accounts could create non-compliant endpoints in the window before the SCP is applied.

Our team does not create SCPs. Provide the following policy to the team that manages SCPs and request it be attached to the PCI OU.

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

### Alternative: Allow List

For a stricter posture, an allow list blocks ALL custom endpoint services except the ones explicitly authorized. New services are denied by default without SCP updates.

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

**How it works:**
- `StringLike` scopes the deny to only custom endpoint services (`vpce-svc-*` pattern)
- `StringNotEquals` carves out the authorized PCI service
- AWS-managed endpoints (S3, KMS, Lambda, etc.) use a different naming pattern (`com.amazonaws.<region>.<service>`) and are never affected

**⚠️ Do not proceed to Step 2 until the SCP is confirmed attached to the PCI OU.**

---

## Step 2: Configure the GWLB Endpoint Service (Inspection Account)

### 2a. Locate the Endpoint Services

The endpoint services already exist in the inspection account (AWS_ISInspection_600001725). Navigate to:

**VPC > Endpoint Services** in the AWS Console.

Note the service names for each GWLB endpoint service. They follow the pattern: `com.amazonaws.vpce.us-east-1.vpce-svc-0abc123def456789`

These are the values needed in the SCP (Step 1) and the RAM share (Step 3).

### 2b. Set Auto-Accept

For each endpoint service that should support automatic association:

1. Select the endpoint service in the console
2. **Actions > Modify endpoint service**
3. Set **Acceptance required** to `false`
4. Save

This ensures that when a consumer account creates a VPC endpoint referencing the service, the connection is automatically accepted with no manual approval needed.

---

## Step 3: Share the Endpoint Service via RAM (Inspection Account)

### 3a. Create the RAM Resource Share

1. Navigate to **RAM > Resource Shares** in the AWS Console (inspection account)
2. Click **Create resource share**
3. Name: `gwlb-general-endpoint-service` (or appropriate name per service)
4. Resource type: **VPC Endpoint Services**
5. Select the endpoint service(s) to share
6. Click **Next**

### 3b. Associate Principals

1. Under **Principals**, select **Allow sharing with anyone in your organization**
2. Add the target OU ARN: `arn:aws:organizations::<mgmt-account-id>:ou/o-xxxxxxxx/ou-aaaa-bbbbbbbb`
3. You can add multiple OUs or individual account IDs as needed
4. Click **Next**, review, and **Create resource share**

### 3c. Verify the Share

Confirm the share shows as **Active** in the RAM console and that the correct principals are listed.

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

**Why this matters:** The allow list SCP option uses `StringLike: com.amazonaws.vpce.*.vpce-svc-*` to scope the deny to only custom services. AWS-managed endpoints never match this pattern, so they are never affected.

---

## Maintenance Notes

- **Adding new GWLB services:** If using the deny list SCP, update the SCP to include the new service name. If using the allow list SCP, no change needed since new services are blocked by default.
- **New PCI-authorized services:** If using the allow list, add the service name to the `StringNotEquals` array.
- **Existing endpoints:** SCPs only block new `CreateVpcEndpoint` calls. Audit PCI accounts for any pre-existing non-compliant endpoints that were created before the SCP was applied and remove them manually.
