- `ata_dev_configure()`: does `dev->quirks |= ata_dev_quirks(dev)`; it never
  assigns, so a bit set earlier survives revalidation and reset unless one of
  the following clears it.
- `ata_dev_init()`: sets `dev->quirks = 0` under `ap->lock`; this explicit
  assignment clears the bits, not the `memset()` from
  `ATA_DEVICE_CLEAR_BEGIN`, which starts after `quirks`.
- `ata_dev_init()` callers: `ata_link_init()` and `ata_eh_schedule_probe()`;
  `ata_eh_detach_dev()` alone leaves `quirks` unchanged.
- `ata_force_quirks()`: clears the `quirk_off` bits of the first
  `libata.force` entry for the device at the start of every
  `ata_dev_configure()`, including bits set at run time in an earlier pass;
  code later in the same pass can set them again.
- `it821x_dev_config()` in `drivers/ata/pata_it821x.c`: clears
  `ATA_QUIRK_DIAGNOSTIC`, which `ata_sff_dev_classify()` may have set during
  reset; `ata_dev_configure()` tests that bit after the `dev_config` hook.
- Which error sets a bit: the tree has no common rule.
  - `ata_read_log_page()`: sets `ATA_QUIRK_NO_DMA_LOG` on any nonzero
    `err_mask` from the DMA read, also when the port is frozen.
  - `ata_dev_config_ncq()`: sets `ATA_QUIRK_BROKEN_FPDMA_AA` only when
    `err_mask` is not `AC_ERR_DEV`, then returns `-EIO`.
  - `ata_hpa_resize()`: sets `ATA_QUIRK_BROKEN_HPA` on `-EACCES`, and on any
    error from `ata_read_native_max_address()` when HPA is not to be unlocked.
- Logging: `ata_dev_print_quirks()` prints only the mask of the matched table
  entry, so a bit set at run time never shows in the "applying quirks" line.
- `ata_read_log_page()`: has no message for setting the bit; `ata_dev_err()`
  runs only if the read finally fails. `ata_hpa_resize()` warns when it sets
  its bit.
- `ATA_QUIRK_NO_LOG_DIR`: not set at run time; it comes only from
  `__ata_dev_quirks[]` and `force_tbl[]`. `ata_identify_page_supported()` sets
  `ATA_QUIRK_NO_ID_DEV_LOG` when `ata_log_supported()` returns 0.
- **Unsafe usage**: setting a quirk bit after a failed command without testing
  that bit before the command is issued.
  - Safe: test the bit first and skip the command, as `ata_hpa_resize()` does
    with `ATA_QUIRK_BROKEN_HPA`; the bit is still set on the next pass because
    `ata_dev_configure()` ORs.
  - Safe: set the bit and fail the pass, as `ata_dev_config_ncq()` does;
    `ata_eh_handle_dev_fail()` requests a reset for `-EIO` without calling
    `ata_dev_init()` while tries remain, and the retry skips the command
    because of the test before it.
