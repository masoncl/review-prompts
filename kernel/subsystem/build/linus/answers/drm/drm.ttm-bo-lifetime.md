- Two counts: `kref` in `struct ttm_buffer_object` and `base.refcount` of the
  embedded GEM object. Drivers, handles and dma-bufs hold the GEM count; the
  GEM object as a whole owns one `kref`.
- `ttm_bo_fini()` in `drivers/gpu/drm/ttm/ttm_bo.c`: the exported drop; it is
  one `ttm_bo_put()`, which puts `bo->kref` with `ttm_bo_release()`.
- `ttm_bo_put()`, `ttm_bo_get()`, `ttm_bo_get_unless_zero()`: TTM-internal,
  in `drivers/gpu/drm/ttm/ttm_bo_internal.h`; `ttm_bo_put()` is not exported.
- Driver drop path: `drm_gem_object_put()`; the driver's
  `struct drm_gem_object_funcs` `.free` calls `ttm_bo_fini()`, for example
  `amdgpu_gem_object_free()`.
- After `ttm_bo_fini()` the `.free` callback must not free the object:
  `ttm_bo_release()` calls `bo->destroy`, at once or later, normally from
  `bdev->wq`, and `destroy` frees the containing struct.
- GEM count zero with `bo->kref` non-zero is a normal state: TTM's LRU walk
  and ghost objects hold `bo->kref` only. A driver callback that needs
  GEM-level state first tries `kref_get_unless_zero()` on `base.refcount`, as
  `xe_bo_get_unless_zero()` does.
- `ttm_bo_init_reserved()`: does not initialise the embedded GEM object. It
  reads `bo->base.size`, uses `bo->base.vma_node`, overwrites `bo->base.resv`
  and, with a NULL `resv`, trylocks `bo->base._resv`.
  `drm_gem_private_object_init()` prepares those; `nouveau_bo_new()` sets
  them by hand and leaves `bo->base.dev` NULL.
- `ttm_bo_release()` defers destruction when any of these holds: unsignalled
  `DMA_RESV_USAGE_BOOKKEEP` fences on `bo->base._resv`;
  `want_init_on_free()` and `bo->ttm` set; `ttm_bo_type_sg`; trylock of
  `bo->base.resv` fails. An idle BO is therefore deferred too under
  init-on-free.
- There is no ttm_bo_cleanup_refs() and no delayed-destroy list; each zombie
  queues its own `bo->delayed_delete` work, `ttm_bo_delayed_delete()`.
- A zombie stays on the LRU. `ttm_bo_evict_cb()`, `ttm_bo_swapout_cb()` and
  `ttm_bo_evict_first()` test `bo->deleted` and call
  `ttm_bo_cleanup_memtype_use()` early; `ttm_bo_delayed_delete()` calls it
  again, so `delete_mem_notify` can run twice, the second time with
  `bo->resource == NULL`.
- **Potentially unsafe usage**: calling `ttm_bo_fini()` outside the GEM
  `.free` callback.
  - Unsafe: on a BO whose GEM object has a `.free` callback that can still
    run; GEM holders keep using the BO, and `.free` later puts `bo->kref` a
    second time.
  - Safe: on a BO that never had a GEM object initialised, so no `.free`
    exists for it, as `nouveau_bo_unpin_del()` does for BOs from
    `nouveau_bo_new()`; `ttm_bo_fini()` is the single put of the `kref_init()`
    in `ttm_bo_init_reserved()`.
  - Safe: after the GEM count reached zero, from work that the `.free`
    callback queued, as `i915_ttm_delayed_free()` does; it is reached only
    through `i915_gem_free_object()`.
  - Safe: on a BO whose GEM object has no `funcs`, so no `.free` exists for
    it, as the KUnit test `ttm_bo_init_reserved_sys_man()` does; the
    `kref_init()` in `ttm_bo_init_reserved()` is the only reference.
- **Unsafe usage**: passing a NULL `destroy` to `ttm_bo_init_reserved()` or
  `ttm_bo_init_validate()`; the kerneldoc promises `kfree()`, but
  `ttm_bo_release()` calls `bo->destroy(bo)` with no NULL test.
  - Safe: always pass a function; `amdgpu_bo_create()` substitutes
    `amdgpu_bo_destroy()` when its parameter is NULL.
