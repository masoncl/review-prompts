- `l2cap_sig_channel()`, packet over `L2CAP_SIG_MTU` (48): sends one
  `L2CAP_REJ_MTU_EXCEEDED` reject and drops the whole packet;
  `l2cap_le_sig_channel()` has no such test.
- `l2cap_sig_channel()`, command with `len > skb->len` or zero ident: sends a
  reject, pulls the smaller of `len` and `skb->len`, and continues the loop.
- `l2cap_sig_channel()`, bytes left over that are fewer than
  `L2CAP_CMD_HDR_SIZE`: sends a reject with ident 0.
- `l2cap_bredr_sig_cmd()`: discards the return value of the response
  handlers, for example `l2cap_config_rsp()`, so a short response gets no
  command reject. `l2cap_le_sig_cmd()` does the same for
  `l2cap_le_connect_rsp()`.
- `l2cap_get_conf_opt()`: takes an `end` pointer and returns `-EINVAL` when
  the option header or value does not fit; callers stop on a negative return.
- `l2cap_get_conf_opt()` with `olen` other than 1, 2 or 4: `*val` is a pointer
  into the buffer; the caller compares `olen` with the destination size
  before `memcpy()`, as `l2cap_parse_conf_req()` does.
- `net/bluetooth/l2cap_core.c` does not call `skb_pull_data()`; the tests are
  explicit compares of `skb->len` and `cmd_len`, plus `pskb_may_pull()` for
  the SDU length.
- `l2cap_recv_acldata()`: takes `struct hci_dev *hdev` and a `u16 handle`,
  finds the hcon under `hci_dev_lock()`, and returns `-ENOENT` after freeing
  the skb if there is none.
- Start fragment longer than the declared frame: `skb->len` is cut to the
  declared length plus `L2CAP_HDR_SIZE`, the frame goes to
  `l2cap_recv_frame()`, and then `l2cap_conn_unreliable()` is called; the
  frame is not dropped.
- Start fragment and MTU: `l2cap_recv_acldata()` does not compare the declared
  length with `conn->mtu`.
- Start fragment shorter than `L2CAP_LEN_SIZE`: buffered in a `conn->rx_skb`
  sized from `conn->mtu`; `l2cap_recv_len()` finishes the length from the next
  fragment.
- `l2cap_recv_frame()` with `hcon->state` not `BT_CONNECTED`: queues the skb
  on `conn->pending_rx` before any length test; `process_pending_rx()` runs
  the tests later.
- `l2cap_ecred_data_rcv()`: returns a negative value only while the caller
  still owns the skb (no credits, over `chan->imtu`, over `chan->mps`, or
  `l2cap_ecred_recv()` failing on an SDU that fits one PDU); on its other
  error paths it frees the skb itself and returns 0, because
  `l2cap_data_channel()` frees the skb on a negative return.
- **Unsafe usage**: passing `l2cap_recv_frame()` an skb shorter than
  `L2CAP_HDR_SIZE`; it reads the header with no length test and ignores the
  result of `skb_pull()`.
  - Safe: `l2cap_recv_acldata()` passes a frame only when the declared length
    plus `L2CAP_HDR_SIZE` equals or was cut to `skb->len`, or when
    `conn->rx_len` has reached 0.
  - Safe: `process_pending_rx()` passes only skbs that `l2cap_recv_frame()`
    itself queued on `conn->pending_rx`.
