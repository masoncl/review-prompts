- ATA_QCFLAG_FAILED: not in this tree; the flag is `ATA_QCFLAG_EH`.
- `ata_qc_complete()`: sets `ATA_QCFLAG_EH` when `err_mask` is non-zero, then
  chooses the EH path by testing `ATA_QCFLAG_EH`, not `err_mask`;
  `ata_do_link_abort()` sets the flag and calls `ata_qc_complete()` without
  touching `err_mask`.
- Internal command (`ata_tag_internal()`): always `fill_result_tf()` then
  `__ata_qc_complete()`, with or without an error; `ata_qc_schedule_eh()` is
  never called for it.
- Failed non-internal command: `ata_qc_complete()` does not call
  `__ata_qc_complete()`; the qc keeps `ATA_QCFLAG_ACTIVE` and its tag until EH
  finishes it in `__ata_eh_qc_complete()`.
- `fill_result_tf()`: returns without calling `qc_fill_rtf` when
  `ATA_QCFLAG_RTF_FILLED` is already set; `ahci_qc_ncq_fill_rtf()` in
  `drivers/ata/libahci.c` sets it for successful NCQ commands.
- `ata_qc_for_each()` and `ata_qc_for_each_with_internal()`: built on
  `ata_qc_from_tag()`, so they yield NULL for a qc that EH owns;
  `ata_qc_for_each_raw()` uses `__ata_qc_from_tag()` and yields every slot
  below `ATA_MAX_QUEUE`.
