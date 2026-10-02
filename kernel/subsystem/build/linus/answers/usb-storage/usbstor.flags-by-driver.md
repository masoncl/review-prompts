Flags both drivers test:

| Flag | uas | usb-storage |
|---|---|---|
| `US_FL_IGNORE_UAS` | `uas_use_uas_driver()` | same function, only under `CONFIG_USB_UAS` |
| `US_FL_NO_ATA_1X` | `uas_queuecommand_lck()` | `queuecommand_lck()` |
| `US_FL_MAX_SECTORS_64` | `uas_sdev_configure()` | `sdev_configure()`, any type |
| `US_FL_BROKEN_FUA` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_ALWAYS_SYNC` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_NO_READ_CAPACITY_16` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_FIX_CAPACITY` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_CAPACITY_HEURISTICS` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_NO_WP_DETECT` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |

Flags only uas tests:

| Flag | uas | usb-storage, with no flag test |
|---|---|---|
| `US_FL_NO_REPORT_LUNS` | `uas_target_alloc()` | `target_alloc()` sets `no_report_luns` for every target |
| `US_FL_NO_REPORT_OPCODES` | `uas_sdev_configure()` | `sdev_configure()` sets `no_report_opcodes` for `TYPE_DISK` only |
| `US_FL_NO_SAME` | `uas_sdev_configure()` | `sdev_configure()` sets `no_write_same` for `TYPE_DISK` only |
| `US_FL_MAX_SECTORS_240` | `uas_sdev_configure()` | not equivalent: 240 is only the template default; `sdev_configure()` raises it for tapes and for SuperSpeed or faster |

- `uas_sdev_configure()`: has no `sdev->type` test; every flag applies to
  every device type.
- `US_FL_NO_READ_DISC_INFO` and `US_FL_IGNORE_RESIDUE`: not tested by uas.
- `read_before_ms`: uas sets it for every device, usb-storage for `TYPE_DISK`
  only.
- The "uas only" and "not on uas" notes under `usb-storage.quirks=` in
  `Documentation/admin-guide/kernel-parameters.txt` do not all follow the
  code; for example `m` and `y` are marked "not on uas" and
  `uas_sdev_configure()` tests both flags.
- The remaining 19 flags are tested only by usb-storage code
  (`drivers/usb/storage/usb.c`, `drivers/usb/storage/transport.c`,
  `drivers/usb/storage/scsiglue.c`, plus `US_FL_IGNORE_RESIDUE` in
  `drivers/usb/storage/ene_ub6250.c`); none is read by neither driver.
