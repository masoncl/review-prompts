- `ata_dev_set_mode()`: calls `ata_dev_revalidate()` with `ATA_DEV_UNKNOWN` and
  flags 0, so a transfer-mode change through `ata_set_mode()` reruns
  `ata_dev_configure()`.
- `ATA_READID_POSTRESET`: passed only by `ata_eh_revalidate_and_attach()`, when
  `ATA_EHI_DID_RESET` is set.
- `ATA_EH_REVALIDATE`: also set by `ata_eh_link_autopsy()` when the port is not
  frozen and no `AC_ERR_HSM` or `AC_ERR_TIMEOUT` was seen: for any error when a
  failed command has `ATA_QCFLAG_IO`, otherwise for an error other than
  `AC_ERR_DEV`; besides `ata_eh_reset()` and `ata_qc_complete()`.
- `ata_eh_revalidate_and_attach()`: returns `-EIO` without calling
  `ata_dev_revalidate()` when `ata_eh_link_established()` is false.
- `new_class` in `ata_dev_revalidate()`: only tested for `ATA_DEV_PMP`
  (`-ENODEV`); it is not compared with `dev->class`.
- `ata_dev_same_device()`: compares `dev->class` with the class that
  `ata_dev_read_id()` returned, by strict equality, then `ATA_ID_PROD` and
  `ATA_ID_SERNO`; the firmware revision is not compared.
- `ata_hpa_resize()` (after it unlocked the HPA) and `ata_acpi_on_devcfg()`
  (under `CONFIG_ATA_ACPI`, after a _GTF command ran): call
  `ata_dev_reread_id()` from inside `ata_dev_configure()`, so the same compare
  can fail there and `ata_dev_configure()` returns its `-ENODEV`.
- Capacity compare after configure: skipped when `dev->class` is not
  `ATA_DEV_ATA` (so not for `ATA_DEV_ZAC`), when the saved `n_sectors` was 0,
  or when `ata_id_is_locked()` is true.
- Late HPA lock (native size unchanged, size shrank, old size equalled native,
  no `ATA_QUIRK_BROKEN_HPA`): not accepted; sets `ATA_DFLAG_UNLOCK_HPA` and
  returns `-EIO` so the retry unlocks.
- `dev->quirks`: there is no dev->horkage or ata_dev_blacklisted() here;
  `ata_dev_configure()` ORs in `ata_dev_quirks()` and never assigns;
  `ata_force_quirks()` clears only the `quirk_off` bits of a `libata.force`
  entry; only `ata_dev_init()` zeroes it.
- `ATA_DFLAG_CFG_MASK`: bits 0 to 16 only; `ATA_DFLAG_DEVSLP`, `ATA_DFLAG_DA`,
  `ATA_DFLAG_NCQ_PRIO_ENABLED` and `ATA_DFLAG_CDL_ENABLED` are above it and
  survive a rerun unless a helper clears them, as the not-supported path of
  `ata_dev_config_cdl()` does for `ATA_DFLAG_CDL_ENABLED`.
