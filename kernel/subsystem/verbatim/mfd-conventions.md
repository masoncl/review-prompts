These are conventions that the maintainers of the MFD subsystem ask of new
code. Existing code may differ. No code in a kernel tree states them, so they
are kept by hand and inserted as they are.

- Commit subjects: always capitalise the description after the subsystem
  prefix, for the MFD, LED and Backlight subsystems. The format is
  "mfd: <driver>: <Capitalised description>", as in
  "mfd: max77650: Remove useless type_invert flag".
- Do not hard-code implementation details in driver, struct or device names.
  Avoid the string "mfd" and the driver's own file name in names.
- Prefer to name the private data structure after the device (for example
  `struct kb3930`) and to name the variable that holds it `ddata`, rather than
  a generic name such as `info` or `priv`.
- MFD is an API in Linux, not just a physical layout. New core drivers that
  register multiple children belong in `drivers/mfd/`, and so do new calls to
  `mfd_add_devices()` or `devm_mfd_add_devices()`.
- Do not use the MFD API for a simple device with a single function. Use it
  only for a device that registers multiple children in different subsystems,
  through the MFD API or `of_platform_populate()`.
- For a simple MFD, consider whether a standard device tree compatible such as
  "simple-mfd" or "simple-pm-bus" can be used instead of a custom driver.
- The core MFD driver should handle only core resources, such as interrupts
  and the regmap.
- A child driver must reach the data of its parent with a standard API, such
  as `dev_get_drvdata()` on `pdev->dev.parent`. Avoid bespoke accessors or
  helper functions in the parent that pass state to child devices.
- Initialise a private resource, such as a regmap or a clock handle, in the
  child driver that consumes it, not in the parent, unless several child
  devices share the resource.
- Define `struct mfd_cell` arrays as `static const`.
- Do not pass platform data for child devices, such as `struct mfd_cell`
  arrays, through the match data of a device id table, such as `data` in
  `struct of_device_id`. To pass which variant a device is, store an enum or
  an integer id in the match data, and select the `static const` cell array
  with a `switch` in the probe code.
- Do not create local copies of cells in order to amend them at run time.
  Always use static references.
- Sibling child drivers, such as the RTC driver and the regulator driver under
  one MFD parent, must not call functions of each other directly. Do not
  expose driver-level callbacks that bypass the standard kernel subsystem
  APIs.
- Prefer `PLATFORM_DEVID_AUTO` for automatic cell indexing.
