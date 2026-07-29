# Concerns with AFT-Vended Custom Service Security Groups

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-07-29 |
| **Prepared by** | Maximilian Browne |
| **Audience** | Cloud Security, Cloud Platform Engineering |
| **Document Type** | Architecture Concerns and Recommendation |

---

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

At first glance, this keeps application resource deployment flexible while centralizing firewall policy enforcement in Sentinel. The concern is that Sentinel would need to reconstruct and validate the architecture from Terraform plan data instead of enforcing a simple paved road contract.

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

Sentinel then has a smaller and clearer responsibility:

- require the root module call to use an approved service parent module source and version
- verify that the centrally managed connectivity module is called from beneath an approved service parent module
- reject direct developer calls to the connectivity module
- allow governed security group rules only when their Terraform module address is beneath the approved parent and nested connectivity module chain
- reject raw service resources where the paved road is mandatory
- reject raw security group rules outside the approved module chain
- reject unmanaged security group attachments
- fail closed when the full parent and nested module provenance cannot be established

For example, Sentinel can allow a security group rule with module ancestry similar to:

```text
module.lambda.module.connectivity.aws_vpc_security_group_egress_rule.this
```

It can reject a direct developer call with ancestry similar to:

```text
module.connectivity.aws_vpc_security_group_egress_rule.this
```

Sentinel can make these decisions from Terraform configuration and plan metadata. The module call data includes the declaring module address, source, and version constraint. The resource data includes the module address where each resource was declared. This allows Sentinel to validate the approved caller chain without maintaining an account, environment, and security group ID catalog.

## Sentinel Policy Rollout and Migration

The enforcement should not be introduced as one hard-mandatory policy covering every existing service resource, security group rule, and attachment on day one.

A policy using `tfconfig/v2` evaluates the full Terraform configuration. If an existing workspace contains a raw Lambda function or legacy security group rule, a hard-mandatory policy requiring all resources to use the new parent module can fail the workspace's next run even when the legacy resource is unrelated to the proposed change.

Soft mandatory is not the desired enforcement state for this contract. A soft-mandatory failure allows an authorized user to override the result, while the intended policy decision is binary: if a deployment is required to use the paved road and it is outside the paved road, it is denied.

Advisory enforcement is appropriate only for initial discovery because it reports violations without blocking runs. Migration should then be controlled through policy scope. A workspace or service cohort remains outside the full policy scope while its existing resources are migrated. Once that cohort is ready, the full policy is applied as hard mandatory with no bypass override.

### Policies that can be hard mandatory immediately

The following policies can be hard mandatory when the new module ecosystem is introduced because they apply only when someone attempts to use the new approved module sources:

- reject any direct developer call to the centrally managed connectivity module
- require the connectivity module to be called from beneath an approved service parent module source
- require approved parent and connectivity module versions
- require security group resources created by the connectivity module to have the complete approved parent and nested module ancestry
- fail closed when a run attempts to use the connectivity module but its caller provenance cannot be established

These policies do not require existing workspaces to already use the paved road. They prevent the new connectivity module from being consumed incorrectly from the beginning.

A separate hard-mandatory policy can also prevent the creation of new raw service resources, security group rules, and unmanaged attachments by evaluating resource creation actions in `tfplan/v2`. This can stop new legacy patterns without immediately rejecting every unchanged legacy resource already present in configuration.

### Policies that require a staged rollout

The following full-configuration policies are likely to identify existing legacy resources and should begin as advisory:

- require every supported service resource to exist beneath its approved service parent module
- reject every raw security group rule outside the approved parent and connectivity module chain
- reject every unmanaged security group attachment
- reject every legacy module source or unsupported parent module version

After inventory and impact analysis, existing resources should be migrated by selected workspace or service cohort. Once a cohort is migrated, the full policies should be applied as hard mandatory for that scope. A deployment inside an enforced scope that is outside the paved road should be denied.

The practical rollout is:

1. Run the full-configuration policies as advisory to inventory violations.
2. Make caller-chain and connectivity-module provenance policies hard mandatory immediately.
3. Make no-new-legacy-resource policies hard mandatory using plan actions.
4. Migrate existing resources by workspace or service cohort.
5. Apply the full paved-road contract as hard mandatory to each cohort after it is clean.

The AFT-vended custom security group approach has the same migration concern. Existing resources would not already use the new security groups, attachments, or rule ownership model. It would also require temporary exceptions while old and new security group models coexist. Migration risk does not provide an advantage to the custom security group approach.

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

## Additional Enforcement Still Required

The paved road module is not an IAM security boundary.

If developers can create resources, modify security groups, or attach arbitrary security groups through the AWS console, API, CloudFormation, or another role, they can bypass Terraform and Sentinel.

AFT and the cloud platform still need to enforce:

- mandatory Sentinel policy assignment
- least-privilege Terraform execution roles
- IAM permission boundaries or SCP controls where appropriate
- restrictions on alternate deployment paths
- detective controls for out-of-band changes

The team is actively working on all of these enforcement dependencies as a parallel effort to the automation work. This includes mandatory policy assignment, execution-role restrictions, IAM and SCP controls where appropriate, restrictions on alternate deployment paths, and detection of out-of-band changes.

## Recommendation

Use full-featured developer-facing service modules that include the nested connectivity policy module and attach the governed security group as part of the same operation.

Use Sentinel to verify that the paved road was used correctly and to prevent raw resource, direct connectivity-module, security group rule, and attachment bypasses through the governed Terraform configuration pipelines.

Do not make Sentinel responsible for maintaining application identity, environment-to-security-group mappings, attachment authorization, and firewall rule authorization at the same time. That would make Sentinel a second control plane that must remain synchronized with AFT, Terraform state, and AWS inventory.
