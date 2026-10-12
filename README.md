# cloud-network-security-documentation

Cloud network security documentation, runbooks, and operational guides

## Architecture decision records

- [GCP third-party ingress reverse-proxy removal](adrs/adr-gcp-third-party-ingress-reverse-proxy-removal.md) - proposed options, detailed SVG diagrams, regional Palo routing constraints, Cloud NGFW inspection gaps, PA/DNAT or Palo NSI candidates
- [GCP internet egress architecture](adrs/adr-gcp-internet-egress-architecture.md)

## AWS diagrams

- [VPC Lattice Resource Gateway → GWLBe / GWLB / Palo → Amazon RDS](diagrams/aws-vpc-lattice-resource-gateway-gwlb-rds-routing.png)
  - [Editable standalone HTML](diagrams/aws-vpc-lattice-resource-gateway-gwlb-rds-routing.html)
- [GWLB shared egress VR — PROD direct / NONPROD COLO hairpin](diagrams/aws-gwlb-rds-shared-egress-vr-prod-nonprod-hairpin.png)
  - [Editable standalone HTML](diagrams/aws-gwlb-rds-shared-egress-vr-prod-nonprod-hairpin.html)
