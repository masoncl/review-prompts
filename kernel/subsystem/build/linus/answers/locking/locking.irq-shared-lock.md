- `Documentation/locking/spinlocks.rst`: Lesson 1 gives
  `spin_lock_irqsave()` as always safe; Lesson 3 allows the plain form only
  for a lock never used in interrupt handlers.
- `Documentation/kernel-hacking/locking.rst`, "Locking Between Hard IRQ and
  Softirqs/Tasklets": the place that lets the handler use plain
  `spin_lock()`; "Table of Minimum Requirements" has every pairing.
- `drivers/net/ethernet/realtek/8139too.c`, `tp->lock`: shows all three;
  `rtl8139_interrupt()` plain, `rtl8139_poll()` irqsave,
  `rtl8139_set_mac_address()` `spin_lock_irq()`.
- **Potentially unsafe usage**: plain `spin_lock()` on a `spinlock_t` in a
  hard interrupt handler.
  - Unsafe: when the handler is requested with `IRQF_NO_THREAD`,
    `IRQF_PERCPU` or `IRQF_ONESHOT`, or `irq_settings_can_thread()` is false
    for the descriptor; forced threading is skipped, so on PREEMPT_RT the
    handler stays in hard interrupt context, where `rt_spin_lock()` can
    sleep.
  - Safe: when requested without those flags on a descriptor for which
    `irq_settings_can_thread()` is true, as `rtl8139_interrupt()` with
    `IRQF_SHARED`; `__handle_irq_event_percpu()` warns if a handler returns
    with interrupts enabled, and on PREEMPT_RT the handler runs in a thread.
  - Safe: when force-threaded on a normal kernel; `irq_forced_thread_fn()`
    runs the handler with BH and interrupts disabled.
- `thread_fn` of `request_threaded_irq()`: `irq_thread_fn()` calls it with
  nothing disabled; it is process context and needs the irq form against
  the primary handler.
- `struct hrtimer` callback on a normal kernel: hard interrupt context unless
  `HRTIMER_MODE_SOFT`, so `spin_lock_bh()` in process context is not enough;
  see `__hrtimer_setup()`.
- `struct hrtimer` callback on PREEMPT_RT: softirq expiry unless
  `HRTIMER_MODE_HARD`.
