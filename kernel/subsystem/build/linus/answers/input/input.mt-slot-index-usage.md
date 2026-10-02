- `input_handle_abs_event()` on an out-of-range `ABS_MT_SLOT`: no warning, no
  error to the driver; it does not call `pr_warn_once()`.
- After an out-of-range slot: `mt->slot` keeps its previous value, so the
  following `input_mt_report_slot_state()` and `ABS_MT_POSITION_X` and other
  MT values activate, release or move the previously selected contact.
- `input_mt_get_value()`, `input_mt_is_active()`, `input_mt_is_used()`: take a
  slot pointer and check nothing; they are no safer than indexing
  `mt->slots[]` directly.
- `input_mt_assign_slots()`: on `-ENXIO` or `-EINVAL` it leaves `slots[]`
  unwritten; on success `input_mt_set_slots()` starts each entry at -1 and
  overwrites it only when a match or a free slot is found.
- **Potentially unsafe usage**: indexing a driver array or bitmap, or
  `dev->mt->slots[]`, with a slot number from the device.
  - Unsafe: when nothing before the access limits the number to the array
    size; the range test in `input_handle_abs_event()` guards only the core's
    `mt->slot`, and the driver never sees its result.
  - Safe: checked against the count that sizes the array and was passed to
    `input_mt_init_slots()`, and the contact skipped on failure, as
    `mt_process_slot()` does with `td->maxcontacts`; `mt_compute_slot()` can
    return the raw contact id, so the upper bound is needed there.
  - Safe: an "id minus one" number checked at both ends, as
    `process_packet_head_v4()` in `drivers/input/mouse/elantech.c` does
    against `ETP_MAX_FINGERS`, the size of `etd->mt[]`, or compared as
    unsigned, as `focaltech_process_abs_packet()` does against
    `FOC_MAX_FINGERS`, the size of `state->fingers[]`.
  - Safe: when the field width cannot exceed the array, as in
    `cyttsp_report_tchdata()`: ids are 4 bits and `CY_MAX_ID` (16) sizes both
    the bitmap and the slot count.
- **Potentially unsafe usage**: passing a slot number from the device to
  `input_mt_slot()` without a range check.
  - Unsafe: when the number can be negative or reach the declared slot count;
    memory stays intact, but the contact's data lands in the previously
    selected slot.
  - Safe: checked first and the contact skipped, as
    `goodix_berlin_report_state()` does against `GOODIX_BERLIN_MAX_TOUCH`,
    the same count it passes to `input_mt_init_slots()`.
  - Safe: when the field width cannot reach the slot count, as in
    `cyttsp_report_tchdata()`.
