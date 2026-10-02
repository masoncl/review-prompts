- `input_dev_toggle()`: static in `drivers/input/input.c`; see "Output events
  and readiness" for its callers.
- `input_dev_toggle()`: calls `dev->event()` directly under
  `dev->event_lock`, skipping `input_get_disposition()`, so the callback sees
  values that did not change.
- Types passed down include `EV_MSC` and `EV_SYN` with `SYN_CONFIG`; both are
  `INPUT_PASS_TO_ALL`.
- `ff->upload()` and `ff->erase()`: called from `input_ff_upload()` and
  `erase_effect()` under `ff->mutex`, outside `dev->event_lock`; they do not
  go through `input_ff_event()`.
