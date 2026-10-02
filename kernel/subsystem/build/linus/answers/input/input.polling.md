- `input_setup_polling()` only allocates `struct input_dev_poller` and sets
  `dev->poller`; it does not set or wrap `dev->open` or `dev->close`.
- A polled device may have its own `open()` and `close()`; the core calls
  `input_dev_poller_start()` and `input_dev_poller_stop()` around them.
- Start, in `input_start_device()` and `input_uninhibit_device()`: after
  `open()` succeeded, after `ready = true` and after the LED/SND/REP replay.
- Stop, in both `input_close_device()` and `input_inhibit_device()`: before
  `input_dev_toggle(dev, false)` and before `close()`.
- Suspend: `input_dev_suspend()` and `input_dev_resume()` do not touch the
  poller; the only suspend handling is that the work is queued on
  `system_freezable_wq`.
- Maximum: `input_dev_poller_finalize()` sets `poll_interval_max` to the
  interval when the driver set none, so user space cannot set an interval
  above the one at registration.
- Minimum: defaults to 0, and interval 0 disables polling;
  `input_dev_poller_start()` then neither polls nor queues.
- Sysfs `poll` write on an enabled device: cancels and requeues the work; it
  does not call the poll function at once.
- `dev->poller`: freed by `input_dev_release()`; there is no devm variant of
  `input_setup_polling()`.
