- **Potentially unsafe usage**: an IRQ handler, timer or work item that calls
  `input_event()` can still run when `input_unregister_device()` is called.
  - Unsafe: unmanaged device; `input_unregister_device()` ends with
    `input_put_device()`, which frees the device unless another reference is
    held.
  - Safe: unmanaged device with the source stopped first, as
    `palmas_pwron_remove()` in `drivers/input/misc/palmas-pwrbutton.c` does
    with `free_irq()` and `cancel_delayed_work_sync()`.
  - Safe: managed device with the source registered with devres after
    `devm_input_allocate_device()`; the struct stays allocated until
    `devm_input_device_release()` runs, as in `gpio_keys_probe()`. For the
    autorepeat timer see "Callbacks after unregistration".
- **Potentially unsafe usage**: a devres-managed source that uses the input
  device, registered before `devm_input_allocate_device()`.
  - Unsafe: when the source is live outside `open()` and `close()`;
    `release_nodes()` in `drivers/base/devres.c` runs entries in reverse, so
    `devm_input_device_release()` puts the device while the source is still
    live.
  - Safe: allocate first, then `devm_add_action()` and the IRQ request, as
    `gpio_keys_setup_key()` does.
  - Safe: an IRQ requested with `IRQF_NO_AUTOEN` that only `open()` enables
    and `close()` disables with `disable_irq()`, as in
    `wacom_w9000_probe()`; `input_close_device()` calls `close()` from the
    unregister entry, which runs before the release entry.
- **Potentially unsafe usage**: cancelling work or URBs that `event()` starts
  before `input_unregister_device()`.
  - Unsafe: when an LED or sound is on; `input_dev_toggle(dev, false)` calls
    `event()` during unregistration and queues the work again before private
    data is freed.
  - Safe: cancel after unregistering, as `usb_kbd_disconnect()` in
    `drivers/hid/usbhid/usbkbd.c` kills `kbd->led` after the call.
- A source started in `open()` and stopped synchronously in `close()` is
  stopped when unregistration returns; `close()` is skipped only when no
  `open()` is outstanding.
- A source started in probe is not stopped by `close()` when the device was
  never opened.
