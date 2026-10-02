- `max_effects` upper limit: `FF_MAX_EFFECTS`, which is `FF_GAIN` (0x60) in
  `include/uapi/linux/input.h`; there is no FF_EFFECTS_MAX.
- `-EINVAL`: returned only for `max_effects == 0` and
  `max_effects > FF_MAX_EFFECTS`.
- Empty `dev->ffbit`: not checked by `input_ff_create()`.
- Size overflow: no separate test; the allocations are `kzalloc_flex()` and
  `kzalloc_objs()`, and a failure returns `-ENOMEM`.
- `upload` and `playback`: both mandatory; `input_ff_upload()` calls
  `ff->upload`, and `erase_effect()` and `input_ff_event()` call
  `ff->playback`, with no NULL test.
- `stop`: a further optional callback of `struct ff_device`, NULL-checked in
  `__input_unregister_device()`; see "Memoryless helper timer".
- `dev->event` and `dev->flush`: overwritten unconditionally by
  `input_ff_create()`; a driver that needs its own installs them after the
  call, as `uinput_create_device()` does.
- Driver-owned `dev->event`: `EV_FF` events reach `ff->playback`,
  `ff->set_gain` and `ff->set_autocenter` only if that handler calls
  `input_ff_event()`, as `hidinput_input_event()` does.
- `dev->ffbit` at registration: `input_cleanse_bitmasks()` zeroes it when
  `EV_FF` is not set in `dev->evbit`, so bits set with `set_bit()` alone,
  without a later `input_ff_create()` before `input_register_device()`, are
  lost; `input_set_capability()` sets `EV_FF` itself.
