- Sub-scheduler: a `struct scx_sched` attached to one cgroup, scheduling the
  tasks of that cgroup's subtree. `p->scx.sched` names a task's scheduler;
  read it with `scx_task_sched()`. `cgrp->scx_sched` names a cgroup's.
- Selecting sub mode: `ops.sub_cgroup_id` greater than 1 makes `scx_enable()`
  run `scx_sub_enable_workfn()` instead of `scx_root_enable_workfn()`.
- `CONFIG_EXT_SUB_SCHED` (`init/Kconfig`): `def_bool y`, depends on
  `SCHED_CLASS_EXT && CGROUPS`, not on `CGROUP_SCHED`. Without it
  `scx_task_sched()` returns `scx_root` and `scx_parent()` returns `NULL`.
- Conditions for attaching include, in `scx_sub_enable_workfn()`,
  `find_parent_sched()` and `scx_validate_ops()`:
  - a root scheduler is enabled
  - the parent, which is the scheduler of the nearest ancestor cgroup,
    implements `ops.sub_attach()` and accepts
  - the cgroup has no scheduler of its own yet
  - both schedulers are cid-form
  - nesting depth is below `SCX_SUB_MAX_DEPTH`
- Dispatch: `dispatch_one()` calls only the root's `ops.dispatch()`. A child
  runs when its parent calls `scx_bpf_sub_dispatch()` for a direct child.
- Capabilities (`enum scx_cap_flags`): the root holds every capability on
  every cid; a child holds what its parent gave it with
  `scx_bpf_sub_grant()`; `scx_bpf_sub_revoke()` clears it from the child and
  its descendants.
- Local DSQ insert without the capability: `scx_resolve_local_dsq()` diverts
  the task to the rq's reject or rescue DSQ, except that it admits the task
  to the local DSQ when the rq is not online, the task is
  migration-disabled or `p->migration_pending` is set. `scx_reenq_reject()`
  hands a rejected task back to `ops.enqueue()` with `SCX_ENQ_REENQ`.
- Cgroup migration across a scheduler boundary: `scx_cgroup_task_migrating()`
  runs the destination's `ops.init_task()` before the move commits, and
  `scx_cgroup_task_migrated()` re-homes the task.
- cid: a dense id in `[0, num_possible_cpus())`, in the default mapping
  ordered by topology so that a core, an LLC and a NUMA node are each a
  contiguous range. CPU numbers are in `[0, nr_cpu_ids)` and may be sparse.
  See the comment at the top of `kernel/sched/ext/cid.h`.
- cid mapping lifetime: built by `scx_cid_init()` on every root enable from
  the CPUs online then, optionally replaced by `scx_bpf_cid_override()` from
  `ops.init_cids()`, retired at root disable. CPUs that were offline get
  cids at the tail with core, LLC and node fields of -1.
- cids need no config symbol. The tables are built for a cpu-form root too.
- cid-form scheduler: one registered as struct_ops type `sched_ext_ops_cid`
  (`struct sched_ext_ops_cid`). `bpf_scx_reg_cid()` requires exactly one BPF
  arena map. All schedulers of a hierarchy share the form
  (`scx_is_cid_type()`).
- Op boundary: `scx_cpu_arg()` converts a CPU to what the op expects and
  `scx_cpu_ret()` converts back; core code keeps CPU numbers.
- `__scx_cid_to_cpu()` and `__scx_cpu_to_cid()`: no range check and no `NULL`
  check of the table; for paths that run only on a live scheduler.
  `scx_cid_to_cpu()` and `scx_cpu_to_cid()` check both and return `-EINVAL`.
