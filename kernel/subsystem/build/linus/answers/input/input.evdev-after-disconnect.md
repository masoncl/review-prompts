- `evdev->exist` is the only thing that stops writes and ioctls after
  disconnect; `input_inject_event()`, `input_ff_upload()` and
  `input_set_keycode()` use `handle->dev` and do not test whether the handle
  is still registered.
- `evdev_write()` and `evdev_ioctl_handler()` test `exist` under
  `evdev->mutex`, so `evdev_mark_dead()` waits for one already running.
- `evdev_read()` and `evdev_poll()` test `exist` without `evdev->mutex`;
  neither calls into the driver.
- `evdev_disconnect()` calls `cdev_device_del()` before `evdev_cleanup()`.
- `evdev_poll()` with events still buffered: returns `EPOLLIN |
  EPOLLRDNORM` as well as `EPOLLHUP | EPOLLERR`; `evdev_read()` still returns
  `-ENODEV`.
