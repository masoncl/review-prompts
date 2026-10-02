- Flags are in `include/linux/input/mt.h`; `INPUT_MT_DIRECT` and
  `INPUT_MT_DROP_UNUSED` are left out of the table.

| Flag | What the core does |
|---|---|
| `INPUT_MT_POINTER` | `BTN_TOOL_TRIPLETAP`, `BTN_TOOL_QUADTAP`, `BTN_TOOL_QUINTTAP` are set only when `num_slots` is at least 3, 4, 5 |
| `INPUT_MT_SEMI_MT` | sets `INPUT_PROP_SEMI_MT`, and makes `input_mt_sync_frame()` skip finger counting even with `INPUT_MT_POINTER` |
| `INPUT_MT_TRACK` | allocates `mt->red` and nothing else; does not turn on `INPUT_MT_DROP_UNUSED` behaviour |
| `INPUT_MT_TOTAL_FORCE` | sets no bit at init; `input_mt_report_pointer_emulation()` reports `ABS_PRESSURE` as the sum of `ABS_MT_PRESSURE` over active slots instead of the oldest contact's value |

- `ABS_MT_TRACKING_ID`: set to 0..`TRKID_MAX` unconditionally, replacing any
  range the driver set earlier.
- Order matters only with `INPUT_MT_POINTER` or `INPUT_MT_DIRECT`; with
  neither flag nothing is copied to the single-touch axes.
- MT axis declared after the call: `copy_abs()` skips an axis whose bit is not
  yet in `dev->absbit`, so `ABS_X`, `ABS_Y` or `ABS_PRESSURE` stays undeclared
  (not zero-ranged) unless the driver declares it itself, and the core drops
  the emulated events for an undeclared axis.
- `touchscreen_parse_properties()` with multitouch true may rewrite and swap
  the MT absinfo; run after the call, it leaves the single-touch copy with the
  earlier ranges.
- `copy_abs()` replaces the whole single-touch absinfo and forces fuzz to 0; a
  driver that wants its own `ABS_X`/`ABS_Y` parameters sets them after the
  call, as `drivers/input/mouse/synaptics.c` does for semi-mt pads.
- Too many slots: the limit is the literal 1024 in `input_mt_init_slots()`;
  there is no MT_SLOT_ABS_MAX in this tree.
- Second call: 0 when `num_slots` equals `dev->mt->num_slots` or is 0,
  `-EINVAL` for any other value; the flags of the second call are ignored.
