- `drm_bridge_enter()`: returns `bool`; the index comes back through its
  `int *idx` argument.
- `drm_bridge_unplug()`: sets `bridge->unplugged`, waits with
  `synchronize_srcu()`, then calls `drm_bridge_remove()`; the driver calls it
  in place of `drm_bridge_remove()`.
- `drm_bridge_remove()` alone never sets `unplugged`, so after it
  `drm_bridge_enter()` still returns true.
- Guarantee inside a section: `drm_bridge_unplug()` has not returned; only
  what the driver releases after that call is still present.
- `drm_bridge_unplug_srcu`: one domain for all bridges, so unplugging one
  bridge waits for the open sections of every bridge.
- The core never enters the guard and never tests `unplugged`: the chain
  helpers and the bridge connector still call the callbacks of an unplugged
  bridge that is attached.
- Each callback, work item and interrupt handler must enter the guard itself;
  see `drivers/gpu/drm/bridge/ti-sn65dsi83.c`, the only user.
- **Unsafe usage**: `devm_drm_bridge_add()` together with
  `drm_bridge_unplug()`; both call `drm_bridge_remove()`, which puts once per
  call for the single get in `drm_bridge_add()`.
  - Safe: `drm_bridge_add()` in probe and `drm_bridge_unplug()` in remove, as
    `sn65dsi83_remove()` does.
