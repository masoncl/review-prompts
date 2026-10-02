- IRQ state: the callback runs in softirq with hard IRQs disabled;
  `expire_timers()` in `kernel/time/timer.c` drops the base lock without
  enabling IRQs for a `TIMER_IRQSAFE` timer.
- Timer CPU, chosen in `__queue_delayed_work()`:

| `housekeeping_enabled(HK_TYPE_TIMER)` | `cpu` argument | Timer armed with |
|---|---|---|
| true | any, explicit CPU included | `add_timer_on()` on the current CPU if it is a housekeeping CPU, else on `housekeeping_any_cpu(HK_TYPE_TIMER)` |
| false | `WORK_CPU_UNBOUND` | `add_timer_global()`, which clears `TIMER_PINNED` |
| false | explicit CPU | `add_timer_on()` on that CPU |

- Explicit `cpu` with timer housekeeping on: the timer can fire on a CPU
  other than `cpu`; the item is still queued for `dwork->cpu`.
- `housekeeping_enabled()`: a stub that returns `false` without
  `CONFIG_CPU_ISOLATION` (`include/linux/sched/isolation.h`).
- Saved `WORK_CPU_UNBOUND`: `__queue_work()` picks the CPU from
  `raw_smp_processor_id()` when the timer fires; a per-CPU workqueue uses that
  CPU, a `WQ_UNBOUND` one passes it to `wq_select_unbound_cpu()`.
- `delayed_work_timer_fn()`: gets the item with `timer_container_of()`; there
  is no from_timer() here.
