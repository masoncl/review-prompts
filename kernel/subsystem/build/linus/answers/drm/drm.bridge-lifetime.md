- Chain iterators: there is no drm_for_each_bridge_in_chain_scoped() here;
  `drm_for_each_bridge_in_chain()` and `drm_for_each_bridge_in_chain_from()`
  in `include/drm/drm_bridge.h` declare the cursor themselves and drop the
  reference on any exit from the loop.
- Both iterators hold `encoder->bridge_chain_mutex` for the whole walk, so the
  body must not start another walk or attach a bridge on the same encoder.
- Lookups, by what the caller gets:

  | Function | Returned bridge |
  |---|---|
  | `of_drm_find_and_get_bridge()` | counted, NULL on failure |
  | `of_drm_get_bridge_by_endpoint()` | counted, `ERR_PTR()` on failure |
  | `of_drm_find_bridge()` | not counted (gets, then puts) |
  | `drm_of_find_panel_or_bridge()` | not counted |
  | `devm_drm_of_get_bridge()` | not counted |
  | `drmm_of_get_bridge()` | not counted |

- `drm_of_find_panel_or_bridge()`: the panel it returns is counted, drop it
  with `drm_panel_put()`; a NULL `panel` argument returns `-EINVAL`.
- `bridge->next_bridge`: `__drm_bridge_free()` puts it after `destroy`, so the
  driver must store a counted reference there and must not put it itself
  unless it also clears or replaces the pointer, as
  `drm_bridge_clear_and_put()` does.
- **Potentially unsafe usage**: storing a looked-up bridge in
  `bridge->next_bridge`.
  - Unsafe: when the pointer came from a lookup that does not count, since
    `__drm_bridge_free()` then drops a reference nobody took.
  - Safe: from `of_drm_find_and_get_bridge()`, as `tpd12s015_probe()` in
    `drivers/gpu/drm/bridge/ti-tpd12s015.c` does.
  - Safe: wrapped in `drm_bridge_get()`, as `imx93_pdfc_bridge_probe()` in
    `drivers/gpu/drm/bridge/imx/imx93-pdfc.c` does for the result of
    `devm_drm_of_get_bridge()`.
- `drm_bridge_add()` and `drm_bridge_attach()` on a bridge without
  `bridge->container`: only `DRM_WARN()`, then they carry on.
- `drm_bridge_attach()`: calls `funcs->atomic_create_state` with no NULL
  test, so every bridge that is attached needs it, with
  `atomic_duplicate_state` and `atomic_destroy_state`.
- `drm_bridge_detach()`: not exported; only `drm_encoder_cleanup()` calls it,
  so the attach reference lasts until the encoder is cleaned up.
- `drm_bridge_remove()`: moves the bridge to `bridge_lingering_list` and
  destroys `hpd_mutex` and `hpd_state_mutex`; a held reference keeps the
  memory, not those mutexes.
- `devm_drm_put_bridge()`: drops the allocation reference early; its
  kerneldoc marks it a temporary workaround, used by
  `drm_panel_bridge_remove()`.
