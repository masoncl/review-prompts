- `data` after success: owned by the helper; `ml_ff_destroy()` runs
  `kfree(ml->private)` at release of the input device, which can be later
  than unbind.
- Probe failure after a successful call: `data` is freed with the input
  device, through `input_free_device()` or `input_ff_destroy()`.
- Callers that free `data` on failure: for example `pl_input_configured()`
  in `drivers/hid/hid-pl.c`, `lg2ff_init()` in `drivers/hid/hid-lg2ff.c` and
  `gc_n64_init_ff()` in `drivers/input/joystick/gamecon.c`; there is no
  plff_init() here.
- `xpad_init_ff()`, `gpio_vibrator_probe()` and `drivers/hid/hid-lg4ff.c`:
  pass NULL, so they have nothing to free.
- **Unsafe usage**: passing `data` that `kfree()` must not free, or that
  something else also frees (devm memory, the driver's main state, a static).
  - Unsafe: `ml_ff_destroy()` runs `kfree()` on `data` at release.
  - Safe: pass NULL and fetch state with `input_get_drvdata()` in
    `play_effect`, as `winwing_init_ff()` and `winwing_play_effect()` do;
    `ml_ff_destroy()` then frees nothing.
  - Safe: pass a dedicated `kzalloc_obj()` block and free it only when
    `input_ff_create_memless()` fails, as `zp_input_configured()` in
    `drivers/hid/hid-zpff.c` does; on failure the helper has not taken
    `data`.
- **Unsafe usage**: using a saved copy of `data` after the driver has dropped
  its reference to the input device.
  - Unsafe: `ml_ff_destroy()` frees `data` at release of the input device.
  - Safe: use `data` only through the `play_effect` argument, as
    `hid_plff_play()` does; `ml_play_effects()` passes `ml->private`, which
    lives as long as the `struct ff_device`.
