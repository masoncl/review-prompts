- `ata_port_abort()` and `ata_port_freeze()` with at least one command aborted:
  do not call `ata_port_schedule_eh()` or `scsi_schedule_eh()`; each
  non-internal command enters EH through `ata_qc_complete()`,
  `ata_qc_schedule_eh()` and `blk_abort_request()`.
- `ata_do_link_abort()`: calls `ata_port_schedule_eh()` only when it aborted
  nothing.
- Aborted internal command (`ATA_TAG_INTERNAL`): `ata_qc_complete()` finishes
  it through `__ata_qc_complete()` and never reaches `ata_qc_schedule_eh()`;
  only `ATA_PFLAG_EH_PENDING`, set by `ata_eh_set_pending()` from
  `ata_do_link_abort()`, remains.
- `ata_std_sched_eh()` while `ATA_PFLAG_INITIALIZING` is set: returns without
  setting `ATA_PFLAG_EH_PENDING` and without `scsi_schedule_eh()`.
- `ata_scsi_error()`: calls `ata_scsi_port_error_handler()` only when a command
  timed out or `ata_port_eh_scheduled()` is true; otherwise it only flushes
  `ap->eh_done_q`.
- `eh_info` and `eh_context`: fields of `struct ata_link`, not of
  `struct ata_port`; the entry loop handles every link of the port.
- `link->eh_context`: zeroed whole by `memset()` before `eh_info` is copied
  into `eh_context.i`, on every pass including a repeat.
- `ATA_PFLAG_RESUMING` at entry: each enabled device gets `ATA_DFLAG_RESUMING`
  and `ATA_EH_SET_ACTIVE` in `ehc->i.dev_action[]`.
- Probing: `ata_scsi_port_error_handler()` does not wait for it;
  `ATA_PFLAG_LOADING` is only cleared in its final clean-up.
