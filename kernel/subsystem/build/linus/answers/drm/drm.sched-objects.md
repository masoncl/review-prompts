- Run queue count: `struct drm_sched_init_args.num_rqs` is stored as
  `num_user_rqs`; `num_rqs` in `struct drm_gpu_scheduler` is that value for
  FIFO and RR, and 1 for `DRM_SCHED_POLICY_FAIR`. See `drm_sched_init()` in
  `drivers/gpu/drm/scheduler/sched_main.c`.
- `sched_rq` array: allocated with `args->num_rqs` slots, but only the first
  `num_rqs` are filled; under FAIR every slot above 0 is NULL.
- Policies: three, `DRM_SCHED_POLICY_RR` (0), `DRM_SCHED_POLICY_FIFO` (1) and
  `DRM_SCHED_POLICY_FAIR` (2), defined in
  `drivers/gpu/drm/scheduler/sched_internal.h`.
- Default: `drm_sched_policy` is initialised to `DRM_SCHED_POLICY_FIFO`; there
  is no DRM_SCHED_POLICY_DEFAULT. The parameter text calls FAIR experimental.
- Selection: all three policies pick from the rb-tree `rb_tree_root` through
  one `drm_sched_rq_select_entity()`; inside a run queue they differ only in
  the key written to `entity->oldest_job_waiting`.
  - FIFO: `submit_ts` of the entity's next job.
  - RR: a fake timestamp, `rr_ts`, bumped in `drm_sched_rq_pop_entity()`.
    There is no list walk and no current_entity field.
  - FAIR: a virtual runtime kept in `struct drm_sched_entity_stats`
    (`sched_internal.h`), scaled per priority by `vruntime_shift[]`.
- `entities` list in `struct drm_sched_rq`: still maintained, but not used for
  selection; for example `drm_sched_increase_karma()` walks it.
- Entity fields: `priority` is the user priority, `rq_priority` is the index
  into `sched_rq[]`. Under FAIR `rq_priority` is
  `DRM_SCHED_PRIORITY_KERNEL`.
- `rq_priority`: written only by `drm_sched_entity_init()`;
  `drm_sched_entity_set_priority()` changes `priority` alone.
- `drm_sched_entity_init()`: compares the priority with `num_user_rqs`, not
  `num_rqs`, and the clamp rewrites `entity->priority`.
- `drm_sched_select_entity()`, the loop over run queues: stays in
  `sched_main.c`.
