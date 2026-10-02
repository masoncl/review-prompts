- `xe_guc_ct_init_noalloc()`: allocates no BO, but does allocate: it calls
  `alloc_ordered_workqueue()` and registers drm-managed actions, so it can
  fail with `-ENOMEM`.
- `xe_guc_ct_init()`: creates two BOs, `ct->ctbs.h2g.bo` and
  `ct->ctbs.g2h.bo`, in system memory, and registers
  `guc_action_disable_ct()` as a devm action.
- `xe_guc_ct_init_post_hwconfig()`: moves only the H2G BO to VRAM, only
  when `IS_DGFX()`; the G2H BO stays in system memory.
- `xe_guc_init_post_hwconfig()` returns through the VF branch first, so
  `xe_guc_ct_init_post_hwconfig()` is not called on a VF.
- `xe_guc_ct_restart()`: same as `xe_guc_ct_enable()` but skips the CTB
  re-initialisation, the registration with the GuC and
  `guc_ct_control_toggle()`; `xe_guc_ct_runtime_resume()` uses it.
- `stack_depot_init()`: called in `ct_dead_init()`, which
  `xe_guc_ct_init_noalloc()` calls; compiled only under
  `CONFIG_DRM_XE_DEBUG_GUC` nested inside `CONFIG_DRM_XE_DEBUG`.
- `fast_req_stack_save()`: the only caller of `stack_depot_save()` in xe;
  `ct_dead_capture()` saves no stack trace.
- `fast_req_stack_save()` runs from `h2g_write()`, which asserts
  `ct->lock` (a mutex) is held.
- **Potentially unsafe usage**: calling `stack_depot_save()` from xe code.
  - Unsafe: in code built without `CONFIG_DRM_XE_DEBUG_GUC`; xe has not
    called `stack_depot_init()`, and `stack_depot_save_flags()` in
    `lib/stackdepot.c` tests `stack_depot_disabled` but not `stack_table`
    for NULL before it indexes `stack_table`.
  - Safe: under `#if IS_ENABLED(CONFIG_DRM_XE_DEBUG_GUC)`, the same guard
    as the init and as the `stack` field of `struct xe_fast_req_fence`, as
    `fast_req_stack_save()` does.
- **Unsafe usage**: a GFP mask that allows direct reclaim for
  `stack_depot_save()` on the CT send path.
  - Unsafe: `primelockdep()` declares `ct->lock` as taken inside
    `fs_reclaim`, so reclaim under `ct->lock` is a lock inversion.
  - Safe: `GFP_NOWAIT`, as `fast_req_stack_save()` uses; `fast_req_dump()`
    prints a fallback when the handle is 0.
