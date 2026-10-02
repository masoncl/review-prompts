- Tag table: `devinfo->cmnd[]` in `struct uas_dev_info`, slot index
  `uas_tag - 1`; there is no uas_find_uas_cmnd() here, and
  `struct uas_cmd_info` has no list member. `uas_stat_cmplt()` indexes the
  array with the tag from the IU.
- `devinfo->shutdown`: not covered by `devinfo->lock`; `uas_shutdown()`
  writes it and `uas_pre_reset()` / `uas_post_reset()` read it unlocked.
- `uas_submit_urbs()`: takes `cmnd` and `devinfo` only, no gfp argument;
  every allocation and submit in it uses `GFP_ATOMIC`.
- `uas_submit_urbs()` return: 0, `-ENOMEM` for a failed allocation, or the
  `usb_submit_urb()` error; never a `SCSI_MLQUEUE_DEVICE_BUSY` style value.
- `uas_submit_urbs()` on failure: leaves the state bit of the failed step
  set, for example `ALLOC_DATA_IN_URB` or `SUBMIT_CMD_URB`, so a retry
  resumes at that step.
- `uas_cmd_cmplt()`: takes no lock and touches no command state; it only
  logs a nonzero `urb->status` and frees the URB.
- `COMMAND_INFLIGHT`: set when the cmd URB is submitted, cleared by
  `uas_stat_cmplt()` on `IU_ID_STATUS` or `IU_ID_RESPONSE` and by
  `uas_zap_pending()`; it means "status not yet received", not "cmd URB not
  yet completed".
- `uas_try_complete()`: `COMMAND_ABORTED` blocks completion as well as the
  three in-flight bits.
- `uas_queuecommand_lck()` when `devinfo->resetting` is set or
  `uas_submit_urbs()` returns an error, all returning 0 unless noted:

  | Condition | Action | Slot stored |
  |---|---|---|
  | `devinfo->resetting` | `DID_ERROR`, `scsi_done()` | no |
  | `-ENODEV`, no in-flight bit set | `DID_NO_CONNECT`, `scsi_done()` | no |
  | `-ENODEV`, an in-flight bit set | nothing; no `scsi_done()`, no `uas_add_work()` | yes |
  | other error, `SUBMIT_STATUS_URB` still set | returns `SCSI_MLQUEUE_DEVICE_BUSY` | no |
  | other error, `SUBMIT_STATUS_URB` clear | `uas_add_work()` | yes |

- `SUBMIT_STATUS_URB` still set after `uas_submit_urbs()` fails in
  `uas_queuecommand_lck()`: only when `uas_submit_sense_urb()` failed; there
  a data or cmd URB allocation or submit failure other than `-ENODEV` always
  goes to `uas_add_work()`, never to `SCSI_MLQUEUE_DEVICE_BUSY`.
- `uas_do_work()` on a failed retry: requeues `devinfo->work`; it sets no
  result and completes no command.
- `uas_add_work()`: uses `queue_work()` on the file-local `workqueue` in
  `drivers/usb/storage/uas.c`, not `schedule_work()`;
  `uas_wait_for_pending_cmnds()` flushes that work with `flush_work()`.
- **Potentially unsafe usage**: calling `scsi_done()` on a uas command
  outside `uas_try_complete()`.
  - Unsafe: when the command is in `devinfo->cmnd[]` or one of its in-flight
    bits is set; `uas_stat_cmplt()` finds it through the slot and
    `uas_data_cmplt()` takes it from `urb->context`.
  - Safe: in `uas_queuecommand_lck()` before the command is stored in
    `devinfo->cmnd[]` and before any of its URBs is submitted, as the
    `devinfo->resetting` branch does.
  - Safe: clear the in-flight bit under `devinfo->lock`, then call
    `uas_try_complete()`, which tests the bits; `uas_data_cmplt()` does this.
