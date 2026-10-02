- **Unsafe usage**: `input_unregister_device()` followed by
  `input_free_device()` on the same unmanaged device, or
  `input_free_device()` on a registered device.
  - Unsafe: unmanaged `input_unregister_device()` ends with
    `input_put_device()`, so the second call puts a reference that is gone.
  - Safe: `input_free_device()` only where registration never succeeded, as
    the `fail1` label of `atkbd_connect()` does.
  - Safe: a flag records success and selects one call, as
    `snd_jack_dev_disconnect()` in `sound/core/jack.c` does with
    `jack->registered`.
  - Safe: the pointer is set to NULL after `input_unregister_device()` and
    before the error path falls through to `input_free_device()`, as
    `sony_laptop_setup_input()` does with `key_dev`; `input_free_device()`
    does nothing for NULL.
- `input_free_device()` on a managed device: removes the allocation devres
  entry and puts; `WARN_ON()` fires only if the entry is not found.
- `input_unregister_device()` has no NULL check and dereferences `dev`;
  `psmouse_disconnect()` tests `psmouse->dev` first.
