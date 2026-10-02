- Undone by the core: `device_del()` on the `-EINTR` path only, and
  `devres_free()` of the unregister devres it allocated for a managed device.
- Not on any list: the device is added to `input_dev_list` only after the
  last failure point.
- `dev->vals` is not freed on failure; `input_dev_release()` frees it.
- The poller is not touched on failure; `input_dev_poller_finalize()` only
  fills in default intervals.
- Left changed when `device_add()` fails or on the `-EINTR` path: `EV_SYN`,
  `KEY_RESERVED`, the cleansed bitmaps, softrepeat settings, default keycode
  callbacks.
- Left changed when `input_device_tune_vals()` fails: `EV_SYN`,
  `KEY_RESERVED` and the cleansed bitmaps, but not softrepeat or the keycode
  defaults.
- No handler was attached on any failure path, so `open()` and `event()`
  have not been called.
