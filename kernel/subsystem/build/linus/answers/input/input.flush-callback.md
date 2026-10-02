- There is no evdev_flush() here and `evdev_fops` has no `.flush`;
  `input_flush_device()` is called from `evdev_release()`, `evdev_revoke()`
  and `evdev_cleanup()` in `drivers/input/evdev.c`.
- `evdev_release()`: the `.release` operation, so once per open file, not on
  every `close()` of a descriptor; it skips the flush when `evdev->exist` is
  clear or the client is revoked.
- `evdev_revoke()`: on the `EVIOCREVOKE` ioctl, with `evdev->mutex` held by
  `evdev_ioctl_handler()`.
- `evdev_cleanup()`: at handler disconnect when `evdev->open` is non-zero,
  with `file == NULL`, just before `input_close_device()`; on device
  unregistration `going_away` is already set.
- `file == NULL`: `input_ff_flush()` erases every effect whatever its owner;
  `uinput_dev_flush()` returns 0 without doing anything.
- `input_flush_device()` tests none of `users`, `inhibited`, `ready` or
  `going_away`; `flush()` can run on an inhibited device, after `close()`.
- `input_close_device()` does not call `flush()`.
- Return value: all three callers ignore it; on `-EINTR` `flush()` did not
  run.
