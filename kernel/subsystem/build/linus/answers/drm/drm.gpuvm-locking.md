- `gpuva.lock`: a `struct mutex` embedded in every `struct drm_gem_object`,
  initialised by `drm_gem_private_object_init()`. It is not a pointer and
  no driver supplies it; drm_gem_gpuva_set_lock() is defined nowhere,
  though the kerneldoc of `drm_gem_gpuva_init()` in
  `include/drm/drm_gem.h` and `Documentation/gpu/drm-vm-bind-locking.rst`
  still name it.
- Without `DRM_GPUVM_IMMEDIATE_MODE`: the GEM's dma-resv protects
  `gpuva.list` and `gpuva.lock` is unused.
- `drm_gem_gpuva_assert_lock_held()`: takes the VM as first argument and
  picks the lock from that VM's flag; empty without `CONFIG_LOCKDEP`.
- One GEM mapped by several VMs: the list is shared and the lock is picked
  per VM, so all those VMs must have the same `DRM_GPUVM_IMMEDIATE_MODE`
  setting; nothing checks this.
- Who takes the GEM list lock:

  | Caller must hold it | Takes `gpuva.lock` itself |
  |---|---|
  | `drm_gpuva_link()`, `drm_gpuva_unlink()` | `drm_gpuva_unlink_defer()` |
  | `drm_gpuvm_bo_find()`, `drm_gpuvm_bo_obtain_locked()` | `drm_gpuvm_bo_obtain_prealloc()` |
  | final `drm_gpuvm_bo_put()` | `drm_gpuvm_bo_put_deferred()` |
  | `drm_gpuvm_bo_unmap_ops_create()`, `drm_gpuvm_bo_gem_evict()` | |

- `drm_gpuvm_bo_put()`: takes no GEM list lock; `drm_gpuvm_bo_destroy()`
  asserts it. It calls `might_sleep()`.
- With `DRM_GPUVM_RESV_PROTECTED`: a final `drm_gpuvm_bo_put()` and
  `drm_gpuvm_bo_extobj_add()` also assert the VM's resv.
- `drm_gpuvm_bo_deferred_cleanup()` with `DRM_GPUVM_RESV_PROTECTED`: calls
  `dma_resv_lock()` on the VM's resv itself, so the caller must not hold
  it; `panthor_vm_cleanup_op_ctx()` skips the call on its `vm_bo_validate`
  path for that reason.
- `drm_gpuvm_bo_evict()`: asserts the GEM's dma-resv in every mode, so
  `drm_gpuvm_bo_gem_evict()` on an immediate-mode VM needs the dma-resv
  and `gpuva.lock`.
- `drm_gpuvm_bo_evict()` with `DRM_GPUVM_RESV_PROTECTED` on an external
  object: only sets `evicted`; `drm_gpuvm_prepare_objects()` puts the
  vm_bo on the evict list later.
- Without `DRM_GPUVM_RESV_PROTECTED`: `drm_gpuvm_prepare_objects()` and
  `drm_gpuvm_validate()` are safe against concurrent list insertion and
  removal but not against a second concurrent call on the same VM; each
  list has one `local_list` pointer.
- Lock order where both are held: dma-resv first, then `gpuva.lock`, as in
  `panthor_vm_bo_free()`. GPUVM core defines no order.
- **Unsafe usage**: calling `drm_gpuvm_bo_obtain_prealloc()`,
  `drm_gpuva_unlink_defer()`, or a `drm_gpuvm_bo_put_deferred()` that may
  drop the last reference, with `gpuva.lock` held; each locks the mutex
  again.
  - Safe: `drm_gpuva_link()` under `gpuva.lock`, then unlock, then the
    deferred put, as `panthor_gpuva_sm_step_map()` does through
    `panthor_vma_link()`.
- **Unsafe usage**: a `drm_gpuvm_bo_put()` or `drm_gpuva_unlink()` that may
  drop the last vm_bo reference while `gpuva.lock` is held and the vm_bo's
  GEM reference may be the last; `drm_gpuvm_bo_destroy_not_in_lists()` then
  frees the GEM object that contains the held mutex.
  - Safe: `drm_gpuva_unlink_defer()` or `drm_gpuvm_bo_put_deferred()`
    without the lock held, as `panthor_vma_unlink()` does;
    `drm_gpuvm_bo_defer_free()` unlocks before it queues the vm_bo.
- **Unsafe usage**: allocating memory that can enter reclaim while holding
  `gpuva.lock`; the mutex is taken inside the fence signalling section
  (`panthor_vm_bind_run_job()`), and `drm_gpuvm_bo_obtain_locked()` warns
  on immediate-mode VMs for this reason.
  - Safe: allocate first, lock after: `drm_gpuvm_bo_create()` followed by
    `drm_gpuvm_bo_obtain_prealloc()`, as `panthor_vm_prepare_map_op_ctx()`
    does.
  - Safe: `drm_gpuvm_bo_unmap_ops_create()`, which allocates under the
    asserted list lock, on a VM without `DRM_GPUVM_IMMEDIATE_MODE`, where
    that lock is the dma-resv, as `vm_bind_ioctl_ops_create()` in
    `drivers/gpu/drm/xe/xe_vm.c` does.
- **Potentially unsafe usage**: taking a dma-resv while holding
  `gpuva.lock`.
  - Unsafe: a blocking `dma_resv_lock()`; it inverts the order used by
    `panthor_vm_bo_free()`.
  - Safe: `dma_resv_trylock()` with back-off, as
    `panthor_gem_try_evict_no_resv_wait()` does.
