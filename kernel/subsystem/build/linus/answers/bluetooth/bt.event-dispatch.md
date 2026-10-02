- `hci_event_packet()`: before it calls `hci_event_func()` it checks only
  that `skb->len` is at least `sizeof(struct hci_event_hdr)` and that
  `hdr->evt` is not 0; it does not read `hdr->plen`.
- `skb->len > max_len`: `hci_event_func()` only warns and still calls the
  handler; `hci_le_meta_evt()` and `hci_cc_func()` do the same.
- Pull before the handler runs: exactly `min_len` bytes; the handler gets
  both `data` (the fixed part) and `skb`, which now starts at the first byte
  after `min_len`.
- `max_len` of variable-length entries: an argument of the macro, not fixed
  by it; `hci_ev_table[]` entries pass `HCI_MAX_EVENT_PLEN` (255),
  `hci_le_ev_table[]` and `hci_cc_table[]` entries pass
  `HCI_MAX_EVENT_SIZE` (260).
- Entries with `req` set: three, not two; `hci_le_meta_evt()` is registered
  with `HCI_EV_REQ_VL()` alongside `hci_cmd_complete_evt()` and
  `hci_cmd_status_evt()`.
- Handler signatures differ by table:

| Table | Handler takes | Returns |
|---|---|---|
| `hci_ev_table[]`, `req` clear | `(hdev, data, skb)` | nothing |
| `hci_ev_table[]`, `req` set | the same plus `opcode`, `status`, `req_complete`, `req_complete_skb` | nothing |
| `hci_le_ev_table[]` | `(hdev, data, skb)` | nothing |
| `hci_cc_table[]` | `(hdev, data, skb)` | `u8` status |
| `hci_cs_table[]` | `(hdev, status)` | nothing |

- `hci_cc_table[]` handler return value: `hci_cmd_complete_evt()` stores it
  in `*status`, so it is the status the pending request completes with, not
  only a log value.
- `HCI_EV_VENDOR`: registered with `min_len` 0, so `hci_vendor_evt()` runs
  with nothing validated or pulled.
