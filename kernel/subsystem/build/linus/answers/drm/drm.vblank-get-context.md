- `drm_crtc_vblank_put()`: takes no lock itself. Only with
  `offdelay_ms < 0` does the last put run `vblank_disable_fn()`, and with it
  `disable_vblank`, in the caller's context; that path uses
  `spin_lock_irqsave()` and is safe from hard interrupt context.
- `drm_crtc_vblank_get()`: on the first reference it runs the driver's
  `enable_vblank` in the caller's context, under `dev->vbl_lock` and
  `dev->vblank_time_lock`.
- Inside `enable_vblank`, `disable_vblank`, `get_vblank_counter` and
  `get_vblank_timestamp`: `drm_crtc_vblank_get()` must not be called;
  `drm_vblank_get()` takes `dev->vbl_lock`, which `drm_vblank_enable()` and
  `drm_vblank_disable_and_save()` assert is already held. A last
  `drm_crtc_vblank_put()` with `offdelay_ms < 0` takes the same lock in
  `vblank_disable_fn()`.
- Lock order: `dev->event_lock`, then `dev->vbl_lock`, then
  `dev->vblank_time_lock`; see `drm_crtc_vblank_off()`.
- Under `dev->event_lock`: both calls are allowed, as
  `drm_crtc_vblank_atomic_flush()` and `drm_handle_vblank_events()` do.
