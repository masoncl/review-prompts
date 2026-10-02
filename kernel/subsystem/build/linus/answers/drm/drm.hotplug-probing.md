- `drm_connector_helper_hpd_irq_event()`: one connector;
  `drm_helper_hpd_irq_event()`: all with `DRM_CONNECTOR_POLL_HPD`. Both run
  detect.
- `drm_kms_helper_connector_hotplug_event()` and
  `drm_kms_helper_hotplug_event()`: only send the event, no detect.
- `drm_helper_hpd_irq_event()`: returns false and does nothing unless
  `mode_config.poll_enabled`, which `drm_kms_helper_poll_init()` sets.
- `drm_connector_helper_hpd_irq_event()`: has no `poll_enabled` test.
- Locks: both hpd helpers and the poll worker hold `mode_config.mutex`, and
  `drm_helper_probe_detect()` takes `connection_mutex` on every path.
- A detect callback therefore must not take `mode_config.mutex` or call the
  hpd helpers.
- Both hpd helpers and the poll worker call detect with `force` false;
  `drm_helper_probe_single_connector_modes()` passes true.
- `drm_helper_probe_detect()` with a ctx: returns `-EDEADLK` to the caller
  without retrying and does not write `connector->status`.
- `drm_helper_probe_detect()` with NULL ctx: retries `-EDEADLK` itself.
- `drm_connector_set_link_status_property()`: takes `connection_mutex`
  itself and sends no event; the driver sends the hotplug event.
- Link status back to GOOD: the kernel resets it only in
  `update_output_state()` in `drivers/gpu/drm/drm_atomic.c`, which
  `__drm_atomic_helper_set_config()` calls for legacy SETCRTC and for
  in-kernel clients.
- Atomic user space must write the property; the kernel accepts only a change
  away from BAD, see `drivers/gpu/drm/drm_atomic_uapi.c`.
