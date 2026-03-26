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
- [ ] Change window approved and communicated

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

**2.1 — Ensure Connection Draining Is Configured**

> **Important:** GCP Internal Network Load Balancers (L4 passthrough) do NOT honor `max-rate` as a traffic routing signal. That is an L7 HTTP(S) LB feature. For L4 ILBs, you must **remove the instance from the backend** to trigger connection draining.

Verify connection draining timeout is set on the backend service (one-time setup):

```bash
# Check current setting
gcloud compute backend-services describe <BACKEND_SERVICE_NAME> \
  --region=<REGION> \
  --format="get(connectionDraining.drainingTimeoutSec)"

# If not set or too low, configure it (300s = 5 min is a good default)
gcloud compute backend-services update <BACKEND_SERVICE_NAME> \
  --region=<REGION> \
  --connection-draining-timeout=300
```

**2.2 — Remove the Target FW from the Instance Group**

This triggers connection draining — GCP stops sending new connections and allows existing ones to finish within the drain timeout window.

```bash
gcloud compute instance-groups unmanaged remove-instances <INSTANCE_GROUP> \
  --instances=<FW_INSTANCE_NAME> \
  --zone=<ZONE>
```

**2.3 — Wait for Connections to Drain**

On the firewall itself:
```
show session info
```

Active sessions should be declining. Wait for the connection draining timeout to elapse (or until sessions reach near zero). This ensures existing flows complete gracefully before reboot.

**2.4 — Verify the Other FW Is Handling All Traffic**

```bash
# Confirm the other backend is HEALTHY and is the only active backend
gcloud compute backend-services get-health <BACKEND_SERVICE_NAME> \
  --region=<REGION>
```

> **STOP if the other firewall is not healthy.** You will cause an outage.

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

```bash
gcloud compute instance-groups unmanaged add-instances <INSTANCE_GROUP> \
  --instances=<FW_INSTANCE_NAME> \
  --zone=<ZONE>
```

**5.2 — Verify Health Probe Passes**

```bash
gcloud compute backend-services get-health <BACKEND_SERVICE_NAME> \
  --region=<REGION>
```

Wait for the upgraded FW to show `HEALTHY`. This typically takes 2-3 probe intervals (~20-30 seconds).

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
6. **GCP health probes** — verify your probe configuration (port, interval, threshold) before starting. If probes are slow (high interval + high threshold), your drain/re-add times will be longer.

---

*Runbook Version: 1.1 | Created: 2026-03-26*
