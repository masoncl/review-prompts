- Lookup and access check: in static `drm_gem_object_lookup_at_offset()` in
  `drivers/gpu/drm/drm_gem.c`, not in the body of `drm_gem_mmap()`.
- `drm_gem_object_lookup_at_offset()`: returns `-ENODEV` first if
  `drm_dev_is_unplugged()`; `drm_gem_get_unmapped_area()` calls it too.
- `drm_gem_mmap_obj()`: takes the reference and sets `vm_private_data` and
  `vma->vm_ops = obj->funcs->vm_ops` before it calls `funcs->mmap`.
- `funcs->mmap` callback: owes `vm_flags` and `vm_page_prot`.
  `drm_gem_mmap_obj()` sets them only when `mmap` is unset, and warns if
  `VM_DONTEXPAND` is missing after the callback.
- Kerneldoc of `mmap` in `include/drm/drm_gem.h`: says the callback must set
  `vma->vm_ops`; the code pre-sets it on both paths.
- `vm_pgoff` on callback entry: includes the fake offset through
  `drm_gem_mmap()` and through `drm_gem_prime_mmap()`, which adds it first.
  `drm_gem_dma_mmap()` subtracts it.
- `drm_gem_prime_mmap()` with a `mmap` callback: makes no access check, and
  sets `vm_private_data` after the callback returns.
- **Potentially unsafe usage**: a `mmap` callback that drops the object
  reference taken by `drm_gem_mmap_obj()`.
  - Unsafe: when the callback returns an error; `drm_gem_mmap_obj()` then
    calls `drm_gem_object_put()` again.
  - Safe: on success only, when something else keeps the mapping alive, as
    `drm_gem_ttm_mmap()` does after `ttm_bo_mmap_obj()` took its own
    reference, and `drm_gem_shmem_mmap()` does after `dma_buf_mmap()` moved
    the vma to the dma-buf file.
