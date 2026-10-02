- `__ata_scsi_queuecmd()`: its first test returns `SCSI_MLQUEUE_DEVICE_BUSY`
  when `ata_port_eh_scheduled()` is true, before any CDB check.
- ata_qc_new_init(): not in this tree; `ata_scsi_qc_new()` in
  `drivers/ata/libata-scsi.c` picks and initialises the slot itself.
- `ata_scsi_qc_new()` fails in two cases only: the port is frozen, or on an
  `ATA_FLAG_SAS_HOST` port `cmd->budget_token >= ATA_MAX_QUEUE`.
- `ata_scsi_qc_new()` failure: completes the command with `DID_OK` and
  `SAM_STAT_TASK_SET_FULL` through `scsi_done()`; `ata_scsi_translate()` then
  returns 0, so no `SCSI_MLQUEUE_*` value reaches SCSI.
- Tag: `ata_scsi_qc_new()` takes `scsi_cmd_to_rq(cmd)->tag`; on
  `ATA_FLAG_SAS_HOST` ports it takes `cmd->budget_token`, not the block tag.
- Bad CDB length in `__ata_scsi_queuecmd()`: `DID_ERROR << 16` with no sense
  data.
- Opcode with no xlat function: goes to `ata_scsi_simulate()`, whose default
  case sets ILLEGAL REQUEST sense; this is not a failure of translation.
- libsas: `sas_queuecommand()` takes `ap->lock` with `spin_lock_irq()` around
  `ata_sas_queuecmd()`, which is `__must_hold(ap->lock)` and locks nothing.
- `ATA_QCFLAG_ACTIVE` and `ap->qc_active`: set in `ata_qc_issue()`, not in
  `ata_scsi_qc_new()`; a qc that was set up but not issued is not active.
- `ata_qc_issue()` failure: returns void; it ORs the error into
  `qc->err_mask` and calls `ata_qc_complete()`, and `ata_scsi_qc_issue()` still
  returns 0.
- Adapter offline (`ata_adapter_is_online()` false): `ata_scsi_find_dev()`
  returns NULL, giving `DID_BAD_TARGET`; `ata_qc_issue()` tests it again and
  fails the qc with `AC_ERR_HOST_BUS`.
- `ATA_DFLAG_SLEEPING` in `ata_qc_issue()`: the command is not issued; the
  link gets `ATA_EH_RESET` and `ata_link_abort()`, so the command goes to EH.
