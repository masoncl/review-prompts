- `devm_mfd_add_devices()`: does not call `devm_add_action_or_reset()`. It
  calls `devres_alloc()` first, `devres_add()` only after `mfd_add_devices()`
  succeeded, and `devres_free()` on failure.
- On failure: no release is registered; what stays registered is what
  `mfd_add_devices()` left (see "Failure while adding").
- `devm_mfd_dev_release()`: not limited to the cells of its call. See
  "Dependency levels" for the cells it removes.
- Several calls on one device: the release of the last call runs first and
  removes the normal children of all calls, including children added with
  plain `mfd_add_devices()`.
- Manual `mfd_remove_devices()` before the release: harmless; the release
  walk finds no normal MFD child left.
- **Unsafe usage**: passing a device other than the one the calling driver is
  being bound to.
  - Unsafe: the release runs when that other device is unbound or deleted,
    not when the caller is unbound. If that device has no driver yet,
    `really_probe()` later fails it with `-EBUSY` because `devres_head` is
    not empty.
  - Safe: pass the device being probed, as `act8945a_i2c_probe()` does;
    `device_unbind_cleanup()` in `drivers/base/dd.c` releases the devres of
    the device being unbound.
- **Unsafe usage**: `devm_mfd_add_devices()` with a `remove()` that frees or
  disables by hand something the children use; the children are still bound
  while `remove()` runs.
  - Safe: every resource the children use is managed and acquired before the
    call, as in `act8945a_i2c_probe()`; `__device_release_driver()` calls
    `device_remove()` before `device_unbind_cleanup()`, and `release_nodes()`
    in `drivers/base/devres.c` releases in reverse order.
  - Safe: plain `mfd_add_devices()` with `mfd_remove_devices()` first in
    `remove()`, as in `ec_device_remove()`.
