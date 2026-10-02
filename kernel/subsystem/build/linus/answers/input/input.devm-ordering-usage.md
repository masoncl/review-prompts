- `probe()` error path after a successful `input_register_device()`: same
  rules as `remove()`; the device stays registered until devres is released
  after `probe()` returns, in `device_unbind_cleanup()` or, for an I2C or HID
  driver, in the `devres_release_group()` of `i2c_device_probe()` or
  `__hid_device_probe()`.
- **Potentially unsafe usage**: releasing a resource by hand in `remove()` of
  a driver whose input device is from `devm_input_allocate_device()`.
  - Unsafe: when the device is left to devres and `open()`, `close()`,
    `flush()`, `event()` or the poll function uses that resource; the device
    is still registered and `close()` runs later, from
    `devm_input_device_unregister()`.
  - Safe: `input_unregister_device()` first, then the teardown, as
    `sun4i_ts_remove()` does; `release_nodes()` in `drivers/base/devres.c`
    runs only after `remove()`.
  - Safe: teardown added as a devres action before `input_register_device()`,
    as `gpio_keys_setup_key()` does with `gpio_keys_quiesce_key()`;
    `release_nodes()` runs it after the unregister entry.
- **Potentially unsafe usage**: acquiring a managed resource after
  `input_register_device()`.
  - Unsafe: when `open()`, `close()`, `flush()`, `event()` or the poll
    function uses it; `release_nodes()` releases it before the unregister
    entry runs.
  - Safe: when it only feeds events and the device has no callback that uses
    it, as the IRQs in `rt5120_pwrkey_probe()`; the release entry keeps the
    device allocated until after the IRQ is freed.
- Explicit `input_unregister_device()` is required when:
  - `remove()` goes on to change state that the callbacks use.
  - The device has to go away while the driver stays bound, as in
    `cyapa_update_fw_store()`.
- Explicit `input_unregister_device()` is redundant when everything the
  callbacks use is managed and acquired before `input_register_device()`;
  `drivers/input/keyboard/gpio_keys.c` has no `remove()`.
- After an explicit `input_unregister_device()` in `remove()`: the driver's
  pointer stays valid until the release entry runs, so a managed IRQ requested
  after `devm_input_allocate_device()` that is still live does not see a freed
  device.
