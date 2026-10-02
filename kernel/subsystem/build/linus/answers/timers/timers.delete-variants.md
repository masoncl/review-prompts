- `__timer_delete_sync()`: second parameter is `bool shutdown`, the same as
  `__timer_delete()`; neither takes a flags word.
- Return 0 or 1 from `timer_delete()`, `timer_delete_sync()`,
  `timer_shutdown()`, `timer_shutdown_sync()`: the queue state found on the
  last pass, nothing more; it is found under `base->lock`, except that
  `timer_delete()` can return 0 from the lockless `timer_pending()` test alone.
- Return 1 from a sync variant with a self-re-arming callback: may mean that the
  instance the callback just re-armed was removed.
- Return value when another path can re-arm concurrently: says nothing about
  the queue state after the function returns, for the non-shutdown variants.
- `timer_shutdown()` while the callback runs: clears `timer->function` at once,
  so the running callback's own re-arm is already discarded.
- `timer_shutdown_sync()` while the callback runs: `__try_to_del_timer_sync()`
  leaves `timer->function` alone until the callback has returned; a re-arm made
  by the callback during the wait succeeds and is removed on the next pass.
  Exception: a callback that re-arms with `add_timer_on()` onto a different
  `struct timer_base`; see "Waiting for a running callback".
