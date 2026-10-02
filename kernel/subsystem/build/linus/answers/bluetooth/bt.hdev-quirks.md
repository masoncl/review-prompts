- `struct hci_dev` has no member named quirks; the bits are in
  `quirk_flags`, a `DECLARE_BITMAP()` of `__HCI_NUM_QUIRKS` bits.
- `hci_set_quirk()`, `hci_clear_quirk()`, `hci_test_quirk()`: macros in
  `include/net/bluetooth/hci_core.h`; no driver in the tree uses a raw bitop
  on `quirk_flags`.
- `DEFINE_QUIRK_ATTRIBUTE()` in `net/bluetooth/hci_debugfs.c`: the one place
  with raw bitops on `quirk_flags`; a debugfs write flips
  `HCI_QUIRK_STRICT_DUPLICATE_FILTER` or `HCI_QUIRK_SIMULTANEOUS_DISCOVERY`,
  and returns `-EBUSY` while `HCI_UP` is set.
- `hci_clear_quirk()`: used by `drivers/bluetooth/btusb.c`, so a quirk set at
  probe can be gone after setup.
- Timing: nothing in the code enforces the "must be set before
  hci_register_dev" comments in `include/net/bluetooth/hci.h`.
- `hci_register_dev()` reads `HCI_QUIRK_RAW_DEVICE` itself and
  `HCI_QUIRK_NO_SUSPEND_NOTIFIER` through `hci_register_suspend_notifier()`;
  setting either from the `setup` callback is too late for those tests.
- `hci_dev_setup_sync()` in `net/bluetooth/hci_sync.c`: tests quirks after
  `hdev->setup()` returns, and `hci_init_sync()` runs after that, so a quirk
  set in `setup` is seen by the init stages.
- `hci_broken_table`: logs only the quirks listed in it; for example
  `HCI_QUIRK_BROKEN_EXT_SCAN` is not listed and is never logged.
