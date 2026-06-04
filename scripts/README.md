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
