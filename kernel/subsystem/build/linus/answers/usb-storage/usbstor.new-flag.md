- `US_DO_ALL_FLAGS`: defined in `include/linux/usb_usual.h`; there is no
  include/linux/usb_storage.h in this tree.
- Bits 0 to 31 are all assigned; `US_FL_SENSE_AFTER_SYNC` is 0x80000000. No
  bit that fits a 32-bit `driver_info` is free.
- A flag above bit 31 in a table entry: lost on a 32-bit build, where
  `driver_info` is `unsigned long`; the `quirks` path and code that ORs into
  the `u64` flag word are not affected.
- `mask` in `usb_stor_adjust_quirks()`: a hand-written OR expression, not
  generated from `US_DO_ALL_FLAGS`; a new lettered flag has to be added to it
  by hand as well as getting a `case`.
- `show_info()` in `drivers/usb/storage/scsiglue.c`: the only expansion of
  `US_DO_ALL_FLAGS` besides the enum in `include/linux/usb_usual.h`; prints
  the new name with no edit.
- uas: gets the letter for free through the exported
  `usb_stor_adjust_quirks()`; acting on the flag still needs a test in
  `drivers/usb/storage/uas.c`.
