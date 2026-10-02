- Where the event comes from: user space, for example through
  `prepare_signaling()` in `drivers/gpu/drm/drm_atomic_uapi.c` for events
  and out-fences, or `page_flip_common()` for the legacy page flip; else
  `drm_atomic_helper_setup_commit()` allocates one.
- `drm_atomic_helper_setup_commit()` installs no event when old and new
  CRTC state are both inactive, or on `legacy_cursor_update`; it completes
  `flip_done` at once. `crtc_state->event` can be NULL in the tail.
- After the swap the driver is the only owner:
  `drm_atomic_helper_swap_state()` clears `commit->event`, so state destroy
  no longer frees the event.
- After send or arm the event belongs to the core: `drm_send_event_helper()`
  frees it or moves it to the file's event list.
- **Unsafe usage**: leaving `crtc_state->event` set after sending or arming
  it, on a commit set up by `drm_atomic_helper_setup_commit()`.
  - Safe: set it to NULL before `drm_atomic_helper_commit_hw_done()`, as
    `drm_crtc_vblank_atomic_flush()` does.
    `drm_atomic_helper_commit_hw_done()` has a `WARN_ON()` for it, and
    `__drm_atomic_helper_crtc_destroy_state()` does an extra
    `drm_crtc_commit_put()` when `state->event` is non-NULL and
    `abort_completion` is set.
- `drm_crtc_send_vblank_event()`: the lock is asserted in
  `drm_send_event_helper()`, not in the function itself.
- `drm_crtc_send_vblank_event()` without `drm_vblank_init()`: sends
  sequence 0 and `ktime_get()`.
- `drm_crtc_arm_vblank_event()`: the target is the vblank count at the call
  plus 1; nothing ties it to the hardware latch. An interrupt handled
  between the register write and the arm delays the event by one frame.
- Armed event without a vblank reference: on delivery `drm_vblank_put()`
  either WARNs and returns (count 0) or drops a reference owned by someone
  else.
- Armed events are delivered, and their reference dropped, by
  `drm_handle_vblank_events()` or by `drm_crtc_vblank_off()`.
- `drm_crtc_vblank_off()`: takes `dev->event_lock` itself with
  `spin_lock_irq()`; call it outside the lock and with interrupts enabled,
  and send `crtc->state->event` in a separate locked section.
