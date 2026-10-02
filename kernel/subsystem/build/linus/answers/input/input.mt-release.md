- `input_inhibit_device()` in `drivers/input/input.c` is the only caller of
  `input_mt_release_slots()`; it is reached by writing to the `inhibited`
  sysfs attribute.
- `input_dev_suspend()`, `input_dev_freeze()`, `input_disconnect_device()` and
  `input_reset_device()`: call `input_dev_release_keys()` and not
  `input_mt_release_slots()`, so `BTN_TOUCH` and the `BTN_TOOL_FINGER` family
  go up while every slot keeps its tracking id.
- `input_close_device()`: releases neither keys nor slots.
- `input_mt_release_slots()`: has no `EXPORT_SYMBOL()` and is declared only in
  `drivers/input/input-core-private.h`; drivers cannot call it.
- `input_mt_release_slots()`: does not call
  `input_mt_report_pointer_emulation()` and sends no `SYN_REPORT`; it sends
  `ABS_PRESSURE` 0 itself, and `input_inhibit_device()` follows it with
  `input_dev_release_keys()` and the `SYN_REPORT`.
- On every path except inhibit (system suspend and resume, controller reset,
  close) the core lifts no contact; where the hardware loses contacts there,
  only the driver can release them. For example `mms114_suspend()` in
  `drivers/input/touchscreen/mms114.c` and `mt_reset_resume()` in
  `drivers/hid/hid-multitouch.c`.
- Driver-side release: loop `input_mt_slot()` plus
  `input_mt_report_slot_inactive()` over all slots, then
  `input_mt_sync_frame()` or `input_mt_report_pointer_emulation()`, then
  `input_sync()`; see `mt_release_contacts()`.
- `input_mt_drop_unused()`: lifts only slots not reported since `mt->frame`
  last advanced, and does no pointer emulation, so `BTN_TOUCH` and
  `ABS_PRESSURE` stay as they were until emulation is run.
