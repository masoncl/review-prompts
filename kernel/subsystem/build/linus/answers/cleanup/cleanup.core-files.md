| Job | File | Easy to miss |
|---|---|---|
| Documentation | `Documentation/core-api/cleanup.rst` | renders only the `DOC: scope-based cleanup helpers` block; the per-macro comments in `include/linux/cleanup.h` are plain comments, read them in the header |
| Compiler attribute | `include/linux/compiler_attributes.h` | defines `__cleanup()`; `include/linux/compiler-clang.h` does not redefine it |
| Slab wrappers | `include/linux/slab.h` | `kfree`, `kvfree`, `kvfree_atomic` skip `IS_ERR_OR_NULL()` pointers; `kfree_sensitive` skips only NULL |
| Mutex guards | `include/linux/mutex.h` | besides `mutex_try` and `mutex_intr` there are `mutex_kill` and `mutex_init` |
| Read-write semaphore guards | `include/linux/rwsem.h` | conditional forms are `rwsem_read_try`, `rwsem_read_intr`, `rwsem_write_try`, `rwsem_write_kill`; no killable read, no interruptible write |
| SRCU and tasks-trace RCU guards | `include/linux/srcu.h`, `include/linux/rcupdate_trace.h` | `srcu` and its fast forms; `rcu_tasks_trace` |
| Preemption guards | `include/linux/preempt.h` | `preempt` and `preempt_notrace` only |
| Migration guard | `include/linux/sched.h` | `migrate` is at the end of this file, not in `include/linux/preempt.h`, which holds only the `migrate_disable()` comment |
| Script that checks a declaration | `scripts/checkpatch.pl` | `ERROR()` of type `UNINITIALIZED_PTR_WITH_FREE`; matches a pointer declared with `__free()` and followed directly by `,` or `;`; explained in `Documentation/dev-tools/checkpatch.rst` |
