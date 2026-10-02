- `drm_panel_prepare()`, `drm_panel_enable()`, `drm_panel_disable()`,
  `drm_panel_unprepare()`: return `void`; a callback failure is not reported
  to the caller.
- NULL panel: the four calls return silently.
- `drm_panel_init()`: `static` in `drivers/gpu/drm/drm_panel.c`; drivers
  cannot call it, `devm_drm_panel_alloc()` is the only way to initialise.
- Double call: skipped with `dev_warn()` in all four; the test of
  `prepared`/`enabled` runs before `follower_lock` is taken.
- `unprepare` or `disable` callback fails: the flag stays true, so the next
  prepare or enable is skipped; the followers were already called, and in
  `drm_panel_disable()` the backlight was already turned off.
- `enable` callback fails: backlight is not enabled.
