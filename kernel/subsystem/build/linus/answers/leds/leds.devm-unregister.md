- `drivers/leds/uleds.c`: `uleds_open()` allocates `struct uleds_device` and
  registers nothing; `uleds_write()` registers against
  `uleds_misc.this_device`; `uleds_release()` calls
  `devm_led_classdev_unregister()` only in `ULEDS_STATE_REGISTERED`, then
  `kfree()`. There is no uleds_device_release and no `dev` field in
  `struct uleds_device`.
- `devm_led_classdev_unregister()` is also needed when a callback uses a
  resource that is not released by devres: `asus_wireless_remove()` and the
  error path of `asus_wireless_probe()` in
  `drivers/platform/x86/asus-wireless.c` call it before
  `destroy_workqueue()`.
- No matching entry: `devres_release()` returns `-ENOENT` without a message;
  the `WARN_ON()` is in `devm_led_classdev_unregister()`, which returns void
  and leaves the LED registered.
- Match: `find_dr()` in `drivers/base/devres.c` needs the same release
  function and the same pointer. An LED registered with
  `devm_led_classdev_flash_register_ext()` or
  `devm_led_classdev_multicolor_register_ext()` is not matched; use
  `devm_led_classdev_flash_unregister()` or
  `devm_led_classdev_multicolor_unregister()` with the container pointer.
- **Unsafe usage**: `led_classdev_unregister()` on an LED registered with
  `devm_led_classdev_register_ext()`.
  - Unsafe: the devres entry stays, `devm_led_classdev_release()` unregisters
    again at release, and the guard does not stop it because `led_cdev->dev`
    is still set.
  - Safe: `devm_led_classdev_unregister()` with the device given at
    registration, as `uleds_release()` does.
