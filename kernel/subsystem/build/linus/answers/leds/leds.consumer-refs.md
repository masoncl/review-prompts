- There is no __led_get() here; `led_module_get()` in
  `drivers/leds/led-class.c` takes the module reference.
- Module reference: blocks only unloading of the provider module; unbinding
  the provider device, for example through `unbind_store()`, is not blocked.
- Getters: create no device link between consumer and provider; for an OF
  `leds` property fw_devlink may create one (`parse_leds()` in
  `drivers/of/property.c`).
- After a provider unbind: `led_classdev_unregister()` has run, and the
  consumer's device reference keeps only `led_cdev->dev` allocated, not the
  provider-owned `struct led_classdev`.
- `led_put()` after a provider unbind: reads
  `led_cdev->dev->parent->driver`, which `device_unbind_cleanup()` has set to
  NULL.
- `led_module_get()` and `led_put()`: read
  `led_cdev->dev->parent->driver->owner` with no NULL test.
- **Unsafe usage**: a lookup entry or `leds` reference that resolves to an LED
  whose parent is NULL or has no bound driver, such as the LEDs of
  `drivers/input/input-leds.c`, whose parent is a `struct input_dev`.
  - Safe: an LED whose parent is the device its driver is bound to, as
    `skl_int3472_register_led()` registers with `int3472->dev` when
    `skl_int3472_discrete_probe()` has set that to its own platform device.
- **Unsafe usage**: `led_put()` on NULL or on an `ERR_PTR()`; `led_put()`
  dereferences its argument with no test.
  - Safe: test first, as `v4l2_subdev_put_privacy_led()` does with
    `IS_ERR_OR_NULL()`.
- **Unsafe usage**: `led_put()` on an LED from `devm_led_get()`,
  `devm_of_led_get()` or `devm_of_led_get_optional()`; `devm_led_release()`
  puts it a second time.
  - Safe: `led_put()` paired with `led_get()`, as in
    `v4l2_subdev_put_privacy_led()`.
