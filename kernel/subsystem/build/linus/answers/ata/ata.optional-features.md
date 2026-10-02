- `ata_dev_config_ncq()`: returns `int`; `ata_dev_config_lba()`, also `int`,
  passes the value on to `ata_dev_configure()`. Every other static helper in
  `drivers/ata/libata-core.c` named like `ata_dev_config_cdl()` is `void`.
- `ata_dev_config_cdl()`: `void`; it absorbs the `-ENOMEM` or `-EIO` of
  `ata_dev_init_cdl_resources()` and goes to its not-supported path.
- `ata_dev_config_cdl()` not-supported path: also taken when SET FEATURES for
  `SETFEATURES_CDL` or `SETFEATURE_SENSE_DATA_SUCC_NCQ` fails; a clear command
  duration guideline bit only warns.
- Flag clearing: only `ata_dev_config_ncq_prio()`, `ata_dev_config_cdl()`,
  `ata_dev_config_depop()` and `ata_dev_config_fua()` have a path that clears
  flags; the other helpers just return, so only bits inside
  `ATA_DFLAG_CFG_MASK` are reset for them.
- **Potentially unsafe usage**: a feature helper that returns on missing or
  invalid data without clearing a `dev->flags` bit that belongs to the
  feature.
  - Unsafe: when the bit is outside `ATA_DFLAG_CFG_MASK`; it keeps the value of
    an earlier `ata_dev_configure()` pass.
  - Safe: when the bit is inside `ATA_DFLAG_CFG_MASK`, which
    `ata_dev_configure()` clears before the helpers run, as
    `ata_dev_config_trusted()` with `ATA_DFLAG_TRUSTED`.
  - Safe: when every failure return goes through a path that clears the bit,
    as the `not_supported` label of `ata_dev_config_cdl()` does for
    `ATA_DFLAG_CDL_ENABLED`.
- `ata_dev_config_zoned()`: there is no ata_dev_config_zac() here; it sets the
  three limits to `U32_MAX` first and takes each field only if its bit 63 is
  set.
- `ata_do_link_spd_quirk()`: the name here for the link-speed step; there is no
  ata_do_link_spd_horkage().
