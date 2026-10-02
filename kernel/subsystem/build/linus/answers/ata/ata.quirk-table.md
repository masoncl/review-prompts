- Entry with mask 0: still ends the walk, so `ata_dev_quirks()` returns 0;
  `{ "INTEL*SSDSC2MH*", NULL, 0 }` in `__ata_dev_quirks[]` uses this to exempt a
  model from the wider globs after it.
- Value quirk: the flag word holds only `ATA_QUIRK_MAX_SEC`; the sector count
  is in `__ata_dev_max_sec_quirks[]`, an array of
  `struct ata_dev_quirk_value`, in `drivers/ata/libata-core.c`.
- `ata_dev_get_quirk_value()`: handles only `ATA_QUIRK_MAX_SEC`, through
  `ata_dev_get_max_sec_quirk_value()`; it returns 0 for any other flag, so a
  new value quirk needs a branch there.
- Sources of the value, in order:
  1. `value` of the first `libata.force` entry for the device, if it is
     nonzero and the entry has `ATA_QUIRK_MAX_SEC` in `quirk_on`.
  2. the first entry of `__ata_dev_max_sec_quirks[]` that matches, with the
     same glob rules as `__ata_dev_quirks[]` but its own patterns.
  3. 0.
- Value 0: `ata_dev_configure()` takes the minimum with `dev->max_sectors`,
  which becomes 0; an `__ata_dev_quirks[]` entry with `ATA_QUIRK_MAX_SEC`
  therefore needs an entry in `__ata_dev_max_sec_quirks[]` that matches the
  same devices, as `"INTEL SSDSC2KG480G8"` has.
- The value is not stored in `struct ata_device`; it is looked up in each
  `ata_dev_configure()` pass.
- `force_tbl[]` keyword that takes a user value: its name ends in `=`, as
  `force_quirk_on(max_sec=, ATA_QUIRK_MAX_SEC)`; `force_quirk_val()` gives a
  keyword a fixed value.
