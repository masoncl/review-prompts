- Models take `hci_cmd_sync_cancel()` to wake the waiter itself. It queues
  `cmd_sync_cancel_work`, which wakes the waiter;
  `hci_cmd_sync_cancel_sync()` wakes the waiter directly.
- Models do not know the flag `HCI_LE_PER_ADV`.
  `hci_cc_le_set_per_adv_enable()` sets and clears it.
- Models take a handler in `net/bluetooth/hci_event.c` to store
  `adv->tx_power` from the Set Extended Advertising Parameters reply.
  `hci_set_ext_adv_params_sync()` in `net/bluetooth/hci_sync.c` stores it, for
  a non-zero instance that has an entry.
- Models take lock requirements here to be stated only by comments and
  lockdep. `net/bluetooth/Makefile` sets `CONTEXT_ANALYSIS := y`, so with
  `CONFIG_WARN_CONTEXT_ANALYSIS` the compiler checks `__must_hold()`; a
  function that locks conditionally is opted out with `__context_unsafe()`,
  for example `hci_set_ext_adv_data_sync()`.
- Models take a `struct hci_dev` that was never registered to hold nothing but
  its memory. `struct hci_dev` has `srcu`, set up in `hci_alloc_dev_priv()`.
- Models take signalling ident allocation never to fail. `l2cap_get_ident()`
  returns 0 when no ident is free in `conn->tx_ida`.
- Models write allocations here as `kzalloc()` or `kmalloc()` of a `sizeof`.
  This tree uses `kzalloc_obj()`, `kmalloc_obj()` and `kzalloc_flex()` from
  `include/linux/slab.h`, as in `mgmt_pending_new()` and
  `hci_cmd_sync_submit()`.
