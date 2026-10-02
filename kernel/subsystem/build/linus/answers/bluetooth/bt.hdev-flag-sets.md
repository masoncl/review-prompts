- `HCI_UP`, `HCI_INIT`, `HCI_RUNNING`, `HCI_RAW` and the other bits of that
  enum: live in `hdev->flags` only, with no accessor macro that takes a bit
  number; the `dev_flags` enum starts at `HCI_SETUP`.
- Enum order in `include/net/bluetooth/hci.h`: quirks, `flags` bits, socket
  flags, `dev_flags` bits; all four are anonymous and number from 0.
- Socket flags (`HCI_SOCK_TRUSTED`, `HCI_MGMT_INDEX_EVENTS`, ...): belong to
  `hci_sock_set_flag()` and `hci_sock_test_flag()`, not to `struct hci_dev`.
- Membership check: none. The accessors in
  `include/net/bluetooth/hci_core.h` are macros that pass `nr` unchanged to
  `set_bit()`, `test_bit()` and friends; there is no `BUILD_BUG_ON()` and no
  test against `__HCI_NUM_FLAGS` or `__HCI_NUM_QUIRKS`.
- Value reported to user space: `hci_get_dev_info()` and
  `hci_get_dev_list()` clear `HCI_UP` in the copy while `HCI_AUTO_OFF` is
  set, so the reported word is not always `hdev->flags`.
- `hdev->conn_flags`: `hci_conn_flags_t` is `u8`; `enum hci_conn_flags`
  values are already `BIT()` masks, combined with `|` and `&`, never passed
  to a bitop as a bit number.
- **Unsafe usage**: passing a bit of one enum to the accessor of another
  set; it compiles and touches an unrelated bit, because the enums overlap.
  - Safe: `test_bit(HCI_INIT, &hdev->flags)` next to
    `hci_dev_test_flag(hdev, HCI_SETUP)`, as `hci_unregister_dev()` does.
  - Safe: `hci_test_quirk()` with an `HCI_QUIRK_` name, as
    `hci_register_dev()` does.
