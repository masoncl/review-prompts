- `flush_workqueue()` macro in `include/linux/workqueue.h`: tests eight
  pointers, `system_percpu_wq`, `system_dfl_wq` and `system_dfl_long_wq`
  among them; it does not test `system_wq`, `system_unbound_wq`,
  `system_bh_wq` or `system_bh_highpri_wq`.
- Run time: `__warn_flushing_systemwide_wq()` in `kernel/workqueue.c` is a
  real function; a call site that got the compile-time warning also does
  `pr_warn()` of "Flushing system-wide workqueues will be prohibited in near
  future." and `dump_stack()` on every call, then flushes normally.
- A system workqueue the compiler cannot prove equal to one of the tested
  pointers: the `flush_workqueue()` macro gives no warning at compile time
  or at run time.
- `__WQ_DESTROYING`: `__queue_work()` tests it together with `__WQ_DRAINING`;
  `destroy_workqueue()` sets it before the drain and never clears it.
