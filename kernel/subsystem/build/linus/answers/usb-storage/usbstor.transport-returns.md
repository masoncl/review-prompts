- `usb_stor_ctrl_transfer()`: returns `USB_STOR_XFER_*`, not an errno;
  `usb_stor_control_msg()` is the control helper that returns the length or a
  negative errno.
- `usb_stor_invoke_transport()`, first test after `us->transport()` returns:
  `US_FLIDX_TIMED_OUT` (not `US_FLIDX_ABORTING`); if set the result is
  `DID_ABORT << 16` and it goes to `Handle_Errors`, whatever was returned.
- Reaction to each transport value:

| Value | `usb_stor_invoke_transport()` |
|---|---|
| `USB_STOR_TRANSPORT_GOOD` | `SAM_STAT_GOOD`; auto-sense only when the protocol is `USB_PR_CB` or `USB_PR_DPCM_USB` and the direction is not `DMA_FROM_DEVICE`, or with `US_FL_SENSE_AFTER_SYNC` on `SYNCHRONIZE_CACHE` |
| `USB_STOR_TRANSPORT_FAILED` | REQUEST SENSE through `us->transport()`; when that returns `USB_STOR_TRANSPORT_GOOD`, `SAM_STAT_CHECK_CONDITION`, or `DID_ERROR << 16` when the sense is empty and the command is not `ATA_12` or `ATA_16` |
| `USB_STOR_TRANSPORT_NO_SENSE` | `SAM_STAT_CHECK_CONDITION`, `last_sector_hacks()`, return; the transport has already filled `srb->sense_buffer` |
| `USB_STOR_TRANSPORT_ERROR` | `DID_ERROR << 16`, `Handle_Errors` |
| any other value | no default case: it matches none of the tests, so `srb->result` is set to `SAM_STAT_GOOD` and the value triggers no auto-sense and no reset |

- The two families overlap in value: `USB_STOR_XFER_SHORT` equals
  `USB_STOR_TRANSPORT_FAILED`, `USB_STOR_XFER_STALLED` equals
  `USB_STOR_TRANSPORT_NO_SENSE`, `USB_STOR_XFER_LONG` equals
  `USB_STOR_TRANSPORT_ERROR`.
- **Unsafe usage**: returning a `USB_STOR_XFER_*` value other than
  `USB_STOR_XFER_GOOD`, or a negative errno, from `us->transport()`.
  - Unsafe: `USB_STOR_XFER_ERROR` (4) and any errno match none of the tests in
    `usb_stor_invoke_transport()` and leave `SAM_STAT_GOOD`; values 1 to 3 are
    taken as the transport code with the same number.
  - Safe: map the transfer result first, as `usb_stor_Bulk_transport()` and
    `usb_stor_CB_transport()` do.
- `us->transport_reset()` result: `device_reset()` treats only a negative value
  as failure; `Handle_Errors` ignores it.
- `interpret_urb_result()`: has no case for `-ENOENT` (what `usb_kill_urb()`
  leaves); it falls to the default and gives `USB_STOR_XFER_ERROR`.
