- `drm_connector_put()` dropping the last reference: calls `funcs->destroy`
  at once, in the caller's context.
- `connector_free_work`: used only when the list iterator drops the last
  reference, since it puts under `connector_list_lock`.
- Static connectors with `destroy`: `drm_mode_config_cleanup()` drops their
  initial reference with `drm_connector_put()`; an extra reference leaves
  them on the list and triggers the "leaked" error.
- `drmm_connector_init()` connectors: `drm_connector_cleanup_action()` cleans
  them up at device release whatever the count; a reference does not keep
  them alive.
- `drm_connector_dynamic_init()`: takes a fifth `ddc` argument and returns
  `-EINVAL` without `funcs->destroy`, so it cannot be combined with drmm.
- `drm_connector_register()`: returns 0 and does nothing before the device is
  registered; it acts only in `DRM_CONNECTOR_INITIALIZING`, so an
  unregistered connector cannot be registered again.
- `drm_connector_unregister()`: leaves the connector on
  `mode_config.connector_list`; only `drm_connector_cleanup()` removes it.
- List iterator: skips only connectors whose count is zero, so it returns
  unregistered ones; test with `drm_connector_is_unregistered()`.
- **Potentially unsafe usage**: walking `mode_config.connector_list` with
  `list_for_each_entry()`.
  - Unsafe: while another task can run `drm_connector_dynamic_register()` or
    `drm_connector_cleanup()`, which change the list under
    `connector_list_lock` only.
  - Safe: with `connector_list_lock` held, as
    `drm_helper_move_panel_connectors_to_head()` does around its
    `list_for_each_entry_safe()`.
  - Safe: with `drm_connector_list_iter_begin()`,
    `drm_for_each_connector_iter()` and `drm_connector_list_iter_end()`.
  - Safe: on the commit path of a driver that has no dynamic connectors, as
    `omap_encoder_mode_set()` does; the list then changes only when
    connectors are initialised or cleaned up.
