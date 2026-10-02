| Job | File | Built as; easy to miss |
|---|---|---|
| Fair class | `kernel/sched/fair.c` | own object; `kernel/sched/Makefile` builds only `core.o`, `fair.o`, `build_policy.o`, `build_utility.o` |
| Stop class | `kernel/sched/stop_task.c` | not on its own; included by `kernel/sched/build_utility.c`, not `kernel/sched/build_policy.c` |
| Load tracking | `kernel/sched/pelt.c` | not on its own; included by `kernel/sched/build_policy.c` |
| System calls | `kernel/sched/syscalls.c` | not on its own; via `kernel/sched/build_policy.c`; holds `sched_yield` and also in-kernel helpers such as `yield()`, `yield_to()`, `set_user_nice()`, `idle_cpu()`; the `membarrier` syscall is in `kernel/sched/membarrier.c` |
| sched_ext sources | `kernel/sched/ext/` | no flat sched_ext files exist in `kernel/sched/`; the directory has no Makefile; `kernel/sched/build_policy.c` includes its five `.c` files under `CONFIG_SCHED_CLASS_EXT` |
| sched_ext core | `kernel/sched/ext/ext.c` | holds `DEFINE_SCHED_CLASS(ext)` and both struct_ops registrations; cid mapping and arena allocator are split out to `kernel/sched/ext/cid.c` and `kernel/sched/ext/arena.c` |
| sched_ext hooks for the rest of the scheduler | `kernel/sched/ext/ext.h` | included at the end of `kernel/sched/sched.h`; `struct scx_rq` itself is in `kernel/sched/sched.h` |
| sched_ext idle tracking | `kernel/sched/ext/idle.c`, `kernel/sched/ext/idle.h` | `kernel/sched/ext/idle.c` is not built on its own; included by `kernel/sched/build_policy.c`, not by `kernel/sched/ext/ext.c` |
| sched_ext sub-schedulers | `kernel/sched/ext/sub.c`, `kernel/sched/ext/sub.h` | body of `kernel/sched/ext/sub.c` under `CONFIG_EXT_SUB_SCHED`; without it that file has only stub kfuncs, for example `scx_bpf_sub_grant()` returning `-EOPNOTSUPP`; more `#ifdef CONFIG_EXT_SUB_SCHED` blocks are elsewhere, for example in `kernel/sched/ext/ext.c` and `kernel/sched/sched.h` |
| sched_ext ops table and internal types | `kernel/sched/ext/internal.h`, `kernel/sched/ext/types.h` | headers; `kernel/sched/ext/internal.h` has two ops tables, `struct sched_ext_ops` and `struct sched_ext_ops_cid`, plus `struct scx_sched`; `kernel/sched/ext/types.h` has `enum scx_consts` and `struct scx_cmask` |
