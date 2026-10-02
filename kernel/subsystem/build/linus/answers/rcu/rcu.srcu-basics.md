- Token type: the fast kinds return a `struct srcu_ctr __percpu *`, not an
  `int`; it goes unchanged to the matching unlock.
- `cleanup_srcu_struct()` in `kernel/rcu/srcutree.c` sleeps: it calls
  `flush_delayed_work()`, `flush_work()` and `timer_delete_sync()`, and
  re-enables interrupts.
- `cleanup_srcu_struct()` on a `DEFINE_SRCU()` or `DEFINE_STATIC_SRCU()`
  domain: runs the same checks but, because `sda_is_static` is set (by
  `check_init_srcu_struct()` on the first update-side call), frees only
  `sup->node`; `rcu_verify_early_boot_tests()` in `kernel/rcu/update.c` does
  this.
- Static domains in a module: `srcu_module_going()` in `kernel/rcu/srcutree.c`
  calls `cleanup_srcu_struct()` and then `free_percpu()` on `ssp->sda`; the
  module does not call `cleanup_srcu_struct()` itself.
- Module unload therefore has the same requirements: no reader left and no
  callback queued; `exit_misc_binfmt()` in `fs/binfmt_misc.c` calls
  `srcu_barrier()` in its exit function.
