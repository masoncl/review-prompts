- `struct hidraw` in `include/linux/hidraw.h`: has no `refcount` field and no
  `struct kref`; `open` and `exist` are plain `int`, written only with
  `minors_rwsem` held for write.
- `hidraw_open()`: takes `minors_rwsem` for write, not read, because it
  changes `open`.
- `hidraw->hid`: never set to NULL; after disconnect it is a stale pointer and
  `exist == 0` is the only marker.
- `struct hidraw` has no mutex; `hidraw->list` is under the `list_lock`
  spinlock, and each `struct hidraw_list` has its own `read_mutex`.
- `hidraw_write()` and `hidraw_ioctl()`: hold `minors_rwsem` for read across
  the whole transport call, so `hidraw_disconnect()`, which takes it for
  write, waits for them to finish.
- `hidraw_read()` and `hidraw_poll()`: do not look at `hidraw_table[]` and do
  not take `minors_rwsem`; they reach `exist` through `list->hidraw`.
- `hidraw_read()` after disconnect: tests `exist` only when its queue is
  empty, so reports already queued are still returned before `-EIO`.
- `revoked` in `struct hidraw_list`: set by `HIDIOCREVOKE`; read, write,
  ioctl and fasync then return `-ENODEV`, and `hidraw_report_event()` skips
  that file.
- **Potentially unsafe usage**: testing `exist` without `minors_rwsem` held.
  - Unsafe: when the code then dereferences `hidraw->hid`; disconnect can
    complete in between and the `struct hid_device` can be gone.
  - Safe: when only the `struct hidraw` and the `struct hidraw_list` are
    touched, which the open count keeps alive, as `hidraw_read()` and
    `hidraw_poll()` do.
  - Safe: holding `minors_rwsem` from the `exist` test to the last use of
    `->hid`, as `hidraw_ioctl()` does; `hidraw_send_report()` and
    `hidraw_get_report()` assert it with `lockdep_assert_held()`.
