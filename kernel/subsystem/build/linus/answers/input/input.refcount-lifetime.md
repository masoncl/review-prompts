- `input_register_handle()` takes no reference; a handler that needs the
  device after disconnect calls `input_get_device()` in its connect, as
  `evdev_connect()` does, and puts it in its release (`evdev_free()`).
- `kbd_connect()` takes no reference; its handle is freed in
  `kbd_disconnect()`.
- Initial reference: from `device_initialize()` in
  `input_allocate_device()`; dropped by `input_unregister_device()` for an
  unmanaged device, by `devm_input_device_release()` for a managed one.
- Unregistration uses `device_del()`, not `device_unregister()`.
- `input_dev_release()` also frees `dev->poller` and calls
  `module_put(THIS_MODULE)`.
- `ff->destroy()` and the `kfree()` of `ff->private` run at the last put,
  which can be after the driver's remove has returned, for example when an
  evdev file is still open.
