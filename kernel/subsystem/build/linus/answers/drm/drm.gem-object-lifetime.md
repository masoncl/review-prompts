- `handle_count`: all handles together hold one `refcount` reference, not one
  each. `drm_gem_object_handle_get()` takes it on 0 -> 1 and
  `drm_gem_object_handle_put_unlocked()` drops it on 1 -> 0.
- `handle_count` also counts framebuffers: `drm_framebuffer_init()` takes one
  handle reference per plane with
  `drm_gem_object_handle_get_if_exists_unlocked()`, recorded in
  `DRM_FRAMEBUFFER_HAS_HANDLE_REF()`, and `drm_framebuffer_cleanup()` drops it.
- Closing every user handle while a framebuffer holds a handle reference:
  `obj->name` and `obj->dma_buf` stay set.
- `drm_gem_object_handle_put_unlocked()`: takes `dev->object_name_lock`
  itself, so the caller must not hold it. `drm_gem_handle_delete()` has only
  replaced the idr slot with NULL by then, and `drm_gem_release()` calls it
  with the entry still in `object_idr`.
- Put functions in `include/drm/drm_gem.h`: `drm_gem_object_put()`, which
  accepts NULL, and `__drm_gem_object_put()`, which does not.
- drm_gem_object_put_locked: named in the kerneldoc of `refcount`, defined
  nowhere.
