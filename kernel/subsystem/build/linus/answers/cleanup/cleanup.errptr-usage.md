- **Potentially unsafe usage**: initialising a `__free()` variable from a
  function that can return an error pointer.
  - Unsafe: when neither the wrapper nor the release function tests
    `IS_ERR()`, as with `kfree_sensitive`, whose wrapper tests only `if (_T)`;
    on the `IS_ERR()` early return `kfree_sensitive()` is called on the error
    pointer.
  - Safe: when the wrapper tests `IS_ERR_OR_NULL()`, as `kfree` does for
    `memdup_user()` in `snd_ctl_elem_read_user()` in `sound/core/control.c`.
  - Safe: when the wrapper tests `IS_ERR()`, as `mntput` does for `fc_mount()`
    in `do_new_mount_fc()` in `fs/namespace.c`.
  - Safe: when the wrapper has no test and the release function makes it, as
    `fwnode_has_op()` does for `fwnode_handle` in `usb_acpi_add_usb4_devlink()`
    in `drivers/usb/core/usb-acpi.c`.
- `_opp_set_availability()` in `drivers/opp/core.c`: initialises a
  `__free(put_opp)` variable with `ERR_PTR(-ENODEV)` on purpose; `put_opp`
  tests `IS_ERR_OR_NULL()`, so an error pointer is a valid "nothing held"
  value.
- `drivers/net/ethernet/intel/ice/ice_debugfs.c`: has no `__free(kfree)`
  variable; use the examples above.
