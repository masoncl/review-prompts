- Driver hooks: there is no hci_dev_driver_ops structure; `open`, `close`,
  `send`, `setup` and the rest are function-pointer members of
  `struct hci_dev` itself.
- `struct hci_drv` (`include/net/bluetooth/hci_drv.h`): optional driver
  table of handlers for `HCI_DRV_PKT`; `hci_send_frame()` hands such a
  packet to `hci_drv_process_cmd()` and never to `hdev->send`.
- `struct hci_chan`: the ACL/LE transmit queue of one `struct l2cap_conn`,
  not an AMP leftover; `hci_chan_create()` is called only from
  `l2cap_conn_add()`, and `hci_chan_sent()` schedules from it.
- SCO and ISO data: queued on `data_q` of the `struct hci_conn` itself, with
  no `struct hci_chan`; see `hci_send_sco()` and `hci_send_iso()`.
- `struct hci_request`: the only instance is a local in
  `__hci_cmd_sync_sk()` (`net/bluetooth/hci_sync.c`); there is no
  hci_request.c, and the helpers that fill a request are static in that
  file.
- `struct hci_conn` counts: `hci_conn_hold()` and `hci_conn_drop()` count
  users of the link and do not pin memory; at zero `hci_conn_drop()` queues
  `disc_work`.
- Who holds what on a `struct hci_conn`: `struct l2cap_conn` takes
  `hci_conn_get()` only; each `struct l2cap_chan` takes `hci_conn_hold()` in
  `__l2cap_chan_add()`, a fixed channel only with `FLAG_HOLD_HCI_CONN`.
- `struct sco_conn` and `struct iso_conn`: carry a keep-link-up count
  (`sco_conn_free()` and `iso_conn_free()` call `hci_conn_drop()`) and take no
  `hci_conn_get()`; each serves one socket.
- Link types: ISO is split into `CIS_LINK`, `BIS_LINK` and `PA_LINK`
  (`include/net/bluetooth/hci.h`); a `PA_LINK` conn is a periodic advertising
  sync; there is no generic ISO link type.
- `struct hci_link`: the parent is the ACL for SCO, the LE link for a CIS, and
  another BIS of the same BIG for a BIS (`hci_bind_bis()`).
- Removed channel test: check `FLAG_DEL` under the channel lock, as
  `l2cap_chan_conn()` in `net/bluetooth/l2cap_sock.c` does; `chan->conn` is
  NULL only before `__l2cap_chan_add()`.
- `chan->data` for L2CAP sockets: the `struct sock`; `l2cap_sock_put_chan()`
  sets it to NULL, and `struct l2cap_ops` callbacks in
  `net/bluetooth/l2cap_sock.c` test it, for example `l2cap_sock_recv_cb()`
  and `l2cap_sock_close_cb()`.
- `chan->data` for SMP: `struct smp_chan` on the per-connection channel
  `conn->smp`, and only while pairing runs; `struct smp_dev` on the listening
  channel in `hdev->smp_data`; NULL on `hdev->smp_bredr_data`.
- `chan->data` for 6LoWPAN: the skb being sent (`send_pkt()`); per-channel
  state is `struct lowpan_peer`, found by `__peer_lookup_chan()`.
- RFCOMM, BNEP and HIDP: hold a `struct socket` but reach through
  `l2cap_pi(sk)->chan` to the channel and its `struct l2cap_conn`.
- `struct l2cap_user`: probe and remove pair hung on a `struct l2cap_conn`;
  `l2cap_conn_del()` calls every `remove`; HIDP is the in-tree user.
- CMTP: not implemented in this tree; only `BTPROTO_CMTP` remains.
- HCI socket state: `struct hci_pinfo` in `net/bluetooth/hci_sock.c`; there is
  no hci_sock structure.
- `struct hci_uart`: defined in `drivers/bluetooth/hci_uart.h`; shared by
  `drivers/bluetooth/hci_ldisc.c` and `drivers/bluetooth/hci_serdev.c`.
