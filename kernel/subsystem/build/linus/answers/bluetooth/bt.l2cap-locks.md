- `struct l2cap_conn`: one mutex, `conn->lock`; there is no chan_lock or
  ident_lock field.
- `conn->lock` covers `conn->chan_l`, `conn->rx_skb`, `conn->rx_len` and
  `conn->users`.
- `conn->hchan`: cleared under `conn->lock` in `l2cap_conn_del()` and tested
  under it in `l2cap_register_user()`.
- Signalling idents: allocated from the IDA `conn->tx_ida` in
  `l2cap_get_ident()`, with no mutex of their own.
- `l2cap_recv_acldata()`: calls `hci_dev_unlock()` before it takes
  `conn->lock`; the reference from `l2cap_conn_hold_unless_zero()`, taken
  under the device lock, keeps the conn alive across the gap.
- Device lock outside `conn->lock`: see `l2cap_chan_connect()`, and
  `l2cap_conn_del()` and `l2cap_security_cfm()`, both marked
  `__must_hold(&hcon->hdev->lock)`.
- `l2cap_chan_add()`: takes `conn->lock`. `__l2cap_chan_add()` and
  `l2cap_chan_del()` link and unlink `conn->chan_l` and do not take
  `conn->lock`.
- `l2cap_chan_timeout()` and `l2cap_sock_shutdown()`: take `conn->lock`, then
  the channel lock, before `l2cap_chan_close()`; `l2cap_sock_shutdown()`
  skips `conn->lock` when `l2cap_conn_hold_unless_zero()` returned NULL.
- Per-connection lookups that return a referenced, locked channel:
  `l2cap_get_chan_by_scid()` and `l2cap_get_chan_by_dcid()`. Neither takes
  `conn->lock`; the caller holds it.
- There is no l2cap_get_chan_by_ident() here. Callers of
  `__l2cap_get_chan_by_ident()`, for example `l2cap_connect_create_rsp()`, call
  `l2cap_chan_hold_unless_zero()` and `l2cap_chan_lock()` themselves.
- `chan_list_lock`: rwlock for the global `chan_list`.
  `l2cap_global_chan_by_psm()` and `l2cap_global_fixed_chan()` return a
  referenced channel that is not locked.
- `l2cap_chan_lock()`: `mutex_lock_nested()` with subclass `chan->nesting`, an
  `atomic_t` that `l2cap_chan_create()` sets to `L2CAP_NESTING_NORMAL`.
- Listening channel: set to `L2CAP_NESTING_PARENT`, as `l2cap_sock_listen()`
  does. `smp_new_conn_cb()` sets `L2CAP_NESTING_SMP`.
- `l2cap_chan_ops` callbacks: `l2cap_sock_teardown_cb()` takes the socket with
  `lock_sock_nested()` at `chan->nesting`; the others that lock the socket,
  for example `l2cap_sock_state_change_cb()`, use `lock_sock()`.
- `l2cap_sock_getsockopt()` and `l2cap_sock_setsockopt()`: take the channel
  lock first, then `lock_sock()`.
- **Unsafe usage**: taking `conn->lock` while holding a socket lock or a
  channel lock.
  - Safe: release both first, as `l2cap_sock_shutdown()` does: it pins the
    conn with `l2cap_conn_hold_unless_zero()` under the channel lock, drops
    that lock, then takes `conn->lock` and the channel lock.
    `l2cap_chan_timeout()` defines the order: `conn->lock`, channel lock, then
    `chan->ops->close()`, which takes the socket lock.
  - Safe: defer the close, as `l2cap_sock_cleanup_listen()` does under the
    parent socket lock: it arms `__set_chan_timer()` with timeout 0, and
    `l2cap_chan_timeout()` closes the channel under `conn->lock`.
