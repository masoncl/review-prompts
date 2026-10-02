- The container is `struct drm_atomic_commit`, defined in
  `include/drm/drm_atomic.h`; no struct named drm_atomic_state exists in this
  tree.

| Name from memory | Name in this tree |
|---|---|
| drm_atomic_state_alloc() | `drm_atomic_commit_alloc()` |
| drm_atomic_state_get() | `drm_atomic_commit_get()` |
| drm_atomic_state_put() | `drm_atomic_commit_put()` |
| drm_atomic_state_clear() | `drm_atomic_commit_clear()` |
| drm_atomic_state_init() | `drm_atomic_commit_init()` |
| drm_atomic_state_default_clear() | `drm_atomic_commit_default_clear()` |
| drm_atomic_state_default_release() | `drm_atomic_commit_default_release()` |
| __drm_atomic_state_free() | `__drm_atomic_commit_free()` |

- `drm_atomic_commit()` is a function (check, then commit, blocking); it is
  not a constructor for the struct of the same name.
- `struct drm_crtc_commit` is the per-CRTC completion tracker, not the
  container.
- Not renamed: the hooks `atomic_state_alloc`, `atomic_state_clear` and
  `atomic_state_free`; the iterators such as
  `for_each_oldnew_crtc_in_state()`; `drm_atomic_helper_swap_state()`; the
  back pointer field `state` in each object state; and most variables of the
  container type, which are still called `state`.
- Array entries for planes, CRTCs, connectors and private objects hold `ptr`,
  `state_to_destroy`, `old_state` and `new_state`; only
  `struct __drm_colorops_state` still has a field named `state`.
- `state_to_destroy`: equals `new_state` until
  `drm_atomic_helper_swap_state()`, equals `old_state` after it;
  `drm_atomic_commit_default_clear()` destroys that one.
- Back pointer after swap: `new_state->state` is NULL and `old_state->state`
  points at the container, so a commit hook cannot reach the container through
  a new state.
- During check, `obj->state` of an object in the update is the same pointer as
  its `old_state`; the getters store it under the modeset lock they take.
- `drm_atomic_helper_commit_planes()` reads `crtc->state` itself, in
  `plane_crtc_active()`; when that is valid in commit code is under "Commit
  sequence".
