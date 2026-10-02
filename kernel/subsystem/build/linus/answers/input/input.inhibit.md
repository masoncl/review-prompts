- Both `input_inhibit_device()` and `input_uninhibit_device()` return
  `-ENODEV` when `dev->going_away` is set; the test comes before the
  "already in that state" test, and `inhibited_store()` returns it to the
  writer.
- Release step: `input_mt_release_slots()`, `input_dev_release_keys()` and
  `SYN_REPORT` run after `close()`, also when `dev->users` is 0.
- `dev->inhibited = true`: set last, in the same `event_lock` section as the
  releases, so the release events still reach handlers.
- `input_uninhibit_device()`: clears `dev->inhibited` before calling `open()`
  and sets it back on error, so events the driver reports from inside
  `open()` are not dropped.
- Events while inhibited: `input_get_disposition()` returns
  `INPUT_IGNORE_EVENT` before any state update; this covers injected output
  events too, so an LED change requested while inhibited is not recorded in
  `dev->led` and `input_dev_toggle()` does not replay it on uninhibit.
- `input_repeat_key()`: stops repeating while `dev->inhibited` is set.
