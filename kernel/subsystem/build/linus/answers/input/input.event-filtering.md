- `dev->inhibited`: first test in `input_get_disposition()`; every event is
  dropped, `SYN_REPORT` included.
- `EV_KEY` value 2: passed to handlers whenever the code is in `dev->keybit`;
  `dev->key` is neither tested nor changed.
- `input_report_key()`: applies `!!value`, so it cannot send 2; a repeat needs
  `input_event()` directly.
- `EV_KEY` that passes: `INPUT_PASS_TO_HANDLERS` only, never `dev->event()`.
- `EV_SND`: dropped only when the code is not in `dev->sndbit`; an unchanged
  value still passes, `dev->snd` is just updated.
- `EV_FF`: dropped only when value < 0; value 0 passes; the core makes no
  `dev->ffbit` test here.
- `EV_MSC`: dropped only when the code is not in `dev->mscbit`; no code is
  special-cased.
- `EV_ABS` codes for which `input_is_mt_value()` is true (this excludes
  `ABS_MT_SLOT`), on a device with no `dev->mt`: no defuzz and no unchanged
  test, every value passes; see `input_handle_abs_event()`.
- Types with no case in the switch, for example `EV_FF_STATUS`: always
  dropped, so `input_report_ff_status()` reaches no handler.
- Passed with an unchanged value: accepted `EV_SYN` codes, `EV_KEY` value 2,
  non-zero `EV_REL`, `EV_MSC`, `EV_SND`, `EV_FF`, `EV_PWR`, and `EV_ABS`
  codes for which `input_is_mt_value()` is true without `dev->mt`.
