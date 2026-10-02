- `fflags` in `struct us_data` and `flags` in `struct uas_dev_info`: both
  `u64`, not `unsigned long`.
- The `fflags` argument of `usb_stor_adjust_quirks()` and the `flags_ret`
  argument of `uas_use_uas_driver()`: both `u64 *`.
- `driver_info` in `struct usb_device_id`: `kernel_ulong_t`, which is
  `unsigned long` (`include/linux/device-id/usb.h`); narrower than the flag
  word on a 32-bit build.
- `UNUSUAL_DEV()` in `drivers/usb/storage/usual-tables.c`: casts the flags to
  `kernel_ulong_t`; the one in `drivers/usb/storage/uas.c` assigns them
  without a cast.
- `mask` in `usb_stor_adjust_quirks()`: holds exactly the 22 flags that have
  a `case` letter, `US_FL_NO_SAME` included; a matching entry can clear every
  flag it can set.
- Flags without a letter: no entry can set or clear them.
- In `uas_use_uas_driver()`: `usb_stor_adjust_quirks()` runs after the flags
  the function ORs in by code, and those flags are all in `mask`; a matching
  entry replaces them as well as the lettered table flags.
