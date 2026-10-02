- A concurrent close drops only the handle's reference. The ioctl's creation
  reference keeps the object alive until the ioctl's own
  `drm_gem_object_put()`.
- **Potentially unsafe usage**: dereferencing the object after
  `drm_gem_handle_create()`.
  - Unsafe: after the ioctl has dropped its creation reference;
    `drm_gem_handle_delete()` from another thread can then free the object.
  - Safe: between `drm_gem_handle_create()` and the put, as
    `panthor_gem_create_with_handle()` reads `bo->base.size`.
  - Safe: copy the value before the handle exists, as `i915_gem_publish()`
    does.
- `drm_gem_dma_create_with_handle()`: reads nothing from the object, and
  returns the pointer after the put. Its two callers only pass it to
  `PTR_ERR_OR_ZERO()`.
- **Potentially unsafe usage**: relying on per-handle state created by
  `funcs->open` after `drm_gem_handle_create()` returns.
  - Unsafe: when the code assumes the state exists; a close that guessed the
    handle has already run `funcs->close`.
  - Safe: look the state up and handle its absence, as
    `panfrost_ioctl_create_bo()` returns `-EINVAL` when
    `panfrost_gem_mapping_get()` finds nothing.
