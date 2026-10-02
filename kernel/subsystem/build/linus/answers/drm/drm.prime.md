- `drm_gem_is_imported()`: returns `!!obj->import_attach`. It does not look
  at `obj->dma_buf`.
- An import whose driver left `import_attach` NULL: tests as not imported.
- `if (obj->import_attach)`: same result as `drm_gem_is_imported()` here;
  `drm_gem_prime_handle_to_dmabuf()` tests the field directly.
- **Unsafe usage**: testing `obj->dma_buf` to decide whether an object is
  imported. `export_and_register_object()` sets it for exports,
  `drm_gem_prime_fd_to_handle()` sets it for imports, and
  `drm_gem_object_exported_dma_buf_free()` clears it at last handle close.
  - Safe: `drm_gem_is_imported()`, as `drm_gem_shmem_vmap_locked()` does;
    `import_attach` is set once at import, for example in
    `drm_gem_prime_import_dev()`.
- Self-import test: `drm_gem_is_prime_exported_dma_buf()` in
  `drivers/gpu/drm/drm_prime.c`, exported; `drm_gem_prime_import_dev()` and
  `drm_gem_shmem_prime_import_no_map()` call it.
- A driver whose `export` uses its own `struct dma_buf_ops`: fails that test,
  since it compares against `drm_gem_prime_dmabuf_ops`. Such a driver needs
  its own check, as `amdgpu_gem_prime_import()` has.
