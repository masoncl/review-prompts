- Error tied to a known active command: goes in `qc->err_mask`, not
  `ehi->err_mask`; `ahci_error_intr()` does this for `PORT_IRQ_TF_ERR`.
- Frozen port: `ata_eh_link_autopsy()` adds `ATA_EH_RESET` whenever the port is
  frozen, unless `ATA_EHI_NO_AUTOPSY` is set; so a port left frozen by
  `ata_port_freeze()` gets `ATA_EH_RESET` even if the handler requested none.
- Aborted but not frozen port: the abort itself adds no reset; one comes from
  `ehi->action`, from `AC_ERR_HSM` or `AC_ERR_TIMEOUT` in the error masks, or
  from the analysis in `ata_eh_link_autopsy()`, for example
  `ata_eh_analyze_serror()` or `ata_eh_speed_down()`.
- `ahci_error_intr()` without FBS: the link is the first one for which
  `ata_link_active()` is true, else `ap->link`.
- `ata_link_abort()` branch in `ahci_error_intr()`: reached only when no
  `PORT_IRQ_FREEZE` bit is set. `PORT_IRQ_IF_ERR` is one of those bits, so an
  FBS device error reported with it freezes the port, unless
  `AHCI_HFLAG_IGN_IRQ_IF_ERR` masked the bit.
