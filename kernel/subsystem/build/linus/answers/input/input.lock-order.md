- One chain nests four of the locks: `evdev_release()` holds `evdev->mutex` →
  `input_flush_device()` takes `dev->mutex` → `input_ff_flush()` takes
  `ff->mutex` → `erase_effect()` takes `dev->event_lock`.
- `ff->mutex` nests inside `dev->mutex`: `input_flush_device()` holds
  `dev->mutex` across `dev->flush()`, so `ff->erase()` may sleep under both.
- `input_ff_upload()` and `input_ff_erase()` from `evdev_do_ioctl()`: entered
  with `evdev->mutex` held and without `dev->mutex`.
- `input_disconnect_device()`: holds `dev->mutex` only while it sets
  `dev->going_away`, releases it, then takes `dev->event_lock`; the two are
  not nested there.
- `dev->event_lock` under `dev->mutex`: `input_reset_device()`,
  `input_start_device()`, `input_close_device()`, `input_inhibit_device()` and
  `input_uninhibit_device()`; the last four take it to change `dev->ready`.
- `handler->disconnect()`: called under `input_mutex`;
  `__input_unregister_device()` holds neither `dev->mutex` nor
  `dev->event_lock` when it takes `input_mutex`.
- evdev disconnect path: `evdev_mark_dead()` releases `evdev->mutex` before
  `evdev_cleanup()` calls `input_flush_device()` and `input_close_device()`;
  the path gives `input_mutex` → `evdev->mutex` and `input_mutex` →
  `dev->mutex`, not `input_mutex` → `evdev->mutex` → `dev->mutex`.
- PM callbacks `input_dev_suspend()`, `input_dev_resume()`,
  `input_dev_freeze()`, `input_dev_poweroff()`: take only `dev->event_lock`,
  not `dev->mutex`.
- `input_enable_softrepeat()`: takes no lock.
- `input_register_handle()`: does not call `synchronize_rcu()`.
- `input_unregister_handle()`: calls `synchronize_rcu()` after it has released
  `dev->mutex`.
- `handle->h_node`: added and removed outside `dev->mutex`; the only
  serialization is `input_mutex`, held by the core around `connect()` and
  `disconnect()`.
- `ff->stop()`: called by `__input_unregister_device()` after `input_mutex` is
  released, with no core lock held; `ml_ff_stop()` waits for a timer whose
  handler `ml_effect_timer()` takes `dev->event_lock`.
- Handler spinlock from process context: `evdev_handle_get_val()` and
  `joydev_0x_read()` take `dev->event_lock` first, then `client->buffer_lock`,
  the same order as the event path.
- mousedev: `mousedev_mix->mutex` → `mousedev->mutex` → `dev->mutex`, in
  `mixdev_open_devices()` and `mixdev_add_device()`; the latter runs from
  `mousedev_connect()`, so under `input_mutex`. The mixdev mutex has lockdep
  subclass `SINGLE_DEPTH_NESTING`.
- uinput: `state_lock` in `struct uinput_device` is outside
  `dev->event_lock`; `uinput_request_send()` takes it, then
  `dev->event_lock`.
- uinput: `udev->mutex` is outside `input_mutex`; `uinput_ioctl_handler()`
  holds it across `input_register_device()` and `input_unregister_device()`.
- `uinput_dev_flush()`: skips `input_ff_flush()` when `file` is NULL;
  `UI_DEV_DESTROY` reaches it with `udev->mutex` held, and the reply to an
  erase request (`UI_END_FF_ERASE`) needs that mutex.
