- `struct drm_panel_follower_funcs`: has `panel_prepared`,
  `panel_unpreparing`, `panel_enabled` and `panel_disabling`; each is
  optional.
- `panel_enabled`: runs in `drm_panel_enable()` after the `enable` callback
  and after `backlight_enable()`.
- `panel_disabling`: runs in `drm_panel_disable()` before
  `backlight_disable()` and before the `disable` callback.
- `drm_panel_add_follower()` on a prepared or enabled panel: calls
  `panel_prepared` if the panel is prepared, then `panel_enabled` if it is
  enabled, and returns 0 even if they fail.
- `drm_panel_add_follower()`: keeps a panel reference and a device reference
  until `drm_panel_remove_follower()`.
