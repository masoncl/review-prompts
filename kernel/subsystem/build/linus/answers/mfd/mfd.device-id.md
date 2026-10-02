- `PLATFORM_DEVID_AUTO` name: `<name>.<N>.auto`, not `<name>.<N>`; see
  `platform_device_add()` in `drivers/base/platform.c`.
- N under `PLATFORM_DEVID_AUTO`: comes from `platform_devid_ida`, one IDA for
  every platform device in the system, so N is neither per name nor per
  parent.
- `PLATFORM_DEVID_NONE` base with `cell->id` k > 0: plain addition, the name is
  `<name>.<k-1>`; nothing rejects it.
- Negative `cell->id`: `platform_device_add()` tests the sum, not the base.
  - Sum of -1 (base 0, `cell->id` -1): bare `<name>`; for example `rtc_devs`
    in `drivers/mfd/max8925-core.c`.
  - Sum of -2 (base -1, `cell->id` -1): treated as `PLATFORM_DEVID_AUTO`.
