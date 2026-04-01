# Network Security Team -- GitHub Projects Implementation Guide

## Table of Contents

1. [Team Context & Design Principles](#team-context--design-principles)
2. [Project Structure](#project-structure)
3. [Custom Fields](#custom-fields)
4. [Issue Types & Workflows](#issue-types--workflows)
5. [Project Delivery Structure](#project-delivery-structure)
6. [Day-to-Day Operating Procedures](#day-to-day-operating-procedures)
7. [Automation & Integration](#automation--integration)
8. [Board Views & Dashboards](#board-views--dashboards)
9. [Worked Examples](#worked-examples)

---

## Team Context & Design Principles

### Who We Are

A 30-person network security team responsible for architecting, engineering, and delivering security infrastructure across the enterprise. The team includes developers, cloud network security architects and engineers, Palo Alto engineers, and Illumio engineers. We operate as an enabling function -- one team supporting many.

### What We Do

| Category | Examples |
|----------|----------|
| Architecture & Design | Solution design, threat modeling, network segmentation strategy |
| Engineering & Build | Terraform/Ansible IaC, automation tooling, GitHub repos, PaC development |
| Platform Management | ~350 physical and ~150 virtual Palo Alto firewalls, multiple Panorama instances, Illumio rollout and policy |
| Consultation & Advisory | Ad-hoc design sessions, solution reviews, cross-team architecture discussions |
| Security Reviews | Cloud service network security reviews, SaaS security support, third-party security review support |
| Governance & Compliance | SOPs, standards, regulatory controls, audit support (multiple per year) |
| Training & Enablement | Training sister teams in operations and public cloud enablement |
| Operations (residual) | Firewall rule management, platform maintenance, operational support for systems not yet handed off |

### Design Principles

1. **Single project, single board.** All work lives in one place. Engineers should never wonder which board to look at.
2. **Minimal ceremony. Kanban, not Scrum.** No sprint planning, no velocity tracking, no story points. The board reflects reality, not a process.
3. **Issue types carry the workflow.** Different work moves through different statuses. The system adapts to the work, not the other way around.
4. **Visibility through filtering, not duplication.** One board with saved views gives each role (engineer, lead, leadership) the view they need without maintaining parallel tracking.
5. **Capture enough, not everything.** The goal is to make all work visible and measurable -- not to create a paperwork burden. If filling out a field doesn't serve reporting or decision-making, remove it.
6. **Automate transitions where possible.** If a GitHub PR can move a ticket, the engineer shouldn't have to.

---

## Project Structure

### GitHub Project: NETSEC (Network Security)

- **Board type:** Kanban (GitHub Projects Board view)
- **One board** with swimlanes by issue type (labels)
- Engineers, leads, and leadership all use the same board with different saved views

### Why Not Multiple Projects?

The same engineer may do a Palo Alto deployment in the morning, join a consultation call at noon, and review a cloud service in the afternoon. Splitting work across projects creates friction:

- Tickets get created in the wrong place
- Cross-cutting work falls through the cracks
- Engineers context-switch between boards instead of working
- Reporting requires aggregating across projects

One project with smart filtering eliminates all of this.

### GitHub Projects vs. Jira Mapping

| Jira Concept | GitHub Projects Equivalent |
|---|---|
| Project (NETSEC) | GitHub Project (board) |
| Issue Type | Label (build, change, consultation, etc.) |
| Custom Fields | Project custom fields (single select, text, date, etc.) |
| Workflow/Status | Project "Status" field (single select, per-view filtering) |
| Components (Workstreams) | Labels or custom field |
| Swimlanes | Group-by in board view |
| Saved Filters | Saved views with filters |
| Jira Automation | GitHub Actions workflows |
| Workflow Schemes | N/A -- use label-based conventions + automation |

---

## Custom Fields

Keep custom fields to a minimum. Every field should serve either day-to-day workflow or reporting. If it doesn't, remove it.

### Required Fields (all issue types)

| Field | Type | Values | Purpose |
|-------|------|--------|---------|
| Domain | Single select | Palo Alto, Illumio, Cloud Network Security, IaC & Automation, Governance & Compliance, Training & Enablement, General Operations | Filter board by specialty; capacity reporting by domain |
| Partner Team | Single select / text | (Team names, e.g., Cloud Engineering, Platform, SaaS Security, Internal) | Identifies who you're supporting; "Internal" = team-owned work |
| Priority | Single select | Critical, High, Medium, Low | Triage and SLA tracking |

### Feature-Level Fields (projects only)

| Field | Type | Values | Purpose |
|-------|------|--------|---------|
| Engagement Type | Single select | Internal Project, External Support | Capacity reporting -- how much time goes to your own initiatives vs. supporting others |
| Target Date | Date | -- | Delivery milestone |
| Project Status | Single select | On Track, At Risk, Blocked, Complete | Leadership-level status at a glance |

### Contextual Fields (use only where relevant)

| Field | Type | When to Use |
|-------|------|-------------|
| Environment | Single select (Non-Prod / Prod) | Change and Build tickets involving deployments |
| Change Risk | Single select (Standard / Significant / Emergency) | Change tickets -- drives workflow complexity |
| ServiceNow Change ID | Text (e.g., CHG0012345678) | Change tickets -- links to the corresponding ServiceNow RFC |
| SLA Due Date | Date | Finding and Incident tickets |
| Compliance Framework | Text (SOX, PCI, NIST, etc.) | Governance, Standards, and audit-related tickets |

---

## Issue Types & Workflows

GitHub Projects doesn't enforce per-label workflows natively. Instead, each issue type (label) has a **documented status convention**, and automation enforces transitions where possible.

### Summary Table

| Issue Type (Label) | Purpose | Status Flow | GitHub Automation | SLA Tracking |
|---|---|---|---|---|
| `build` | IaC, automation, tooling, new capabilities | Backlog > In Progress > In Review > Changes Requested > Merged > Closed | Yes (PR lifecycle) | No |
| `change` | Deploying/modifying infrastructure | Standard: To Do > Closed / Significant: Draft > Ready for Review > Approved > Scheduled > Closed / Emergency: In Progress > Closed | Partial (PR links) | Optional |
| `consultation` | Design sessions, advisory, cross-team support | Open > In Progress > Completed | No | No |
| `review` | Cloud service, SaaS, third-party security reviews | Open > In Review > Decision | No | Optional |
| `finding` | Vulnerabilities, misconfigs, audit findings | Open > Triaged > Assigned > In Remediation > Verified > Closed / Risk Accepted | Yes (scanner webhooks) | Yes |
| `incident` | Reactive security events | Detected > Investigating > Remediating > Resolved > RCA > Closed | Partial | Yes |
| `task` | Ops work, documentation, training, meetings | To Do > In Progress > Blocked > Done | No | No |
| `standards` | SOPs, baselines, regulatory controls | Draft > Internal Review > Stakeholder Review > Approved > Published / Retired | Partial (scheduled) | Optional |
| `milestone` | Zero-effort delivery checkpoint | Open > Achieved | No | No |

### Build

*Net-new IaC, automation, tooling, or platform capability work.*

**Status Flow:** `Backlog` > `In Progress` > `In Review` > `Changes Requested` > `Merged` > `Closed`

| Status | Description |
|--------|-------------|
| Backlog | Defined but not yet started |
| In Progress | Engineer actively building |
| In Review | PR open, awaiting peer review |
| Changes Requested | Reviewer flagged issues, back to engineer |
| Merged | PR merged into main |
| Closed | Complete -- deployed or ready for a separate Change ticket |

**GitHub automation:** PR opened > In Review. Review requested changes > Changes Requested. PR approved and merged > Merged.

**When to use:** Any work that produces a code artifact -- Terraform modules, Ansible playbooks, PaC rules, automation scripts, GitHub Actions workflows.

**When NOT to use:** If the work is deploying existing code to an environment or modifying live infrastructure (including firewall rules in Panorama, whether via IaC or manually), that's a Change.

### Change

*Deploying, modifying, or decommissioning infrastructure in an actual environment.*

Changes have three workflow tracks based on risk:

#### Standard Change (routine, low-risk, pre-approved patterns)

**Status Flow:** `To Do` > `Closed`

Examples: adding a firewall rule from an approved request, deploying a tested Terraform module to non-prod, routine Panorama config push.

#### Significant Change (new deployments, production changes, architectural shifts)

**Status Flow:** `Draft` > `Ready for Review` > `Approved` > `Scheduled` > `Closed`

Examples: new Palo Alto virtual firewall deployment, production VPC peering changes, Illumio policy enforcement mode switch.

#### Emergency Change (unplanned, must happen now)

**Status Flow:** `In Progress` > `Closed`

Examples: critical vulnerability patching, production outage remediation, emergency firewall rule for active incident.

### Consultation

*Ad-hoc design sessions, solution reviews, cross-team architecture discussions.*

**Status Flow:** `Open` > `In Progress` > `Completed`

**When to use:** Another team asks for design help, architecture guidance, or a working session. The deliverable is advice or a recommendation, not a code artifact or infrastructure change.

### Review

*Cloud service network security reviews, SaaS security support, third-party security review support.*

**Status Flow:** `Open` > `In Review` > `Approved` | `Approved with Conditions` | `Denied`

| Status | Description |
|--------|-------------|
| Open | Review requested, not yet started |
| In Review | Actively evaluating |
| Approved | Service/product cleared with no conditions |
| Approved with Conditions | Cleared with specific requirements that must be met |
| Denied | Not approved -- documented rationale required |

**Required fields:** Partner Team (who requested the review), Summary (service name, vendor, use case).

**Guidance:**
- Attach or link the review artifact (document, spreadsheet, email thread) to the ticket.
- For "Approved with Conditions," document the conditions in the ticket.
- Reviews supporting SaaS security or third-party security teams should set Partner Team accordingly for reporting on support metrics.

**When to use:** A team is onboarding a new cloud service or SaaS product and needs network security sign-off.

### Finding

*Vulnerabilities, misconfigurations, or audit findings requiring remediation.*

**Status Flow:** `Open` > `Triaged` > `Assigned` > `In Remediation` > `Remediated` > `Verified` > `Closed` | `Risk Accepted`

| Status | Description |
|--------|-------------|
| Open | Finding identified -- often auto-created by security tooling |
| Triaged | Severity confirmed, validity assessed |
| Assigned | Owner identified -- SLA clock starts |
| In Remediation | Active work underway |
| Remediated | Fix applied, pending confirmation |
| Verified | Scanner or manual check confirms resolution |
| Closed | Complete |
| Risk Accepted | Conscious decision not to remediate, with documented rationale and approver |

**SLA targets by severity:**

| Severity | Time to Assign | Time to Verified |
|----------|---------------|-----------------|
| Critical | 24 hours | 7 days |
| High | 3 business days | 30 days |
| Medium | 5 business days | 90 days |
| Low | 10 business days | 180 days |

These times will be adjusted as required.

**Risk Accepted** is a terminal state, not a workaround. It requires:
- Documented rationale
- Named approver (manager or above)
- Review date (when to reassess)

**Automation:** Security scanners (Prisma, Earlybird) can auto-create Finding issues via webhook with severity label and SLA due date pre-populated.

### Incident

*Reactive work triggered by a security event.*

**Status Flow:** `Detected` > `Investigating` > `Remediating` > `Resolved` > `RCA` > `Closed`

| Status | Description |
|--------|-------------|
| Detected | Event identified, ticket created |
| Investigating | Assigned, actively triaging and determining scope |
| Remediating | Root cause identified, fix being applied |
| Resolved | Threat addressed, systems stable |
| RCA | Root cause analysis in progress |
| Closed | RCA complete and documented |

**Incidents spawn child tickets.** An incident often surfaces Findings (underlying vulnerabilities), requires Changes (infrastructure modifications), and generates Build work (tooling improvements). The Incident ticket is the parent that ties them together. Child tickets can outlive the parent -- the Incident closes when the RCA is done, even if remediation work continues under linked tickets.

### Task

*Catch-all for work that doesn't fit other types -- operational tasks, documentation, training sessions, meetings, handoff activities.*

**Status Flow:** `To Do` > `In Progress` > `Blocked` > `Done`

| Status | Description |
|--------|-------------|
| To Do | Defined, not started |
| In Progress | Actively working |
| Blocked | Waiting on an external dependency -- gets its own status for standup visibility |
| Done | Complete |

**When to use:**
- Writing or updating documentation and runbooks
- Conducting training sessions
- Attending handoff meetings
- Recurring operational work (access audits, certificate renewals)
- Anything that doesn't fit the other issue types

**When NOT to use:** If the work produces code, it's a Build. If it's deploying to or modifying a live environment (including manual firewall rule changes in Panorama), it's a Change. If you're advising another team, it's a Consultation. Keep Task as a true catch-all, not a dumping ground for work that should be properly categorized.

### Standards

*Standards, SOPs, baselines, control documentation, and required configurations -- the technical "how we do it" documents that implement organizational policies.*

**Status Flow:** `Draft` > `Internal Review` > `Stakeholder Review` > `Approved` > `Published` | `Retired`

| Status | Description |
|--------|-------------|
| Draft | Standard/SOP being written or revised |
| Internal Review | Security team peer review |
| Stakeholder Review | Out to affected teams or leadership for sign-off |
| Approved | Sign-off received, ready to publish |
| Published | Active standard -- terminal state until next review cycle |
| Retired | Standard formally decommissioned with documented rationale |

**Review cadence:** Set a due date on Published tickets. Use GitHub Actions automation to create a new Draft ticket 30 days before the review date, so standards reviews are never forgotten.

**Compliance Framework field:** Tag Standards tickets with applicable frameworks (SOX, PCI, NIST, etc.) to quickly pull all standards relevant to a specific audit.

### Milestone

*Zero-effort delivery checkpoint.*

**Status Flow:** `Open` > `Achieved`

Zero-effort markers that give leadership and PMs phase visibility without reading every underlying ticket. Link milestones to related issues.

---

## Project Delivery Structure

### Hierarchy

```
Feature (the project)
  └── Workstream (the phase or track)
        └── Issue Type tickets (the actual work)
              └── Milestone (phase gate)
```

- **Features** represent projects -- either internal initiatives or external support engagements.
- **Workstreams** are implemented as GitHub Milestones within the project. Standard components: **Discovery, Design, Build, Deployment, Handoff**. PMs can add project-specific milestones as needed (e.g., "Migration - Wave 1", "Enforcement"). Filter with milestone labels or combine with project context.
- **Individual tickets** use the appropriate issue type based on the nature of the work.
- **Milestones** mark phase boundaries within the Feature.

### Internal vs. External Projects

**Internal Projects** -- your team defines the scope, owns the deliverables, and controls the timeline. Examples: Palo Alto platform migration, new Terraform module library, Illumio policy enforcement rollout.

**External Support Projects** -- another team has a project, and your team is providing network security architecture, engineering, or consultation. Examples: EKS security enablement for Cloud Engineering, network security review for a new SaaS platform. You contribute but don't own the overall delivery.

The distinction matters for capacity reporting. Leadership needs to see how much of the team's time goes to internal initiatives vs. supporting other teams.

### Standard Workstream Components

Every project should use a consistent set of milestones (workstreams) to represent phases:

| Workstream | Purpose |
|------------|---------|
| Discovery | Requirements gathering, current state analysis, stakeholder interviews |
| Design | Architecture decisions, solution design, design doc creation |
| Build | IaC development, automation, tooling, code artifacts |
| Deployment | Environment setup, config push, cutover execution |
| Handoff | Documentation, training, operational handoff to steady-state team |

PMs can add project-specific milestones as needed (e.g., "Migration - Wave 1", "Enforcement", "Pilot"). The standard set ensures consistency across projects while allowing flexibility.

### Example: Panorama Consolidation

```
Feature: Panorama Consolidation
  Engagement Type: Internal Project
  Target Date: 2026-Q3
  Project Status: On Track

  Milestone: Discovery
    > Issue (Build): Inventory current Panorama instances
    > Issue (Consultation): Architecture review with TAC
    > Milestone Issue: Discovery Complete

  Milestone: Build
    > Issue (Build): Ansible playbook for config backup
    > Issue (Build): Terraform module for bootstrap
    > Milestone Issue: Tooling Ready

  Milestone: Migration
    > Issue (Change - Significant): Migrate device groups batch 1
    > Issue (Change - Significant): Migrate device groups batch 2
    > Milestone Issue: Migration Complete
```

---

## Day-to-Day Operating Procedures

### For Engineers

**Start of day:**
1. Open the Kanban board (filtered to your Domain if preferred)
2. Check your In Progress tickets -- update status if anything moved
3. Check for new tickets assigned to you

**During the day:**
- When you start work on something, move the ticket to In Progress
- When you're pulled into an ad-hoc call or design session, create a Consultation ticket (or update an existing one) before the day ends
- When you finish something, move it to the appropriate next status -- don't let tickets sit in a stale state
- If you're blocked, move the ticket to Blocked and add a comment explaining what you're waiting on

**End of day:**
- Every piece of work you did today should be reflected on the board. If you spent two hours on a call helping another team, there should be a ticket for it.

### Ticket Creation Guidelines

**When to create a ticket:**
- When the work is meaningful enough that someone would want to know about it -- whether that's your lead, a partner team, or a future you trying to remember what you worked on last quarter
- After any ad-hoc request, consultation call, or review -- even if the work is already done
- When a new request comes in via Slack, email, or a meeting

**What to fill out:**
- **Summary:** Clear, descriptive title. "Fix firewall rule" is bad. "NETSEC-East: Add egress rule for app-x to reach payment gateway" is good.
- **Issue Type:** Pick the right one (see guidance under each type above)
- **Domain:** Which specialty area does this fall under?
- **Partner Team:** Who is this for? Use "Internal" for team-owned work.
- **Priority:** Critical/High/Medium/Low
- **Description:** Enough context that another team member could pick this up if you were unavailable.

**What NOT to do:**
- Don't create a single ticket and dump unrelated work into it
- Don't leave tickets in Backlog/To Do forever -- if it's not going to happen, close it
- Don't skip the ticket because "it was just a quick thing" -- quick things add up and become invisible work

### Weekly Lead Review

Use the "Lead View" (saved view filtered by team + status). Look for:
- Anything stuck in the same status for > 5 days
- Blocked items with no recent comments
- SLA due dates approaching on Findings and Incidents

---

## Automation & Integration

### GitHub PR Automation (Build Tickets)

A GitHub Actions workflow (`.github/workflows/build-pr-automation.yml`) automates Build ticket transitions:

| PR Event | Issue Status Change |
|----------|-------------------|
| PR opened (with `Closes #123`) | In Review |
| Review: changes requested | Changes Requested |
| PR merged | Merged |

### Security Scanner Integration (Finding Tickets)

Prisma Cloud and Earlybird can create Finding issues via GitHub API webhook:

```
POST /repos/{owner}/{repo}/issues
{
  "title": "[Prisma] Critical: S3 bucket public access",
  "labels": ["finding", "Critical"],
  "body": "..."
}
```

The webhook sets severity, SLA due date, and affected resources automatically.

### Standards Review Cadence Automation

A GitHub Actions workflow (`.github/workflows/standards-review-reminder.yml`) runs daily on weekdays and checks for Published standards with a review date approaching within 30 days. When found, it auto-creates a new Draft issue linked to the original standard, so reviews are never forgotten.

### Slack Integration

GitHub's native Slack integration supports:
- `/github subscribe owner/repo issues` -- get notified on new issues
- Quick issue creation from Slack messages via GitHub's Slack app

---

## Board Views & Dashboards

### View 1: Kanban Board (default, all engineers)

- **Layout:** Board
- **Group by:** Status
- **Swimlanes:** Label (issue type)
- **Filter:** `is:open`

Everyone's single pane of glass.

### View 2: My Work

- **Layout:** Board
- **Filter:** `assignee:@me is:open`
- **Sort by:** Priority

What am I working on right now?

### View 3: Incoming Requests

- **Layout:** Table
- **Filter:** `label:consultation,review,change is:open status:Open,"To Do",Draft`
- **Sort by:** Created date

New work that needs triage or assignment.

### View 4: Incidents & Findings (SLA Tracker)

- **Layout:** Table
- **Filter:** `label:incident,finding is:open`
- **Sort by:** SLA Due Date
- **Fields shown:** Priority, SLA Due Date, Assignee, Status

Are we meeting our SLAs?

### View 5: Leadership Rollup

- **Layout:** Table
- **Group by:** Engagement Type (Internal Project / External Support)
- **Filter:** `label:milestone OR field:project-status`
- **Fields shown:** Project Status, Target Date, Domain, Priority

High-level: what are we delivering, is it on track?

### View 6: Capacity by Domain

- **Layout:** Table
- **Group by:** Domain
- **Filter:** `is:open`
- **Fields shown:** Assignee, Priority, Status

How is work distributed across Palo Alto vs. Illumio vs. Cloud vs. IaC?

### View 7: Partner Team Support

- **Layout:** Table
- **Group by:** Partner Team
- **Filter:** `is:open -label:task`

How much are we supporting each partner team?

---

## Worked Examples

### Example 1: Firewall Rule Request (Standard Change)

1. Cloud Engineering team needs egress to Datadog from their VPC
2. They open an issue using the **Change (Standard)** template
3. Fields: Domain = Palo Alto, Partner Team = Cloud Engineering, Priority = Medium, Environment = Prod
4. Engineer picks it up, implements the rule, closes the ticket
5. Flow: `To Do` > `Closed`

### Example 2: New Terraform Module (Build)

1. Engineer identifies need for a reusable GWLB endpoint module
2. Opens a **Build** issue, assigns themselves
3. Creates a branch, opens PR referencing `Closes #45`
4. Automation moves issue to `In Review`
5. Reviewer requests changes > automation moves to `Changes Requested`
6. Engineer fixes, reviewer approves, PR merged > automation moves to `Merged`
7. Engineer closes issue > `Closed`

### Example 3: Prisma Cloud Finding (Finding)

1. Prisma webhook auto-creates a Finding issue: "Critical: VPC flow logs disabled"
2. Issue auto-labeled `finding`, `Critical`, SLA Due Date set to 48 hours
3. Lead triages > `Triaged`, assigns engineer > `Assigned`
4. Engineer remediates > `In Remediation`
5. Verified in scanner > `Verified` > `Closed`

### Example 4: Panorama Consolidation (Project)

1. Lead creates a **Build** issue as the parent: "Panorama Consolidation"
2. Sets Engagement Type = Internal Project, Target Date = Q3, Project Status = On Track
3. Creates GitHub Milestone: "Discovery"
4. Creates child issues: inventory (Build), TAC review (Consultation)
5. Creates Milestone issue: "Discovery Complete" linked to children
6. As children close, milestone is marked `Achieved`
7. Repeat for Build phase and Migration phase

### Example 5: Emergency Change

1. Active incident requires immediate firewall rule change
2. Engineer opens **Change (Emergency)** template
3. Auto-labeled Critical, starts in `In Progress`
4. Implements the change, documents in the ticket, closes
5. Flow: `In Progress` > `Closed`
6. Separately, an Incident ticket tracks the full incident lifecycle
