- `raw_event` positive: treated as zero; `__hid_input_report()` tests only
  `ret < 0`, goes on to `hid_report_raw_event()` and returns that result.
- Stopping the core from `raw_event`: return a negative value, as
  `gfrm_raw_event()` does with `-1`.
- Comment above `struct hid_driver`: says negative is an error and any other
  value passes the event on.
- `raw_event`: the code matches the comment.
- `event`: the code does not match; any nonzero return skips
  `hidinput_hid_event()` and `hid->hiddev_hid_event()` for that usage, and
  `magicmouse_event()` relies on it by returning 1.
- `event` negative: logged as `"%s's event failed with %d\n"` with
  `hid_err()`; positive is not logged.
- `event` nonzero: affects one usage only; the remaining usages, `report` and
  `hidinput_report_event()` still run.
- `raw_event` rewriting `data[0]` on a numbered device:
  `hid_report_raw_event()` looks the report up again from `data`, so the
  rewritten id selects the report that is parsed.
