- Retry order with atomic state: `drm_atomic_commit_clear()`, then
  `drm_modeset_backoff()`, then retry; see `drm_mode_atomic_ioctl()`.
- **Potentially unsafe usage**: returning `-EDEADLK` from a modeset lock call
  without `drm_modeset_backoff()`.
  - Unsafe: in the function that called `drm_modeset_acquire_init()` on the
    context; `drm_modeset_drop_locks()` warns while `ctx->contended` is set,
    and the error leaves the retry loop.
  - Safe: in a function that got the context from its caller; it returns
    `-EDEADLK` unchanged, as `drm_modeset_lock_all_ctx()`,
    `drm_atomic_get_crtc_state()` and `drm_atomic_helper_set_config()` do.
- `drm_modeset_backoff()` can fail only for a context made with
  `DRM_MODESET_ACQUIRE_INTERRUPTIBLE`; then return its error, do not retry.
- `drm_modeset_backoff()` on a context with flags 0: always 0;
  `drm_helper_probe_detect_ctx()` ignores the result.
- `drm_modeset_lock_all()`: handles `-EDEADLK` itself in a backoff loop and
  returns void.
- `drm_modeset_lock_all()` is brittle because its context is stored in
  `mode_config.acquire_ctx` and it takes `mode_config.mutex` first; a nested
  call blocks on that mutex before it reaches `WARN_ON(config->acquire_ctx)`.
- `DRM_MODESET_LOCK_ALL_BEGIN()`: takes `mode_config.mutex` only when
  `drm_drv_uses_atomic_modeset()` is false; `DRM_MODESET_LOCK_ALL_END()`
  releases it under the same test.
- `DRM_MODESET_LOCK_ALL_END()`: leaves `ret` alone unless it is `-EDEADLK`;
  then `ret` becomes the result of `drm_modeset_backoff()`.
