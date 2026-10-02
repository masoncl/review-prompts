- `pages_use_count`, `pages_pin_count`, `vmap_use_count`: all `refcount_t`.
- `drm_gem_shmem_vmap()`, `drm_gem_shmem_vunmap()`,
  `drm_gem_shmem_madvise()`, `drm_gem_shmem_purge()`: built only under
  `IS_ENABLED(CONFIG_KUNIT)` and exported with `EXPORT_SYMBOL_IF_KUNIT()`.
  Drivers have only the `_locked` forms.
- `drm_gem_shmem_get_pages_locked()`: static. A driver gets pages for example
  through `drm_gem_shmem_pin()` or `drm_gem_shmem_get_pages_sgt()`.
- `drm_gem_shmem_object_pin()`, `drm_gem_shmem_object_unpin()`: call the
  `_locked` forms and need `resv` held, although their kerneldoc names the
  locking forms.
- `drm_gem_shmem_get_sg_table()`: no lock assertion, but reads
  `shmem->pages`; `drm_gem_shmem_get_pages_sgt_locked()` and the
  `get_sg_table` path through `drm_gem_map_dma_buf()` call it with `resv`
  held.
- `drm_gem_shmem_is_purgeable()`: tests `madv > 0`, not a particular value,
  and also requires `sgt` to be set.
- A user mapping does not block a purge: `pages_use_count` is not tested.
  `drm_gem_shmem_purge_locked()` zaps the mapping with `drm_vma_node_unmap()`.
- `drm_gem_shmem_purge_locked()`: only warns when the object is not
  purgeable, then purges anyway; the caller must test first.
