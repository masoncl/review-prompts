- `drm_dev_enter()` protects a `devm_` resource only in a driver that calls
  `drm_dev_unplug()`. `dev->unplugged` is set nowhere else except the
  `drm_dev_register()` error path.
- `devm_drm_dev_init_release()`: only calls `drm_dev_put()`. It is not a
  hardware teardown hook and runs no driver code unless that put is the last.
- Devres is released in reverse order, see `release_nodes()` in
  `drivers/base/devres.c`. Every `devm_` resource acquired on the same device
  after `devm_drm_dev_alloc()` is gone before `struct drm_driver.release` and
  the `drmm_` actions can run.
- `devm_drm_bridge_alloc()` and `devm_drm_panel_alloc()`: the memory is
  `kzalloc()` plus a kref. The devres action only drops one reference, so the
  object is not freed at unbind while `drm_bridge_get()` or `drm_panel_get()`
  holders remain.
- `drm_managed_release()` frees a `drmm_kzalloc()` block before it runs any
  action registered earlier. An action must not touch `drmm_` memory allocated
  after the action was added.
- `drmm_mode_config_init()` is such an earlier action. It runs
  `drm_mode_config_cleanup()`, which calls `->destroy` on every encoder,
  colorop, plane and CRTC still on the lists.
- `drmm_crtc_alloc_with_planes()`, `drmm_crtc_init_with_planes()`,
  `drmm_encoder_alloc()`, `drmm_encoder_init()`,
  `drmm_universal_plane_alloc()` and `drmm_connector_init()`: each registers
  its own cleanup action after it initialises the object; the action unlinks
  the object before `drmm_` memory allocated earlier is freed.
- Those `drmm_` helpers warn when `->destroy` is set. `drm_crtc_init_with_planes()`,
  `drm_encoder_init()`, `drm_universal_plane_init()` and `drm_connector_init()`
  warn when it is not.
- **Potentially unsafe usage**: `drmm_kzalloc()` for a KMS object that is
  initialised with a non-`drmm_` init function.
  - Unsafe: when `drmm_mode_config_init()` was called before the allocation
    and nothing removes the object earlier; `drm_mode_config_cleanup()` then
    calls `->destroy` on freed memory.
  - Safe: allocation made before `drmm_mode_config_init()`, as
    `virtio_gpu_init()` does for the outputs in `struct virtio_gpu_device`;
    `drm_managed_release()` runs the later `drm_mode_config_cleanup()` action
    before it frees the earlier block.
  - Safe: `drmm_kzalloc()` followed by the `drmm_` init function, or the
    `drmm_` alloc helper, as `__drmm_crtc_alloc_with_planes()` does; the
    cleanup action is added after the allocation, so `drm_managed_release()`
    runs it before it frees the block.
  - Safe: object embedded in the `devm_drm_dev_alloc()` container, as
    `gm12u320_usb_probe()` does; `drm_dev_release()` frees the container
    after `drm_managed_release()`.
- Action registered with `data` `NULL`: the callback receives `NULL`, and
  `drmm_release_action()` with `data` `NULL` matches the earliest added
  entry with that function.
