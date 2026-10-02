- `delete_endpoint()` and `cxl_detach_ep()`: separate devres actions on
  `&cxlmd->dev`; neither calls the other.
- Order on memdev unbind: `delete_endpoint()` is registered later, so it runs
  first; the endpoint port is gone before the memdev is detached from the
  ports above.
- `cxl_detach_ep()`: visits depths `cxlmd->depth - 1` down to 1;
  `cxlmd->depth` is -1 from `cxl_memdev_alloc()` until
  `cxl_endpoint_autoremove()` writes it, and until then the action visits no
  port.
- `unregister_port()`: sets `port->dead` under the lock of
  `port_to_host(port)`, which it asserts; it does not hold the port's own
  lock.
- `port->dead` is read in three places: `add_ep()` (returns `-ENXIO`),
  `cxl_detach_ep()` (no second reap) and `delete_endpoint()` (skips the
  release actions).
- `cxl_port_add_dport()` and `probe_dport()`: do not test `port->dead`;
  `probe_dport()` tests `port->dev.driver`.
- Locks in `cxl_detach_ep()`: `device_lock(&parent_port->dev)`, then
  `device_lock(&port->dev)`; the parent lock is the parent port's own device
  even when the parent is the root.
- `cxl_detach_ep()`: takes no `cxl_rwsem` lock itself.
- Port lock: dropped before `delete_switch_port()`; the parent lock is held
  through it, as `unregister_port()` asserts.
- There is no reap_dports() here; `del_dports()` in
  `drivers/cxl/core/port.c` releases each dport's devres group with
  `del_dport()`, under the port lock, before `delete_switch_port()`.
- `delete_switch_port()`: calls `devm_release_action()` on `port->dev.parent`;
  that equals `port_to_host(port)` only because `cxl_detach_ep()` tests
  `!is_cxl_root(parent_port)` first.
- `devm_release_action()`: warns when the action is not on that device; the
  `->driver` and `!dead` tests are what keep it from being called after the
  host's devres already ran.
- `detach_memdev()`: unbinds the memdev, or the memdev's parent when
  `cxlmd->attach` is set.
- `cxl_mem_probe()`: returns `-EBUSY` while `cxlmd->detach_work` is pending.
