- `hci_add_adv_instance()` in `net/bluetooth/hci_core.c`, new entry: needs
  `1 <= instance <= hdev->le_num_of_adv_sets + 1` and
  `hdev->adv_instance_cnt < hdev->le_num_of_adv_sets`.
- Refusal on range or count: `ERR_PTR(-EOVERFLOW)`; allocation failure:
  `ERR_PTR(-ENOMEM)`. It does not return NULL, `-EINVAL` or `-EBUSY`.
- Instance `le_num_of_adv_sets + 1`: used by `mesh_send_sync()` in
  `net/bluetooth/mgmt.c`; the MGMT add handlers reject
  `cp->instance > hdev->le_num_of_adv_sets` before they call.
- `adv->handle` is a separate member of `struct adv_info`: 0x00 when
  `le_num_of_adv_sets == 1 && instance == 1`, otherwise equal to
  `adv->instance`.
- Commands that send `adv ? adv->handle : instance`: search `adv->handle` in
  `net/bluetooth/hci_sync.c`; for example `hci_enable_ext_advertising_sync()`
  and `hci_set_ext_adv_data_sync()`.
- Commands that send the instance number unchanged: for example
  `hci_remove_ext_adv_instance_sync()`, `hci_set_adv_set_random_addr_sync()`,
  `hci_set_per_adv_params_sync()`, `hci_enable_per_advertising_sync()`.
- Handle back to entry: reply and event handlers in
  `net/bluetooth/hci_event.c` pass the handle to `hci_find_adv_instance()`,
  which compares `adv->instance`; an entry whose `adv->handle` is 0x00 is not
  found by its handle.
- `instance` argument 0x00 to `hci_disable_ext_adv_instance_sync()`: disables
  every set (`num_of_sets` 0), not handle 0x00 alone.
- `hci_disable_ext_adv_legacy_instance_sync()`: disables handle 0x00 alone,
  and sends nothing when `HCI_LE_ADV_0` is clear.
- `hci_remove_ext_adv_instance_sync()` with instance 0: disables every set,
  then removes only handle 0x00.
