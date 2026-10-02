- `migrate_disable()`: keeps the current CPU in `cpu_online_mask` under
  `CONFIG_HOTPLUG_CPU`; `sched_cpu_wait_empty()` waits until
  `rq_has_pinned_tasks()` is false.
- `migrate_disable()`, limit: the CPU may already be out of
  `cpu_active_mask`, and teardown callbacks of states above
  `CPUHP_AP_SCHED_WAIT_EMPTY` have already run on it.
- `preempt_disable()` and `local_irq_disable()`: also keep every other CPU in
  `cpu_online_mask`; `takedown_cpu()` uses `stop_machine_cpuslocked()`,
  which needs the stopper thread to run on every online CPU before
  `take_cpu_down()` runs.
- `preempt_disable()` and `local_irq_disable()`, limit: on other CPUs the
  teardown callbacks above `CPUHP_TEARDOWN_CPU` still run, and a CPU can
  still come online.
- `cpus_read_trylock()`: does not sleep; `percpu_down_read_trylock()` has no
  `might_sleep()` and fails instead of waiting. It has no caller in this
  tree.
- `Documentation/core-api/cpu_hotplug.rst`: does not mention
  `cpus_read_lock()`; the rules are in `kernel/cpu.c` and
  `include/linux/percpu-rwsem.h`.
