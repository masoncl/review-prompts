- `input_mt_report_pointer_emulation()`: takes `ABS_X`, `ABS_Y` from the
  oldest active contact (wrap-aware compare of tracking ids), not from the
  lowest-numbered active slot.
- `input_mt_report_slot_state()` with a changed `tool_type` on an active slot:
  keeps the tracking id; the kerneldoc above it says a new id is assigned, the
  body assigns one only when the stored id is negative.
- `input_mt_sync_frame()` with `INPUT_MT_DROP_UNUSED`, and
  `input_mt_drop_unused()`: leave `mt->slot` at the last slot they dropped, so
  the next frame has to call `input_mt_slot()` before
  `input_mt_report_slot_state()`.
- `mt->frame` advances only in `input_mt_sync_frame()`,
  `input_mt_drop_unused()` and `input_mt_release_slots()`.
- `input_mt_get_slot_by_key()` with a driver that calls neither
  `input_mt_sync_frame()` nor `input_mt_drop_unused()`: while `mt->frame` does
  not advance, a slot that was reported once is not handed out again after
  release, since only slots that are inactive and not stamped with the
  current `mt->frame` are taken.
