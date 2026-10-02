- Written style rules: none specific to input; the nearest thing is the
  example driver in `Documentation/input/input-programming.rst`, which uses
  `int error` with `goto err_free_dev` / `err_free_irq` labels and no cleanup
  helper.
- `Documentation/input/input-programming.rst`: has no text on `devm_`
  (managed) allocation.
- Guard conversion is per file, not core-wide:

| Files under `drivers/input/` | Locking style |
|---|---|
| `input.c`, `ff-core.c`, `ff-memless.c`, `input-mt.c`, `input-poller.c`, `serio/serio.c` | `guard()`, `scoped_guard()`, `scoped_cond_guard()` |
| `evdev.c`, `joydev.c`, `mousedev.c`, `misc/uinput.c` | open-coded lock/unlock pairs with `goto out`; no cleanup helper anywhere in the file |

- `drivers/input/input.c`, the open-coded exception:
  `input_devices_seq_start()` and `input_handlers_seq_start()` call
  `mutex_lock_interruptible(&input_mutex)` and `input_seq_stop()` unlocks,
  because the lock spans two seq_file callbacks; `mutex_acquired` in
  `struct input_seq_state` records whether to unlock.
- `input_register_device()`: combines
  `scoped_cond_guard(mutex_intr, goto err_device_del, &input_mutex)` with the
  `err_device_del` and `err_devres_free` labels; both labels sit after the
  guarded block and no `goto` jumps into it.
- `input_register_device()`: sets `error = -EINTR` on the line before the
  `scoped_cond_guard()`, since the fail statement is a `goto`, not a
  `return -EINTR`.
- `__free()` in the top-level files: ownership is handed over only with
  `no_free_ptr()`, as in `input_ff_create()` and `input_mt_init_slots()`;
  `retain_and_null_ptr()` and `return_ptr()` are not used there.
- `DEFINE_FREE()` / `DEFINE_GUARD()`: the only one in the input headers or
  under `drivers/input/` is the `serio_pause_rx` guard in
  `include/linux/serio.h`; there is no `__free()` class for
  `struct input_dev`.
- `error` is the dominant name but not the only one for a pure errno in the
  core:
  - `retval`: `evdev_open_device()`, `joydev_open_device()`,
    `mousedev_open_device()`, all holding only 0 or a negative errno.
  - `err`: `input_init()`, `input_dev_set_poll_interval()` in
    `drivers/input/input-poller.c`, and the `INPUT_ADD_HOTPLUG_VAR()` macro
    family in `drivers/input/input.c`.
- `retval` in `input_handler_for_each_handle()`: holds whatever the callback
  returned, not necessarily an errno.
