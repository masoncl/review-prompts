- ATA_QUIRK_NO_NCQ_LOG: not in this tree.

| Name | Tested in | Effect |
|---|---|---|
| `ATA_FLAG_NO_LOG_PAGE` | `ata_read_log_page()` | returns `AC_ERR_DEV`, no command, no `ata_dev_err()` message |
| `ATA_QUIRK_NO_DMA_LOG` | `ata_read_log_page()` | PIO only; the read still happens |
| `ATA_QUIRK_NO_LOG_DIR` | `ata_log_supported()` | directory not read |
| `ATA_QUIRK_NO_ID_DEV_LOG` | `ata_identify_page_supported()` | IDENTIFY DEVICE data log not read |

- `ata_eh_read_log_10h()` and `ata_eh_get_ncq_success_sense()` in
  `drivers/ata/libata-sata.c`: call `ata_read_log_page()` directly, so only the
  first two rows apply to them.
