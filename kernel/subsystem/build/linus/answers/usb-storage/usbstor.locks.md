- `struct us_data` has one lock member, `dev_mutex`, and no spinlock member of
  its own.
- `usb_stor_reset_resume()`: does not take `dev_mutex`; it only calls
  `usb_stor_report_bus_reset()`.
- `usb_stor_probe1()` and `usb_stor_probe2()`: do not take `dev_mutex`;
  `usb_stor_scan_dwork()` does, around `usb_stor_Bulk_max_lun()`.
- `usb_stor_disconnect()`: never takes `dev_mutex`; `kthread_stop()` in
  `usb_stor_release_resources()` is what waits for a running command before
  the URB and buffers are freed.
- Sub-drivers take `dev_mutex` too; search `drivers/usb/storage/` for
  `dev_mutex`.
- `dflags` bits and the host lock:

| Bit | Set in | Cleared in | Host lock at every site |
|---|---|---|---|
| `US_FLIDX_URB_ACTIVE` | `usb_stor_msg_common()` | same; `usb_stor_stop_transport()` | no; only the `usb_stor_stop_transport()` site, through its caller |
| `US_FLIDX_SG_ACTIVE` | `usb_stor_bulk_transfer_sglist()` | same; `usb_stor_stop_transport()` | no; as above |
| `US_FLIDX_ABORTING` | `command_abort_matching()` | `usb_stor_control_thread()`; `Handle_Errors`; `isd200_invoke_transport()` | no; the first three sites hold it, `isd200_invoke_transport()` does not |
| `US_FLIDX_DISCONNECTING` | `quiesce_and_remove_host()`, twice | never | no; the first set (device `USB_STATE_NOTATTACHED`) is unlocked |
| `US_FLIDX_RESETTING` | `Handle_Errors` | end of `usb_stor_invoke_transport()` | no; set locked, cleared unlocked |
| `US_FLIDX_TIMED_OUT` | `command_abort_matching()` | `usb_stor_control_thread()` | yes |
| `US_FLIDX_SCAN_PENDING` | `usb_stor_probe2()` | `usb_stor_scan_dwork()` | no |
| `US_FLIDX_REDO_READ10` | `usb_stor_probe2()`; `usb_stor_invoke_transport()` | `usb_stor_invoke_transport()` | no |
| `US_FLIDX_READ10_WORKED` | `usb_stor_invoke_transport()` | `usb_stor_invoke_transport()` | no |

- US_FLIDX_DONT_SCAN is not defined in this tree.
- `last_sector_hacks()`: touches no `dflags` bit.
- `command_abort_matching()` tests `US_FLIDX_RESETTING` and sets
  `US_FLIDX_ABORTING`, and `Handle_Errors` sets `US_FLIDX_RESETTING` and
  clears `US_FLIDX_ABORTING`, each inside one host-lock section; that pairing
  is what the host lock gives these bits.
