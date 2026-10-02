- EH ownership: not asserted; `ata_exec_internal()` calls `ata_eh_release()`
  and `ata_eh_acquire()` around the wait only when
  `ap->host->eh_owner == current`.
- Probe: there is no ata_bus_probe() here; `ata_port_probe()` schedules EH, so
  probing issues its internal commands from EH.
- `dma_dir != DMA_NONE` with a NULL `buf`: `WARN_ON()` and `AC_ERR_INVALID`,
  before any lock is taken; a non-NULL `buf` with `DMA_NONE` is not checked
  and is ignored.
- `timeout` of 0: the module parameter `ata_probe_timeout` (seconds) is used
  when it is non-zero; only otherwise `ata_internal_cmd_timeout()`.
- Returned mask when the qc has `ATA_QCFLAG_EH`: `AC_ERR_DEV` is added if the
  result status has `ATA_ERR` or `ATA_DF`; an empty mask becomes
  `AC_ERR_OTHER`; `AC_ERR_OTHER` is cleared when any other bit is set.
- **Potentially unsafe usage**: calling `ata_exec_internal()` while commands
  are outstanding on the port.
  - Unsafe: when the normal path can still issue or complete commands;
    `ata_exec_internal()` sets `link->active_tag` to `ATA_TAG_POISON`, zeroes
    `link->sactive`, `ap->qc_active` and `ap->nr_active_links`, drops
    `ap->lock` to wait, and writes the saved values back afterwards.
  - Safe: from EH, as `ata_eh_read_log_10h()` does through
    `ata_read_log_page()`; the outstanding qcs have `ATA_QCFLAG_EH`, and
    `__ata_scsi_queuecmd()` refuses new commands while
    `ata_port_eh_scheduled()` is true.
