- `dev->vals`: allocated by `input_allocate_device()` with `dev->max_vals` 10,
  so a pre-registration value is queued like any other.
- Many seeded values: the threshold flush at 8 queued values keeps the array
  from overflowing; it delivers to an empty `dev->h_list`.
- `input_sync()` before registration: dropped in `input_event()` unless the
  driver set `EV_SYN` in `dev->evbit`; `input_register_device()` is what sets
  it.
- `dev->num_vals`: written only in `input_event_dispose()`;
  `input_register_device()` does not reset it.
- `dev->event()`: not called before registration, because `dev->ready` is
  false; `dev->led`, `dev->snd` and `dev->rep` are still updated.
- `input_register_device()`: sends no event and no sync to handlers for the
  seeded state; handlers read the cached bitmaps and values instead.
- `EV_ABS` before registration: `input_handle_abs_event()` dereferences
  `dev->absinfo` with no NULL test; the test in `input_register_device()` has
  not run yet.
- `input_alloc_absinfo()` failure: only logged, and `input_set_abs_params()`
  has set the `dev->absbit` bit by then.
