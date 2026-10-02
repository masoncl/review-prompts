| Job | Type | Core code | Config |
|---|---|---|---|
| Address range | `struct drm_mm` | `drivers/gpu/drm/drm_mm.c` | part of the DRM core |
| Power-of-two blocks | `struct gpu_buddy` | `drivers/gpu/buddy.c`, `include/linux/gpu_buddy.h` | `CONFIG_GPU_BUDDY` |
| Short-lived, fenced | `struct drm_suballoc_manager` | `drivers/gpu/drm/drm_suballoc.c` | `CONFIG_DRM_SUBALLOC_HELPER` |

- There is no struct drm_buddy, drm_buddy_alloc_blocks() or
  DRM_BUDDY_RANGE_ALLOCATION here. The calls are `gpu_buddy_init()`,
  `gpu_buddy_alloc_blocks()`, `gpu_buddy_free_list()`,
  `gpu_buddy_block_trim()`, with flags such as `GPU_BUDDY_RANGE_ALLOCATION`.
- `include/drm/drm_buddy.h` and `drivers/gpu/drm/drm_buddy.c` hold only
  `drm_buddy_print()` and `drm_buddy_block_print()`, which take
  `struct gpu_buddy`. `CONFIG_DRM_BUDDY` selects `CONFIG_GPU_BUDDY`.
- Buddy locking: none inside. A driver can register its lock with
  `gpu_buddy_driver_set_lock()`; exported calls such as
  `gpu_buddy_alloc_blocks()` and `gpu_buddy_free_list()` then assert it
  through `gpu_buddy_driver_lock_held()`. `gpu_buddy_init()`,
  `gpu_buddy_fini()` and `gpu_buddy_block_print()` do not assert.
- `gpu_buddy_driver_lock_held()` checks nothing without `CONFIG_LOCKDEP`, or
  when no lock was registered; in this tree only
  `drivers/gpu/drm/xe/xe_ttm_vram_mgr.c` registers one.
- The buddy caller's lock must allow sleeping: `gpu_block_alloc()` allocates
  with `GFP_KERNEL` when a block is split, and `gpu_buddy_free_list()` calls
  `cond_resched()` per block.
- `drm_mm_scan_init()` exists, as a static inline in `include/drm/drm_mm.h`
  that calls `drm_mm_scan_init_with_range()`.
- `struct amdgpu_sa_manager` and `struct radeon_sa_manager` still exist; each
  embeds `struct drm_suballoc_manager` as `base`, and `amdgpu_sa_bo_new()`
  calls `drm_suballoc_new()`.
- Suballoc two-step form: `drm_suballoc_alloc()` allocates the object, then
  `drm_suballoc_insert()` places it; `drm_suballoc_new()` is both.
  `drm_suballoc_free()` on an object that was never inserted just frees it.
- Suballoc locking: `sa_manager->wq.lock`, taken with plain `spin_lock()`,
  which does not disable interrupts. `drm_suballoc_manager_fini()` takes no
  lock.
