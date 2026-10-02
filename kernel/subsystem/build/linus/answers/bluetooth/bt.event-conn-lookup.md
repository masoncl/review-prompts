- There is no hci_conn_hash_lookup_state() here; the helpers in
  `include/net/bluetooth/hci_core.h` that take a state argument are
  `hci_conn_hash_lookup_big_state()` (`BIS_LINK` only) and
  `hci_conn_hash_list_state()`, which calls a callback for each match;
  `hci_lookup_le_connect()` has `BT_CONNECT` built in.
- `hci_event_func()`: calls the handler without `hdev->lock`;
  `hci_event_packet()` takes it only around the `hdev->recv_event` clone and
  around `hci_store_wake_reason()`, so a new handler must take
  `hci_dev_lock()` itself before a lookup.
- Helpers that look up without locking, for example `cs_le_create_conn()`:
  rely on the caller's `hci_dev_lock()`.
- `hci_conn_hold()`: increments `conn->refcnt` and cancels `disc_work`;
  `hci_conn_del()` deletes whatever `conn->refcnt` is, so a hold does not
  keep the pointer usable after `hci_dev_unlock()`.
- `hci_conn_get()`: pins the memory only; code that runs later checks
  `hci_conn_valid()` before it acts on the connection, as
  `create_big_complete()` in `net/bluetooth/hci_conn.c` does under
  `hdev->lock`; a callback that only calls `hci_conn_drop()` and
  `hci_conn_put()` makes no check, as `le_read_features_complete()` in
  `net/bluetooth/hci_sync.c`.
- Cmd_sync entry that carries the conn, queued from a handler: the queue
  site takes `hci_conn_get()`, for example `hci_le_conn_rate_request()`;
  `hci_le_read_remote_features()` in `net/bluetooth/hci_sync.c` also takes
  `hci_conn_hold()`, with `hci_conn_hold(hci_conn_get(conn))`.
- `hci_conn_failed()`: ends in `hci_conn_del()`; after either call the
  pointer is dead even though the handler still holds `hdev->lock`.
- `hci_conn_hash_lookup_handle()`: compares the full 16-bit value with no
  range check; a connection from `hci_conn_add_unset()` carries a placeholder
  above `HCI_CONN_HANDLE_MAX` until `hci_conn_set_handle()` replaces it.
- Connection-complete handlers (`hci_conn_complete_evt()`,
  `hci_sync_conn_complete_evt()`, `le_conn_complete_evt()`): look up by
  address (`hci_conn_hash_lookup_ba()`, `hci_conn_hash_lookup_role()`), not by
  the handle in the event.
- Lookup helpers return the first match only; a
  `while ((conn = lookup(...)))` loop ends only if each pass deletes the
  match or changes the field matched, as `hci_le_big_sync_lost_evt()` does
  with `hci_conn_del()`.
