- `quirks` in `struct ata_device`: `u64`.
- `enum ata_quirks`: holds bit numbers spelled like `__ATA_QUIRK_NODMA`; the
  masks, spelled like `ATA_QUIRK_NODMA`, are in the anonymous enum after it and
  use `BIT_ULL()`. No enumerator has a _BIT suffix.
- Limit: `BUILD_BUG_ON(__ATA_QUIRK_MAX > 64)` in the body of
  `ata_dev_quirks()` in `drivers/ata/libata-core.c`. There is no
  `static_assert()` for it; `include/linux/libata.h` has only a comment.
- `ata_dev_print_quirks()`: takes the mask as `unsigned int` and tests
  `1U << i`, so a flag with bit number 32 or more is cut from the mask;
  printing it needs the parameter and the test widened.
- `ata_quirk_names[]` with a hole for the new flag: the entry is NULL and the
  log shows "(null)".
- `ata_quirk_names[]` with no entry for the last enumerator: the array is
  shorter, the loop never reaches the bit, nothing is printed for it.
- `force_tbl[]`: a separate table at file scope in
  `drivers/ata/libata-core.c`, under `CONFIG_ATA_FORCE`; `ata_parse_force_one()`
  reads only this table, never `ata_quirk_names[]`.
- Keywords in `force_tbl[]` are their own strings, for example `trim_zero` there
  against `"zeroaftertrim"` in `ata_quirk_names[]`.
- A flag with no `force_tbl[]` entry works but cannot be forced; several flags
  have none, for example `ATA_QUIRK_BROKEN_HPA`.
- `ata_parse_force_one()` accepts any unique prefix of a keyword, exact match
  first; a new keyword that shares a prefix with an existing one makes that
  abbreviation fail with "ambiguous value".
