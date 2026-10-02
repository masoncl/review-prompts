- There is no drm_do_get_edid() here; `_drm_do_get_edid()` is static and
  `drm_edid_read_custom()` is the exported form.
- Still defined and usable on raw `struct edid`: `drm_get_edid()`,
  `drm_get_edid_switcheroo()`, `drm_edid_duplicate()`,
  `drm_add_edid_modes()`, `drm_connector_update_edid_property()`,
  `drm_edid_is_valid()`, `drm_detect_hdmi_monitor()`,
  `drm_detect_monitor_audio()`.
- Kerneldoc marks only `drm_add_edid_modes()` and
  `drm_connector_update_edid_property()` as deprecated.
- `drm_edid_read()`: warns and returns NULL when `connector->ddc` is NULL.
- `drm_edid_read_ddc()`: returns NULL before looking at override or firmware
  EDID when the connector is not forced and `drm_probe_ddc()` fails.
- That case is covered by `drm_edid_override_connector_update()`, called from
  `drm_helper_probe_get_modes()` when `get_modes` returned 0 and the
  connector status is connected.
- `drm_edid_read_custom()`: does not test `connector->force` and does not
  probe.
- `drm_edid_connector_update()`: copies the bytes into
  `connector->edid_blob_ptr`; the connector keeps no pointer to the
  `struct drm_edid` passed in.
- `drm_edid_connector_add_modes()`: parses that blob again.
