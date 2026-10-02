- `TIMER_IRQSAFE` callback: runs with interrupts disabled and `base->lock`
  released; `expire_timers()` drops the lock with `raw_spin_unlock()` before
  the call.
- Preempt-count warning text: `"timer: %pS preempt leak: %08x -> %08x\n"`, from
  `WARN_ONCE()` in `call_timer_fn()`.
- Threaded expiry: when `force_irqthreads()` is true, `raise_timer_softirq()` in
  `include/linux/interrupt.h` hands `TIMER_SOFTIRQ` to the per-CPU `ktimerd`
  thread (comm "ktimers/%u"), which runs it from `run_ktimerd()` in
  `kernel/softirq.c`; it is not run by `ksoftirqd`.
- `force_irqthreads()`: false without `CONFIG_IRQ_FORCED_THREADING`; with it,
  always true with `CONFIG_PREEMPT_RT` and a static key without
  `CONFIG_PREEMPT_RT`, so threaded expiry is not limited to
  `CONFIG_PREEMPT_RT`.
- CPU the callback runs on: not always the CPU in `timer->flags`;
  `timer_expire_remote()`, reached from `tmigr_handle_remote()` in the timer
  softirq, expires the `BASE_GLOBAL` base of another CPU.
- Timers on `BASE_GLOBAL`: those with neither `TIMER_PINNED` nor
  `TIMER_DEFERRABLE`, under `CONFIG_NO_HZ_COMMON`; see `get_timer_cpu_base()`.
