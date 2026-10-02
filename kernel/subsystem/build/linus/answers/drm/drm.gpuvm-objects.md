- There is no drm_gpuvm_bo_obtain() here; `drm_gpuvm_bo_obtain_locked()` in
  `drivers/gpu/drm/drm_gpuvm.c` is the find-or-create function. Comments in
  that file still use the old name.
- Functions that create or look up a `struct drm_gpuvm_bo`, each returning
  one reference for the caller:

  | Function | GEM list lock | On failure | VM mode |
  |---|---|---|---|
  | `drm_gpuvm_bo_create()` | none; vm_bo is on no list | `NULL` | any |
  | `drm_gpuvm_bo_find()` | caller holds | `NULL` if none | any |
  | `drm_gpuvm_bo_obtain_locked()` | caller holds | `ERR_PTR(-ENOMEM)` | `drm_WARN_ON()` if immediate |
  | `drm_gpuvm_bo_obtain_prealloc()` | takes `gpuva.lock` itself | cannot fail | `drm_WARN_ON()` if not immediate |

- `drm_gpuvm_bo_obtain_prealloc()`, when a vm_bo already exists: drops the
  preallocated one through `drm_gpuvm_bo_destroy_not_in_lists()`, which
  calls `vm_bo_free` if the driver set it and puts the VM and the GEM
  object.
- `drm_gpuvm_bo_obtain_prealloc()` call site: at prepare time, before the
  walk, for example `panthor_vm_prepare_map_op_ctx()`;
  `panthor_gpuva_sm_step_map()` later calls no obtain function, only
  `drm_gpuva_link()` and `drm_gpuvm_bo_put_deferred()` on that vm_bo.
- `struct drm_gpuva`: holds a `struct drm_gpuvm` reference while in the
  tree; `drm_gpuva_insert()` takes it and `drm_gpuva_remove()` drops it.
  `kernel_alloc_node` is the one va that holds none.
- `drm_gpuva_remove()`: may therefore be the final VM put and run
  `vm_free`.
- vm_bo after a deferred final put (`drm_gpuvm_bo_put_deferred()`,
  `drm_gpuva_unlink_defer()`): off the GEM list at once, but still
  allocated on `bo_defer` in `struct drm_gpuvm`, holding its VM and GEM
  references, until `drm_gpuvm_bo_deferred_cleanup()` runs.
- With `DRM_GPUVM_RESV_PROTECTED`, such a vm_bo also stays on the extobj
  and evict lists with refcount zero until then; the list walkers skip it
  with `drm_gpuvm_bo_is_zombie()`.
- `DRM_GPUVM_IMMEDIATE_MODE`: no GPUVM function changes behaviour on it.
  It selects the lock that `drm_gem_gpuva_assert_lock_held()` checks, and
  which functions `drm_WARN_ON()`: `drm_gpuvm_bo_obtain_locked()` when set;
  `drm_gpuvm_bo_obtain_prealloc()`, `drm_gpuvm_bo_put_deferred()` and
  `drm_gpuva_unlink_defer()` when clear.
