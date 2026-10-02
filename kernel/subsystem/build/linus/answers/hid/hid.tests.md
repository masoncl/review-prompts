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
