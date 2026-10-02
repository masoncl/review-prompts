- Buddy allocator tests: `drivers/gpu/tests/gpu_buddy_test.c`, with
  `gpu_random.c` beside it, built by `CONFIG_GPU_BUDDY_KUNIT_TEST`; there is
  no drm_buddy_test.c in `drivers/gpu/drm/tests/`.
- Atomic tests: `drm_atomic_test.c` and `drm_atomic_commit_test.c`; there is
  no drm_atomic_state_test.c.
- `drm_panic_test.c` and `drm_client_modeset_test.c`: not in
  `drivers/gpu/drm/tests/Makefile`; `drm_panic.c` and `drm_client_modeset.c`
  `#include` them, so they can reach static functions. The guard is
  `#ifdef CONFIG_DRM_KUNIT_TEST`, which is false when the option is `m`.
- `CONFIG_DRM_KUNIT_TEST_HELPERS`: has no prompt, so only a `select` turns it
  on, as `CONFIG_DRM_TTM_KUNIT_TEST` does.
- `drm_kunit_helper_alloc_device()`: registers a KUnit-bus device with
  `kunit_device_register()`, not a platform device.
- `__drm_kunit_helper_alloc_drm_device_with_driver()`: also calls
  `drmm_mode_config_init()` and sets `mode_config.funcs` to
  `drm_atomic_helper_check()` and `drm_atomic_helper_commit()`.
- Mock `struct drm_device`: the helpers call neither `drm_dev_register()` nor
  `drm_mode_config_reset()`; a test that needs either calls it itself, as
  `drm_atomic_commit_test.c` does for the reset.
- `drm_kunit_helper_atomic_state_alloc()`: returns
  `struct drm_atomic_commit *`; the KUnit action calls
  `drm_atomic_commit_put()`, so the test must not.
- Acquire context: there is no drm_kunit_helper_acquire_ctx_alloc() or other
  helper for it; a test calls `drm_modeset_acquire_init()`, passes the
  context to `drm_kunit_helper_atomic_state_alloc()`, retries through
  `drm_modeset_backoff()` on `-EDEADLK`, then calls
  `drm_modeset_drop_locks()` and `drm_modeset_acquire_fini()`.
- `drm_kunit_helper_enable_crtc_connector()`: can return `-EDEADLK`; the
  caller owns the retry.
- Encoders and connectors: no helper builds them; tests call
  `drmm_encoder_init()` and `drmm_connector_init()` directly.
