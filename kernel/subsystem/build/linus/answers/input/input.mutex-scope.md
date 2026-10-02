- `dev->mutex` also protects `dev->h_list` changes
  (`input_register_handle()`, `input_unregister_handle()`) and `dev->grab`
  changes.
- `dev->ready`: written with both `dev->mutex` and `dev->event_lock` held.
- `dev->inhibited`: set by `input_inhibit_device()` under both locks;
  `input_uninhibit_device()` clears it, and sets it back when `open()` fails,
  under `dev->mutex` only.
- `handle->open`: counted under `dev->mutex`, but zeroed by
  `input_disconnect_device()` under `dev->event_lock` only.
- `input_dev_set_poll_interval()` in `drivers/input/input-poller.c` takes the
  mutex but calls neither `open()` nor `close()`.
- Poll function: the first call, from `input_dev_poller_start()`, runs with
  `dev->mutex` held; later calls from the work item do not.
- Poll function must not take `dev->mutex`: `input_dev_poller_stop()` and the
  sysfs `poll` store call `cancel_delayed_work_sync()` with it held.
- `event()`: runs with `dev->mutex` held as well as `event_lock` when
  `input_dev_toggle()` calls it from open, close, inhibit, uninhibit or
  `input_reset_device()`; `input_event()`, `input_inject_event()` and the
  input PM callbacks do not take `dev->mutex`.
- Driver state read in `open()` or `close()` can be written under
  `input->mutex` from elsewhere; for example `ad7879_suspend()` sets
  `suspended`, which `ad7879_open()` reads.
- Driver sysfs store that reprograms hardware: takes `input->mutex` to
  exclude `open()` and `close()`, as `kxtj9_set_poll()` does.
