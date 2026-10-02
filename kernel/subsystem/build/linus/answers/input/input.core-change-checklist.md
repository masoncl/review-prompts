- There is no input_to_handler() here; `input_pass_values()` in
  `drivers/input/input.c` calls `handle->handle_events()` with no NULL test.
- `handle->handle_events`: set by `input_handle_setup_event_handler()` at the
  top of `input_register_handle()`, before the handle goes on `dev->h_list`.
- `handle_events()` return value: the number of values left; the walk stops
  when it is 0, and the autorepeat loop after the walk uses the same count.
- `handler->events()`: returns `unsigned int` and must return the count it
  was given unless it drops values; `evdev_events()` is the only in-tree one.
- `input_handle_events_filter()`: compacts `vals` in place, so later handles
  see the filtered array.
- `handle->open`: `input_disconnect_device()` zeroes it for every handle under
  `dev->event_lock` alone, with no `dev->mutex` and no grace period; the walk
  relies on `dev->event_lock` for this, which `input_pass_values()` asserts.
- RCU read section in the event path of `drivers/input/input.c`: opened in
  `input_pass_values()` and `input_inject_event()`, not in `input_event()`.
- `dev->event()` called from `input_event()`: runs under `dev->event_lock`
  outside the RCU read section; called from `input_inject_event()` it runs
  inside it.
- `synchronize_rcu()` in `drivers/input/input.c`: four calls, in
  `__input_release_device()`, the error path of `input_open_device()`,
  `input_close_device()` and `input_unregister_handle()`; the first three run
  under `dev->mutex`.
- There is no INPUT_COMPAT_TEST in this tree.
- Compat test for events (`input_event_size()`, `input_event_from_user()`,
  `input_event_to_user()`), under `CONFIG_COMPAT`:
  `in_compat_syscall() && !COMPAT_USE_64BIT_TIME`.
- Compat test for effects (`input_ff_effect_from_user()`,
  `uinput_ff_upload_to_user()`, `uinput_ff_upload_from_user()`), under
  `CONFIG_COMPAT`: `in_compat_syscall()` alone.
- `input_ff_effect_from_user()`, compat branch: copies
  `sizeof(struct ff_effect_compat)` bytes into the native `struct ff_effect`
  through a cast, then rewrites only `u.periodic.custom_data`, and only for
  `FF_PERIODIC` with `FF_CUSTOM`.
- uinput upload helpers: `memcpy()` of `sizeof(struct ff_effect_compat)`
  between the native and compat structs, with no pointer fix-up.
- Both copies rely on every field before `custom_data` having the same offset
  in `struct ff_effect` and `struct ff_effect_compat`, and on `custom_data`
  being last.
- `haptic` (`struct ff_haptic_effect`): in the union of `struct ff_effect`,
  absent from `struct ff_effect_compat`; the bulk copy carries it because it
  holds no pointer or `long` and is smaller than
  `struct ff_periodic_effect_compat`.
- `EVIOCSFF`: matched with `EVIOC_MASK_SIZE()`, which ignores the size bits;
  `input_ff_effect_from_user()` then requires `size` to equal the struct size
  exactly and returns `-EINVAL` otherwise, which `evdev_do_ioctl()` reports
  as `-EFAULT`.
- Changing `sizeof(struct ff_effect)`: makes `EVIOCSFF` from existing native
  binaries fail that equality test; compat callers are compared against
  `sizeof(struct ff_effect_compat)`.
- `EVIOCSFF` write-back: `evdev_do_ioctl()` stores `effect.id` through
  `&((struct ff_effect __user *)p)->id` for compat callers too, so `id` must
  keep the same offset in both structs.
- There is no tools/testing/selftests/input/ directory in this tree.
- `tools/testing/selftests/bpf/test_lirc_mode2_user.c`: the only file under
  `tools/` that names `struct input_event`; it reads
  `sizeof(struct input_event)` bytes from an evdev node.
- `struct ff_effect` and `EVIOCSFF`: named by no file under `tools/`.
- `tools/testing/selftests/hid/`: creates devices through uhid and reads
  them with the Python libevdev module; it does not use uinput.
- `drivers/input/tests/input_test.c`: sends no event and touches neither
  struct.
- Size assertions: `drivers/input/evdev.c`, `drivers/input/input-compat.c`,
  `drivers/input/input-compat.h` and `drivers/input/misc/uinput.c` contain no
  `BUILD_BUG_ON()` or `static_assert()`, so a layout change builds cleanly.
