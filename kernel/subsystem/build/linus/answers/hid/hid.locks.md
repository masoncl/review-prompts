- Device-event programs: `dispatch_hid_bpf_device_event()` in
  `drivers/hid/bpf/hid_bpf_dispatch.c` walks `bpf.prog_list` under
  `rcu_read_lock()`, not SRCU.
- `bpf.srcu`: read side is taken only in `dispatch_hid_bpf_raw_requests()` and
  `dispatch_hid_bpf_output_report()`, both on paths that may sleep.
- HID-BPF attach and detach: the mutex is `prog_list_lock` in `struct hid_bpf`;
  `hid_bpf_reg()` and `hid_bpf_unreg()` call `synchronize_srcu()` under it.
- `hid_bpf_reconnect()`: runs after `prog_list_lock` is released, so
  `device_reprobe()` is not under that mutex.
- hidraw locks, all in `drivers/hid/hidraw.c` and `include/linux/hidraw.h`:

| Lock | Kind | Interrupt context |
|---|---|---|
| `minors_rwsem` | file-scope rwsem | no |
| `list_lock` in `struct hidraw` | spinlock, irqsave | yes, `hidraw_report_event()` |
| `read_mutex` in `struct hidraw_list` | mutex | no |

- `hidraw_read()`: takes `read_mutex`; it does not take `minors_rwsem`
  or `list_lock`.
- hid-input: `drivers/hid/hid-input.c` has no lock of its own.
- `hidinput_input_event()` for `EV_LED`: does no I/O; it schedules `led_work`,
  and `hidinput_led_worker()` does the transfer.
- Paths that sleep on `driver_input_lock`:

| Path | Call |
|---|---|
| `hid_device_probe()` | `down_interruptible()`, returns `-EINTR` |
| `hid_device_remove()` | `down()` |
| `hid_device_io_stop()` | `down()` |
| `hid_hw_stop()` | through `hid_device_io_stop()`, only when `io_started` |
| `__hid_device_probe()` failure path | same, only when `io_started` |
| `hid_debug_rdesc_show()` in `drivers/hid/hid-debug.c` | `down_interruptible()` |
| kfunc `hid_bpf_input_report()` | `down_interruptible()` |

- Drivers also take `driver_input_lock` directly; search for the field name.
  For example a work item in `drivers/hid/hid-asus.c` holds it with `down()`
  around `hid_report_raw_event()`.
- `hid_bpf_try_input_report()`: passes `lock_already_taken` only when the
  context data is the device's `bpf.device_data`, that is, inside a
  `hid_device_event` program.
- `hid_bpf_try_input_report()` from any other hook: `__hid_input_report()`
  takes the semaphore with `down_trylock()` and returns `-EBUSY` on failure.
- Nesting, outer first:
  - `driver_input_lock` → `minors_rwsem` (write) → `ll_open_lock`: probe and
    remove reach `hidraw_connect()` and `hidraw_disconnect()`; `drop_ref()`
    calls `hid_hw_close()`.
  - `driver_input_lock` → `rcu_read_lock()` for device-event programs.
  - `driver_input_lock` → `list_lock`, and separately `driver_input_lock` →
    `debug_list_lock`.
  - `minors_rwsem` (read) → `bpf.srcu` read side: `hidraw_write()` and
    `hidraw_ioctl()` reach `__hid_hw_raw_request()`.
- `list_lock` is not held across hid-input: `hid_report_raw_event()` calls
  `hidraw_report_event()` before `hid_process_report()`, and it drops
  `list_lock` before returning.
