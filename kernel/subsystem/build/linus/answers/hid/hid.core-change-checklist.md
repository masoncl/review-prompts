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
