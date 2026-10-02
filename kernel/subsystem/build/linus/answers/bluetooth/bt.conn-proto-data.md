- Pointer lock: the spinlock `proto_lock` in `struct hci_conn`, not
  `hdev->lock` alone.

| Pointer | Annotation | Write | Read |
|---|---|---|---|
| `l2cap_data` | `__guarded_by(&proto_lock, &hdev->lock)` | both locks | either |
| `iso_data` | `__guarded_by(&proto_lock)` | `proto_lock` | `proto_lock` |
| `sco_data` | none | no `proto_lock` use | under `hdev->lock` |

- `__guarded_by()` is compiler-checked only with
  `CONFIG_WARN_CONTEXT_ANALYSIS`; `net/bluetooth/Makefile` sets
  `CONTEXT_ANALYSIS := y`.
- `l2cap_disconn_ind()`: reads `l2cap_data` under `proto_lock` only; it runs
  from `hci_conn_timeout()` without `hdev->lock`.
- `smp_conn_security()`: reads `l2cap_data` through `context_unsafe()`; its
  caller must exclude `l2cap_conn_del()`.
- `iso_data`: cleared by `iso_conn_del()` under `hdev->lock`, and by
  `iso_conn_free()` on the last `iso_conn_put()`, with or without
  `hdev->lock`; `iso_conn_free()` clears it only if it still points at that
  `struct iso_conn`.
- `sco_data`: cleared by `sco_conn_free()`, not by `sco_conn_del()`.
- `struct hci_cb`: five callbacks only (`connect_cfm`, `disconn_cfm`,
  `security_cfm`, `key_change_cfm`, `role_switch_cfm`); no filter member; the
  `connect_cfm` and `disconn_cfm` implementations test `hcon->type`
  themselves, `l2cap_security_cfm()` and `rfcomm_security_cfm()` do not.
- `hci_cb_list`: walked under the mutex `hci_cb_list_lock`, not RCU.
- `hci_auth_cfm()`: calls nothing while `HCI_CONN_ENCRYPT_PEND` is set.
- `hci_encrypt_cfm()` in `BT_CONFIG`: calls `hci_connect_cfm()` and
  `hci_conn_drop()` instead of `security_cfm`.
- **Unsafe usage**: after `release_sock()`, `hci_dev_lock()`, `lock_sock()`,
  acting on socket state or a conn pointer read before the release.
  - Safe: recheck `sk->sk_state` is still `BT_OPEN` or `BT_BOUND`, as
    `sco_connect()` does (`-EBADFD`); `sco_chan_add()` then rejects a socket
    or conn already attached (`-EBUSY`).
  - Safe: recheck `iso_pi(sk)->conn` and its `hcon` (`-ENOTCONN`):
    `iso_sock_rebind_bc()` tests that `hcon` is unchanged,
    `iso_conn_big_sync()` that it is non-NULL; `iso_conn_del()` clears both.
  - Safe: recheck `sk->sk_state` before restoring a state set earlier, as
    `iso_sock_recvmsg()` does around `iso_conn_big_sync()`.
