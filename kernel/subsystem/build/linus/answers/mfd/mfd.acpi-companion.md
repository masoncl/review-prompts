- `mfd_acpi_add_device()`: does not use `ACPI_COMPANION_SET()`; it calls
  `set_primary_fwnode(&pdev->dev, acpi_fwnode_handle(adev ?: parent))`.
- Without `acpi_match`: no search of any kind; the child gets the parent's
  companion, and `pdev->id` is not compared with `_ADR`.
- `pnpid`: copied into a one-entry `struct acpi_device_id` table and
  matched with `acpi_match_device_ids()` over `acpi_dev_for_each_child()`;
  `acpi_dev_hid_match()` is not used.
- Search finds nothing (either member): falls back to the parent's
  companion, with no message.
- Device tree node already set: `dev->of_node` is left as it is;
  `dev->fwnode` is replaced by the ACPI fwnode, and the OF fwnode is not
  kept as its secondary.
- After that, `dev_fwnode()` still returns the OF node, because
  `__dev_fwnode()` in `drivers/base/property.c` prefers `dev->of_node`.
- `ACPI_COMPANION()` and `has_acpi_companion()` read `dev->fwnode`, so they
  see the ACPI node.
