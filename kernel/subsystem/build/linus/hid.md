# HID Subsystem

## Main structures

### Objects and how they relate

- `hid_add_device()`: builds no reports itself; it calls `ll_driver->parse()`,
  which stores the device bytes in `dev_rdesc`, then `hid_set_group()`, then
  `device_add()`.
- Report/field/usage tree: built by `hid_open_report()` (`hid_parse()` is the
  same call), from the driver's `probe`; `__hid_device_probe()` calls it
  itself, then `hid_hw_start()` with `HID_CONNECT_DEFAULT`, when the driver
  has no `probe`.
- `hdev->rdesc`: the descriptor that `hid_parse_collections()` parses; for the
  three descriptor pointers see "Report descriptor copies".
- Descriptor is walked twice: `hid_scan_report()` runs before binding and only
  sets `hdev->group`, which is part of the match key; it is skipped when the
  transport already set `group`, `HID_QUIRK_HAVE_SPECIAL_DRIVER` is set, or
  `hid_ignore_special_drivers` is set.
- `struct hid_parser`: used by both passes, `hid_scan_report()` and
  `hid_parse_collections()`.
- Attaching or detaching a HID-BPF `hid_rdesc_fixup` program: reprobes the
  device, see `hid_bpf_reconnect()` in `drivers/hid/bpf/hid_bpf_dispatch.c`;
  the whole parsed tree is rebuilt.
- HID-BPF lives in `drivers/hid/bpf/`. `struct hid_bpf_ops` is one attached
  program set (a BPF struct_ops), `struct hid_bpf` is the per-device state at
  `hdev->bpf`, `struct hid_ops` is the table through which the BPF side calls
  back into the core.
- Input path, in order; there is no hid_input_field() here:
  1. `hid_input_report()` or `hid_safe_input_report()`; the second also
     passes the allocated buffer size.
  2. `__hid_input_report()`: `dispatch_hid_bpf_device_event()`, which may
     return a different buffer.
  3. The driver's `raw_event`.
  4. `hid_report_raw_event()`: hiddev and hidraw get the report, so hidraw
     sees bytes already changed by BPF and by `raw_event`.
  5. `hid_process_report()`, then per usage `hid_process_event()`: the
     driver's `event`, then `hidinput_hid_event()` and hiddev.
  6. The driver's `report`, then `hidinput_report_event()`.
- `struct hid_field_entry`: one (field, usage index) slot in
  `report->field_entry_list`. After `hid_connect()`, input reports deliver
  variable usages in that list's priority order, which can differ from
  descriptor order; priorities come from `hidinput_configure_usage()`.
- `struct hid_usage`, not `struct hid_field`, holds the collection index
  (`collection_index`). The field holds copies of the enclosing application,
  physical and logical usages.
- `field->hidinput`: the link the event path follows to a
  `struct input_dev`; `hidinput_hid_event()` sends to
  `field->hidinput->input`. For when it is set and when it is NULL see
  "Inputs list and hidinput pointers".
- `hidinput->report`: set only under `HID_QUIRK_MULTI_INPUT`. With or without
  the quirk, reports hang on `hidinput->reports` through
  `report->hidinput_list`.
- `struct hid_battery`: one power supply per report id that carries a battery
  usage, on the list `hdev->batteries`, under `CONFIG_HID_BATTERY_STRENGTH`.
  There is no single battery field in `struct hid_device`.
- HID drivers that are also transports for child devices: they call
  `hid_allocate_device()` and supply a `struct hid_ll_driver`, for example
  `drivers/hid/hid-logitech-dj.c` and `drivers/hid/hid-steam.c`.
  `drivers/hid/hid-multitouch.c` and `drivers/hid/wacom_sys.c` do not call
  `hid_allocate_device()`.

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| Quirk tables | No single file. `drivers/hid/hid-quirks.c` holds four static tables (`hid_quirks[]`, `hid_have_special_driver[]`, `hid_ignore_list[]`, `hid_mouse_ignore_list[]`) and the dynamic quirks; `hid_lookup_quirk()` is the lookup over them. Outside it, for example: `i2c_hid_quirks[]` in `drivers/hid/i2c-hid/i2c-hid-core.c`, `i2c_hid_dmi_quirk_table[]` in `drivers/hid/i2c-hid/i2c-hid-dmi-quirks.c`, `hid_battery_quirks[]` in `drivers/hid/hid-input.c` |
| HID-BPF | No single file. `drivers/hid/bpf/hid_bpf_dispatch.c` and `drivers/hid/bpf/hid_bpf_struct_ops.c`, shared `drivers/hid/bpf/hid_bpf_dispatch.h`, public `include/linux/hid_bpf.h`. There is no hid_bpf_jmp_table.c. `drivers/hid/bpf/progs/` is not built by `drivers/hid/bpf/Makefile`; it has its own `Makefile` and its objects are loaded by `udev-hid-bpf` |
| I2C transport | No single file. `drivers/hid/i2c-hid/i2c-hid-core.c` plus the glue drivers listed in `drivers/hid/i2c-hid/Makefile`; easy to miss is `drivers/hid/i2c-hid/i2c-hid-acpi-prp0001.c`, built with `CONFIG_I2C_HID_ACPI`. `include/linux/hid-over-i2c.h` does not belong to this directory: only `drivers/hid/intel-thc-hid/intel-quicki2c/` includes it |
| Headers drivers include | No single file. `include/linux/hid.h` is the main one; `struct hid_device_id`, `HID_ANY_ID`, `HID_BUS_ANY` and `HID_GROUP_ANY` are defined in `include/linux/device-id/hid.h`, which `include/linux/hid.h` and `include/linux/mod_devicetable.h` both include |
| Bus and parser, input bridge, raw and legacy USB character devices, user-space transport, generic driver, device id constants, debugfs, USB transport | Models have these right |

**KUnit suites and selftests**

- KUnit suites in `drivers/hid/`: six, not only UC-Logic.

| Suite name | Source | Config | Calls |
|---|---|---|---|
| `hid_uclogic_rdesc_test` | `drivers/hid/hid-uclogic-rdesc-test.c` | `CONFIG_HID_KUNIT_TEST` | `uclogic_rdesc_template_apply()` |
| `hid_uclogic_params_test` | `drivers/hid/hid-uclogic-params-test.c` | `CONFIG_HID_KUNIT_TEST` | `uclogic_params_parse_ugee_v2_desc()`, `uclogic_params_ugee_v2_init_event_hooks()`, `uclogic_params_cleanup_event_hooks()` |
| `hid_uclogic_core_test` | `drivers/hid/hid-uclogic-core-test.c` | `CONFIG_HID_KUNIT_TEST` | `uclogic_exec_event_hook()` |
| `hid_input` | `drivers/hid/hid-input-test.c` | `CONFIG_HID_KUNIT_TEST` | `hidinput_update_battery_charge_status()`, `hidinput_get_battery_property()` |
| `hid-roccat-kone` | end of `drivers/hid/hid-roccat-kone.c` | `CONFIG_HID_ROCCAT_KONE_KUNIT_TEST` | `kone_keep_values_up_to_date()` with an out-of-range profile index |
| `hid_hyperv_mouse` | end of `drivers/hid/hid-hyperv.c` | `CONFIG_HID_HYPERV_MOUSE_KUNIT_TEST` | `mousevsc_on_receive_device_info()` |

- `hid-uclogic-rdesc-test.c`: the only test built as its own object
  (`hid-uclogic-test.o` in `drivers/hid/Makefile`); it reaches the driver
  through `EXPORT_SYMBOL_IF_KUNIT()`.
- `hid-uclogic-params-test.c`, `hid-uclogic-core-test.c`, `hid-input-test.c`:
  each is `#include`d at the end of the file it tests, under
  `#ifdef CONFIG_HID_KUNIT_TEST`, so it can call static functions.
- `CONFIG_HID_KUNIT_TEST=m`: the `#ifdef` is false, so those three suites are
  not compiled; of the four `CONFIG_HID_KUNIT_TEST` suites only
  `hid_uclogic_rdesc_test` is built.
- `drivers/hid/.kunitconfig`: the only test option it sets is
  `CONFIG_HID_KUNIT_TEST`; it enables neither the Roccat Kone nor the Hyper-V
  suite.
- `mousevsc_on_receive_device_info()`: with
  `CONFIG_HID_HYPERV_MOUSE_KUNIT_TEST` enabled, it skips `vmbus_sendpacket()`
  when `input_device->device` is NULL.
- C selftests: two programs, `hid_bpf.c` and `hidraw.c`, both in
  `TEST_GEN_PROGS` of `tools/testing/selftests/hid/Makefile`; `hidraw.c`
  covers the hidraw ioctls and `HIDIOCREVOKE`.
- C device creation: `uhid_create()` in
  `tools/testing/selftests/hid/hid_common.h` writes `UHID_CREATE`, not
  `UHID_CREATE2`; input goes in with `UHID_INPUT2`.
- Python tests: the test files are in `tools/testing/selftests/hid/tests/`,
  for example `tests/test_mouse.py`; each wrapper script in `TEST_PROGS`, for
  example `hid-mouse.sh`, sets `TARGET` to one of them and calls
  `run-hid-tools-tests.sh`.
- Python device creation: `BaseDevice` in `tests/base_device.py` subclasses
  `UHIDDevice` from the `hidtools` package; that package is not in the tree,
  so the uhid events it writes cannot be read here.
- `run-hid-tools-tests.sh`: exits with the kselftest skip code when `python3`,
  `pytest`, `pytest_tap` or `hidtools` is missing, so a run can report no
  failure without running a Python test.
- `tests/test_hid_core.py`: holds one class, `TestCollectionOverflow`; its own
  test `test_rdesc` has an empty body, and it inherits `test_creation` from
  `BaseTestCase.TestUhid` in `tests/base.py`; it is not general coverage of
  the parser in `drivers/hid/hid-core.c`.
- `check_taint` in `tests/base.py`: an autouse fixture that asserts
  `/proc/sys/kernel/tainted` is unchanged after each test; it is the only
  check in `tests/test_usb_crash.py`, whose `test_creation` is overridden
  with `assert True`.
- In-tree HID-BPF programs: `tests/test_tablet.py` and `tests/test_gamepad.py`
  set `hid_bpfs` to objects from `drivers/hid/bpf/progs/`;
  `load_hid_bpfs()` in `tests/base.py` loads them with `udev-hid-bpf` and
  skips the test when that tool is not in `$PATH`.

## Transport callbacks

**Mandatory and optional callbacks**

- `raw_request`: mandatory and the only callback tested at registration;
  `hid_add_device()` logs "transport driver missing .raw_request()" and
  returns `-EINVAL` before it calls `parse`.
- `__hid_hw_raw_request()`: has no NULL test of its own and never returns an
  errno for a missing callback; it relies on the `hid_add_device()` test.
- `start`: called only from `hid_hw_start()`, not from `hid_connect()`.
- `request` missing: `hid_hw_request()` calls `__hid_request()` in
  `drivers/hid/hid-core.c`, which builds the buffer and uses `raw_request`.
  There is no __hid_hw_request() in this tree.
- `idle` missing: `hid_hw_idle()` returns 0.
- `may_wakeup` missing: `hid_hw_may_wakeup()` returns `device_may_wakeup()` of
  `hdev->dev.parent`, or `false` when there is no parent.
- `struct hid_ll_driver` has no member named sched_inputs.
- `Documentation/hid/hid-transport.rst`: calls only `raw_request` mandatory
  and only `request` optional; it gives no status for `start`, `stop`,
  `open`, `close` or `parse`, which the core calls unchecked.

**Parse callback**

- `parse` is called from one place, `hid_add_device()`, before `device_add()`;
  `hid_open_report()` and driver probe never call it.
- Success without `hid_parse_report()`: `hid_add_device()` finds
  `hdev->dev_rdesc` NULL and returns `-ENODEV`; no driver probe ever runs.
- `hid_parse_report()` called a second time: overwrites `hid->dev_rdesc`
  without freeing the earlier copy.

**Raw request contract**

- `__hid_hw_raw_request()` checks only `len >= 1`, `len <= max_buffer_size`
  and `buf != NULL`; it does not test that `raw_request` exists and does not
  look at `reportnum`.
- `rtype` under `CONFIG_HID_BPF`: `dispatch_hid_bpf_raw_requests()` returns
  `-EINVAL` for `rtype >= HID_REPORT_TYPES`, and `-ENODEV` when
  `hdev->bpf.destroyed`.
- `rtype` without `CONFIG_HID_BPF`: the stub in `include/linux/hid_bpf.h`
  returns 0, so the core does not test `rtype`; `uhid_hid_raw_request()`
  tests it itself.
- Unknown `reqtype`: `-EIO` in, for example, `usbhid_raw_request()` and
  `i2c_hid_raw_request()`; not every transport does so,
  `goodix_hid_raw_request()` returns `-EINVAL`.
- `usbhid_raw_request()`: dispatches to `usbhid_get_raw_report()` and
  `usbhid_set_raw_report()`; there is no hid_get_class_report() or
  hid_set_class_report() here.
- `usbhid_set_raw_report()`: sends every report type, output included, with
  `usb_control_msg()`; it never uses the interrupt OUT endpoint.
- `buf` is not checked for DMA capability: usbhid passes it to
  `usb_control_msg()` without copying, and on a host controller that uses
  DMA `usb_hcd_map_urb_for_dma()` fails an on-stack transfer buffer with
  `-EAGAIN`; `hid_bpf_hw_request()` copies into a `kmemdup()` buffer before
  the call.

**Raw request calling context**

- `usbhid_raw_request()` never calls `usb_interrupt_msg()`; its get and set
  paths both block in `usb_control_msg()`.
- `hid_hw_raw_request()` kerneldoc states no calling context; the transports
  are the evidence, for example `uhid_hid_get_report()` with
  `mutex_lock_interruptible()` and, in `__uhid_report_queue_and_wait()`,
  `wait_event_interruptible_timeout()`.

**Output report contract**

- `hidraw_send_report()`: calls `__hid_hw_output_report()` only for
  `HID_OUTPUT_REPORT` on a device without
  `HID_QUIRK_NO_OUTPUT_REPORTS_ON_INTR_EP`; with the quirk it goes straight
  to `__hid_hw_raw_request()` with `HID_REQ_SET_REPORT`.
- `hidraw_send_report()` fallback test: `ret != -ENOSYS` on the return value;
  it does not look at the `output_report` pointer, and returns every other
  error unchanged.
- `-ENOSYS` does not prove the callback is absent: `usbhid_output_report()`
  returns it when `usbhid->urbout` is NULL, and
  `i2c_hid_set_or_send_report()` when `wMaxOutputLength` is 0.
- `hidinput_led_worker()`: calls `ll_driver->request` directly when the
  transport has one; only otherwise does it try `hid_hw_output_report()`,
  then `hid_hw_raw_request()` on `-ENOSYS`.
- `Documentation/hid/hid-transport.rst` says `output_report` must be
  asynchronous and that asynchronous calls work in atomic context; the code
  does not: `usbhid_output_report()` blocks in `usb_interrupt_msg()` and
  `i2c_hid_output_raw_report()` takes a mutex.

**Open and close counting**

- `Documentation/hid/hid-transport.rst` says "->open() calls are nested for
  each client that opens the HID device"; `hid_hw_open()` never nests them,
  so a transport sees one `open` and one `close` and needs no counter.
- `hdev->ll_open_count` is an `unsigned int` and `hid_hw_close()` decrements
  it with no test for zero; a close without a successful `hid_hw_open()`
  wraps the count, and the next `hid_hw_open()` does not call `open`.
- `hid_hw_open()` can fail before it counts: `mutex_lock_killable()` returns
  an error with `ll_open_count` unchanged, so that caller must not call
  `hid_hw_close()`.

## Device lifetime in a transport

**Registering a device**

- `name`, `uniq`, `type`, `version`: not only informational; `hid_ignore()`
  matches on `name`, `uniq` and `type`, `hid_lookup_quirk()` on `version`, both
  in `hid_add_device()` before `->parse()` runs.
- `ll_driver`: the only pointer field of `struct hid_device` that
  `hid_add_device()` dereferences with no NULL test; the other fields a
  transport sets start zeroed in `hid_allocate_device()`, and for example
  `goodix_hid_init()` sets neither `phys` nor `uniq`.
- **Potentially unsafe usage**: calling `hid_add_device()` from the context
  that services the transport's I/O, or under a lock its callbacks take.
  - Unsafe: when a HID driver's probe, run synchronously inside `device_add()`,
    blocks in `->raw_request()` waiting on that context.
  - Safe: from a work item, as `uhid_device_add_worker()` and
    `hidp_session_dev_work()` do; `uhid_char_write()` holds `devlock` and
    delivers the reply that `uhid_hid_get_report()` waits for.
  - Safe: from bus probe when callbacks complete on their own, as
    `usbhid_probe()` does; `usbhid_raw_request()` blocks only in
    `usb_control_msg()`.

**Registration checks**

- `hid_add_device()` calls `ll_driver->parse()`, not `hid_parse_report()`;
  before `device_add()` it calls neither `hid_open_report()` nor any HID-BPF
  hook.
- Order of the failing checks: `HID_STAT_ADDED` (`-EBUSY`), `hid_ignore()`
  (`-ENODEV`), missing `->raw_request` (`-EINVAL`), `->parse()` (its return
  value), `dev_rdesc` still NULL (`-ENODEV`).
- `hid_scan_report()` failure: `hid_set_group()` only prints `hid_warn()`;
  registration continues.
- `-ENODEV` reaches the transport from several places it cannot tell apart:
  `hid_ignore()`, the `dev_rdesc` check, and `->parse()` itself, for example
  `usbhid_parse()`.
- Suppressing the log for `-ENODEV`: see `usbhid_probe()` and
  `i2c_hid_core_register_hid()`; this also hides the `dev_rdesc` and
  `->parse()` cases.
- HID driver probe failure: does not fail `hid_add_device()`; every error path
  of `device_add()` precedes `bus_probe_device()`.

**Destroying a device**

- `hiddev_free()` in `drivers/hid/hid-core.c`: the function that does
  `kfree()` of the `struct hid_device`; it is the kref release of `ref` and is
  unrelated to `struct hiddev` in `include/linux/hiddev.h`.
- `hid_device_release()`: frees nothing itself; it only does
  `kref_put(&hid->ref, hiddev_free)`.
- Two counts gate the free: the `struct device` refcount and `ref`; the memory
  goes when the device is released and every `ref` holder has dropped.
- `hid_destroy_device()`: calls `hid_bpf_destroy_device()`, then
  `hid_remove_device()`, then `put_device()`; it does not call `hiddev_free()`.
- `hid_remove_device()`: frees and NULLs `dev_rdesc` whether or not the device
  was added, so a later holder sees `dev_rdesc == NULL`.

| Holder after `hid_destroy_device()` returns | Holds | Dropped by |
|---|---|---|
| open debugfs `events` file (`CONFIG_DEBUG_FS`) | `ref`, via `hid_debug_events_open()` | `hid_debug_events_release()`, which may run `hiddev_free()` |
| HID-BPF context from `hid_bpf_allocate_context()` (`CONFIG_HID_BPF`) | device reference | `hid_bpf_release_context()` |
| `hid_haptic_init()` (`CONFIG_HID_HAPTIC`) | device reference | `hid_haptic_destroy()`, run from `input_dev_release()` |
| transport's own, for example `hidp_session_dev_add()` | device reference | the transport |

- HID-BPF struct_ops attachments (`hid_bpf_reg()`): their references are
  dropped inside `hid_destroy_device()` by `__hid_bpf_ops_destroy_device()`.
- Open hidraw and hiddev files: hold no reference on the `struct hid_device`;
  they keep `struct hidraw` or `struct hiddev` and test `exist`.
- Child devices: `device_del()` drops the reference on the parent, so an
  unregistered input or hidraw device no longer pins the hid device.

**Transport teardown order**

- There is no hid_stop() here; `hid_hw_stop()` in `drivers/hid/hid-core.c` is
  what calls `->stop()`.
- `usbhid_stop()`: runs inside `hid_destroy_device()` through `->stop()`, not
  before it; before that call `usbhid_disconnect()` only sets
  `HID_DISCONNECTED`.
- `i2c_hid_core_remove()` sequence:
  1. `drm_panel_remove_follower()` for a panel follower, otherwise
     `i2c_hid_core_suspend()`, which calls `disable_irq()` and powers down
     when `hid_driver_suspend()` succeeds.
  2. `hid_destroy_device()`.
  3. `free_irq()`.
  4. `i2c_hid_free_buffers()`.
- `i2c_hid_core_shutdown_tail()`: called only from `i2c_hid_core_shutdown()`,
  not on remove.
- Both orders of quiescing input exist: before destroy (`goodix_spi_remove()`
  calls `disable_irq()`), and inside destroy (`usbhid_stop()`).
- On teardown `->stop()` is reached only through `hid_hw_stop()`;
  `hid_device_remove()` calls `hid_hw_stop()` itself only when the bound driver
  has no `remove`.
- With no driver bound, `hid_destroy_device()` makes no `ll_driver` call.
- The guarantee after return has no single gate in the core; it rests on
  driver unbind in `device_del()`, `exist` cleared by `hidraw_disconnect()` and
  `hiddev_disconnect()`, and, under `CONFIG_HID_BPF`, `bpf.destroyed`.
- `bpf.destroyed`, under `CONFIG_HID_BPF`: makes
  `dispatch_hid_bpf_raw_requests()` and `dispatch_hid_bpf_output_report()`
  return `-ENODEV` before the `ll_driver` call, for every caller, including a
  HID-BPF context that outlives the device; without `CONFIG_HID_BPF` nothing
  sets it.
- `__hid_input_report()`: returns `-ENODEV` once `hid->driver` is NULL, so
  input arriving after the unbind is dropped, provided the memory is still
  there.
- **Potentially unsafe usage**: transport input path calling
  `hid_input_report()` after `hid_destroy_device()` returned.
  - Unsafe: when the transport holds only the allocation reference;
    `put_device()` may already have run `hiddev_free()`.
  - Safe: when the transport holds its own reference, as
    `hidp_session_dev_add()` takes with `get_device()`.
  - Safe: when the source is stopped before or inside destroy, as
    `goodix_spi_remove()` and `usbhid_stop()` do.

**Freeing a transport's device**

- In-tree examples: `usbhid_probe()` with `usbhid_disconnect()`, and
  `quicki2c_hid_probe()` with `quicki2c_hid_remove()`.
- Failed `hid_add_device()`: no HID driver was probed, and
  `hid_destroy_device()` on a never-added device makes no `ll_driver` call;
  that is why `usbhid_probe()` may `kfree()` its private data first.
- Clearing the transport's copy of the pointer: not needed by the core;
  `usbhid_disconnect()` and `i2c_hid_core_remove()` leave it set.
- `uhid_dev_destroy()` clears `uhid->hid` because `uhid_dev_create2()` tests it.
- **Unsafe usage**: calling `hid_destroy_device()` twice on one allocation;
  `put_device()` drops a reference each time, and under `CONFIG_HID_BPF`
  `hid_bpf_destroy_device()` runs `cleanup_srcu_struct()` each time.
  - Safe: one call per allocation, guarded by the transport's own pointer, as
    `uhid_dev_destroy()` does.
- **Unsafe usage**: `hid_destroy_device()` while a work item that calls
  `hid_add_device()` may still run; `HID_STAT_ADDED` is set and tested with no
  lock.
  - Safe: `cancel_work_sync()` first, as `uhid_dev_destroy()` and
    `hidp_session_remove()` do.
- **Potentially unsafe usage**: `put_device(&hid->dev)` by a transport, or use
  of the device after `hid_destroy_device()`.
  - Unsafe: when it drops or relies on the allocation reference, which
    `hid_destroy_device()` owns; `hid_bpf_destroy_device()` and
    `hid_remove_device()` are then skipped, or the memory is already freed.
  - Safe: for a reference the transport took with `get_device()` after
    `hid_add_device()` succeeded, as `hidp_session_dev_add()` takes.

## Probe and start

**Generic and specific drivers**

- `HID_QUIRK_HAVE_SPECIAL_DRIVER`: the only code that sets it is
  `hid_gets_squirk()` in `drivers/hid/hid-quirks.c`, from the
  `hid_have_special_driver` table; `hid_ignore()` and `hid_match_device()` do
  not read the table.
- Dynamic quirk entry for the device: `hid_lookup_quirk()` returns that entry
  alone and skips `hid_gets_squirk()`, so the table entry has no effect.
- Table entry, side effect: `hid_set_group()` skips `hid_scan_report()`, so
  with `hid_ignore_special_drivers` clear `hdev->group` stays 0 unless the
  transport set it. `hid_match_one_id()` then rejects any id entry whose
  `group` is not `HID_GROUP_ANY`.
- Dynamic id added through `new_id_store()`: only `driver_attach()` runs, and
  `__driver_probe_device()` returns `-EBUSY` for a bound device. A device
  already bound to hid-generic stays there; the reprobe walk runs only from
  `__hid_register_driver()`.

**Forcing the generic driver**

- `hid_check_device_match()`: returns `bool`. False for the specific driver
  becomes `-ENODEV` in `__hid_device_probe()`.
- `hid_generic_match()`: has no test of `hdev->group` of its own; the group
  counts only in `hid_match_device()`, which it calls for the other drivers.
- `HID_QUIRK_IGNORE_SPECIAL_DRIVER`: no table or driver in this tree sets it.
- HID-BPF programs cannot set it: `hid_bpf_ops_btf_struct_access()` in
  `drivers/hid/bpf/hid_bpf_struct_ops.c` allows writes to `name`, `uniq` and
  `phys` of `struct hid_device` only.
- Ways the bit reaches `hdev->quirks`: the dynamic quirk list filled by
  `hid_quirks_init()` (usbhid module parameter), or `hdev->initial_quirks`.
- `hid_ignore_special_drivers` set: `hid_set_group()` also forces
  `hdev->group` to `HID_GROUP_GENERIC` without scanning the descriptor.

**Core work around probe**

- `driver_input_lock`: a `struct semaphore`, initialised to 1 in
  `hid_allocate_device()`. There is no ll_driver_lock in this tree.
- First step of `__hid_device_probe()`, when `hdev->bpf_rsize` is 0:
  `call_hid_bpf_rdesc_fixup()` fills `hdev->bpf_rdesc` and `hdev->bpf_rsize`.
  If the descriptor changed, `hdev->group` is recomputed by `hid_set_group()`.
  This runs before the match check.
- Without `CONFIG_HID_BPF`: `call_hid_bpf_rdesc_fixup()` returns its argument,
  so `hdev->bpf_rdesc` is `hdev->dev_rdesc`.
- `hdev->quirks = hid_lookup_quirk(hdev)`: runs on every probe, after the
  match check and after the devres group is opened, just before
  `hdev->driver` is set.

**Devres in device drivers**

- Allocation on `&hdev->dev` made while no driver is bound: `really_probe()`
  in `drivers/base/dd.c` finds the devres list not empty and fails the next
  bind with `-EBUSY`.
- The rest is as models expect; see `__hid_device_probe()` and
  `hid_device_remove()` in `drivers/hid/hid-core.c`.

**Parsing in probe**

- Second call while `HID_STAT_PARSED` is set: `WARN_ON()` and `-EBUSY`; it
  does not return 0.
- No way to parse again inside one binding after a parse succeeded:
  `hid_close_report()` is static in `drivers/hid/hid-core.c`.
- Source descriptor: `hdev->bpf_rdesc` and `hdev->bpf_rsize`, not
  `hdev->dev_rdesc`. `__hid_device_probe()` sets them, so a call before the
  first probe hits `WARN_ON(!start)` and returns `-ENODEV`.
- On failure of `hid_parse_collections()`: `hid_open_report()` calls
  `hid_close_report()` itself before it returns the error; for what that
  frees and what stays for the next probe see "Report descriptor copies".
- **Unsafe usage**: calling `hid_hw_start()` after `hid_parse()` failed or was
  skipped. Nothing in `hid_hw_start()` tests `HID_STAT_PARSED`, and
  `usbhid_start()` dereferences `hid->collection`, which is NULL then.
  - Safe: return the error of `hid_parse()` first, as `hid_generic_probe()`
    does.

**Connect mask**

- `HID_CONNECT_HIDDEV` on USB: added only by `HID_QUIRK_HIDDEV_FORCE`;
  otherwise it must be in the mask.
- `hdev->bus != BUS_USB`: clears `HID_CONNECT_HIDDEV` after the quirk test, so
  `HID_QUIRK_HIDDEV_FORCE` cannot connect hiddev on another bus.
- `hdev->hiddev_connect`: set only by `usbhid_probe()`, under
  `CONFIG_USB_HIDDEV`.
- Failure for lack of listeners: `-ENODEV` with "device has no listeners,
  quitting", only when `hdev->claimed` is 0 and the driver has no `raw_event`.
- Failed `hidinput_connect()`, `hidraw_connect()` or `hiddev_connect`: not an
  error for `hid_connect()`; the claimed bit just stays clear.
- `HID_CONNECT_DRIVER`, second effect: `hid_report_raw_event()` skips
  `hid_process_report()` and the `report` callback when `hdev->claimed` equals
  `HID_CLAIMED_HIDRAW`. With `HID_CLAIMED_DRIVER` also set, a hidraw-only
  device gets `event` and `report`; `udraw_probe()` in
  `drivers/hid/hid-udraw-ps3.c` passes that mask.
- `HID_CONNECT_HIDINPUT_FORCE`: skips only the test for a collection of type
  `HID_COLLECTION_APPLICATION` or `HID_COLLECTION_PHYSICAL` whose usage
  satisfies `IS_INPUT_APPLICATION()`.
- With force, an input device that `hidinput_has_been_populated()` rejects is
  still dropped, and `hidinput_connect()` fails when no input is left.
- `HID_CONNECT_FF`: read inside `hidinput_connect()`, which calls
  `hid->ff_init` before it registers the first input device; `hid_connect()`
  itself does not call `ff_init`.

**Starting the hardware**

- Stop from a devm action: `mcp2221_probe()` registers
  `mcp2221_hid_unregister()` with `devm_add_action_or_reset()`; for what such
  a driver needs in `remove` see "Stopping hardware from devres".
- After a failed `hid_hw_start()`: when `hid_connect()` failed,
  `ll_driver->stop()` has already run; when `ll_driver->start()` failed, it
  was not called. Either way the driver does not call `hid_hw_stop()`.

**Input lock during probe**

- Probe failure: `__hid_device_probe()` calls `hid_device_io_stop()` when
  `io_started` is still set, before it releases the devres group.
  `hid_device_probe()` then does the `up()`.
- Driver error path: needs no `hid_device_io_stop()` of its own.
  `mcp2221_probe()` returns errors after `hid_device_io_start()` without it.
- `hid_device_io_stop()` with I/O already stopped: `dev_warn()` and no
  `down()`. An explicit stop goes before `hid_hw_stop()`, as in
  `nintendo_hid_probe()`, not after.
- `hdev->io_started` after a probe that returned with I/O started: stays true.
  Only `hid_device_probe()`, `hid_device_remove()` and `hid_device_io_stop()`
  clear it.
- **Unsafe usage**: calling `hid_hw_stop()` outside probe and remove on a
  device whose probe left I/O started. It takes `driver_input_lock` and
  nothing releases it: every report gets `-EBUSY` and `hid_device_remove()`
  blocks in `down()`.
  - Safe: in `remove`, as `logi_dj_remove()` does; `hid_device_remove()` has
    cleared `io_started` and holds the semaphore already.
  - Safe: in the error path of `probe`, as `hidpp_probe()` does; the core
    releases the semaphore after `probe` returns.

**Opening from a driver**

- Open during probe: does not deliver reports to the driver by itself;
  `driver_input_lock` still drops them until `hid_device_io_start()` or the
  return of probe.
- I2C while closed: the interrupt is live; `i2c_hid_get_input()` reads the
  report from the device and drops it unless `I2C_HID_STARTED` is set.
- USB while closed, with `HID_QUIRK_ALWAYS_POLL`: `usbhid_start()` submits the
  interrupt-in URB, but `hid_irq_in()` discards the data while `HID_OPENED` is
  clear.
- USB control-pipe replies: `hid_ctrl()` passes them to
  `hid_safe_input_report()` without testing `HID_OPENED`, so a reply to
  `HID_REQ_GET_REPORT` arrives even with the device closed.
- `ll_open_count`: written only by `hid_hw_open()` and `hid_hw_close()`. The
  core never resets it, so a missing `hid_hw_close()` carries over into the
  next binding, whose first open then skips `ll_driver->open`.
- Drivers that open in probe and close in `remove`: for example
  `logi_dj_probe()`, `ps_probe()`, `cp2112_probe()`.
- `hidpp_probe()`: opens for the duration of probe only and calls
  `hid_hw_close()` before it returns.

**Probe failure cleanup**

- Order in `__hid_device_probe()` on error: `hid_device_io_stop()` when
  `hdev->io_started` is set, `devres_release_group()`, `hid_close_report()`,
  `hdev->driver = NULL`.
- **Potentially unsafe usage**: returning an error from `probe` after
  `hid_hw_start()` succeeded, without `hid_hw_stop()`.
  - Unsafe: when nothing else stops the hardware. `__hid_device_probe()`
    calls neither `hid_hw_stop()` nor `hid_hw_close()`; the nodes made by
    `hid_connect()` stay registered while `hid_close_report()` frees the
    reports.
  - Safe: when a devm action on `&hdev->dev` closes and stops, as
    `mcp2221_hid_unregister()` registered in `mcp2221_probe()`; the
    `devres_release_group()` of the core runs it.

**Callbacks during probe**

- `input_mapping`, `input_mapped`, `input_configured`, `feature_mapping`: run
  only inside `hidinput_connect()`, so only when the mask has
  `HID_CONNECT_HIDINPUT`; never on incoming reports.
- `on_hid_hw_open` and `on_hid_hw_close`: called by `hid_hw_open()` and
  `hid_hw_close()` on the first open and last close, for example when user
  space opens the evdev or hidraw node. `driver_input_lock` does not hold
  them off.
- `suspend`, `resume`, `reset_resume`, under `CONFIG_PM`: reached through
  `hid_driver_suspend()`, `hid_driver_resume()` and
  `hid_driver_reset_resume()`, which take no lock and test only
  `hdev->driver`, set before `probe` is called. Transports call them from
  their own PM callbacks, for example `hid_suspend()` in
  `drivers/hid/usbhid/hid-core.c`.
- Hold-off of `raw_event`, `event` and `report`: sits only in
  `__hid_input_report()`. `hid_report_raw_event()` takes no lock; a caller
  that uses it directly, such as `drivers/staging/greybus/hid.c`, reaches
  `event` and `report` during probe.
- **Potentially unsafe usage**: setting or initialising driver private data
  after `hid_hw_start()`.
  - Unsafe: when the mask has `HID_CONNECT_HIDINPUT` and a mapping callback
    reads `hid_get_drvdata()`, or when `on_hid_hw_open` or an attribute or
    device already registered reads it.
  - Safe: when only `raw_event`, `event` or `report` read it and it is set
    before `hid_device_io_start()`, as in `cp2112_probe()` with mask
    `HID_CONNECT_HIDRAW`; `__hid_input_report()` drops reports until then.
  - Safe: when only `raw_event` reads it and probe never calls
    `hid_device_io_start()`, as `ps_probe()`, which sets drvdata in
    `dualshock4_create()`, after `hid_hw_open()`; `__hid_input_report()`
    drops reports until probe returns, and `ps_raw_event()` also tests for
    NULL.
  - Safe: set before `hid_hw_start()`, as `logi_dj_probe()` does, or before
    `hid_parse()` when `report_fixup` reads it, as `hidpp_probe()` does.

## Stop, remove and teardown

**Core work around remove**

- Devres release: `hid_device_remove()` in `drivers/hid/hid-core.c` calls
  `devres_release_group()` on `hdev->devres_group_id` right after the
  callback (or the default `hid_hw_stop()`), before `hid_close_report()` and
  before `hdev->driver = NULL`; it does not call `devres_release_all()`.
- Devres group: `__hid_device_probe()` opens it and never closes it, so a
  `devm_*` resource added to `&hdev->dev` after probe is released at the same
  point.
- `driver_input_lock` during the release: still held, unless the callback
  left io started.
- `hid_device_io_start()` inside `remove`: releases the semaphore early; the
  final `up()` is skipped only if `hdev->io_started` is still true at the
  end.
- `hdrv->raw_event`: called only from `__hid_input_report()`, so it cannot
  run while `hid_device_remove()` holds the semaphore.
- Listener callbacks: not gated by the semaphore; an input callback on a
  hidinput `struct input_dev`, such as `sony_play_effect()` in
  `drivers/hid/hid-sony.c`, can still enter the driver until `hid_hw_stop()`
  has run.

**Stopping the hardware**

- `hid_hw_stop()`: defined in `drivers/hid/hid-core.c`, not an inline.
- Input lock: if `hdev->io_started` is set, `hid_hw_stop()` first calls
  `hid_device_io_stop()`, which clears `io_started` and does `down()` on
  `driver_input_lock`; otherwise it leaves the lock alone.
- Order: `hid_device_io_stop()` (conditional), `hid_disconnect()`,
  `hdev->ll_driver->stop()`.
- `hid_disconnect()` order: removes the `country` attribute first, then
  input, hiddev, hidraw according to `HID_CLAIMED_INPUT`,
  `HID_CLAIMED_HIDDEV`, `HID_CLAIMED_HIDRAW` in `hdev->claimed`, clears
  `claimed`, and calls `hid_bpf_disconnect_device()` last.
- `hid_disconnect()`: does no debug teardown.
- No started state: `hid_hw_stop()` has no test of whether `hid_hw_start()`
  succeeded; it calls `ll_driver->stop()` unconditionally.
- **Unsafe usage**: calling `hid_hw_stop()` after `hid_hw_start()` returned
  an error.
  - Unsafe: `hid_hw_start()` has already run `ll_driver->stop()` when
    `hid_connect()` failed, and a failed `usbhid_start()` has freed its
    buffers; `usbhid_stop()` then calls `hid_free_buffers()` in
    `drivers/hid/usbhid/hid-core.c`, which frees through pointers it never
    clears.
  - Safe: the `hid_hw_start()` failure branch returns without the stop, and
    only later failures reach it, as `ps_probe()` in
    `drivers/hid/hid-playstation.c` does.

**Stopping hardware in remove**

- `hid_disconnect()` and `ll_driver->stop()`: at remove, reached only
  through `hid_hw_stop()`; with a `remove` callback the core runs neither.
- `hid_device_io_stop()` before `hid_hw_stop()` in `remove`: not needed,
  `io_started` is false at entry; calling it only logs "io already stopped".
- `hid_hw_close()`: `hid_hw_stop()` closes only for its listeners
  (`hidraw_disconnect()` calls `hid_hw_close()` for an open node); a
  driver's own `hid_hw_open()` left open keeps `hdev->ll_open_count`
  non-zero for the next driver bound, whose first `hid_hw_open()` then skips
  `ll_driver->open()`.
- State used by listener callbacks (force feedback, LED events): must stay
  valid until `hid_hw_stop()` returns; `raw_event` is not among them, see
  "Core work around remove".
- **Potentially unsafe usage**: a `remove` callback with a path that returns
  before `hid_hw_stop()` has run, in a driver with no devres action that
  runs it.
  - Unsafe: when probe can succeed in the state that takes that path and
    leave the hardware started; `hid_device_remove()` then runs
    `hid_close_report()` with the listeners still registered and the
    transport never stopped.
  - Safe: when probe cannot leave the hardware started in that state, as
    `ft260_remove()` in `drivers/hid/hid-ft260.c` returns for NULL driver
    data: `ft260_probe()` sets the driver data before its final `return 0`,
    and its other return of 0, when `ft260_is_interface_enabled()` returns 0,
    comes after its own `hid_hw_close()` and `hid_hw_stop()`.
  - Safe: stop on every path, including the one where probe returned after a
    bare `hid_hw_start()` with no driver data, as `hidpp_remove()` in
    `drivers/hid/hid-logitech-hidpp.c` does with
    `if (!hidpp) return hid_hw_stop(hdev);`.
  - Safe: driver cleanup, `hid_hw_close()` matching the `hid_hw_open()` of
    probe, then `hid_hw_stop()`, as `ps_remove()` in
    `drivers/hid/hid-playstation.c`.
  - Safe: no stop in `remove` when a devres action does it, as
    `hammer_remove()` in `drivers/hid/hid-google-hammer.c`; see "Stopping
    hardware from devres".

**Stopping hardware from devres**

- When the action runs: inside `devres_release_group()`, so before
  `hid_close_report()` and before `hdev->driver = NULL`, both in
  `hid_device_remove()` and in a failed `__hid_device_probe()`.
- Lock state when the action runs: `__hid_device_probe()` calls
  `hid_device_io_stop()` first if probe left io started, so the action runs
  with `driver_input_lock` held; a probe error path after registration just
  returns the error.
- In-tree examples: `mcp2221_hid_unregister()` in
  `drivers/hid/hid-mcp2221.c` and `hammer_stop()` in
  `drivers/hid/hid-google-hammer.c`.
- `mcp2221_remove()`: empty except under `IS_REACHABLE(CONFIG_IIO)`, where
  it cancels `init_work`, which itself adds `devm_*` resources, before the
  group is released.
- `hammer_probe()`: when `hammer_has_folded_event()`, calls `hid_hw_open()`
  after registering the action, and `hammer_remove()` calls the matching
  `hid_hw_close()`, so the close still precedes the stop.
- **Unsafe usage**: a devres action that calls `hid_hw_stop()` in a driver
  with no `remove` callback, or whose `remove` also stops.
  - Safe: the driver sets a `remove` callback that does not call
    `hid_hw_stop()`, as `hammer_remove()` does; `hid_device_remove()` then
    skips its default stop and the action is the only stop.

**Timers and work at teardown**

- Reports during `remove`: cannot queue work or re-arm a timer, because the
  core holds `driver_input_lock` for the whole callback unless the driver
  calls `hid_device_io_start()`.
- Sources that stay live in `remove`: input callbacks until
  `hid_hw_stop()`, class devices until unregistered, and the work or timer
  itself.
- After `remove` or a failed probe returns: `devres_release_group()` frees
  `devm_kzalloc()` driver data at once, so every cancel has to be
  synchronous and finished by then.
- **Unsafe usage**: calling `hid_hw_stop()` while a timer or work that uses
  the hidinput `struct input_dev` can still run; `hidinput_disconnect()`
  unregisters and frees those devices.
  - Safe: kill the timer first, as `uclogic_remove()` in
    `drivers/hid/hid-uclogic-core.c` (`timer_shutdown_sync()`) and
    `mt_remove()` in `drivers/hid/hid-multitouch.c` (`timer_delete_sync()`)
    do; the held `driver_input_lock` keeps reports from re-arming it.
- **Potentially unsafe usage**: cancelling work in `remove` while a class
  device that queues it is still registered.
  - Unsafe: when the class device was registered with `devm_*` on
    `&hdev->dev` and its callback queues unconditionally; it is unregistered
    only after `remove` returns and can queue the work after the cancel.
  - Safe: the callback tests a flag under the lock that `remove` clears
    before `cancel_work_sync()`, as `dualsense_schedule_work()` with
    `dualsense_remove()` in `drivers/hid/hid-playstation.c`, and
    `sony_schedule_work()` with `sony_cancel_work_sync()` in
    `drivers/hid/hid-sony.c`.
  - Safe: the class device is unregistered explicitly first, as
    `gt683r_led_remove()` in `drivers/hid/hid-gt683r.c` calls
    `led_classdev_unregister()` before `flush_work()` and `hid_hw_stop()`.
- **Potentially unsafe usage**: on the probe error path, cancelling
  report-armed work before `hid_hw_stop()`.
  - Unsafe: after `hid_device_io_start()`, when `raw_event` can queue the
    work again between the cancel and the stop.
  - Safe: stop first, then cancel, as the `hid_hw_open_fail` and
    `hid_hw_start_fail` labels of `hidpp_probe()` in
    `drivers/hid/hid-logitech-hidpp.c`; `hid_hw_stop()` re-takes
    `driver_input_lock` when `io_started` is set.
  - Safe: when probe never called `hid_device_io_start()`, as
    `sony_probe()` in `drivers/hid/hid-sony.c`; the core holds the lock for
    the whole probe.

## The input path and event callbacks

**Feeding input reports**

- `hid_safe_input_report()`: defined in `drivers/hid/hid-core.c`; arguments
  are `(hid, type, data, bufsize, size, interrupt)`, `bufsize` before `size`.
- `hid_input_report()`: passes `size` as both `bufsize` and `size`.
- `hid_report_raw_event()` tests, in order, each returning `-EINVAL` with
  `hid_warn_ratelimited()`:
  - numbered enum and (`size < 1` or `bufsize < 1`)
  - `bufsize < size`
  - `bufsize` (less the id byte) below the declared length `rsize`
- Short data with enough buffer: `dbg_hid()` only, then the tail is zeroed and
  processing continues.
- `rsize`: from `hid_compute_report_size()`, not `hid_report_len()`; it
  excludes the id byte.
- Data longer than `rsize`: not clamped; hidraw receives the full `size`.
- Short report via `hid_input_report()` with no HID-BPF program attached:
  rejected with `-EINVAL`, never padded, because `bufsize == size`.
- Rejected report: `raw_event` has already run; hiddev, hidraw, parsing and
  `report` do not see it.
- HID-BPF attached (`hdev->bpf.device_data` set):
  `dispatch_hid_bpf_device_event()` replaces `data` with its own buffer and
  `bufsize` with `hdev->bpf.allocated_data`, so short reports are padded
  even when they came through `hid_input_report()`.
- **Unsafe usage**: passing a `bufsize` larger than the writable bytes that
  start at `data`; the `memset()` in `hid_report_raw_event()` writes up to
  `rsize` bytes there.
  - Safe: `data` points past a header and `bufsize` is reduced by the same
    amount, as `i2c_hid_get_input()` does with `sizeof(__le16)`.
  - Safe: `bufsize` is the URB buffer length, as `hid_irq_in()` and
    `hid_ctrl()` pass `urb->transfer_buffer_length` (not `usbhid->bufsize`).
  - Safe: `bufsize` is the fixed array size, as `uhid_dev_input()` passes
    `UHID_DATA_MAX` and clamps `size` to it.

**Input path context and errors**

- `hid->driver` NULL: tested straight after the trylock succeeds, before
  HID-BPF, `raw_event`, hiddev and hidraw; nothing sees the report.
- `-EBUSY`: returned whenever anything holds `hid->driver_input_lock`, not
  only probe or remove; for example another report in flight,
  `hid_debug_rdesc_show()` in `drivers/hid/hid-debug.c`, or
  `hid_bpf_input_report()`.
- `hid_device_io_start()` called in probe: does the `up()`, so reports are
  delivered for the rest of probe and `hid_device_probe()` skips its own
  `up()` (it tests `hdev->io_started`).

**Path of an input report**

- `raw_event`: runs before the size check; hiddev and then hidraw run after
  it, inside `hid_report_raw_event()`.
- Field parsing, `event` and `report`: gated by
  `hid->claimed != HID_CLAIMED_HIDRAW && report->maxfield`, not by
  `HID_CLAIMED_INPUT`.
- `HID_CLAIMED_INPUT`: gates only `hidinput_hid_event()` inside
  `hid_process_event()` and the final `hidinput_report_event()`.
- There is no hid_input_field() here; `hid_process_report()` calls
  `hid_input_fetch_field()` for every field first, then dispatches usages.
- `hid_process_report()` with a non-empty `report->field_entry_list`: walks
  that list, so `event` calls do not follow field index order.
- `report_table`: a driver filter in `struct hid_driver`, matched by
  `hid_match_report()` on report type only, never on report id; gates only
  `raw_event`.
- `usage_table`: a driver filter matched by `hid_match_usage()` on
  `usage_hid`, `usage_type` and `usage_code`; gates only `event`; a usage
  that fails still goes to `hidinput_hid_event()`.

**Context of event callbacks**

- There is no driver_lock field in `struct hid_device`;
  `driver_input_lock` is the only lock `__hid_input_report()` takes around
  the callbacks.
- `hid_report_raw_event()` called directly: does not take
  `driver_input_lock`, and still calls `event` and `report`; the caller
  provides the exclusion, for example `gfrm_raw_event()` (already inside
  `raw_event`) or `asus_kbd_wmi_fan()` (explicit `down()`).
- **Potentially unsafe usage**: calling `hid_hw_request()` from `raw_event`,
  `event` or `report`.
  - Unsafe: on a transport that delivers input in atomic context and whose
    `struct hid_ll_driver` has no `request`, for example a child device of
    `drivers/hid/hid-logitech-dj.c` (`logi_dj_ll_driver`, fed under a
    spinlock by `logi_dj_dj_event()`); `hid_hw_request()` falls back to
    `__hid_request()`, which allocates with `GFP_KERNEL` and calls
    `hid_hw_raw_request()`.
  - Safe: on usbhid, where `request` is `usbhid_request()`; it queues under
    `usbhid->lock` and allocates with `GFP_ATOMIC`, as `pk_raw_event()` in
    `drivers/hid/hid-prodikeys.c` relies on after `pk_probe()` tested
    `hid_is_usb()`.

**Event callback return values**

- `raw_event` positive: treated as zero; `__hid_input_report()` tests only
  `ret < 0`, goes on to `hid_report_raw_event()` and returns that result.
- Stopping the core from `raw_event`: return a negative value, as
  `gfrm_raw_event()` does with `-1`.
- Comment above `struct hid_driver`: says negative is an error and any other
  value passes the event on.
- `raw_event`: the code matches the comment.
- `event`: the code does not match; any nonzero return skips
  `hidinput_hid_event()` and `hid->hiddev_hid_event()` for that usage, and
  `magicmouse_event()` relies on it by returning 1.
- `event` negative: logged as `"%s's event failed with %d\n"` with
  `hid_err()`; positive is not logged.
- `event` nonzero: affects one usage only; the remaining usages, `report` and
  `hidinput_report_event()` still run.
- `raw_event` rewriting `data[0]` on a numbered device:
  `hid_report_raw_event()` looks the report up again from `data`, so the
  rewritten id selects the report that is parsed.

**Indexing raw event data**

- Short report after `raw_event`: either zero-padded or rejected with
  `-EINVAL`; see "Feeding input reports" for which.
- `size` against the buffer: the `bufsize < size` test is in
  `hid_report_raw_event()`, so it too runs after `raw_event`.
- Example that tests `size` before indexing: `gfrm_raw_event()` in
  `drivers/hid/hid-gfrm.c` (`size < 2` before `data[1]`).

## Sending reports

**Request, raw request, output report**

- `hid_hw_request()` without `->request`: falls back to `__hid_request()` in
  `drivers/hid/hid-core.c`, which allocates with `GFP_KERNEL` and returns only
  after `hid_hw_raw_request()` did; the return value of `__hid_request()` is
  discarded.
- `__hid_request()`: sends through `hid_hw_raw_request()`, not the transport
  callback directly, so the length checks and the HID-BPF hook apply to it.
- `hid_hw_request()` on usbhid: `__usbhid_submit_report()` uses the interrupt
  OUT queue only for a SET of a `HID_OUTPUT_REPORT` when `usbhid->urbout`
  exists; every other `HID_REQ_GET_REPORT` or `HID_REQ_SET_REPORT` goes on
  the control queue.
- `usbhid_request()` drops the request with no error to the caller when: the
  queue is full, the `GFP_ATOMIC` allocation fails, `HID_DISCONNECTED` is set,
  or the request is a GET and the device has `HID_QUIRK_NOGET`.
- `hid_hw_output_report()` waiting is transport-dependent:
  `usbhid_output_report()` waits for the transfer; `hidp_output_report()` and
  `uhid_hid_output_raw()` queue the data and return the count at once.
- `__hid_hw_output_report()` order: length check, then the HID-BPF hook, then
  the test for a NULL `->output_report`.

**Report id byte**

- `hid_report_len()`: counts the id byte only when `report->id > 0`; for
  report id 0 it is the payload size alone.
- `hid_alloc_report_buf()`: allocates `hid_report_len()` + 7, plus 1 more byte
  when `report->id == 0`, so the caller can reserve byte 0.
- `__hid_request()` with `report->id == 0`: leaves byte 0 zero, fills the
  payload from byte 1 for a SET, and passes `hid_report_len()` + 1 as the
  length.
- Input path: the id byte is present when `report_enum->numbered` is set, and
  that flag is per report type; `hid_register_report()` sets it as soon as one
  report of that type has a non-zero id.
- `raw_event`: gets the same `data` and `size` as the core, id byte included
  for a numbered type; the byte is skipped only later, in
  `hid_report_raw_event()`.
- `hid_hw_raw_request()` buffer: byte 0 is the report id slot for every report,
  0 for report id 0, and `len` counts it.
- Byte 0 of a SET buffer: `usbhid_set_raw_report()` and
  `hidp_set_raw_report()` overwrite it with `reportnum`;
  `i2c_hid_raw_request()` returns `-EINVAL` when `buf[0] != reportnum`.
- `HID_QUIRK_SKIP_OUTPUT_REPORT_ID`: makes `usbhid_set_raw_report()` zero
  byte 0 of an output report, so the id byte is not sent.
- usbhid with report id 0: the skip of byte 0 is in `usbhid_get_raw_report()`
  and `usbhid_set_raw_report()`, not in `usbhid_raw_request()`; the returned
  count includes the skipped byte.
- `hid_hw_output_report()` buffer: has no report number argument; byte 0 is
  the id slot: `usbhid_output_report()` skips it when it is 0, and
  `i2c_hid_output_raw_report()` takes the id from it and always strips it.
- **Potentially unsafe usage**: filling a buffer with `hid_output_report()` at
  offset 0 and passing it with `hid_report_len()` to `hid_hw_raw_request()` or
  `hid_hw_output_report()`.
  - Unsafe: when `report->id == 0`; byte 0 then holds payload, which the
    transport overwrites or strips as the id, and the length is one short.
  - Safe: when `report->id > 0`; `hid_output_report()` puts the id in byte 0
    and `hid_report_len()` counts it.
  - Safe: for id 0, fill from byte 1 and pass the length plus 1, as
    `__hid_request()` does for SET; `usbhid_set_raw_report()` then skips
    byte 0.
  - Safe: for a GET of id 0, pass the length plus 1 and skip byte 0 of the
    reply before giving it to `hid_report_raw_event()`, as
    `vivaldi_feature_mapping()` in `drivers/hid/hid-vivaldi-common.c` does;
    `usbhid_get_raw_report()` stores the reply from byte 1.

**Requests from event callbacks**

- `->request`: of the transports that implement it, only `usbhid_request()`
  is usable in atomic context.
- `amdtp_hid_request()`: sleeps for a GET; `amd_sfh_get_report()` takes a
  mutex and allocates with `GFP_KERNEL`.
- `ishtp_hid_request()`: can sleep; it allocates with `GFP_KERNEL` for a SET.
- i2c-hid input context: `i2c_hid_irq()` is a threaded handler
  (`request_threaded_irq()` with no hard handler), so callbacks run in process
  context there; on usbhid they run from `hid_irq_in()` and `hid_ctrl()`.
- Deferred send from `raw_event`: `dualsense_parse_report()` in
  `drivers/hid/hid-playstation.c` records state under a spinlock and calls
  `dualsense_schedule_work()`; `dualsense_output_worker()` then reaches
  `hid_hw_output_report()` through `dualsense_send_output_report()`.

**Request buffers**

- Maximum length: `hdev->ll_driver->max_buffer_size` when it is non-zero,
  otherwise `HID_MAX_BUFFER_SIZE`; see `__hid_hw_raw_request()` and
  `__hid_hw_output_report()` in `drivers/hid/hid-core.c`.
- uhid: sets `max_buffer_size` to `UHID_DATA_MAX`, so the core rejects a longer
  buffer there with `-EINVAL`; it is the only transport that sets the field.
- `hid_hw_output_report()` with a NULL `buf`: rejected with `-EINVAL`, by the
  same test as in `hid_hw_raw_request()` (`len < 1`, `len` above the maximum,
  or `!buf`).
- **Unsafe usage**: passing `const` or read-only data as the buffer of a
  SET_REPORT.
  - Safe: copy the template with `kmemdup()` and free it after the call, as
    `kysona_m600_fetch_online()` in `drivers/hid/hid-kysona.c` does;
    `usbhid_set_raw_report()` and `hidp_set_raw_report()` write byte 0 of
    the buffer.
- Length for report id 0: must count the reserved byte 0; see "Report id
  byte".

## Report descriptors and fixups

**Report descriptor copies**

- `struct hid_device` holds three descriptor pointers, each with its own size
  field:

| Pointer | Set in | May equal | Freed in |
|---|---|---|---|
| `dev_rdesc` | `hid_parse_report()`, a `kmemdup()` of the transport's bytes | no earlier copy | `hid_remove_device()`, which also sets it NULL; `hiddev_free()` calls `kfree()` on it again, on NULL after `hid_remove_device()` |
| `bpf_rdesc` | `__hid_device_probe()`, from `call_hid_bpf_rdesc_fixup()` | `dev_rdesc`, when no HID-BPF rdesc program is attached or it fails; always without `CONFIG_HID_BPF` | `hid_free_bpf_rdesc()`, only if it differs from `dev_rdesc` |
| `rdesc` | `hid_open_report()` | `bpf_rdesc` (and through it `dev_rdesc`), only when the driver has no `report_fixup` | `hid_close_report()`, only if it differs from both `dev_rdesc` and `bpf_rdesc` |

- `rdesc` with a `report_fixup`: always a fresh `kmemdup()` owned by the
  core, also when the fixup returns its input unchanged.
- `rdesc` without a `report_fixup`: `hid_open_report()` makes no copy.
- `hid_close_report()`: never frees `dev_rdesc` or `bpf_rdesc`.
- `hid_free_bpf_rdesc()`: called from `__hid_device_probe()` before a
  recompute, from `hid_remove_device()` and from `hiddev_free()`.

**Fixup contract**

- Buffer passed to `report_fixup`: a temporary `kmemdup()` of `bpf_rdesc`,
  not `dev_rdesc`; `hid_open_report()` frees it itself through
  `__free(kfree)`.
- Returned pointer: has to be readable for `*size` bytes only until the
  `kmemdup()` that `hid_open_report()` runs right after the fixup returns.
- `rdesc` holds that second copy, never the pointer the fixup returned.
- Returned pointer other than the passed buffer: the core never frees it.
- NULL return: not tested and no fallback; `hid_open_report()` passes it
  straight to `kmemdup()`, which copies `*size` bytes from it.
- **Unsafe usage**: freeing the passed buffer inside `report_fixup`.
  - Safe: leave it alone and return it or another pointer, as
    `gembird_report_fixup()` in `drivers/hid/hid-gembird.c` does; the
    `__free(kfree)` on `buf` in `hid_open_report()` frees it.

**Descriptor size in a fixup**

- `hid_parse_report()` and `hid_open_report()`: test no size before the fixup
  runs, neither a minimum nor `HID_MAX_DESCRIPTOR_SIZE`.
- Zero-length and `HID_MAX_DESCRIPTOR_SIZE` tests: in individual transports,
  for example `usbhid_parse()` and `i2c_hid_parse()`; search for
  `HID_MAX_DESCRIPTOR_SIZE` to see which, since others call
  `hid_parse_report()` with no such test, for example `surface_hid_parse()`.
- Bytes passed to the fixup: a copy of `bpf_rdesc`, so the output of a HID-BPF
  program when one is attached, not always the device's bytes.
- Returned `*size`: the core checks it against nothing but zero;
  `hid_parse_collections()` returns `-EINVAL` for a 0-sized descriptor.
- Returned `*size` larger than the returned buffer: the `kmemdup()` in
  `hid_open_report()` reads past its end.

**Allocating in a fixup**

- `report_fixup`: called only from `hid_open_report()`, which returns
  `-EBUSY` while `HID_STAT_PARSED` is set, so it does not run again in a
  binding once a parse succeeded.
- `devm_kzalloc()` on `&hdev->dev` inside the fixup: lands in the devres group
  that `__hid_device_probe()` opens, released by `devres_release_group()` on
  probe failure and in `hid_device_remove()`; it does not accumulate.
- `asus_report_fixup()` in `drivers/hid/hid-asus.c` and
  `gembird_report_fixup()` in `drivers/hid/hid-gembird.c`: allocate that way,
  never free explicitly, and return the passed buffer if allocation fails.
- `drivers/hid/hid-uclogic-core.c`: `uclogic_probe()` fills
  `drvdata->desc_ptr` with `uclogic_params_get_desc()`, a `krealloc()`
  buffer, before `hid_parse()`; `uclogic_report_fixup()` returns it;
  `uclogic_remove()` frees it with `kfree(drvdata->desc_ptr)`. The `failure:`
  label of `uclogic_probe()` calls only `uclogic_params_cleanup()`, so the
  buffer is not freed when `hid_parse()` or `hid_hw_start()` fails; that is
  the first Unsafe case below, not a model to copy.
- `uclogic_params_cleanup()` in `drivers/hid/hid-uclogic-params.c`: frees
  `params->desc_ptr`, a different buffer from the `drvdata->desc_ptr` that
  `uclogic_report_fixup()` returns.
- **Unsafe usage**: a replacement from `kmalloc()` or `krealloc()` that is
  freed only in the driver's `remove`.
  - Unsafe: when probe fails after the allocation; `__hid_device_probe()`
    then runs `devres_release_group()` and `hid_close_report()`, not
    `remove`.
  - Safe: a devm allocation on `&hdev->dev`, as `asus_report_fixup()` does;
    `devres_release_group()` in `__hid_device_probe()` covers probe failure.
- **Unsafe usage**: `kmalloc()` or `kmemdup()` inside `report_fixup` with the
  result only returned, not stored or devm-managed.
  - Safe: `devm_kzalloc()` on `&hdev->dev`, as `gembird_report_fixup()` does;
    `hid_open_report()` copies the result and drops the pointer.

## Trusting the device and the descriptor

**Ownership of device fields**

- `hdev->driver_data`: belongs to the code that called
  `hid_allocate_device()` for this device and is set before
  `hid_add_device()`; the bound driver's pointer is the `hdev->dev` drvdata.
- `i2c_hid_core_probe()`: stores the `struct i2c_client *` in `driver_data`,
  not its own state struct.
- Child devices: a HID driver that allocates them is their transport, so
  `drivers/hid/hid-logitech-dj.c` and `drivers/hid/hid-steam.c` write
  `driver_data` on the devices they created, never on the one they bind to.
- **Potentially unsafe usage**: a bound driver casting `hdev->driver_data` to
  `struct usbhid_device *`.
  - Unsafe: when the only evidence is `hdev->bus == BUS_USB` or the id table;
    devices from `drivers/hid/uhid.c` and `drivers/hid/hid-logitech-dj.c`
    can carry `BUS_USB` with another type there.
  - Safe: after `hid_is_usb()` returned true, as `u2fzero_probe()` checks
    before `u2fzero_fill_in_urb()` reads it; `usbhid_probe()` is what stores
    that type and sets the `ll_driver` that `hid_is_usb()` compares.
- Driver quirk bits read during start or connect: the deadline is
  `hid_hw_start()`; `drivers/hid/hid-core.c` reads `hdev->quirks` in
  `hid_connect()`, `hid_check_device_match()` and `hid_set_group()`, not in
  `hid_open_report()`.
- `hdev->claimed`: transports write it too, zeroing it in their `->stop()`
  (for example `usbhid_stop()`); no bound driver writes it.

**Field array sizes**

- `hid_register_field()`: takes `(report, usages)` and makes one `kvzalloc()`
  holding the struct and its trailing arrays.
- `usage`, `value`, `new_value` and `usages_priorities`: each has `usages`
  entries, where `usages` is the larger of the declared usage count and
  `report_count`; that number is `field->maxusage`.
- `value` and `new_value`: not sized by `report_count`; entries from
  `report_count` up to `maxusage` exist, and the core never copies report
  data into them.
- `usage`: never has fewer than `report_count` entries.

**hid_validate_values checks**

- Range checks come first: `type > HID_FEATURE_REPORT` or
  `id >= HID_MAX_IDS` returns NULL before any lookup.
- Lookup: does not call `hid_get_report()` and ignores
  `report_enum->numbered`; a non-zero id indexes `report_id_hash[id]`
  directly, id 0 uses `list_first_entry_or_null()` on `report_list`.

**Indexing fields**

- `->raw_event()`: called from `__hid_input_report()` before
  `hid_report_raw_event()`; with no HID-BPF program attached, `data` and
  `size` are as the transport delivered them. `size` is tested only for
  non-zero, not against the report length; the report may have
  `maxfield == 0`.
- Missing field: `hid_add_field()` returns 0 when `hid_register_field()`
  fails (allocation, or `HID_MAX_FIELDS` reached), so parsing succeeds with
  fewer fields than the descriptor has main items.

**Indexing usages and values**

- `hid_set_field()` value check: no clamping and no comparison of the value
  with `logical_minimum` or `logical_maximum`.
- `hid_set_field()` on a field with `logical_minimum < 0`: returns -1 after
  `hid_err()` when the value does not fit in `report_size` bits; on other
  fields any value is stored.
- Array field (no `HID_MAIN_ITEM_VARIABLE`): the `usage[]` index is
  `value - field->logical_minimum` and must be below `field->maxusage`.
- `hid_array_value_is_valid()`: makes that check for the core but is static
  in `drivers/hid/hid-core.c`; a driver has to write the test itself.

**Inputs list and hidinput pointers**

- `hid_hw_start()` with `connect_mask` 0: skips `hid_connect()` entirely and
  succeeds if the transport's `->start()` does, as in
  `drivers/hid/hid-ft260.c`.
- `hid_connect()`: apart from an error of `hid_bpf_connect_device()`, fails
  only when `hdev->claimed` is 0 and the driver has no `raw_event`;
  `HID_CONNECT_DRIVER` alone sets `HID_CLAIMED_DRIVER`.
- `hdev->claimed & HID_CLAIMED_INPUT`: set only when `hidinput_connect()`
  returned 0, which requires a non-empty `hdev->inputs` whose entries are all
  registered.
- `hdev->inputs`: the core initialises it only at the top of
  `hidinput_connect()`; `hid_allocate_device()` leaves it zeroed.
- **Potentially unsafe usage**: `list_empty(&hdev->inputs)` as the only test
  before taking the first entry.
  - Unsafe: when `hidinput_connect()` never ran on this device (mask 0 or no
    `HID_CONNECT_HIDINPUT`); the zeroed head is not "empty" and the entry is
    computed from a NULL pointer.
  - Safe: when the driver itself passed `HID_CONNECT_HIDINPUT` to
    `hid_hw_start()`, as `lg_probe()` does before `lgff_init()`.
  - Safe: testing `HID_CLAIMED_INPUT` first, as `elo_raw_event()` does.
  - Safe: initialising the list before `hid_hw_start()`, as
    `sensor_hub_probe()` does.
- `field->hidinput`: `hidinput_configure_usage()` sets it before any mapping
  decision, for every field of input and output reports, mapped or not.
- `field->hidinput` is NULL: for feature-report fields, for output fields
  under `HID_QUIRK_SKIP_OUTPUT_REPORTS`, when `hidinput_connect()` returned
  before its report loop, and after `hidinput_cleanup_hidinput()` dropped
  that input.
- `hidinput_connect()` failure after `input_configured` ran: an
  `input_configured` error or an `input_register_device()` error goes to
  `hidinput_disconnect()`, which frees every `struct hid_input` on the list,
  including ones the driver already saved.
- Input with no capability: `hidinput_cleanup_hidinput()` frees it right
  after its `input_configured` call, also when the connect then succeeds; if
  no input is left the connect fails.
- **Potentially unsafe usage**: dereferencing `field->hidinput` or a
  `struct hid_input` saved in `input_configured` after `hid_hw_start()`
  succeeded.
  - Unsafe: when `HID_CLAIMED_INPUT` is not set; the pointer can be non-NULL
    and freed, because hidraw or `raw_event` let `hid_connect()` succeed.
  - Safe: `field->hidinput` after testing `hdev->claimed & HID_CLAIMED_INPUT`
    and the pointer for NULL, as `gyration_event()` does;
    `hidinput_cleanup_hidinput()` sets it to NULL for an input it frees.
  - Safe: a saved input after testing `hdev->claimed & HID_CLAIMED_INPUT`,
    when it is the device's only input or `input_configured` gave it a
    capability, as `asus_probe()` does before it uses `drvdata->input`.

**USB transport test**

- `hid_is_usb()`: an out-of-line function in `drivers/hid/usbhid/hid-core.c`
  with `EXPORT_SYMBOL_GPL`, so it lives in the usbhid module.
- `include/linux/hid.h`: has only the `extern` declaration, under no `#if`;
  there is no inline version and no stub for `CONFIG_USB_HID=n`.
- `usb_hid_driver`: `static const` in that file and not exported; there is no
  hid_is_using_ll_driver() in this tree.
- Inherited dependency: enough when a parent symbol depends on `USB_HID`, as
  `HID_LOGITECH_HIDPP` does through `HID_LOGITECH`.
- Callers outside `drivers/hid`: need the same dependency, as
  `SENSORS_ARCTIC_FAN_CONTROLLER` in `drivers/hwmon/Kconfig` has.

**Parent as a USB interface**

- Non-usbhid creators that can produce a `BUS_USB` device, among the callers
  of `hid_allocate_device()`:

| Creator | `bus` comes from | `dev.parent` is |
|---|---|---|
| `uhid_dev_create2()` in `drivers/hid/uhid.c` | userspace | `uhid_misc.this_device` |
| `drivers/hid/hid-logitech-dj.c` | hard-coded `BUS_USB` | the receiver's `struct hid_device` |
| `steam_create_client_hid()` in `drivers/hid/hid-steam.c` | copied from the real device | copied from the real device |

- hid-steam client device: its parent can be a real USB interface, yet
  `hid_is_usb()` is false because `ll_driver` is `steam_client_ll_driver`.
- HID-BPF: creates no devices.
- Multi-transport guard: see `asus_probe()` in `drivers/hid/hid-asus.c`,
  which tests `hid_is_usb()` beside each `to_usb_interface()`.

## The input bridge and hidraw

**Mapping callback returns**

- Before any callback: `hidinput_configure_usage()` goes to `ignore` without
  calling `input_mapping` for `HID_MAIN_ITEM_CONSTANT` fields, for
  `report_count < 1`, and for output-report usages outside `HID_UP_LED` and
  `HID_UP_HAPTIC`.
- `ignore` versus plain `return`: only `ignore` zeroes `usage->type` and
  `usage->code`; the two early returns at `mapped` leave them as written.
- `input_mapped` < 0: plain `return`, not `ignore`; `usage->type` and
  `usage->code` keep the mapping, the core does not set `usage->type` in
  `input->evbit` or `usage->code` in `*bit`, and no duplicate check runs.
- `input_mapped` is not called when `bit` is NULL at `mapped`, nor for a usage
  that went to `ignore`.
- Positive `input_mapping` with `*bit` left NULL: the generic switch is
  skipped and the core touches neither the usage nor the input device; this is
  how a driver claims a usage it handles itself, for example
  `mt_touch_input_mapping()` in `drivers/hid/hid-multitouch.c` for
  `HID_DG_CONTACTID`.
- `hid_map_usage()` failure: writes only `*bit = NULL`; `usage->type`,
  `usage->code` and `*max` keep their previous values.
- `hid_map_usage()` accepted types: `EV_ABS`, `EV_REL`, `EV_KEY`, `EV_LED`,
  `EV_MSC`; any other type, for example `EV_SW`, fails.
- **Potentially unsafe usage**: setting the code's bit in the input bitmap by
  hand, then returning positive from `input_mapping` with `*bit` non-NULL.
  - Unsafe: when `input_mapped` is absent or returns >= 0 for that usage; the
    `test_and_set_bit()` in `hidinput_configure_usage()` sees a duplicate and,
    without `HID_QUIRK_INCREMENT_USAGE_ON_DUPLICATE`, sets
    `HID_STAT_DUP_DETECTED` and zeroes `usage->type` and `usage->code`, while
    the capability bit stays set.
  - Safe: when `input_mapped` returns negative for the same usage, so the
    duplicate check never runs, as `mt_touch_input_mapping()` with
    `mt_input_mapped()` does for buttons.
  - Safe: map with `hid_map_usage_clear()` and let the core set the bit, as
    `ch_input_mapping()` in `drivers/hid/hid-chicony.c` does; the cleared bit
    makes the `test_and_set_bit()` in `hidinput_configure_usage()` return 0.

**Input splitting quirks**

- There is no hidinput_app_is_shared helper here;
  `hidinput_match_application()` in `drivers/hid/hid-input.c` does the sharing.
- Shared under `HID_QUIRK_INPUT_PER_APP`: only `HID_GD_SYSTEM_CONTROL` and
  `HID_CP_CONSUMER_CONTROL` reports, and only into a `struct hid_input` whose
  `application` is `HID_GD_KEYBOARD`; vendor-defined applications are not.
- Order dependence: the keyboard test is made per list entry, so a keyboard
  input earlier on `hid->inputs` takes those reports even if an exact match
  sits later; with no keyboard input on the list yet they get their own.
- `HID_QUIRK_INPUT_PER_APP` with `hid->maxapplication <= 1` and without
  `HID_QUIRK_MULTI_INPUT`: no matching is done and no suffix added; all
  reports share one `struct hid_input`, as with neither quirk.
- Per-application key: `report->application`, set once by
  `hid_register_report()` from the application collection around the first
  main item of that report; every field of a report goes to the same input,
  whatever its `field->application`.
- `hidinput->application`: a driver may overwrite it during mapping, which
  changes what later reports match; `mt_input_mapping()` sets it to
  `HID_DG_STYLUS` for a field whose `physical` is `HID_DG_STYLUS`.
- Both quirks set: matching is by report id only, but `hidinput_allocate()`
  still records `application` and appends the per-application name suffix,
  since it tests only `HID_QUIRK_INPUT_PER_APP` and `hid->maxapplication > 1`.

**Connecting the input layer**

- Return value: -1 on every failure, never an errno; `hid_connect()` only
  tests for non-zero.
- Decline test: scans `hid->collection[]`, not reports or usages, for an
  application or physical collection whose usage passes
  `IS_INPUT_APPLICATION()`.
- `hidinput_connect()` has no force argument; the test is
  `connect_mask & HID_CONNECT_HIDINPUT_FORCE` inside `hidinput_connect()`.
- Declined connect: returns before `report_features()`, so `feature_mapping`
  is never called for that device.
- `HID_CLAIMED_INPUT`: `hidinput_connect()` never writes `hid->claimed`;
  `hid_connect()` sets the bit on a zero return and has nothing to clear on
  failure.
- Empty test: `hidinput_has_been_populated()` ORs nine bitmaps, not just
  `evbit`; `propbit` is not among them.
- Order: `input_configured` runs before the empty test, so a non-zero return
  on an empty input still aborts the whole connect.
- All inputs dropped as empty: `hid->inputs` is empty, so the connect goes to
  `out_unwind` and returns -1.
- `hidinput_cleanup_hidinput()`: resets `field->hidinput` to NULL on matching
  fields; does not unlink `report->hidinput_list` from the freed
  `hidinput->reports`.
- `hidinput_disconnect()`: does not reset `field->hidinput`, and does not undo
  `report_features()`.
- Batteries: not cleaned by `hidinput_disconnect()`;
  `hidinput_setup_battery()` registers them as devres on `hid->dev`, so they
  outlive the unwind.
- `hid->ff_init()`: called inside the registration loop under
  `HID_CONNECT_FF`; its return value is ignored and cannot fail the connect.

**hidraw device lifetime**

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

## Quirks

**Quirk tables and lookup**

- `hid_lookup_quirk()` order: two hard-coded early returns, then the dynamic
  list, then `hid_gets_squirk()` only if no dynamic entry matched.
- Early returns consult no table and return one bit alone: USB NCR product
  range gives `HID_QUIRK_NO_INIT_REPORTS`; USB Jabra Speak 410/510 with
  `hdev->version` below a threshold gives `HID_QUIRK_IGNORE`.
- Dynamic match: the entry's `driver_data` is the whole result; it replaces.
- `hid_gets_squirk()`: adds. It ORs `hdev->initial_quirks`,
  `hid_ignore_list` (`HID_QUIRK_IGNORE`), `hid_mouse_ignore_list`
  (`HID_QUIRK_IGNORE_MOUSE`), `hid_have_special_driver`
  (`HID_QUIRK_HAVE_SPECIAL_DRIVER`) and the `hid_quirks[]` entry.
- `hdev->initial_quirks`: is the start value inside `hid_gets_squirk()`; no
  caller ORs it in. An early return or a dynamic match leaves it out.
- `initial_quirks` writers: only `i2c_hid_core_probe()` and
  `__i2c_hid_core_probe()` in `drivers/hid/i2c-hid/i2c-hid-core.c`. There is
  no usbhid_quirks_init() function.
- Dynamic entries: come from the `quirks` parameter of usbhid, not of hid;
  `hid_quirks_init()` is called only from `drivers/hid/usbhid/hid-core.c`
  with `BUS_USB`.
- Dynamic entries and `initial_quirks` together: no in-tree device has both,
  since dynamic entries match only `BUS_USB` and `initial_quirks` is set only
  on `BUS_I2C` devices.
- `hid_ignore_list` is matched twice: as a bit in `hid_gets_squirk()`, and
  directly on the last line of `hid_ignore()`, even when `HID_QUIRK_IGNORE`
  is clear.
- Direct match in `hid_ignore()`: a listed device stays ignored when a
  dynamic entry replaced the static result, and when `hid_ignore()` runs
  before any lookup, as in `hidp_setup_hid()` in `net/bluetooth/hidp/core.c`.
- `HID_QUIRK_NO_IGNORE`: the only override, tested first in `hid_ignore()`;
  nothing in the tree sets it, so only a dynamic entry can supply it.
- `hid_mouse_ignore_list`: `hid_ignore()` tests only the bit
  `HID_QUIRK_IGNORE_MOUSE`, not the list, so a dynamic entry without that bit
  un-ignores the mouse interface.
- Product ranges and name-based ignores: code in the `switch` of
  `hid_ignore()`, not entries of `hid_ignore_list`.

**Quirks set by a driver**

- `hdev->quirks` is assigned from `hid_lookup_quirk()` in two places:
  `hid_add_device()` and `__hid_device_probe()`, the second on every bind.
- `usbhid_parse()` is the third caller of `hid_lookup_quirk()`;
  `hid_ignore()` and `hid_quirks_init()` do not call it.
- Reset position in `__hid_device_probe()`: after
  `hid_check_device_match()`, so `->match()` and the
  `HID_QUIRK_IGNORE_SPECIAL_DRIVER` test see the value left by
  `hid_add_device()` or by the previous driver.
- Reset and the default probe: the reset also runs when the driver has no
  `->probe()`.
- No hid_set_quirk() helper exists; drivers write `hdev->quirks |= ...`.
- `hid_open_report()` and the parser in `drivers/hid/hid-core.c`: test no
  bit of `hdev->quirks`, so the core imposes no order relative to
  `hid_parse()`.
- Bits set between `hid_parse()` and `hid_hw_start()`: have the same effect
  as bits set before `hid_parse()`, as `HID_QUIRK_NOGET` in `mt_probe()` and
  `HID_QUIRK_INPUT_PER_APP` in `logi_dj_probe()`.
- `HID_QUIRK_INCREMENT_USAGE_ON_DUPLICATE`: tested in
  `hidinput_configure_usage()` during `hid_connect()`, not while parsing.
- HID_QUIRK_NO_EMPTY_INPUT: not defined; bit 8 is reserved in
  `include/linux/hid.h`.
- HID-BPF: nothing under `drivers/hid/bpf` names `quirks`; in
  `__hid_device_probe()` the rdesc fixup and `hid_set_group()` run before the
  reset.
- **Unsafe usage**: relying, in a bound driver, on a bit ORed into
  `hdev->quirks` before the bind, for example from `ll_driver->parse()`;
  the assignment in `__hid_device_probe()` drops every bit the lookup does
  not return.
  - Safe: set `hdev->initial_quirks` before `hid_add_device()`, as
    `i2c_hid_core_probe()` does; `hid_gets_squirk()` starts every lookup
    from it when no early return or dynamic entry applies.
  - Safe: set the bit in `->probe()`, after the reset, as
    `hid_generic_probe()` does.
- **Potentially unsafe usage**: setting a bit once `hid_hw_start()` has
  been called.
  - Unsafe: when the bit is tested once during start or connect, such as
    `HID_QUIRK_FULLSPEED_INTERVAL` in `usbhid_start()` or
    `HID_QUIRK_MULTI_INPUT` in `hidinput_connect()`.
  - Safe: when the bit is tested on each transfer, as
    `HID_QUIRK_SKIP_OUTPUT_REPORT_ID` in `usbhid_set_raw_report()` and
    `HID_QUIRK_NO_OUTPUT_REPORTS_ON_INTR_EP` in `hidraw_send_report()`;
    `sony_input_configured()` sets both during `hid_connect()`.

## HID-BPF

**Attaching programs**

- `hid_bpf_reg()` in `drivers/hid/bpf/hid_bpf_struct_ops.c` refuses, in this
  order:

  | Condition | Error |
  |---|---|
  | `ops->hdev` already set (same struct_ops attached twice) | `-EINVAL` |
  | `hid_get_device()` finds no device with that `hdev->id`, or `hid_ops` is NULL | `-EINVAL` |
  | `hdev->bpf.prog_list` already holds `HID_BPF_MAX_PROGS_PER_DEV` ops | `-E2BIG` |
  | ops has `hid_rdesc_fixup` and `hdev->bpf.rdesc_ops` is already set | `-EINVAL` |
  | ops has `hid_device_event` and `hid_bpf_allocate_event_data()` fails | `-ENOMEM` |

- `hid_bpf_reg()` returns neither `-EEXIST` nor `-ENODEV`.
- `hdev->bpf.destroyed`: `hid_bpf_reg()` does not test it.
- `hid_rdesc_fixup` is the only hook `hid_bpf_reg()` limits to one per
  device.
- Unknown bits in `flags`: refused with `-EINVAL` by
  `hid_bpf_ops_init_member()` when the map value is written, before
  `hid_bpf_reg()` runs; `hid_bpf_reg()` only tests `BPF_F_BEFORE`.
- `hid_bpf_attach_prog()`: only an `extern` declaration in
  `samples/hid/hid_bpf_helpers.h`; nothing defines it, and the samples attach
  with `bpf_map__attach_struct_ops()`.

**Programs and device lifetime**

- `hid_bpf_reconnect()` in `drivers/hid/bpf/hid_bpf_dispatch.c`: calls
  `device_reprobe()` directly, inside `hid_bpf_reg()` and `hid_bpf_unreg()`;
  there is no work item.
- `hid_bpf_reconnect()` when the reprobe bit is already set: returns 0 and
  does not reprobe; `hid_device_probe()` clears the bit.
- Reprobe bit: every user passes `ffs(HID_STAT_REPROBED)` to
  `test_and_set_bit()` or `clear_bit()`, so
  `hdev->status & HID_STAT_REPROBED` tests a different bit.
- Return value of `hid_bpf_reconnect()`: ignored by `hid_bpf_reg()` and
  `hid_bpf_unreg()`; the attach succeeds even when the reprobe fails.
- `hdev->bpf_rsize = 0` in `hid_bpf_reconnect()` is what makes the fixup run
  again: `__hid_device_probe()` in `drivers/hid/hid-core.c` calls
  `call_hid_bpf_rdesc_fixup()` only when `bpf_rsize` is 0.
- A reprobe that does not zero `bpf_rsize`, for example from
  `__hid_bus_reprobe_drivers()`, reuses the cached `hdev->bpf_rdesc`.
- Changed descriptor: `__hid_device_probe()` zeroes `hdev->group` and calls
  `hid_set_group()` before `hid_check_device_match()`, so the driver match
  is redone on the new descriptor.
- `hdev->bpf.device_data`: freed by `hid_bpf_disconnect_device()`, called
  from `hid_disconnect()`, so also during a reprobe;
  `hid_bpf_destroy_device()` does not free it.
- `hid_bpf_connect_device()`, from `hid_connect()`: allocates `device_data`
  again when an ops on `prog_list` has `hid_device_event`.
- `struct hid_bpf`: embedded in `struct hid_device` as `bpf`, under
  `CONFIG_HID_BPF`; not freed on its own.
- `__hid_bpf_ops_destroy_device()`: leaves every ops on `prog_list`; it sets
  `hdev` to NULL in each, then drops one device reference per ops after
  releasing `prog_list_lock`.
- `hdev->bpf.destroyed`: read only by `dispatch_hid_bpf_device_event()`,
  `dispatch_hid_bpf_raw_requests()` and `dispatch_hid_bpf_output_report()`,
  which fail with `-ENODEV`; `call_hid_bpf_rdesc_fixup()` does not read it.
- Attach after destroy: fails only because `hid_get_device()` no longer finds
  the device once `hid_remove_device()` has called `device_del()`.
- `hid_destroy_device()`: calls `hid_bpf_destroy_device()` before
  `hid_remove_device()`, so the driver is still bound when `destroyed` is
  set.
- Under `CONFIG_HID_BPF`, from that point `hid_hw_raw_request()` and
  `hid_hw_output_report()` fail with `-ENODEV`, with or without attached
  programs; this covers the driver's `remove` run by `device_del()`.
- Input reports from that point: `-EBUSY` from `__hid_input_report()` while
  `driver_input_lock` is held, otherwise `-ENODEV`.

**HID-BPF hooks**

| Hook | Called from | Return value | Sleepable program | Per device |
|---|---|---|---|---|
| `hid_device_event` | `dispatch_hid_bpf_device_event()`, from `__hid_input_report()` | `<0`: walk stops, event dropped, error returned; `0`: size kept; `>0`: new `ctx.size`, seen by the next program | refused by `hid_bpf_ops_check_member()` | up to the ops limit |
| `hid_rdesc_fixup` | `call_hid_bpf_rdesc_fixup()`, from `__hid_device_probe()` | `<0` or above `HID_MAX_DESCRIPTOR_SIZE`: original descriptor kept; `0`: program's buffer used at the old size; `>0`: buffer used at that size | allowed | one |
| `hid_hw_request` | `dispatch_hid_bpf_raw_requests()`, from `__hid_hw_raw_request()` | `0`: next program, then `ll_driver->raw_request()`; nonzero: walk stops, value returned, transport not called | allowed | up to the ops limit |
| `hid_hw_output_report` | `dispatch_hid_bpf_output_report()`, from `__hid_hw_output_report()` | `0`: next program, then `ll_driver->output_report()`; nonzero: walk stops, value returned, transport not called | allowed | up to the ops limit |

- Ops limit: `HID_BPF_MAX_PROGS_PER_DEV` (64) counts `struct hid_bpf_ops` on
  `hdev->bpf.prog_list`, whatever hooks each one fills; there is no per-hook
  count.
- `hid_open_report()`: does not call `hid_rdesc_fixup`; it starts from
  `hdev->bpf_rdesc`, which `__hid_device_probe()` filled before the driver's
  `probe`.
- `hid_hw_request()` in `drivers/hid/hid-core.c`: runs the `hid_hw_request`
  hook only through `__hid_request()`; when the transport has
  `ll_driver->request`, the hook is not run.
- `hid_device_event` size check: made once after the walk; a final `ctx.size`
  above `allocated_size` gives `-EINVAL`.
- `from_bpf` in `struct hid_bpf_ctx_kern`: true in a hook run that a HID-BPF
  kfunc started, whichever hook it is.
- With `from_bpf` true, `hid_bpf_hw_request()`,
  `hid_bpf_hw_output_report()`, `hid_bpf_input_report()` and
  `hid_bpf_try_input_report()` return `-EDEADLOCK` on that context.
- `KF_SLEEPABLE` kfuncs (see `hid_bpf_kfunc_ids` in
  `drivers/hid/bpf/hid_bpf_dispatch.c`): the verifier refuses them in a
  `hid_device_event` program, since that program cannot be sleepable.
- `hid_bpf_try_input_report()`: the only injecting kfunc without
  `KF_SLEEPABLE`, so the one a `hid_device_event` program can call directly.
- `hid_bpf_input_report()` from `hid_device_event`: reached through a
  `bpf_wq` callback with its own `hid_bpf_allocate_context()`; see
  `tools/testing/selftests/hid/progs/hid.c`.
- `hid_bpf_try_input_report()` inside `hid_device_event`: the nested dispatch
  zeroes and refills `hdev->bpf.device_data`, the buffer the program got
  from `hid_bpf_get_data()`, so the program must pass a copy and must not
  rely on the old contents afterwards.

## Core locks and other users

**Locks in the core**

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

**Changing the core**

- Search: `struct hid_ll_driver` over the whole tree; each definition has a
  matching `hid_allocate_device()` caller.
- Transports outside `drivers/hid/`: `net/bluetooth/hidp/core.c`,
  `drivers/staging/greybus/hid.c`, `drivers/platform/x86/asus-tf103c-dock.c`,
  `drivers/platform/x86/tuxedo/nb04/wmi_ab.c`, `sound/soc/sdca/sdca_hid.c`.
- Nothing under `drivers/input/`, `drivers/i2c/` or `drivers/usb/` defines a
  `struct hid_ll_driver`; usbhid and i2c-hid live under `drivers/hid/`.
- Non-`const` definitions: `quicki2c_hid_ll_driver`, `quickspi_hid_ll_driver`
  and `goodix_hid_ll_driver`; a search that includes `const` misses them.
- Callbacks the core calls with no NULL test: `parse`, `start`, `stop`,
  `open`, `close`. See `hid_add_device()`, `hid_hw_start()`, `hid_hw_stop()`,
  `hid_hw_open()`, `hid_hw_close()` in `drivers/hid/hid-core.c`.
- `hid_ops` direction: HID-BPF calls the core through it. The core calls
  HID-BPF directly, through exported functions, for example
  `dispatch_hid_bpf_device_event()`, `dispatch_hid_bpf_raw_requests()` and
  `dispatch_hid_bpf_output_report()`.
- `hid_ops` pointer: defined in `drivers/hid/bpf/hid_bpf_dispatch.c`, assigned
  by `hid_init()` and cleared by `hid_exit()` in `drivers/hid/hid-core.c`.
- Function members of `struct hid_ops`: four, filled from `hid_get_report()`,
  `__hid_hw_raw_request()`, `__hid_hw_output_report()` and
  `__hid_input_report()`.
- `hid_get_report()` and `__hid_input_report()`: `static` in
  `drivers/hid/hid-core.c`; none of the four has an `EXPORT_SYMBOL`.
- `hid_hw_request()`, `hid_allocate_device()` and `hid_add_device()`: not
  reached through `struct hid_ops`.
- `__hid_input_report()` and `hid_get_report()`: must not sleep. The kfunc
  `hid_bpf_try_input_report()` has no `KF_SLEEPABLE` and calls both from
  `hid_device_event` programs.
- `__hid_hw_raw_request()` and `__hid_hw_output_report()`: through
  `struct hid_ops`, reached only from kfuncs flagged `KF_SLEEPABLE`.
- `from_bpf`: the core only passes it on. The dispatch functions do not test
  it and still run the attached programs; recursion stops because a kfunc
  called with `from_bpf` set in its context returns `-EDEADLOCK`.
- `lock_already_taken` in `__hid_input_report()`: it still calls
  `down_trylock()`. If that succeeds the caller did not hold the lock; it
  releases it and returns `-EINVAL`.
- Buffer passed by the kfuncs: `hid_bpf_hw_request()` and
  `hid_bpf_hw_output_report()` pass a `kmemdup()` copy.
  `__hid_bpf_input_report()` passes the BPF buffer itself, with `bufsize`
  equal to `size`.
- No KUnit suite under `drivers/hid/` calls `hid_parse_report()` or
  `hid_open_report()`; the core parser gets no malformed descriptor from KUnit.
- There is no hid-core-test.c in `drivers/hid/`.
- Selftests built around an abnormal descriptor, both through uhid:

| Class | File | Descriptor |
|---|---|---|
| `BadReportDescriptorMouse` | `tests/test_mouse.py` | feature item with no Report Size |
| `TestCollectionOverflow` | `tests/test_hid_core.py` | well formed, deep collection nesting |

- `tests/test_usb_crash.py`: its descriptor is a plain mouse. It loads each
  installed HID module and creates a uhid device on `BUS_USB` with a vendor
  and product id from that module's aliases.
- `TestCollectionOverflow`: its own `test_rdesc` body is `pass`; it also runs
  the `test_creation` it inherits from `TestUhid` in `tests/base.py`, which
  asserts that the evdev node exists.
- `hid_bpf.c` and `hidraw.c`: both create their device from fixed arrays in
  `tools/testing/selftests/hid/hid_common.h`; `hidraw.c` uses `rdesc`,
  `hid_bpf.c` has one fixture variant for `rdesc` and one for `fido2_rdesc`.

## Model gaps

### Other mistakes models make

- Models take `hid_report_raw_event()` to take `size` only. It takes
  `bufsize` then `size`; drivers that call it directly pass six arguments, as
  in `drivers/hid/wacom_sys.c`.
- Models take `hid_hw_open()` and `hid_hw_close()` to call only the
  transport. On the first open and last close they also call the driver's
  `on_hid_hw_open` or `on_hid_hw_close`, under `ll_open_lock`, and
  dereference `hdev->driver` to do so. See `drivers/hid/hid-multitouch.c`.
- Models take `HID_CONNECT_FF` to always reach `ff_init`.
  `hidinput_connect()` skips the call when `hid_has_ff_input()` finds `EV_FF`
  already set on an input device on `hdev->inputs`.
- Models take a device to have one battery. `hid_get_battery()` in
  `include/linux/hid.h`, defined only under `CONFIG_HID_BATTERY_STRENGTH`,
  returns only the first `struct hid_battery` on `hdev->batteries`, or NULL
  when the list is empty.
- Models do not know `kzalloc_obj()`, `kzalloc_objs()` and `kmalloc_obj()`,
  used across `drivers/hid/`. They are in `include/linux/slab.h` and default to
  `GFP_KERNEL` when no flags are given.
