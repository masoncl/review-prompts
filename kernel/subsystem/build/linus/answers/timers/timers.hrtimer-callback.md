- Hard timers: `__run_hrtimer()` is reached from `hrtimer_interrupt()`, or
  from `hrtimer_run_queues()` while high resolution mode is not active; both
  are hard interrupt context with interrupts disabled.
- Interrupt state in the callback: `__run_hrtimer()` drops `cpu_base->lock`
  with the flags its caller saved, so soft timers run with interrupts
  enabled.
- Soft timers on `CONFIG_PREEMPT_RT`: the callback runs with
  `cpu_base->softirq_expiry_lock` held, taken in `hrtimer_run_softirq()`; the
  field does not exist without `CONFIG_PREEMPT_RT`.
- `lockdep_hrtimer_enter()` in `include/linux/irqflags.h`: with
  `CONFIG_TRACE_IRQFLAGS`, tells lockdep from `timer->is_hard` whether the
  callback stays in hard interrupt context on RT; with
  `CONFIG_PROVE_RAW_LOCK_NESTING` a callback of a `HRTIMER_MODE_HARD` timer
  is checked as one that may take raw spinlocks only.
- Timer memory after the callback returns: `__run_hrtimer()` reads
  `timer->is_queued` only when the return value is `HRTIMER_RESTART`;
  otherwise it only compares the pointer with `base->running`.
- **Potentially unsafe usage**: freeing the object that holds the timer from
  its callback.
  - Unsafe: when the callback returns `HRTIMER_RESTART`, or another context
    can still start or cancel the timer.
  - Safe: when the callback returns `HRTIMER_NORESTART` and nothing else
    touches the timer, as `tcp_pace_kick()` in `net/ipv4/tcp_output.c` does
    when its `sock_put()` drops the reference taken at the start;
    `__run_hrtimer()` reads `timer->is_queued` only for `HRTIMER_RESTART`.
