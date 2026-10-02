- `ff->stop`: set to `ml_ff_stop()` by `input_ff_create_memless()`; it runs
  `timer_shutdown_sync()` on `ml->timer`.
- Caller of `ff->stop`: `__input_unregister_device()` in
  `drivers/input/input.c`, after the handlers are disconnected and before
  `device_del()`; both `input_unregister_device()` and
  `devm_input_device_unregister()` go through it.
- After `input_unregister_device()` returns: the timer cannot fire or be
  re-armed; `mod_timer()` on a shut-down timer is ignored.
- `ff->destroy`: `ml_ff_destroy()` runs `timer_shutdown_sync()` again at
  release; this is the only stop for a device that was never registered.
- `ff->playback` with value 0: reaches `ml_schedule_timer()`, which calls
  `timer_delete()` (not synchronous) once no started effect has a future
  event; `erase_effect()` and `input_ff_flush()` stop the timer only this way.
- `ff->erase`: not set by the helper; there is no ml_ff_erase() or
  ml_ff_flush().
- `dev->close`, suspend, inhibit: no helper hook; `input_inhibit_device()`
  calls `dev->close` but not `dev->flush`, so effects stay started and the
  timer keeps calling `play_effect`.
- Left to the driver: stopping the hardware and its own work or URBs at
  close, suspend and unbind; see "Deferred effect playback".
