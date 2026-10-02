- `.target_alloc`: set to `target_alloc()`, which takes
  `struct scsi_target *`; it is the only per-target callback.
- `.cmd_per_lun`, `.dma_boundary`, `.no_write_same`: not set in
  `usb_stor_host_template`; `uas_host_template` is the one with
  `.dma_boundary`.
- Fixed for every device: `can_queue = 1`, `dma_alignment = 511`,
  `emulated`, `skip_settle_delay`.
- Template values that are only starting points:
  - `sg_tablesize`: `usb_stor_probe1()` overwrites `host->sg_tablesize` for
    every host with `usb_stor_sg_tablesize()`.
  - `this_id`: `usb_stor_probe2()` sets it to 7 with `US_FL_SCM_MULT_TARG`.
  - `max_sectors`: see "Per-device SCSI settings".
- `usb_stor_host_template_init()`: sets `name`, `proc_name` and `module`
  after the struct copy; `name` and `proc_name` get the same string.
- `module_usb_stor_driver()` in `drivers/usb/storage/usb.h`: the only caller
  of `usb_stor_host_template_init()`; `drivers/usb/storage/usb.c` and every
  ums sub-driver use it, and it runs in module init, not in probe.
