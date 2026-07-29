# AWS Paved Road Sentinel Policy and Rollout Considerations

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-07-29 |
| **Prepared by** | Maximilian Browne |
| **Audience** | Cloud Security, Cloud Platform Engineering |
| **Document Type** | Policy Design and Rollout Considerations |

---

## Important Context Before Review

> I may be missing context from prior planning or decisions related to Sentinel policies, AFT, and existing policy-set deployment. The considerations in this document are based on my current understanding and expectations for how paved-road enforcement would need to operate. They should be reviewed against any prior requirements, design decisions, implementation constraints, and existing Sentinel policies before being treated as final.

## Purpose

This document separates the Sentinel policy design and rollout considerations from the broader comparison between AFT-vended custom service security groups and developer-facing paved-road service modules.

The related architecture comparison is documented in [Concerns with AFT-Vended Custom Service Security Groups](./aws-aft-vended-custom-service-security-group-concerns.md).

## Intended Enforcement Boundary

Under the paved-road approach:

- an approved service parent module establishes the application resource type
- the parent calls the centrally managed connectivity module
- the connectivity module validates the requested destination and port
- the connectivity module creates the governed security group and rules
- the parent receives the security group ID as an output
- the parent attaches the security group and any required baseline security groups to the service resource

Sentinel should verify that this approved contract was used and prevent Terraform configuration from bypassing it.

Sentinel should not duplicate the nested connectivity module's CIDR and port authorization logic.

## Sentinel Policy Responsibilities

Sentinel should:

- require the root module call to use an approved service parent module source and version
- verify that the centrally managed connectivity module is called from beneath an approved service parent module
- reject direct developer calls to the connectivity module
- allow governed security group rules only when their Terraform module address is beneath the approved parent and nested connectivity module chain
- reject raw service resources where the paved road is mandatory
- reject raw security group rules outside the approved module chain
- reject unmanaged security group attachments
- fail closed when the full parent and nested module provenance cannot be established

The intended policy decision is binary:

> If a deployment is required to use the paved road and it is outside the paved road, it is denied.

## Module Ancestry Example

Sentinel can allow a security group rule with module ancestry similar to:

```text
module.lambda.module.connectivity.aws_vpc_security_group_egress_rule.this
```

It can reject a direct developer call with ancestry similar to:

```text
module.connectivity.aws_vpc_security_group_egress_rule.this
```

Sentinel can make these decisions from Terraform configuration and plan metadata.

The `tfconfig/v2` module call data includes:

- the module address where the call was declared
- the module name
- the module source
- the version constraint

The resource data includes the module address where each resource was declared. This allows Sentinel to validate the approved caller chain without maintaining an account, environment, and security group ID catalog.

## Policy Rollout and Migration

The enforcement should not be introduced as one hard-mandatory policy covering every existing service resource, security group rule, and attachment on day one.

A policy using `tfconfig/v2` evaluates the full Terraform configuration. If an existing workspace contains a raw Lambda function or legacy security group rule, a hard-mandatory policy requiring all resources to use the new parent module can fail the workspace's next run even when the legacy resource is unrelated to the proposed change.

Soft mandatory is not the desired enforcement state for this contract. A soft-mandatory failure allows an authorized user to override the result, while the intended policy decision does not allow paved-road bypasses.

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

## Additional Enforcement Still Required

The paved-road module is not an IAM security boundary.

If developers can create resources, modify security groups, or attach arbitrary security groups through the AWS console, API, CloudFormation, or another role, they can bypass Terraform and Sentinel.

AFT and the cloud platform still need to enforce:

- mandatory Sentinel policy assignment
- least-privilege Terraform execution roles
- IAM permission boundaries or SCP controls where appropriate
- restrictions on alternate deployment paths
- detective controls for out-of-band changes

The team is actively working on all of these enforcement dependencies as a parallel effort to the automation work. This includes mandatory policy assignment, execution-role restrictions, IAM and SCP controls where appropriate, restrictions on alternate deployment paths, and detection of out-of-band changes.

## Recommendation

Implement Sentinel as the enforcement layer for paved-road provenance and Terraform bypass prevention.

Keep the connectivity authorization decision inside the nested connectivity module, where the developer's requested destination and port remain explicit.

Use advisory policies only to inventory migration impact. Once a workspace or service cohort enters the enforced scope, require the complete paved-road contract through hard-mandatory policies without bypass overrides.
