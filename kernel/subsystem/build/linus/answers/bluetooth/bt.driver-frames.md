- `send` is not called in two cases, and the core frees the skb in both:
  `HCI_RUNNING` clear (returns `-EINVAL`), and packet type `HCI_DRV_PKT`,
  which goes to `hci_drv_process_cmd()`.
- `hci_recv_frame()` does not call `skb_orphan()`; it sets
  `bt_cb(skb)->incoming` and the timestamp. `skb_orphan()` is in
  `hci_send_frame()`.
- Accepted by `hci_recv_frame()`: `HCI_EVENT_PKT`, `HCI_ACLDATA_PKT`,
  `HCI_SCODATA_PKT`, `HCI_ISODATA_PKT`, `HCI_DRV_PKT`.
- The type tested is the one returned by the driver's `classify_pkt_type`
  callback, when the driver sets one; a callback that returns
  `HCI_DIAG_PKT` or `HCI_VENDOR_PKT` gets the frame freed with `-EINVAL`,
  not delivered as a diagnostic frame.
- `-ENXIO` test runs first: a frame of an unaccepted type on a controller
  that is neither `HCI_UP` nor `HCI_INIT` returns `-ENXIO`, not `-EINVAL`.
- **Potentially unsafe usage**: `kfree_skb()` after `hci_recv_frame()`
  returned an error.
  - Unsafe: on the skb that was passed in; `hci_recv_frame()` already freed
    it on both error paths.
  - Safe: on a separate clone made before the call, as
    `btmtk_usb_wmt_recv()` in `drivers/bluetooth/btmtk.c` frees
    `data->evt_skb`.
