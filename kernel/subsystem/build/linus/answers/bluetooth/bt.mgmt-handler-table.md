- Header tests in `hci_mgmt_cmd()` (`net/bluetooth/hci_sock.c`): a short
  header, or `hdr->len` not equal to the payload length, returns `-EINVAL`
  to `sendmsg()` and sends no status event.
- `HCI_MGMT` is not tested by `hci_mgmt_cmd()`; the device-state tests are
  `HCI_SETUP`, `HCI_CONFIG`, `HCI_USER_CHANNEL` and `HCI_UNCONFIGURED` only.
- `HCI_MGMT_HDEV_OPTIONAL`: skips only the test that the presence of `hdev`
  matches `HCI_MGMT_NO_HDEV`.
- With `HCI_MGMT_HDEV_OPTIONAL` and an index other than `MGMT_INDEX_NONE`:
  the lookup and the device-state tests still run, so a bad index still
  gets `MGMT_STATUS_INVALID_INDEX`.
- Handler of an `HCI_MGMT_HDEV_OPTIONAL` entry: must accept `hdev == NULL`.
- `mgmt_event()` and `mgmt_event_skb()` in `net/bluetooth/mgmt.c`: take no
  flag and always send with `HCI_SOCK_TRUSTED`.
- `mgmt_limited_event()` and `mgmt_index_event()`: take the socket flag as
  an argument; these are the ones that can reach a socket that is not
  trusted.
- Delivery of a limited event: `__hci_send_to_channel()` skips every socket
  that lacks the flag, so a new flag reaches no socket until code sets it.
- Flags set at bind: `hci_sock_bind()` sets six event flags, for example
  `HCI_MGMT_INDEX_EVENTS` and `HCI_MGMT_SETTING_EVENTS`, on every
  `HCI_CHANNEL_CONTROL` socket, trusted or not.
- Other event flags: set on the calling socket by a command handler or its
  completion callback, for example `read_ext_controller_info()` sets
  `HCI_MGMT_EXT_INFO_EVENTS` and clears two of the bind-time flags.
- `mgmt_commands[]`, `mgmt_events[]`, `mgmt_untrusted_commands[]` and
  `mgmt_untrusted_events[]`: maintained by hand; `read_commands()` copies
  them verbatim and nothing checks them against `mgmt_handlers`.
- `MGMT_OP_READ_VERSION` and `MGMT_OP_READ_COMMANDS`: have
  `HCI_MGMT_UNTRUSTED` in `mgmt_handlers` and are in neither command array.
