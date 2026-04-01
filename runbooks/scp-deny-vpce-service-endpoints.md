# SCP: Deny VPC Endpoint Service Connections (GWLB / Custom)

## Purpose

Prevent specific accounts (e.g., PCI-scoped accounts) from creating VPC endpoints to non-authorized custom VPC endpoint services (such as general workload GWLB services shared via RAM at the OU level).

This does **not** affect AWS-managed interface/gateway endpoints (S3, KMS, Lambda, etc.) — only custom `vpce-svc-*` services.

## Background

When sharing GWLB endpoint services via AWS RAM at the OU level, all accounts in the OU can create VPC endpoints to the shared service. For compliance isolation (e.g., PCI accounts should not route through general workload inspection), an SCP can deny endpoint creation against specific services.

## Option 1: Deny Specific Services (Deny List)

Block a known set of custom endpoint services. Accounts can still connect to anything not on the list, including their own dedicated services.

**Use when:** You have a defined set of services to block and PCI accounts may need access to other custom endpoint services in the future.

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

**Pros:**
- Simple, explicit
- No risk of blocking AWS-managed endpoints
- PCI accounts retain access to their own dedicated services automatically

**Cons:**
- Must update the SCP when new GWLB services are created
- Maintenance burden scales with number of services

## Option 2: Allow Only Authorized Services (Allow List)

Deny all custom endpoint services except explicitly authorized ones. Tighter posture — new services are blocked by default.

**Use when:** PCI accounts should only ever connect to a single known custom service.

> ⚠️ **Warning:** This does NOT block AWS-managed endpoints (`com.amazonaws.<region>.<service>`), only custom endpoint services matching the `vpce-svc-*` pattern. See condition key behavior below.

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
- AWS-managed endpoints (S3, KMS, Lambda, etc.) use a different naming pattern (`com.amazonaws.<region>.<service>`) and are not affected

**Pros:**
- Zero-trust: new custom services are denied by default
- No maintenance when general workload services are added
- PCI-compliant posture (explicit allow list)

**Cons:**
- Must update the allow list if PCI accounts need additional custom services
- Requires understanding of the naming pattern distinction

## Naming Convention Reference

| Type | Pattern | Example |
|------|---------|---------|
| AWS managed (interface) | `com.amazonaws.<region>.<service>` | `com.amazonaws.us-east-1.kms` |
| AWS managed (gateway) | `com.amazonaws.<region>.<service>` | `com.amazonaws.us-east-1.s3` |
| Custom / GWLB | `com.amazonaws.vpce.<region>.vpce-svc-<id>` | `com.amazonaws.vpce.us-east-1.vpce-svc-abc123` |

## Deployment Notes

- Attach the SCP to the OU or accounts that need restriction (e.g., PCI OU)
- **Existing endpoints are not affected** — this only prevents new `CreateVpcEndpoint` calls. Audit and remove any pre-existing non-compliant endpoints separately.
- Recommend managing the SCP via Terraform with the service list as a variable for change tracking and review.
- Condition key `ec2:VpceServiceName` is documented for the `ec2:CreateVpcEndpoint` action.

## Related

- [AWS RAM Resource Shares](https://docs.aws.amazon.com/ram/latest/userguide/working-with-sharing.html)
- [VPC Endpoint Service Condition Keys](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-iam.html)
- [SCP Syntax Reference](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_syntax.html)
