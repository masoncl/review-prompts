- `IRQF_ONESHOT`: a handler registered with it is not force-threaded;
  `irq_setup_forced_threading()` in `kernel/irq/manage.c` returns early for
  `IRQF_NO_THREAD`, `IRQF_PERCPU` and `IRQF_ONESHOT`.
- Primary handler given with `IRQF_ONESHOT` and a `thread_fn`: runs in hard
  interrupt context on RT; without `IRQF_ONESHOT` it is threaded too.
- Descriptor opt-out: `__setup_irq()` skips forced threading when
  `irq_settings_can_thread()` is false (`_IRQ_NOTHREAD`).
- `force_irqthreads()`: constant true only with `CONFIG_PREEMPT_RT` and
  `CONFIG_IRQ_FORCED_THREADING`; the architecture selects the latter,
  `config PREEMPT_RT` selects only `PREEMPTION`.
- `TIMER_IRQSAFE` timers: run from a thread on RT (`run_ktimerd()` in
  `kernel/softirq.c`), but `kernel/time/timer.c` calls the callback with
  interrupts disabled, so the callback is atomic and cannot take a
  `spinlock_t`.
- Sleeper hrtimers on RT: `__hrtimer_setup_sleeper()` adds
  `HRTIMER_MODE_HARD` when `rt_or_dl_task_policy(current)` is true and
  `HRTIMER_MODE_SOFT` was not requested.
- `lockdep_assert_RT_in_threaded_ctx()` in `include/linux/lockdep.h`: warns
  under `CONFIG_PROVE_RAW_LOCK_NESTING` when in hard interrupt context that
  is marked neither `hardirq_threaded` nor `irq_config`.
