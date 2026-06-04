# Scripts

Operational helper scripts for cloud/network security analysis and documentation workflows.

## `panorama_object_cleanup_candidates.py`

Offline, read-only analyzer for exported Palo Alto Panorama/PAN-OS XML configs. It reports likely unused address/service objects, recursively accounts for static object groups, and emits duplicate address/service value reports.

Example:

```bash
python3 scripts/panorama_object_cleanup_candidates.py panorama.xml \
  --csv cleanup_candidates.csv \
  --refs object_refs.csv \
  --duplicates duplicate_values.csv
```

Treat the output as review candidates, not automatic delete instructions. Validate against Panorama before removing objects.


## `panorama_candidates_to_delete_commands.py`

Converts reviewed rows from `panorama_cleanup_candidates.csv` into Panorama CLI `delete` commands.

Example:

```bash
python3 scripts/panorama_candidates_to_delete_commands.py panorama_cleanup_candidates.csv   --out delete-unused-objects.txt   --limit 500
```

Run generated commands from Panorama CLI configure mode only after review and a config snapshot. Prefer small batches with validate/commit between waves.
