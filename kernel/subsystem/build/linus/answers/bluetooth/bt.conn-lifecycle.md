- `HCI_CONN_HANDLE_UNSET()`: a predicate (`handle > HCI_CONN_HANDLE_MAX`), not
  a value; each conn from `hci_conn_add_unset()` has its own placeholder from
  `hdev->unset_handle_ida`.
- `hci_conn_hash_lookup_handle()`: also finds a conn by its placeholder;
  `hci_abort_conn_sync()` depends on that.
- `hci_conn_del()` sleeps (`disable_delayed_work_sync()`,
  `synchronize_rcu()`); it cannot run inside `rcu_read_lock()` or under a
  spinlock.
- `le_conn_timeout`: only `cancel_delayed_work()`, only for `LE_LINK`; a
  running `le_conn_timeout()` is not waited for, and for `HCI_ROLE_SLAVE` it
  takes `hci_dev_lock()`.
- `hci_conn_unlink()` is the first step of `hci_conn_del()`; on a parent it
  unlinks every child, and with `HCI_UP` set it can delete children too,
  through `hci_conn_cleanup_child()` -> `hci_conn_failed()`, for example a SCO
  child whose handle is still unset.
- **Potentially unsafe usage**: calling `hci_conn_del()` while iterating
  `hdev->conn_hash.list`.
  - Unsafe: when a deleted entry can be a parent in `hci_conn_link()`; the
    child it deletes may be the saved next entry.
  - Safe: re-read the first entry each round, as `hci_conn_hash_flush()` does.
  - Safe: delete only `CIS_LINK` entries, as `hci_unbound_cis_failed()` does;
    no `hci_conn_link()` caller passes a CIS as parent.
- Initial reference: dropped in `hci_conn_del_sysfs()` (`put_device()` or
  `device_unregister()`), not by `hci_conn_put()`; without another
  `hci_conn_get()` reference `bt_link_release()` frees the conn before
  `hci_conn_del()` returns.
- RCU: `hci_conn_hash_del()` runs `synchronize_rcu()` before that reference is
  dropped, so `hci_conn_get()` on an entry found inside `rcu_read_lock()` is
  safe, as in `hci_disconnect_all_sync()`.
- Lookup helpers return the pointer after `rcu_read_unlock()` with no
  reference; it stays valid only while the caller holds `hdev->lock`.
- `hci_cmd_sync_dequeue(hdev, NULL, conn, NULL)`: removes only queued entries
  whose `data` is the conn itself, calling their destroy with `-ECANCELED`.
- Entries that wrap the conn stay queued, for example
  `struct le_conn_update_data`; that entry holds `hci_conn_get()`, and
  `le_conn_update_sync()` tests `hci_conn_valid()` under `hdev->lock`.
- `hci_conn_del()` calls neither `hci_disconn_cfm()` nor `hci_connect_cfm()`
  for the conn it deletes; a caller whose conn the upper layers may know does
  so first, as `hci_conn_hash_flush()` and `hci_conn_failed()` do.
