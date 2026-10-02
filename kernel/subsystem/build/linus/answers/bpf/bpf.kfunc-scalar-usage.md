- Constant is guaranteed only for these, see `get_kfunc_arg_type()`:
  - a scalar with the `__k` suffix
  - a scalar with the `__szk` suffix
  - a scalar named exactly `rdonly_buf_size` or `rdwr_buf_size`
- `rdonly_buf_size` and `rdwr_buf_size`: `process_const_alloc_mem_size()` also
  rejects a value above `U32_MAX`; `process_const_arg()` puts no bound on a
  `__k` or `__szk` value.
- `__sz` and `__szk` with a buffer that is not NULL: `check_mem_size_reg()`
  rejects a negative minimum and a maximum of `BPF_MAX_VAR_SIZ` or more.
- `__sz` or `__szk` with a NULL `__nullable` buffer: `check_kfunc_args()`
  skips the size check, so the body must not trust the size.
- `array_index_nospec()`: no kfunc in `kernel/bpf/helpers.c` calls it;
  `bpf_cgroup_ancestor()` relies on the two bounds tests alone.
- **Unsafe usage**: indexing an array with a signed scalar argument after
  testing only the upper bound; `check_kfunc_args()` checks only that the
  register is `SCALAR_VALUE`.
  - Safe: test both bounds first, as `bpf_cgroup_ancestor()` in
    `kernel/bpf/helpers.c` does for `int level` before it reads
    `cgrp->ancestors[level]`.
  - Safe: `scx_bpf_cpu_curr()` in `kernel/sched/ext/ext.c` passes `s32 cpu`
    to `scx_cpu_valid()`, which through `__cpu_valid()` tests `cpu >= 0` and
    `cpu < nr_cpu_ids`.
- `scx_bpf_cpu_rq()` is not defined under `kernel/sched/`; it is only declared
  in `tools/sched_ext/include/scx/common.bpf.h`. There is no
  kernel/sched/ext.c here; sched_ext kfuncs are under `kernel/sched/ext/`.
- `bpf_task_from_vpid()`: takes `s32 vpid` and looks it up; it indexes no
  array.
