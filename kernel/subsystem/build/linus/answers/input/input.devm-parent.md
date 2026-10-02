- `input_register_device()`, `input_unregister_device()` and
  `input_free_device()` read `dev->dev.parent` at call time to find the devres
  list; nothing else records the device given to
  `devm_input_allocate_device()`.
- Parent changed before registration: the unregister entry goes on the new
  parent, the release entry stays on the owner.
- Owner unbind with a changed parent: the reference is dropped while the
  device is still registered.
- `input_unregister_device()` with a parent changed before registration: finds
  its entry on the new parent, no warning.
- `input_free_device()` with a changed parent: misses the release entry, warns,
  puts; the entry left on the owner puts again at unbind.
- **Unsafe usage**: assigning a different device to `dev.parent` of a managed
  input device.
  - Safe: assigning the same device that was passed to
    `devm_input_allocate_device()`, as `gpio_keys_probe()` does; the devres
    calls in `drivers/input/input.c` then use the owner.
- Helpers with `dev.parent` NULL:

| Helper | Behaviour |
|---|---|
| `matrix_keypad_build_keymap()` | `WARN_ON()`, returns `-EINVAL` |
| `touchscreen_parse_properties()` | no check; `dev_fwnode()` dereferences NULL |
| `touch_overlay_map()` | no check; `dev_fwnode()` dereferences NULL |
| `input_setup_polling()` | works; parent only used for `dev_err()`, falls back to `&dev->dev` |
| `sparse_keymap_setup()` | works; managed keymap copy is attached to `&dev->dev` |

- `drivers/input/ff-memless.c`: does not use the parent or devres.
