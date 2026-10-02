- **Potentially unsafe usage**: indexing a counted array, or reading a
  trailing block, that lies beyond the `min_len` the dispatcher pulled.
  - Unsafe: when nothing has compared the count times the element size, or
    the block length, with `skb->len`; the read runs past the end of the skb.
  - Safe: after pulling the whole array, as `hci_num_comp_pkts_evt()` does
    with `hci_ev_skb_pull()` and
    `flex_array_size(ev, handles, ev->num)`; indexing `ev->handles[i]` is
    then correct. `skb_pull_data()` returns NULL when `skb->len` is short.
  - Safe: after comparing `skb->len` with the array size without a pull, as
    `hci_cc_le_read_conn_interval()` does with `flex_array_size()` and
    `hci_cc_le_set_cig_params()` does with `array_size()`.
- **Potentially unsafe usage**: calling `hci_proto_connect_ind()` for an
  event whose trailing data `iso_connect_ind()` reads.
  - Unsafe: when the handler has not checked the trailing length against the
    skb first; `hci_recv_event_data()` returns a pointer into
    `hdev->recv_event` with no length check, and `iso_connect_ind()` in
    `net/bluetooth/iso.c` copies `ev3->length` bytes from it.
  - Safe: after pulling `ev->length`, as `hci_le_per_adv_report_evt()` does
    before the call.
- Count field of `struct hci_ev_num_comp_pkts` and
  `struct hci_ev_le_ext_adv_report`: `num`; `hci_le_adv_report_evt()` and
  `hci_le_ext_adv_report_evt()` loop with `while (ev->num--)`.
- `hci_le_ext_adv_report_evt()`: has no length-limit check of its own;
  `process_adv_report()` drops a report with `len > max_adv_len(hdev)`.
- There is no hci_le_past_report_evt() here; `hci_le_past_received_evt()` is
  a fixed-length entry, and `hci_le_per_adv_report_evt()` is a handler with
  a trailing data block.
- `__counted_by()` in `include/net/bluetooth/hci.h`: only on command
  structs, for example `struct hci_cp_le_set_cig_params`; the event structs'
  flexible arrays are not annotated, so no compiler bound backs the
  handler's own check.
- `hci_le_big_sync_established_evt()`: uses `ev->num_bis` to size its pull,
  to match `conn->num_bis` in `hci_conn_hash_lookup_big_sync_pend()` and to
  bound its loops over `ev->bis[]`; the `ISO_MAX_NUM_BIS` bound is checked in
  `hci_conn_big_create_sync()`, on the command side.
