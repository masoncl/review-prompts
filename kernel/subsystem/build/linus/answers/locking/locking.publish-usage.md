- `READ_ONCE()` gives the reader the same ordering as `rcu_dereference()`:
  `__rcu_dereference_check()` in `include/linux/rcupdate.h` is `READ_ONCE()`
  plus `RCU_LOCKDEP_WARN()` and `rcu_check_sparse()`, nothing stronger.
- `READ_ONCE()` instead of `rcu_dereference()`: allowed by
  `Documentation/RCU/rcu_dereference.rst` only where data is added but never
  removed while readers access the structure.
- There is no smp_read_barrier_depends() macro here; Alpha's `__READ_ONCE()`
  in `arch/alpha/include/asm/rwonce.h` contains `mb()` under `CONFIG_SMP`.
- Documents, and what each says:
  - `Documentation/RCU/rcu_dereference.rst`: the `READ_ONCE()` case above, and
    the rules that keep the compiler from breaking the dependency (comparison
    with NULL is safe; with another non-NULL address it is not, with listed
    exceptions).
  - `Documentation/memory-barriers.txt`, item "(2) Address-dependency barriers
    (historical)" and section "ADDRESS-DEPENDENCY BARRIERS (HISTORICAL)":
    `READ_ONCE()` and `rcu_dereference()` provide the implicit
    address-dependency barrier; both defer to
    `Documentation/RCU/rcu_dereference.rst`.
  - `tools/memory-model/Documentation/explanation.txt`, "AND THEN THERE WAS
    ALPHA": a plain load of the pointer is not ordered; a `READ_ONCE()` is.
  - `tools/memory-model/Documentation/control-dependencies.txt`: a control
    dependency does not order a later load.
- **Potentially unsafe usage**: storing the pointer with `RCU_INIT_POINTER()`,
  which is `WRITE_ONCE()` with no release ordering.
  - Unsafe: when readers can already load the pointer and the object has
    reader-visible stores since it was last published; readers may see the
    fields from before initialisation.
  - Safe: storing NULL, as `swevent_hlist_release()` in
    `kernel/events/core.c` does; `rcu_assign_pointer()` itself uses
    `WRITE_ONCE()` for a constant NULL.
  - Safe: when the structure that holds the pointer is not yet reachable by
    readers, as `copy_sighand()` in `kernel/fork.c` does for a task that
    `copy_process()` has not linked yet; the kerneldoc above
    `RCU_INIT_POINTER()` in `include/linux/rcupdate.h` lists the cases.
