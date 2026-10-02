- `of_syscon_register_regmap()`: returns `-EINVAL` for a NULL `np` or
  `regmap`, before anything else.
- Node reference: neither `of_syscon_register_regmap()` nor
  `of_syscon_register()` calls `of_node_get()`; the entry stores the bare
  pointer and lookups match by pointer.
- Node lifetime: the entry does not keep the node alive; a reference held
  elsewhere must.
- Node without `syscon`, before registration: `syscon_node_to_regmap()` and
  the phandle and compatible lookups return `-EPROBE_DEFER`, so consumers
  defer until the registration.
- `device_node_to_regmap()` before registration: creates an entry for any
  node, and the registration then returns `-EEXIST`.
- **Potentially unsafe usage**: registering a regmap made by a devm
  initializer such as `devm_regmap_init_mmio()`.
  - Unsafe: when the device can be unbound, or probe can fail after the
    registration; devres frees the regmap and `device_node_get_regmap()` keeps
    returning the pointer, since nothing in `drivers/mfd/syscon.c` removes an
    entry.
  - Safe: registration as the last step of probe, in a built-in driver that
    sets `suppress_bind_attrs`, as `rz_sysc_probe()` does; `bus_add_driver()`
    then creates no `unbind` file, so `devm_regmap_release()` does not run
    from a sysfs unbind or a module unload.
