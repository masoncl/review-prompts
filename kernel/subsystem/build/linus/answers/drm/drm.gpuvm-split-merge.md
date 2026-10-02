- `struct drm_gpuvm_map_req`: its only member is `map`.
- A failing step: the walk stops and `drm_gpuvm_sm_map()` or
  `drm_gpuvm_sm_unmap()` returns the callback's error; core rolls nothing
  back. For example `panthor_vm_bind_run_job()` then marks the VM unusable,
  through `panthor_vm_exec_op()` and `panthor_vm_declare_unusable()`.
- Preallocation is not a core requirement: it is needed only when the walk
  runs where allocation is forbidden. `msm_gem_vm_sm_step_map()` allocates
  inside the callback, because `vm_bind_job_prepare()` runs the walk at
  ioctl time and queues only the page-table updates.
- Preallocation for a walk inside the fence signalling section: see
  `panthor_vm_op_ctx_prealloc_vmas()` (three vas for map, two for unmap)
  and `panthor_vm_prepare_map_op_ctx()` (vm_bo, page tables).
- `drm_gpuvm_sm_map()` sequence: never empty on success; the map step for
  the request is always issued last. An identical existing mapping yields
  an unmap step followed by the map step, contrary to the kerneldoc.
- `drm_gpuvm_sm_unmap()` sequence: empty when nothing overlaps.
- `drm_gpuva_map()` and `drm_gpuva_remap()`: return void and discard the
  result of `drm_gpuva_insert()`, which can be `-EINVAL` or `-EEXIST`; on
  failure the va is not in the tree and holds no VM reference.
- `struct drm_gpuva_op` passed to a callback: lives on the stack of
  `op_map_cb()`, `op_remap_cb()` or `op_unmap_cb()`, and a remap's `prev`,
  `next` and `unmap` point at locals of the walker. A driver that keeps a
  step for later must copy all of them, as `drm_gpuva_sm_step()` does.
- Ops list: its ops hold bare `struct drm_gpuva` pointers with no
  reference, so the driver must keep each named va allocated until the ops
  are used.
- Ops-list creation failure: returns an `ERR_PTR`, frees the partial list
  and leaves the VM untouched.
- `drm_gpuvm_madvise_ops_create()`: exists, in ops-list form only. It emits
  no unmap steps, only remap and map steps, and skips every existing va
  that has a GEM object; `xe_vm_alloc_vma()` in
  `drivers/gpu/drm/xe/xe_vm.c` is its caller.
