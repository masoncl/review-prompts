- `drm_atomic_helper_setup_commit()` stores the new commit in
  `new_crtc_state->commit` but does not put it on `crtc->commit_list`;
  `drm_atomic_helper_swap_state()` adds it under `commit_lock`.
- Private object states get no commit: `struct drm_private_state` has no such
  member. A driver orders them itself through `atomic_commit_setup` in
  `struct drm_mode_config_helper_funcs`, as `vc4_atomic_commit_setup()` does.

| Where | Waits for | Result |
|---|---|---|
| `stall_checks()` | `flip_done` of the newest commit on the CRTC | nonblocking: `-EBUSY`; blocking: no wait here |
| `stall_checks()` | `cleanup_done` of the second-newest commit | both modes; interruptible, 10 s; a timeout only logs |
| `drm_atomic_helper_setup_commit()` | `flip_done` of the commit in an old plane or connector state | nonblocking: `-EBUSY` |
| `drm_atomic_helper_swap_state()`, `stall` true | `hw_done` of commits in old CRTC, connector, plane states | interruptible, no timeout |
| `drm_atomic_helper_wait_for_dependencies()` | `hw_done`, then `flip_done`, via `drm_crtc_commit_wait()` | 10 s each; a timeout only logs |

- `flip_done` is completed in `drm_send_event_helper()` in
  `drivers/gpu/drm/drm_file.c` when the event is delivered.
- `fake_commit` (planes and connectors with no CRTC): `hw_done` and
  `flip_done` are completed by `drm_atomic_helper_commit_hw_done()`,
  `cleanup_done` by `drm_atomic_helper_commit_cleanup_done()`.
- An `atomic_commit_tail` hook under `drm_atomic_helper_commit()` must call
  `drm_atomic_helper_commit_hw_done()` and consume every
  `new_crtc_state->event`; `commit_tail()` does the dependency wait before
  the hook and the cleanup_done call after it.
- `drm_atomic_helper_commit_cleanup_done()` takes the commit from
  `old_crtc_state->commit`, which `drm_atomic_helper_commit_hw_done()` fills;
  without hw_done first it hits `WARN_ON(!commit)` or completes an older
  commit.
- **Potentially unsafe usage**: a driver calling
  `drm_atomic_helper_commit_cleanup_done()` itself.
  - Unsafe: from an `atomic_commit_tail` hook; `commit_tail()` calls it again
    after the hook, and each call does `list_del()` on `commit_entry`.
  - Safe: in a driver with its own `atomic_commit` that never enters
    `commit_tail()`, as `nv50_disp_atomic_commit_tail()` does.
