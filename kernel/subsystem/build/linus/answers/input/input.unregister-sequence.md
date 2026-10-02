- Order in `__input_unregister_device()`:
  1. `input_disconnect_device()`: `going_away`, key-up events, every
     `handle->open = 0`.
  2. Under `input_mutex`: `disconnect()` for each handle,
     `timer_delete_sync(&dev->timer)`, `list_del_init(&dev->node)`, wake
     procfs readers.
  3. `dev->ff->stop()`, outside `input_mutex`.
  4. `device_del()`.
- There is no del_timer_sync in this tree; the call is
  `timer_delete_sync()`.
- Poller: `__input_unregister_device()` does not call
  `input_dev_poller_stop()`; the poller stops only when a handler's
  disconnect reaches `input_close_device()` and `dev->users` drops to 0.
- `dev->timer` is deleted, not shut down; see "Callbacks after
  unregistration" for what re-arms it.
