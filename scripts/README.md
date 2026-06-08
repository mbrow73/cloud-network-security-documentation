# Scripts

Operational helper scripts for cloud/network security analysis and documentation workflows.

## `panorama_object_cleanup_candidates.py`

Offline, read-only analyzer for exported Palo Alto Panorama/PAN-OS XML configs. It reports likely unused address/service objects, recursively accounts for static object groups, emits duplicate address/service value reports, and performs a conservative whole-config exact-name reference scan.

Example:

```bash
python3 scripts/panorama_object_cleanup_candidates.py panorama.xml \
  --csv cleanup_candidates.csv \
  --refs object_refs.csv \
  --duplicates duplicate_values.csv \
  --global-refs global_refs.csv
```

The cleanup candidate CSV includes `policy_reference_count`, `global_reference_count`, `group_membership_count`, and `delete_eligible`. Treat rows with `delete_eligible=no`, `global_reference_count > 0`, or `group_membership_count > 0` as not ready for delete until reviewed.

Treat the output as review candidates, not automatic delete instructions. Validate against Panorama before removing objects.


## `panorama_candidates_to_delete_commands.py`

Converts reviewed rows from `panorama_cleanup_candidates.csv` into Panorama CLI `delete` commands. The generator fails closed unless the CSV includes the current safety columns: `global_reference_count`, `group_membership_count`, and `delete_eligible`. Unsafe rows are skipped by default.

Example:

```bash
python3 scripts/panorama_candidates_to_delete_commands.py panorama_cleanup_candidates.csv \
  --out delete-unused-objects.txt \
  --limit 500
```

Run generated commands from Panorama CLI configure mode only after review and a config snapshot. Prefer small batches with validate/commit between waves.

## `generate_url_filtering_profile_commands.py`

Generates exhaustive Panorama `set` commands for a URL Filtering profile from the live predefined URL category list on the target Panorama/PAN-OS content version.

Use this for egress profiles where every predefined category must be explicitly set to either `block` or `alert` so URL Filtering logs are generated consistently.

Example:

```bash
python3 scripts/generate_url_filtering_profile_commands.py \
  --categories-file live-url-categories.txt \
  --device-group AWS_GWLB_EGRESSCORE_NP \
  --profile URLF-EGRESS-PROXY-GUARDRAILS \
  --include-base \
  > generated-url-filtering-profile-commands.txt
```

Review the generated commands before applying them. The script blocks the default high-risk guardrail categories and alerts every other discovered predefined category.
