- `free`: mandatory. Without it `drm_gem_object_free()` warns and returns, and
  the object is never freed.
- `obj->funcs`: must be set. `drm_gem_object_free()`,
  `drm_gem_handle_create_tail()` and `drm_gem_mmap_obj()` dereference it
  without a NULL test.
- `vm_ops`: required when `mmap` is unset; `drm_gem_mmap_obj()` otherwise
  returns `-EINVAL`.
- `pin`, `unpin`: there is no drm_gem_pin_locked or drm_gem_pin here. The
  only callers are `drm_gem_map_attach()` and `drm_gem_map_detach()` in
  `drivers/gpu/drm/drm_prime.c`, which lock `obj->resv` around the call.
- `get_sg_table`: `drm_gem_map_dma_buf()` takes no lock itself; `resv` is
  held on that path because `dma_buf_map_attachment()` asserts it before
  calling `map_dma_buf`.
- `status`, `rss`: called by `drm_show_memory_stats()` under the spinlock
  `file->table_lock`, without `resv`; they must not sleep.
- `evict`: `drm_gem_evict_locked()` asserts `resv`, but nothing in this tree
  installs `evict` or calls `drm_gem_evict_locked()`; drm_gem_object_evict,
  named in the kerneldoc, does not exist.
