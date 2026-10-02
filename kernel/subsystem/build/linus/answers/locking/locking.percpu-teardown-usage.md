- **Unsafe usage**: `migrate_disable()` as the only protection for a sleeping
  user of state torn down at `CPUHP_AP_ONLINE_DYN`. On the way down that
  teardown runs before `sched_cpu_wait_empty()` at
  `CPUHP_AP_SCHED_WAIT_EMPTY`, which is the step that waits for pinned
  tasks.
  - Safe: `cpus_read_lock()` around the use; `_cpu_down()` in `kernel/cpu.c`
    takes `cpus_write_lock()` before any teardown runs.
  - Safe: state that hotplug never tears down. `mm/zswap.c` registers
    `zswap_cpu_comp_prepare()` with a NULL teardown, so `zswap_compress()` can
    sleep on `acomp_ctx->mutex`; `zswap_pool_destroy()` calls
    `acomp_ctx_free()` only after `cpuhp_state_remove_instance()`.
- Where a callback runs: for states above `CPUHP_TEARDOWN_CPU`, such as
  `CPUHP_AP_ONLINE_DYN`, in `cpuhp_thread_fun()` on the CPU itself; for
  states up to `CPUHP_BRINGUP_CPU`, such as `CPUHP_BP_PREPARE_DYN`, on the CPU
  that controls the operation. See `cpuhp_is_ap_state()`.
- `preempt_disable()` for a non-sleeping local user: enough only where the
  callbacks run on the CPU itself; not for states up to `CPUHP_BRINGUP_CPU`.
- `cpuhp_setup_state()` startup calls: made for each present CPU whose
  hotplug state has reached the new state. For states that run on the CPU
  itself `cpuhp_invoke_ap_callback()` skips a CPU that is not online.
- Return value: the allocated state number, positive, for both
  `CPUHP_AP_ONLINE_DYN` and `CPUHP_BP_PREPARE_DYN`; 0 for a fixed state.
