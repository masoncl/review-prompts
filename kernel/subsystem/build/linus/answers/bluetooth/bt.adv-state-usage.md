- `HCI_LE_ADV_0` in `include/net/bluetooth/hci.h`: tracks the enable and
  disable commands that name handle 0x00 on a controller with extended
  advertising.
- `HCI_LE_ADV_0` writers: `hci_cc_le_set_ext_adv_enable()` sets or clears it
  when a command with `num_of_sets` non-zero names handle 0x00 and the lookup
  finds no entry; `hci_resume_advertising_sync()` clears it.
- `HCI_LE_ADV_0` after a disable with `num_of_sets == 0`: still set; that
  reply clears every `adv->enabled` and `HCI_LE_ADV` only.
- `HCI_LE_ADV`: set by every successful enable reply, for any handle; it is
  not specific to instance zero.
- `HCI_LE_ADV` clear while an `adv->enabled` is true: `le_conn_complete_evt()`
  clears `HCI_LE_ADV` on success status and writes no `adv->enabled`.
- `adv->enabled`: set by `hci_cc_le_set_ext_adv_enable()` for any entry found,
  periodic or not; `periodic_enabled` is separate, kept by
  `hci_cc_le_set_per_adv_enable()`.
- `adv->enabled`: written only by `hci_cc_le_set_ext_adv_enable()` and
  `hci_le_ext_adv_term_evt()`; `hci_cc_le_set_adv_enable()` maintains
  `HCI_LE_ADV` only.
- Entry with `adv->handle` 0x00 (`le_num_of_adv_sets == 1`, instance 1): its
  enable and disable replies change `HCI_LE_ADV_0`, not `adv->enabled`.
- **Unsafe usage**: testing `HCI_LE_ADV` to decide that handle 0x00 is enabled
  on a controller with extended advertising; an enable of any set sets
  `HCI_LE_ADV`.
  - Safe: test `HCI_LE_ADV_0`, which `hci_cc_le_set_ext_adv_enable()` writes
    only for handle 0x00, as `hci_disable_ext_adv_legacy_instance_sync()`
    does; the flag can be set while handle 0x00 is off, and that function then
    sends a disable for handle 0x00.
- **Unsafe usage**: reading a `struct adv_info` outside `hci_dev_lock()` while
  a reply or event handler can run; `hci_remove_adv_instance()` frees the
  entry, for example from `hci_le_ext_adv_term_evt()`.
  - Safe: look up and read under `hci_dev_lock()`, and unlock before sending
    the command, as `hci_set_ext_adv_data_sync()` does.
- Set Ext Adv Params reply: there is no hci_cc_set_ext_adv_param() here;
  `hci_set_ext_adv_params_sync()` in `net/bluetooth/hci_sync.c` parses the
  reply and stores `hdev->adv_tx_power` for instance 0.
- `hci_cc_le_set_adv_set_random_addr()`: returns without storing anything
  when the handle is 0.
- `hdev->random_addr` for instance zero: stored by
  `hci_cc_le_set_random_addr()`; `hci_set_adv_set_random_addr_sync()` calls
  `hci_set_random_addr_sync()` first when the instance is 0, which sends
  `HCI_OP_LE_SET_RANDOM_ADDR` unless it defers the update.
