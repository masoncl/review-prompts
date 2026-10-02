- `device_add_software_node()`: returns `-EBUSY` only when the device
  already has a software node (`dev_to_swnode()`); a node that is already
  registered gets one more reference with `swnode_get()`.
- One constant static node for every parent instance: supported;
  `intel_lpss_probe()` in `drivers/mfd/intel-lpss.c` passes the same static
  node for each instance.
- `device_add_software_node()` does not set `managed`; only
  `device_create_managed_software_node()` does, so removal is explicit.
- Node registered by the driver beforehand: accepted;
  `rohm_register_pwrbutton()` in `drivers/mfd/rohm-pwrbutton.c` registers
  the nodes through `software_node_register_node_group()` first, then names
  the node in the cell.
- Unregistration: happens when the last reference is put, so a shared node
  stays registered until the last child that uses it is removed.
- `platform_device_release()`: also calls `device_remove_software_node()`;
  a no-op once `mfd_remove_devices_fn()` has removed the node.
- `mfd_remove_devices_fn()`: detaches the node before
  `platform_device_unregister()`, so the child driver's `remove()` runs
  with the software node already gone.
- Child with a primary fwnode: `set_secondary_fwnode()` stores the node in
  the primary's `secondary`; a child that got the parent's ACPI companion
  shares that pointer with the parent.
- Second cell with `swnode` on the same shared primary:
  `device_add_software_node()` finds the first node and returns `-EBUSY`.
- **Unsafe usage**: one `struct software_node` per parent instance, each
  with the same non-NULL `name` and no `parent`; `swnode_register()` uses
  `name` as the kobject name in `swnode_kset`, and the second registration
  fails with `-EEXIST`.
  - Safe: a name built from `dev_name()` of the parent, as
    `rohm_register_pwrbutton()` does.
  - Safe: `name` left NULL; `swnode_register()` then names the node
    "node%d" from an IDA.
  - Safe: one shared constant node, as `intel_lpss_probe()` uses.
