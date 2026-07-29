# Concerns with AFT-Vended Custom Service Security Groups

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-07-29 |
| **Prepared by** | Maximilian Browne |
| **Audience** | Cloud Security, Cloud Platform Engineering |
| **Document Type** | Architecture Concerns and Recommendation |

---

## Important Context Before Review

> I may be missing context from prior planning or decisions related to Sentinel policies, AFT, and the proposed custom security group approach. The concerns and recommendations in this document are based on my current understanding of the proposal and my expectations for how these controls would need to operate. They should be reviewed against any prior requirements, design decisions, or implementation constraints before being treated as final conclusions.

## Purpose

This document captures concerns with using AFT to vend empty custom service security groups into AWS accounts and then relying on Sentinel to control how application teams add rules and attach those security groups to resources.

The alternative is a developer-facing paved road module that deploys the application resource, validates the requested connectivity through a nested connectivity module, and attaches the correct security group as one operation.

## Proposed Custom Security Group Approach

The proposed flow is:

1. AFT creates an empty custom service security group during account vending.
2. An application team uses its own Terraform module to deploy a resource, such as a Lambda function.
3. The application team references the AFT-vended security group from its module.
4. The application team creates security group rule resources against that security group.
5. Sentinel determines whether the rules are allowed and whether the security group can be attached to the resource.

This keeps application resource deployment flexible while centralizing firewall policy enforcement in Sentinel. The concern is that Sentinel would need to reconstruct and validate the architecture from Terraform plan data instead of enforcing a simple paved road contract.

## Potential Advantages of the Custom Security Group Approach

There are valid arguments in favor of the AFT-vended custom security group approach.

### Application teams retain BYOM flexibility

Application teams can continue using their own modules and can expose the AWS provider features they need without waiting for a centrally maintained parent module to support every service option.

This may be valuable for teams with advanced use cases or for AWS services whose Terraform resource schemas change frequently.

### Fewer centrally maintained service wrappers may be required

A full paved-road model can create a large parent module estate. Each parent module may require:

- ongoing AWS provider compatibility work
- feature additions as service capabilities change
- version and release management
- documentation and examples
- migration support for consuming teams

If the organization did not already maintain these parent modules, this could be a significant implementation and ownership commitment.

### Connectivity policy can be centralized independently of application modules

The custom security group approach allows the firewall rule policy to be updated in Sentinel without requiring each application parent module to release a new version.

This can reduce coupling between connectivity-policy changes and application-module release schedules.

### AFT can establish a consistent account-level starting point

Vending the empty security groups through AFT can provide a predictable security group in every applicable account from the beginning of the account lifecycle.

This could make the expected security group easier to discover and could give the cloud platform a consistent inventory of centrally created security groups.

### Adoption may require fewer immediate application changes

Teams may be able to keep their existing application modules and add references to the vended security groups instead of migrating the full application resource into a new parent module.

That could reduce initial module migration work, especially where application teams already have mature BYOM implementations.

### The ownership boundary may appear simpler

The proposed model creates a straightforward ownership split on paper:

- AFT creates the empty security group
- the application team owns its service resource and requested rules
- Sentinel owns policy enforcement

This separation can be attractive if the goal is to avoid central ownership of application-resource implementation.

These benefits are real and should be considered. The remaining concern is whether they reduce total operational complexity or move that complexity into Sentinel catalogs, plan parsing, attachment validation, and cross-workspace state management.

In this environment, centrally maintained parent service modules already exist today. The paved-road proposal therefore extends an existing operating model rather than requiring an entirely new parent module estate. The custom security group approach would still need service-specific Sentinel logic for each supported resource and attachment pattern.

## Concerns

### Sentinel would need an authoritative security group catalog

Sentinel would need to know which security group belongs to each account, environment, and service type.

For example, if a plan references `sg-123`, Sentinel would need to determine:

- whether `sg-123` is the approved security group for the target account
- whether it belongs to development, test, or production
- whether it is intended for Lambda or another service
- whether the catalog is current if AFT replaced or recreated the security group

This creates another source of truth that has to remain synchronized with AFT and AWS.

### A custom security group does not prove resource identity

Calling or tagging a security group as a Lambda security group does not prove that it is attached only to Lambda functions.

Sentinel would need to check every resource attaching the security group. It would also need to understand all supported attachment paths, including direct resource arguments, network interfaces, launch templates, autoscaling resources, and nested modules.

For example, Sentinel would need to allow:

```hcl
resource "aws_lambda_function" "application" {
  # ...

  vpc_config {
    security_group_ids = ["sg-123"]
  }
}
```

It would also need to reject an EC2 instance, EKS workload, or other resource attaching that same supposedly Lambda-specific security group.

### Sentinel would need to validate both rules and attachments

Validating the security group rule is only half of the problem.

For a rule allowing `10.50.0.0/24` on TCP port `5432`, Sentinel would need to determine:

- whether the destination is allowed
- whether port `5432` is allowed for that destination
- whether the rule is being written to the correct security group
- whether the security group is approved for the environment
- whether the security group is attached to the intended service
- whether another unauthorized resource also uses the security group

The rule can be valid by itself while the attachment is still wrong.

### Sentinel would be rebuilding developer intent from plan data

The developer's actual request is simple:

> Deploy a Lambda function that needs to connect to this database on port 5432.

With the custom security group approach, Sentinel sees lower-level Terraform resources, security group IDs, rule resources, module outputs, and attachment properties. It then has to reconstruct the original intent from those details.

Terraform plans can also contain computed or unknown values. Security group IDs may come from data sources, remote state, module outputs, or conditional resources. This makes the policy more complicated and its result harder to explain.

### The design creates split ownership

AFT would own creation of the empty security group. The application team's Terraform would own the application resource and security group rules. Sentinel would own the logic that decides whether those separate pieces are allowed to work together.

This creates several places where the design can drift:

- AFT replaces a security group but the Sentinel catalog is not updated
- an application workspace references an old security group
- a security group is attached outside the expected workspace
- rules are changed through another Terraform workspace
- rules or attachments are changed through the console, API, or another automation system

Sentinel only evaluates the Terraform plans presented to it. It does not make the security group an enforcement boundary by itself.

### Every supported resource type increases policy complexity

Each AWS service represents networking and security group attachments differently.

Adding support for Lambda, EC2, ECS, EKS, RDS, load balancers, and other services would require Sentinel logic and testing for each Terraform resource shape and attachment mechanism. Provider changes could also require updates to Sentinel plan parsing.

This turns Sentinel policy into a growing AWS resource parser instead of a focused guardrail.

### Troubleshooting would be harder for developers

A failed Sentinel policy would likely report that a security group ID, rule resource, or attachment relationship did not match a central catalog.

That is less useful than a module validation error such as:

> Lambda production is not allowed to access `10.50.0.0/24` on TCP port `5432`.

Module validation can evaluate the request while the inputs still represent clear developer intent.

## Paved Road Module Comparison

Under the paved road approach, the developer uses an approved service module:

```hcl
module "application" {
  source = "company/lambda/aws"

  database_connections = [{
    destination = "10.50.0.0/24"
    port        = 5432
  }]
}
```

The parent module:

- establishes that the resource is a Lambda function
- derives or receives trusted account and environment context
- calls the centrally managed connectivity module as a nested module
- passes the connectivity request and hard-coded service identity to the nested connectivity module
- relies on the nested connectivity module to validate the destination and port
- relies on the nested connectivity module to create the governed security group and rules
- receives the security group ID as an output from the nested connectivity module
- attaches that output security group to the Lambda function

The resource identity, connectivity decision, security group, and attachment remain in the same Terraform graph.

Sentinel then has a smaller responsibility centered on approved module provenance and prevention of raw resource, security group rule, and attachment bypasses through governed Terraform pipelines.

Detailed policy behavior, module ancestry checks, enforcement levels, rollout sequencing, and out-of-band control dependencies are covered separately in [AWS Paved Road Sentinel Policy and Rollout Considerations](./aws-paved-road-sentinel-policy-and-rollout-considerations.md).

## Example Comparison

With the custom security group approach, Sentinel must answer:

1. Is `sg-123` the correct security group for this account and environment?
2. Is it intended for Lambda?
3. Is this Lambda allowed to attach it?
4. Is any other resource attaching it?
5. Is `10.50.0.0/24` on port `5432` allowed?
6. Did the security group ID come from the expected AFT-managed source?
7. Are there any other rule or attachment resources bypassing these checks?

With the paved road module, the module already knows the resource type, context, policy, security group, and attachment. Sentinel only needs to answer:

1. Did the developer use an approved service parent module source and version?
2. Did that approved parent call the approved connectivity module?
3. Did the developer try to call the connectivity module directly?
4. Did the developer create any raw resource, rule, or attachment outside the approved module chain?

The custom security group approach requires Sentinel to understand and validate the full design. The paved road approach builds the design correctly and uses Sentinel to prevent bypass through the governed Terraform configuration pipelines.

Neither the paved-road module nor Sentinel is an IAM security boundary. The companion Sentinel policy document covers the additional controls required for alternate deployment paths and out-of-band changes.

## Recommendation

Use full-featured developer-facing service modules that include the nested connectivity policy module and attach the governed security group as part of the same operation.

Use Sentinel to verify that the paved road was used correctly and to prevent raw resource, direct connectivity-module, security group rule, and attachment bypasses through the governed Terraform configuration pipelines.

Do not make Sentinel responsible for maintaining application identity, environment-to-security-group mappings, attachment authorization, and firewall rule authorization at the same time. That would make Sentinel a second control plane that must remain synchronized with AFT, Terraform state, and AWS inventory.

Based on my current understanding and the operating model already in place, I have high confidence that the paved-road parent module approach is the better option and recommend it over the AFT-vended custom security group approach unless missing prior context materially changes the requirements.
