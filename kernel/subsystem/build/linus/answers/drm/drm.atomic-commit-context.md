- `commit_tail()` and `drm_atomic_helper_commit_tail()`: do not call
  `dma_fence_begin_signalling()`, so lockdep does not flag a `GFP_KERNEL`
  allocation in a tail callback on the helper path.
- A driver's own `atomic_commit_tail` can add the annotation, for example
  `komeda_kms_commit_tail()`; callbacks run inside it are then checked.
- `handle_vblank_timeout` in `struct drm_crtc_helper_funcs`: runs from the
  hrtimer callback `drm_vblank_timer_function()`.
- `get_scanout_buffer` and `panic_flush` in `struct drm_plane_helper_funcs`
  (`CONFIG_DRM_PANIC`): run during a panic under `drm_panic_trylock()`, a
  raw spinlock with interrupts off; see `drivers/gpu/drm/drm_panic.c`.
- `get_vblank_timestamp`: also called with no lock held, from
  `drm_crtc_next_vblank_start()`; it still must not sleep because the other
  callers hold `dev->vblank_time_lock`.
- Tail callbacks can be atomic by the driver's own choice: for example
  `vkms_crtc_atomic_begin()` takes a spinlock with `spin_lock_irq()` that
  `vkms_crtc_atomic_flush()` releases, so that driver's plane
  `atomic_update` runs with interrupts off.
- **Potentially unsafe usage**: a synchronous runtime-PM resume, such as
  `pm_runtime_resume_and_get()`, in `enable_vblank`.
  - Unsafe: when the device can be suspended at that point; the resume
    sleeps under `dev->vbl_lock` with interrupts off.
  - Safe: when the device is already `RPM_ACTIVE` whenever vblank can be
    enabled, as in `tidss_crtc_enable_vblank()`:
    `tidss_crtc_atomic_enable()` takes the runtime-PM reference before
    `drm_crtc_vblank_on()` and `tidss_crtc_atomic_disable()` drops it after
    `drm_crtc_vblank_off()`. `might_sleep_if()` in `__pm_runtime_resume()`
    defines the condition.
