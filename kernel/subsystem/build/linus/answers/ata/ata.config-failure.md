- Budget: `ehc->tries[]` is set at the start of each `ata_eh_recover()` call,
  to `ATA_EH_DEV_TRIES`, or to 1 on a link with `ATA_LFLAG_NO_RETRY`;
  `ata_eh_handle_dev_fail()` sets it back to `ATA_EH_DEV_TRIES` when it
  schedules a probe. Every `rest_fail` path in the same call that reports a
  failed device draws on it, for example set-mode, flush and LPM failures.

| errno | Effect in `ata_eh_handle_dev_fail()` | Attempts in total, from `ATA_EH_DEV_TRIES` |
|---|---|---|
| `-EAGAIN` | no decrement, no slow-down | not limited here |
| `-ENODEV` | decrement, `probe_mask` bit, clamp to 1, slow-down | 2 |
| `-EINVAL` | decrement, clamp to 1, slow-down | 2 |
| `-EIO` | decrement, slow-down when 1 is left | 3 |
| any other, such as `-ENOENT` | decrement only | 3 |

- `-EAGAIN`: comes from `ata_do_link_spd_quirk()` in `ata_dev_configure()`,
  which lowers `sata_spd_limit` first so that the retry makes progress.
- `-ENOENT` from `ata_dev_read_id()`: swallowed only in the new-device branch of
  `ata_eh_revalidate_and_attach()`, which thaws the port with
  `ata_eh_thaw_port()` and ignores the device; through `ata_dev_revalidate()`
  it reaches `ata_eh_handle_dev_fail()` and matches no case.
- Slow-down: runs only when tries is exactly 1 after the decrement and clamp;
  it lowers the link speed with `sata_down_spd_limit()` on the physical link,
  and calls `ata_down_xfermask_limit()` with `ATA_DNXFER_PIO` only if
  `dev->pio_mode > XFER_PIO_0`.
- `ata_dev_disable()`: does not set `ATA_DEV_NONE`; `ata_eh_dev_disable()` does
  `dev->class++`, giving for example `ATA_DEV_ATA_UNSUP`, and frees `dev->cdl`.
- `ata_eh_detach_dev()` in `ata_eh_handle_dev_fail()`: called only if the
  physical link is offline, or from `ata_eh_schedule_probe()`.
- `ata_eh_schedule_probe()`: acts only if the `probe_mask` bit is set and the
  `did_probe_mask` bit is clear, so once per slot per EH pass; it calls
  `ata_dev_init()`, which zeroes `dev->quirks`.
- New device that fails IDENTIFY or configure: `dev->class` is
  `ATA_DEV_UNKNOWN` when `ata_eh_handle_dev_fail()` runs, so
  `ata_dev_disable()` is never called; with tries at 0
  `ata_eh_revalidate_and_attach()` skips the slot and it stays
  `ATA_DEV_UNKNOWN`.
- Return value of `ata_eh_handle_dev_fail()`: ignored by `ata_eh_recover()`,
  which retries whenever any link failed, except on a frozen port with a PMP
  attached.
