- `drivers/input/misc/uinput.c`: an event source, not a consumer; it registers
  a `struct input_dev` and has no `struct input_handler`.
- `dev->grab`: written under `dev->mutex`, read under RCU; `event_lock` does
  not protect it.
- With `dev->grab` set: `input_pass_values()` calls the grabbing handle only;
  filter handles, for example sysrq, are skipped as well.
- `struct evdev` has its own `grab` and `open`: `dev->grab` picks the handle,
  `evdev->grab` picks one `struct evdev_client` of that handle;
  `evdev_open_device()` calls `input_open_device()` for the first file only.
- `dev->open()` and `dev->close()`: not tied to first and last handle open
  alone. The first open of an inhibited device does not call `dev->open()`;
  `input_inhibit_device()` calls `dev->close()` and `input_uninhibit_device()`
  calls `dev->open()` while handles stay open.
- Handler-to-device direction: `input_inject_event()` goes through the same
  `input_handle_event()`, so an injected `EV_LED` reaches `dev->event()` while
  `dev->ready` is set and is passed to handles like a driver event, back to
  the injecting handle too; it is dropped when another handle holds the grab.
- `struct input_handle` memory: owned by the handler. The core does not
  allocate or free it, and `input_register_handle()` takes no reference on the
  device.
- Handle that outlives `disconnect()`: `evdev_disconnect()` does not free the
  `struct evdev`, it drops a reference with `put_device()`; `evdev_free()`
  frees the `struct evdev` after the last file closes, so `evdev_connect()`
  holds the device with `input_get_device()`.
- `connect()` need not create a handle: `kgdboc_reset_connect()` in
  `drivers/tty/serial/kgdboc.c` resets the device and returns `-ENODEV`.
- `struct ff_device`: the `event` and `flush` callbacks that
  `input_ff_create()` installs on the device are `input_ff_event()` and
  `input_ff_flush()` in `drivers/input/ff-core.c`.
