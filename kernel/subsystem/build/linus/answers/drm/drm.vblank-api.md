- `enable_vblank` and `disable_vblank`: `drivers/gpu/drm/drm_vblank.c` calls
  only the `struct drm_crtc_funcs` hooks; `struct drm_driver` has none.
  Without `enable_vblank`, `__enable_vblank()` returns `-EINVAL`.
- `drm_crtc_vblank_get()` returns `-EINVAL` and takes no reference:
  - without `drm_vblank_init()`
  - after `drm_crtc_vblank_off()` or `drm_crtc_vblank_reset()`, until
    `drm_crtc_vblank_on()`
- CRTC that was never reset or turned off after `drm_vblank_init()`:
  `drm_crtc_vblank_get()` calls `enable_vblank` and can return 0 with the
  CRTC disabled.
- `drm_atomic_helper_commit_crtc_disable()`: after the CRTC disable hook it
  calls `drm_crtc_vblank_get()` and WARNs "driver forgot to call
  drm_crtc_vblank_off()" unless the result is `-EINVAL`.
- `new_crtc_state->self_refresh_active`: the same check WARNs if the get
  fails, so the disable hook must leave vblank on in that case.
- `drm_crtc_vblank_on()`: copies `drm_vblank_offdelay` and
  `dev->vblank_disable_immediate` into `vblank->config`. A later change of
  either takes effect at the next `drm_crtc_vblank_on()`.
- `drm_crtc_vblank_on_config()`: takes a `struct drm_vblank_crtc_config`
  with `offdelay_ms` and `disable_immediate` for one CRTC.
- When the interrupt is switched off after the last
  `drm_crtc_vblank_put()`:

| `offdelay_ms` | `disable_immediate` | What happens |
|---|---|---|
| 0 | either | never; `drm_crtc_vblank_on_config()` also enables it at once |
| < 0 | either | `drm_vblank_put()` calls `vblank_disable_fn()` synchronously |
| > 0 | false | `disable_timer` is armed for `offdelay_ms` |
| > 0 | true | nothing at put; the next `drm_handle_vblank()` that sees refcount 0 disables it after sending events |

- `disable_immediate`: `drivers/gpu/drm/drm_vblank.c` has no check that the
  counter or timestamp is accurate; that is left to the driver.
- `max_vblank_count`: `drm_max_vblank_count()` uses the per-CRTC value if
  non-zero, else `dev->max_vblank_count`.
- Non-zero `max_vblank_count` without `get_vblank_counter`:
  `drm_vblank_no_hw_counter()` WARNs.
- `max_vblank_count` 0 and no usable timestamp (`get_vblank_timestamp`
  fails or `framedur_ns` is 0): `drm_update_vblank_count()` adds 1 per
  interrupt and nothing for the time the interrupt was off.
- `drm_crtc_set_max_vblank_count()`: WARNs if `dev->max_vblank_count` is
  non-zero or if vblank is not off (`inmodeset` clear).
