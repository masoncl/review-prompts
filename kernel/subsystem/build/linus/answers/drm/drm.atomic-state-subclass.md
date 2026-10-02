- `atomic_create_state`: hook in `struct drm_crtc_funcs`,
  `struct drm_plane_funcs` and `struct drm_connector_funcs`, an alternative
  to `reset`. It returns a new state; the core assigns `obj->state`.
- Subclassed `atomic_create_state`: allocate the driver struct zeroed, then
  call `__drm_atomic_helper_crtc_state_init()`,
  `__drm_atomic_helper_plane_state_init()` or
  `__drm_atomic_helper_connector_state_init()` on the embedded base; see
  `tidss_crtc_create_state()`.
- `atomic_create_state` failure: `ERR_PTR()`. The callers in
  `drivers/gpu/drm/drm_mode_config.c` test `IS_ERR()` only, so NULL is
  installed as the state. `atomic_duplicate_state` fails with NULL.
- `drm_mode_config_reset()`: calls `reset` when set; otherwise, when
  `atomic_create_state` is set, it destroys the current state with
  `atomic_destroy_state` and installs a new one.
- `drm_mode_config_create_initial_state()`: fills only objects whose `state`
  is NULL and calls no `reset` hook.
- `drm_crtc_vblank_reset()`: `__drm_atomic_helper_crtc_reset()` calls it;
  `__drm_atomic_helper_crtc_state_init()` does not, and
  `drm_mode_config_crtc_create_state()` calls it instead. Both only when
  `drm_dev_has_vblank()`.
- Plane property defaults: there is no __drm_atomic_helper_plane_state_reset()
  here; `__drm_atomic_helper_plane_state_init()` sets them and
  `__drm_atomic_helper_plane_reset()` calls it.
- Base-state fields that the duplicate helper clears instead of taking a
  reference, for example in `__drm_atomic_helper_plane_duplicate_state()`,
  and what the destroy helper does with them:

| Field | Duplicate helper | Destroy helper |
|---|---|---|
| `commit` (CRTC, plane, connector) | sets NULL | `drm_crtc_commit_put()` |
| plane `fence` | sets NULL | `dma_fence_put()` |
| plane `fb_damage_clips` | sets NULL | `drm_property_blob_put()` |
| connector `writeback_job` (not refcounted) | sets NULL | `drm_writeback_cleanup_job()` |

- Connector `hdr_output_metadata`:
  `__drm_atomic_helper_connector_duplicate_state()` takes a reference with
  `drm_property_blob_get()` and
  `__drm_atomic_helper_connector_destroy_state()` drops it with
  `drm_property_blob_put()`.
- `commit` reference: set in `drm_atomic_helper_setup_commit()`, not in
  duplicate.
- **Potentially unsafe usage**: installing a state allocated by a default
  helper, for example `drm_atomic_helper_plane_reset()`, on an object whose
  driver converts the state with `container_of()` to a larger struct.
  - Unsafe: when a hook can read or write a driver field of that state; the
    default helpers allocate `sizeof` the base state only, see
    `kzalloc_obj()` in `drm_atomic_helper_plane_reset()`.
  - Safe: every hook that allocates does so for the driver struct, as
    `tidss_crtc_create_state()` and `tidss_crtc_duplicate_state()` do.
  - Safe: every access to a driver field is behind a test that the default
    state fails, as `virtio_gpu_plane_prepare_fb()` and
    `virtio_gpu_plane_cleanup_fb()` return for a NULL `fb`, which
    `kzalloc_obj()` in `drm_atomic_helper_plane_reset()` leaves NULL.
