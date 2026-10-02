- Timeout with the qc still active: `ata_port_freeze()` reaches
  `ata_do_link_abort()`, which sets `ATA_QCFLAG_EH` and calls
  `ata_qc_complete()`; the qc goes through `__ata_qc_complete()`, so it is
  unmapped and inactive before `post_internal_cmd` runs.
- After that timeout: the port is frozen and `ATA_PFLAG_EH_PENDING` is set;
  `ata_exec_internal()` does no reset and no thaw.
- `AC_ERR_SYSTEM`: returned for a frozen port before any command is issued,
  and also set by the `sys_err` path of `ata_qc_issue()`, which does not
  freeze the port; test `ata_port_is_frozen()` to learn whether the port is
  frozen, as `ata_read_log_page()` does before it retries.
