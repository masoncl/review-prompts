- `RCU_INIT_POINTER()`: the comment above it in `include/linux/rcupdate.h`
  gives three cases and no more. A lock held by the writer is not one of them.
- Third case of `RCU_INIT_POINTER()`: the object was already exposed to
  readers, and either nothing reader-visible changed since, or readers may see
  its old state (for example statistical counters).
- `rcu_replace_pointer()`: returns `typeof(ptr)`, the type of the new value,
  not of `rcu_ptr`.
- **Potentially unsafe usage**: `rcu_replace_pointer()` with a constant-true
  `c`.
  - Unsafe: while another task can write the same pointer. The old value is a
    plain load followed by a separate store, so two callers can both get the
    same old pointer and free it twice.
  - Safe: under the lock that serialises the writers, as `tcf_pedit_init()` in
    `net/sched/act_pedit.c` does under `tcf_lock`.
  - Safe: lockless writers use
    `unrcu_pointer(xchg(&p, RCU_INITIALIZER(new)))` instead, as
    `proc_do_cad_pid()` in `kernel/reboot.c` does.
