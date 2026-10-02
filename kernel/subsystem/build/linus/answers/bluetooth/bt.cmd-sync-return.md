- Controller error status: `__hci_cmd_sync_sk()` returns
  `ERR_PTR(-bt_to_errno(hdev->req_result))`; `bt_to_errno()` returns a
  positive errno.
- `__hci_cmd_sync_status()` and `hci_cmd_sync_status()` on success: return
  `skb->data[0]` unchanged, so the result can be a positive HCI status; test
  for non-zero, not for negative.
- `mgmt_status()` and `bt_status()`: accept both a negative errno and a
  positive HCI status.
- `hci_cmd_sync_cancel()`: stores `err` unchanged in `hdev->req_result`, and
  `__hci_cmd_sync_sk()` negates it; pass a positive errno, as
  `hci_cmd_sync_cancel(hdev, ECANCELED)` in `net/bluetooth/hci_sync.c`.
- `hci_cmd_sync_cancel()` with a negative errno: the waiter gets
  `ERR_PTR(-ENODATA)`, which the status variants return as 0.
- `hci_cmd_sync_cancel_sync()`: accepts either sign and stores the positive
  value.
