- `timer_destroy_on_stack()`: releases a timer set up with
  `timer_setup_on_stack()`; destroy_timer_on_stack is not defined in this tree.
- `timer_delete_sync_try()`: the name of the non-waiting try variant, declared in
  `include/linux/timer.h`.
- del_timer(), del_timer_sync(), try_to_del_timer_sync() and from_timer(): no
  function or macro of these names is defined in this tree, and there are no
  compatibility aliases; a patch that calls them does not build.
- Old spelling inside `kernel/time/timer.c`: the static helpers
  `__try_to_del_timer_sync()` and `del_timer_wait_running()` keep it; they are
  not API.
