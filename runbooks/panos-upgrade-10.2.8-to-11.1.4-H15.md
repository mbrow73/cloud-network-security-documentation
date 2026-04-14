# PAN-OS Upgrade Runbook: 10.2.8 → 11.1.4-H15

## GCP Internal Load Balancer Sandwiched Palo Altos (Non-HA)

---

### Overview

| Item | Detail |
|---|---|
| **Current Version** | PAN-OS 10.2.8 |
| **Target Version** | PAN-OS 11.1.4-H15 |
| **Upgrade Path** | 10.2.8 → 11.0 (latest maint.) → 11.1.4-H15 |
| **Architecture** | LB-sandwiched PA-VM (frontend INLB + backend INLB) |
| **HA Mode** | None — LB health probes provide failover |
| **Estimated Downtime Per FW** | ~15-20 min per reboot (x2 reboots per FW) |
| **Total Impact** | Zero downtime — 2 firewalls behind each LB |

> **PAN-OS requires stepping through major versions.** You cannot jump from 10.2 → 11.1 directly. You **must** install 11.0.x first, reboot, then install 11.1.4-H15 and reboot again.

---

### Prerequisites

- [ ] **Panorama** (if managing these FWs) is already upgraded to >= 11.1.x
- [ ] Verify current version: `show system info | match sw-version`
- [ ] Confirm firewall model is supported on 11.1 — check [compatibility matrix](https://docs.paloaltonetworks.com/compatibility-matrix/pan-os)
- [ ] Verify active support/license: `request license info`
- [ ] Confirm **both firewalls** are healthy behind each LB (required for zero-downtime rolling upgrade)
- [ ] PAN-OS 11.0 latest maintenance release image downloaded
- [ ] PAN-OS 11.1.4-H15 image downloaded
- [ ] **Connection draining timeout** is configured on both frontend and backend backend services (see below)
- [ ] Change window approved and communicated

**Verify/set connection draining timeout (one-time setup):**

Manage this in Terraform, not with ad-hoc `gcloud`.

```hcl
resource "google_compute_region_backend_service" "frontend_inlb" {
  name                  = "<FRONTEND_BACKEND_SERVICE_NAME>"
  region                = var.region
  load_balancing_scheme = "INTERNAL"
  protocol              = "TCP"

  connection_draining_timeout_sec = 300

  backend {
    group = google_compute_instance_group.pa_01.self_link
  }

  backend {
    group = google_compute_instance_group.pa_02.self_link
  }

  health_checks = [google_compute_region_health_check.panorama_probe.id]
}

resource "google_compute_region_backend_service" "backend_inlb" {
  name                  = "<BACKEND_BACKEND_SERVICE_NAME>"
  region                = var.region
  load_balancing_scheme = "INTERNAL"
  protocol              = "TCP"

  connection_draining_timeout_sec = 300

  backend {
    group = google_compute_instance_group.pa_01.self_link
  }

  backend {
    group = google_compute_instance_group.pa_02.self_link
  }

  health_checks = [google_compute_region_health_check.workload_probe.id]
}
```

To verify the current value from Terraform state:

```bash
terraform state show google_compute_region_backend_service.frontend_inlb | grep connection_draining_timeout_sec
terraform state show google_compute_region_backend_service.backend_inlb  | grep connection_draining_timeout_sec
```

> This setting controls what happens when an instance is removed from the backend. Without it, removal is a hard cut — existing connections are dropped immediately. With it configured, GCP stops new connections but continues forwarding packets for existing connections until the timeout elapses.

---

### Pre-Stage Images (Do This Ahead of Time — No Impact)

Run on **both** firewalls before the maintenance window:

```
# Check available versions
request system software check

# Download the intermediate 11.0 release (use latest available, e.g., 11.0.6)
request system software download version 11.0.6
# Monitor: request system software download status

# Download the target release
request system software download version 11.1.4-h15
# Monitor: request system software download status
```

> Downloads happen in the background with zero traffic impact. Do this during business hours to save time in the window.

Verify both images show `Downloaded: yes`:
```
show system software status
```

---

### Architecture Context

```
                    +------------------+
    Traffic In ---> |  Frontend INLB   |
                    +--------+---------+
                             |
                    +--------+--------+
                    v                 v
              +---------+       +---------+
              |  PA-01  |       |  PA-02  |
              +---------+       +---------+
                    |                 |
                    v                 v
                    +--------+--------+
                             |
                    +------------------+
                    |  Backend INLB    |
                    +------------------+
                             |
                    v  Backend Servers  v
```

**How failover works:** GCP INLB health probes check each firewall. When a FW goes down for reboot, the LB stops sending traffic to it within ~10 seconds (default probe interval). Traffic shifts to the remaining healthy FW. When the rebooted FW comes back and passes probes, the LB re-adds it.

---

### Rolling Upgrade Procedure

> **CRITICAL:** Upgrade firewalls **one at a time.** Never upgrade both simultaneously. Wait for the first FW to fully recover and pass health probes before starting the second.

---

#### Repeat the following for EACH firewall (PA-01 first, then PA-02)

---

#### Phase 1: Pre-Upgrade Snapshot

**1.1 — Generate Tech Support File (State Backup)**

```
request tech-support dump
```

Save this. It's your rollback reference if things go sideways.

**1.2 — Export Running Configuration**

```
show running security-policy
save config to pre-upgrade-config-backup.xml
scp export configuration from pre-upgrade-config-backup.xml to <SCP_DESTINATION>
```

> Or use Panorama to push a config backup if centrally managed.

**1.3 — Capture Current State**

Document these outputs — you'll compare them post-upgrade:

```
show system info
show interface all
show routing protocol bgp summary       # if using BGP
show routing route                       # routing table
show session info                        # session counts
show running resource-monitor            # CPU/memory baseline
show high-availability all               # should show "not configured" for non-HA
show system state filter-pretty sys.s1.p*.stats.dp-monitor
```

**1.4 — Verify Images Are Downloaded**

```
show system software status
```

Confirm both `11.0.6` (or your chosen 11.0.x) and `11.1.4-h15` show `Downloaded: yes`.

---

#### Phase 2: Drain Firewall from Load Balancer

**2.1 — Remove the Target FW from the Instance Group**

This triggers connection draining — GCP stops sending new connections and allows existing ones to finish within the drain timeout window.

Do this by temporarily removing the target firewall from the Terraform-managed unmanaged instance group membership.

```hcl
resource "google_compute_instance_group" "pa_01" {
  name      = "<PA_01_INSTANCE_GROUP>"
  zone      = var.zone_1
  network   = google_compute_network.firewall_vpc.id
  instances = []
}

resource "google_compute_instance_group" "pa_02" {
  name      = "<PA_02_INSTANCE_GROUP>"
  zone      = var.zone_2
  network   = google_compute_network.firewall_vpc.id
  instances = [google_compute_instance.pa_02.self_link]
}
```

Then run:

```bash
terraform plan
terraform apply
```

> If your module builds `instances` from variables or locals, make the temporary change there instead of editing the resource block directly. The point is the same: remove the target PA from the IG in Terraform and apply it so GCP drains it cleanly.

**2.2 — Verify Drain via Firewall Session Logs**

Monitor active sessions on the firewall being drained:

```
# Check current session count
show session info

# Watch active sessions — run this a few times over 1-2 minutes
show session info | match "num-active"

# For more detail, check sessions by policy to see what's still flowing
show session all filter state active
```

Active session count should be declining and approaching zero. No new sessions should be establishing after the instance is removed from the IG. Wait until active sessions are at or near zero before proceeding.

> If sessions are NOT declining, verify the instance was actually removed from the IG. If new sessions are still being established, something went wrong with the drain.

**2.3 — Verify the Other FW Is Healthy**

On the other firewall (the one staying in production):

```
show session info | match "num-active"
show system state filter-pretty sys.s1.p*.stats.dp-monitor
show running resource-monitor
```

Confirm it is actively handling sessions and resource utilization is within acceptable range. It will be carrying 100% of traffic during the upgrade.

> **STOP if the other firewall is showing errors or high resource usage.** Fix it before proceeding.

---

#### Phase 3: Upgrade to PAN-OS 11.0.x (Intermediate Step)

**3.1 — Install 11.0.x**

```
request system software install version 11.0.6
```

Monitor installation:
```
show jobs all
```

Wait for the install job to complete (status: `FIN`).

**3.2 — Reboot into 11.0.x**

```
request restart system
```

> **Expected reboot time: ~10-15 minutes.** The firewall will be unreachable during this time.

**3.3 — Verify 11.0.x Boot**

Once the FW is back:
```
show system info | match sw-version
# Expected: 11.0.6 (or your chosen version)

show interface all
show routing route
show system state filter-pretty sys.s1.p*.stats.dp-monitor
```

Confirm:
- [ ] Correct version running
- [ ] All interfaces are up
- [ ] Routing table looks correct
- [ ] No critical system logs: `show log system severity critical`
- [ ] Dataplane is up: `show system state filter sys.s1.dp0.status`

> Do **NOT** re-add to the LB yet. Stay drained for the second upgrade.

---

#### Phase 4: Upgrade to PAN-OS 11.1.4-H15 (Target Version)

**4.1 — Install 11.1.4-H15**

```
request system software install version 11.1.4-h15
```

Monitor:
```
show jobs all
```

**4.2 — Reboot into 11.1.4-H15**

```
request restart system
```

> **Expected reboot time: ~10-15 minutes.**

**4.3 — Post-Upgrade Verification**

```
show system info | match sw-version
# Expected: 11.1.4-h15
```

Run the full validation suite:

```
# Interfaces
show interface all

# Routing
show routing route
show routing protocol bgp summary          # if applicable

# Policies loaded
show running security-policy | match rules
show running nat-policy | match rules

# Licenses
request license info

# Content versions
show system info | match -i "threat-version\|app-version\|antivirus-version"

# Dataplane health
show running resource-monitor
show system state filter-pretty sys.s1.p*.stats.dp-monitor

# System health
show log system severity critical direction backward last 50
show system disk-space
```

**Confirm ALL of the following before proceeding:**
- [ ] Version is 11.1.4-h15
- [ ] All interfaces are UP
- [ ] Routing table matches pre-upgrade snapshot
- [ ] Security policies are loaded and match expected count
- [ ] NAT policies are loaded and match expected count
- [ ] Licenses are valid
- [ ] Content/threat versions are loaded
- [ ] No critical errors in system log
- [ ] CPU/memory are within normal range
- [ ] Dataplane is processing traffic

---

#### Phase 5: Re-Add to Load Balancer

**5.1 — Add FW Back to Instance Group**

Revert the temporary Terraform change so the upgraded firewall is back in its unmanaged instance group:

```hcl
resource "google_compute_instance_group" "pa_01" {
  name      = "<PA_01_INSTANCE_GROUP>"
  zone      = var.zone_1
  network   = google_compute_network.firewall_vpc.id
  instances = [google_compute_instance.pa_01.self_link]
}
```

Then run:

```bash
terraform plan    # should show the instance being added back to the IG
terraform apply
```

**5.2 — Verify Health Probe Passes**

Verify from the Terraform-managed load balancer path using the GCP Console or your normal monitoring stack. At a minimum, confirm the firewall has been re-associated with the unmanaged IG in Terraform state and is passing traffic again.

```bash
terraform state show google_compute_instance_group.pa_01
terraform state show google_compute_region_backend_service.frontend_inlb
terraform state show google_compute_region_backend_service.backend_inlb
```

Wait for the upgraded FW to show healthy in your operational view. This typically takes 2-3 probe intervals (~20-30 seconds).

**5.3 — Verify Traffic Is Flowing**

On the firewall:
```
show session info
```

Active sessions should begin climbing. Monitor for 5-10 minutes to confirm stable traffic flow.

---

#### Phase 6: Bake Time

> **Wait a minimum of 15-30 minutes** with the upgraded FW handling production traffic before moving to the next firewall.

During bake time, monitor:
- Session counts (should be stable/growing)
- CPU/memory (should be within baseline)
- Health probe status (should stay HEALTHY)
- Application logs for errors from clients behind this FW

**Only proceed to PA-02 after bake time passes with no issues.**

---

#### NEXT FIREWALL

Go back to **Phase 1** and repeat for PA-02.

---

### Rollback Procedure

If anything goes wrong during or after upgrade:

**Option 1: Revert to Previous PAN-OS (Preferred)**

```
# PAN-OS keeps the previous version — revert to it
request system software revert
request restart system
```

This boots back to the last working version.

**Option 2: Restore Configuration**

If the version is fine but config is broken:

```
# Load the pre-upgrade backup
load config from pre-upgrade-config-backup.xml
commit
```

**Option 3: Nuclear — Keep FW Drained**

If the FW is completely broken:
1. Keep it removed from the LB
2. The other FW handles all traffic
3. Open a Palo Alto TAC case
4. Do **not** proceed with the other FW upgrade

---

### Upgrade Tracker

| Firewall | Pre-Stage | Drained | 11.0.x Installed | 11.1.4-H15 Installed | Verified | Re-Added | Bake OK | Operator |
|---|---|---|---|---|---|---|---|---|
| PA-01 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PA-02 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |

---

### Post-Upgrade Checklist (After Both Firewalls Done)

- [ ] Both firewalls running 11.1.4-H15: `show system info | match sw-version`
- [ ] Both firewalls HEALTHY in frontend and backend LBs
- [ ] Session distribution is balanced across both FWs
- [ ] Threat/content updates are current on both FWs
- [ ] Panorama shows both FWs connected and in-sync (if applicable)
- [ ] Monitoring/alerting thresholds reviewed for new version
- [ ] Update CMDB/asset inventory with new PAN-OS version
- [ ] Close change ticket with upgrade tracker + verification outputs
- [ ] Keep pre-upgrade config backups for 30 days minimum

---

### Estimated Timeline

| Activity | Duration |
|---|---|
| Pre-stage images (both FWs) | 15-30 min (do ahead of window) |
| Per-firewall upgrade cycle | ~45-60 min |
| Bake time per firewall | 15-30 min |
| **Total per firewall** | **~60-90 min** |
| **Total for both firewalls** | **~2-3 hours** |

---

### Important Notes

1. **Never upgrade both FWs at the same time.** The LB health probes are your only failover mechanism — respect it.
2. **The 11.0.x intermediate step requires a full reboot.** There's no way around this — PAN-OS enforces the major version stepping.
3. **Pre-staging images is free.** Download them days before the window to reduce change window duration.
4. **If you're Panorama-managed**, ensure Panorama is upgraded to 11.1.x FIRST. Managing a FW on a version higher than Panorama is unsupported and will cause issues.
5. **Content updates** may need to be refreshed after the major version jump. Run `request content upgrade check` and install the latest after reaching 11.1.4-H15.
6. **GCP health probes** — verify your Terraform-defined probe configuration (port, interval, threshold) before starting. If probes are slow (high interval + high threshold), your drain/re-add times will be longer.

---

### References

**PAN-OS Upgrade Path and Procedures:**
- [Determine the Upgrade Path to PAN-OS 11.1](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-upgrade/upgrade-pan-os/upgrade-the-firewall-pan-os/determine-the-upgrade-path) — Official version stepping requirements
- [Upgrade a Standalone Firewall](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-upgrade/upgrade-pan-os/upgrade-the-firewall-pan-os/upgrade-a-standalone-firewall) — Step-by-step standalone upgrade procedure
- [PAN-OS 11.1 Release Notes](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-release-notes) — Known issues, resolved issues, and upgrade considerations
- [PAN-OS Compatibility Matrix](https://docs.paloaltonetworks.com/compatibility-matrix/pan-os) — Supported models and versions

**PAN-OS CLI Reference:**
- [show session info](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-cli-quick-start/cli-cheat-sheets/cli-cheat-sheet-networking) — Active session counts and statistics
- [request system software](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-cli-quick-start/cli-cheat-sheets/cli-cheat-sheet-device-management) — Software download, install, and revert commands
- [show system info](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-cli-quick-start/cli-cheat-sheets/cli-cheat-sheet-device-management) — Version, content, and license info

**GCP Connection Draining and Load Balancing:**
- [Enabling Connection Draining on Backend Services](https://cloud.google.com/load-balancing/docs/enabling-connection-draining) — How connection draining works, timeout configuration
- [Internal Passthrough Network Load Balancer Overview](https://cloud.google.com/load-balancing/docs/internal) — L4 ILB architecture (Maglev/Andromeda), health probes, backend behavior
- [Unmanaged Instance Groups](https://cloud.google.com/compute/docs/instance-groups/creating-groups-of-unmanaged-instances) — Backend membership model used by this runbook
- [Terraform: google_compute_region_backend_service](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_region_backend_service) — Backend service resource, including connection draining
- [Terraform: google_compute_instance_group](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance_group) — Zonal unmanaged instance groups for 1:1 PA membership

**GCP L4 vs L7 Behavior (Important):**
- [Backend Service Settings](https://cloud.google.com/load-balancing/docs/backend-service) — Note: `max-rate` is an L7 HTTP(S) LB capacity scaler. L4 passthrough ILBs do not use it as a traffic routing signal. For L4, removing the instance from the backend is the correct way to stop new connections.

---

*Runbook Version: 1.6 | Created: 2026-03-26 | Updated: 2026-04-14*
