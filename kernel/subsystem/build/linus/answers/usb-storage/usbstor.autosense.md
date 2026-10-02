- `need_auto_sense` in `usb_stor_invoke_transport()` is set by exactly three
  tests:
  - the transport returned `USB_STOR_TRANSPORT_FAILED`;
  - `us->protocol` is `USB_PR_CB` or `USB_PR_DPCM_USB` and
    `srb->sc_data_direction != DMA_FROM_DEVICE`, even when the transport
    returned `USB_STOR_TRANSPORT_GOOD`;
  - `US_FL_SENSE_AFTER_SYNC` is set and `srb->cmnd[0] == SYNCHRONIZE_CACHE`.
- `srb->cmnd[0] == REQUEST_SENSE`: no test of it gates auto-sense; a failed
  REQUEST SENSE is auto-sensed like any other command.
- Nonzero residue on a command not expected to be short: debug message only,
  no auto-sense. `isd200_invoke_transport()` in
  `drivers/usb/storage/isd200.c` is the one that auto-senses on it.
- `USB_STOR_TRANSPORT_GOOD` on `ATA_12` or `ATA_16` with
  `!(srb->cmnd[2] & 0x20)`: sets `US_FL_SANE_SENSE` (unless it or
  `US_FL_BAD_SENSE` is set); this test does not set `need_auto_sense`.
- `USB_STOR_TRANSPORT_NO_SENSE` from the command itself: result
  `SAM_STAT_CHECK_CONDITION`, no auto-sense, no reset.
- Sense length: `US_SENSE_SIZE` (18), or `~0` with `US_FL_SANE_SENSE`, which
  `scsi_eh_prep_cmnd()` clamps to `SCSI_SENSE_BUFFERSIZE` (96). There is no
  32-byte request.
- Sense longer than 18 bytes (`sense_buffer[7] > US_SENSE_SIZE - 8`) with
  `(sense_buffer[0] & 0x7C) == 0x70`: no second REQUEST SENSE; sets
  `US_FL_SANE_SENSE` for later commands and truncates byte 7 to 10.
- `US_FL_SANE_SENSE` is also set by `sdev_configure()` in
  `drivers/usb/storage/scsiglue.c`, for `TYPE_DISK` with
  `scsi_level > SCSI_SPC_2`, unless `US_FL_BAD_SENSE`.
- Large sense request that returns `USB_STOR_TRANSPORT_FAILED`: clears
  `US_FL_SANE_SENSE`, sets `US_FL_BAD_SENSE`, retries once with 18 bytes. An
  abort during a large sense request makes the same flag change.
- `US_FL_BAD_SENSE`: blocks both tests in `usb_stor_invoke_transport()` that
  set `US_FL_SANE_SENSE`.
- Sense fetch aborted (`US_FLIDX_TIMED_OUT`): `DID_ABORT << 16`, then reset.
- Any other sense fetch that is not `USB_STOR_TRANSPORT_GOOD`,
  `USB_STOR_TRANSPORT_NO_SENSE` included: `DID_ERROR << 16`, then reset.
- `US_FL_SCM_MULT_TARG` on that path: returns with `DID_ERROR << 16`, no
  reset, and without calling `last_sector_hacks()`.
- Empty sense (key, ASC, ASCQ zero and filemark/ILI bits clear), no retry of
  the sense command:

| Case | Result |
|---|---|
| command returned `USB_STOR_TRANSPORT_GOOD` | `SAM_STAT_GOOD`, `sense_buffer[0] = 0` |
| `ATA_12` or `ATA_16` | `SAM_STAT_CHECK_CONDITION`, sense untouched |
| otherwise | `DID_ERROR << 16`, sense key forced to `HARDWARE_ERROR` |

- `DID_IMM_RETRY << 16`: only for `READ_10` with `US_FL_INITIAL_READ10`.
  `usb_stor_probe2()` pre-sets `US_FLIDX_REDO_READ10`, so the first
  `READ_10` to reach that test is retried whatever its result; later ones
  when a `READ_10` fails after one succeeded.
- Underflow to `DID_ERROR << 16`: applies when result is `SAM_STAT_GOOD` or
  `srb->sense_buffer[2] == 0`, so also to a `SAM_STAT_CHECK_CONDITION` whose
  byte 2 is zero.
