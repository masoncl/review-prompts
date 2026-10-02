- `drm_file_free()`: does not drop the open file's device reference.
  `drm_minor_release()` drops it as the last step of `drm_release()` and
  `drm_release_noglobal()`, so `struct drm_driver.postclose` and
  `drm_lastclose()` still run with the reference held.
- `accel_open()` in `drivers/accel/drm_accel.c`: takes the same reference
  through `drm_minor_acquire()`.
- Open files are not the only holders after unbind: search `drm_dev_get(`; for
  example `drm_gem_dmabuf_export()` holds one until `drm_gem_dmabuf_release()`.
- `devm_drm_dev_alloc()` does not go through `drm_dev_alloc()`. The chain is
  `__devm_drm_dev_alloc()` -> `devm_drm_dev_init()` -> `drm_dev_init()`.
- `drm_dev_alloc()` and `__drm_dev_alloc()`: register no devres action; the
  driver drops the initial reference itself with `drm_dev_put()`.
- `drm_dev_init()` and `devm_drm_dev_init()` are static in
  `drivers/gpu/drm/drm_drv.c`; a driver cannot initialise a
  `struct drm_device` inside memory it allocated itself.
- Container from `__devm_drm_dev_alloc()`: plain `kzalloc()`, not on the
  `drmm_` list. `drm_dev_release()` frees it with
  `kfree(dev->managed.final_kfree)` after `drm_managed_release()` returns, so
  `struct drm_driver.release` and every `drmm_` action may still use fields
  embedded in it.
