- `usb_stor_control_thread()` in `drivers/usb/storage/usb.c`: completes the
  command with `scsi_done_direct()`, not `scsi_done()`.
- Order at the end of a command: `us->srb = NULL` under the host lock,
  `scsi_unlock()`, `mutex_unlock(&us->dev_mutex)`, then `scsi_done_direct()`;
  neither lock is held at the call.
- `queuecommand_lck()` in `drivers/usb/storage/scsiglue.c`: its two early
  completions (`US_FLIDX_DISCONNECTING`, and `US_FL_NO_ATA_1X` with `ATA_12` or
  `ATA_16`) call `scsi_done()` in the context that called the queue callback,
  with the host lock held by `DEF_SCSI_QCMD()`.
- On wake-up the thread tests `US_FLIDX_TIMED_OUT`, not `US_FLIDX_ABORTING`,
  under the host lock; if set it sets `DID_ABORT << 16` and skips the protocol
  handler.
- End of command, two independent tests under the host lock:
  - `srb->result == DID_ABORT << 16`: `scsi_done_direct()` is skipped.
  - `US_FLIDX_TIMED_OUT` set: `complete(&us->notify)`, then
    `US_FLIDX_ABORTING` and `US_FLIDX_TIMED_OUT` are cleared.
  - A command that finished with another result before the abort was noticed
    gets both `complete(&us->notify)` and `scsi_done_direct()`.
- `usb_stor_host_template`: sets `.can_queue = 1` and does not set
  `.cmd_per_lun`; the one-command limit is `can_queue` plus the
  `us->srb != NULL` test in `queuecommand_lck()`.
