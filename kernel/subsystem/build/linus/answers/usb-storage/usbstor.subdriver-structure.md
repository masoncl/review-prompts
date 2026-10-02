- `.driver_info`: holds the entry's flags, which `get_device_info()` copies
  to `us->fflags`; it is not the index.
- Index: the pointer difference `id - karma_usb_ids`, with no range check in
  `karma_probe()`; `karma_driver` sets `.no_dynamic_id = 1`, so no id from
  outside the table arrives.
- `karma_usb_ids[]` and `karma_unusual_dev_list[]`: both `static const`.
- Main driver exclusion: `ignore_ids[]` in
  `drivers/usb/storage/usual-tables.c`, tested by `usb_usual_ignore_device()`
  in `storage_probe()` before `usb_stor_probe1()`; on a match
  `storage_probe()` returns `-ENXIO`, whatever `unusual_devs.h` says for the
  device; there is no USB_US_TYPE_NONE.
  - The list of `unusual_*.h` includes there is written by hand; a new
    sub-driver header must be added to it.
  - The match is on the device's vendor, product and `bcdDevice` range only,
    so every interface of the device is refused.
  - The guard in `unusual_karma.h` is a compile-time test, so the main driver
    refuses the device whenever the option is `y` or `m`, even if `ums-karma`
    is not loaded.
- `NO_SDDR09` in `unusual_devs.h`: the one place where the main table itself
  changes with a sub-driver option; when `CONFIG_USB_STORAGE_SDDR09` is off
  it adds entries for devices that `unusual_sddr09.h` claims when the option
  is on.
- `karma_host_template`: declared by the source as a non-const
  `static struct scsi_host_template`, with no initialiser.
  - `module_usb_stor_driver()` does not define it; it fills it with
    `usb_stor_host_template_init()` and then calls `usb_register()`.
- `MODULE_DEVICE_TABLE(usb, karma_usb_ids)`: needed for autoloading.
- Symbol namespace: the core uses plain `EXPORT_SYMBOL_GPL()`; the namespace
  comes from `DEFAULT_SYMBOL_NAMESPACE` in `drivers/usb/storage/Makefile`.
- `CONFIG_USB_STORAGE_KARMA`: has no `depends on` line; the entry sits inside
  the `if USB_STORAGE` block of `drivers/usb/storage/Kconfig`.
