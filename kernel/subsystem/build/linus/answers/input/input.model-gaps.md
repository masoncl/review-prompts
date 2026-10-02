- Models take `handler->start()` to reach `dev->event()` before `dev->open()`
  has run; `input_open_device()` calls `start()` after
  `input_start_device()` has returned 0 (that call is skipped for a handler
  with `passive_observer`), and an event injected from `start()` reaches
  `dev->event()` only while `dev->ready` is set.
- Models take `input_register_device()` to test `EV_REP` before it installs
  soft repeat; `EV_REP` is tested later, in `input_start_autorepeat()`.
- Models write the core's allocations as `kzalloc()`, `kcalloc()` and
  `struct_size()`; `drivers/input/input.c`, `drivers/input/ff-core.c` and
  `drivers/input/input-mt.c` use `kzalloc_obj()`, `kzalloc_objs()` and
  `kzalloc_flex()` from `include/linux/slab.h`, for example in
  `input_allocate_device()` and `input_ff_create()`.
- Models name from_timer(); it is not defined in this tree. The core uses
  `timer_container_of()`, for example in `input_repeat_key()`.
