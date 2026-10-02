- `platform_match()` with a driver that has `id_table`: returns the
  `platform_match_id()` result; the `strcmp()` against `drv->name` runs only
  when `id_table` is NULL.
- Driver override: `struct platform_device` has no `driver_override` member
  here; `platform_match()` calls `device_match_driver_override()` in
  `include/linux/device.h`, which reads `dev->driver_override.name`.
- `mfd_match_of_node_to_dev()`: sets the node with `device_set_node()` only; it
  does not set `DEV_FLAG_OF_NODE_REUSED`, so `dev_of_node_reused()` is false
  and the child matches and emits `of:` on its own node.
- `mfd_acpi_add_device()`, when the parent has an ACPI companion: calls
  `set_primary_fwnode()` with the matched ACPI child, or with the parent's
  companion when `cell->acpi_match` is NULL or finds nothing; it does not call
  `acpi_device_set_enumerated()`.
- MODALIAS for a child with an ACPI companion depends on
  `acpi_companion_match()` in `drivers/acpi/bus.c`:

| companion | MODALIAS | module must declare |
|---|---|---|
| own, has PNP ids, child is its first physical node | `acpi:<HID>:<CID>:` | `MODULE_DEVICE_TABLE(acpi, ...)` |
| own, with `data.of_compatible` set, child is its first physical node | `of:N<name>T` plus compatibles, from `create_of_modalias()` | `MODULE_DEVICE_TABLE(of, ...)` |
| own, `pnp.ids` empty | `platform:<name>` | `MODULE_ALIAS("platform:<name>")` or `MODULE_DEVICE_TABLE(platform, ...)` |
| the parent's, already bound to the parent by `acpi_bind_one()` | `platform:<name>` | same as the row above |

- `acpi_driver_match_device()` with a driver that has no `acpi_match_table`:
  passes `ACPI_COMPANION(dev)` straight to `acpi_of_match_device()`, so a child
  that shares the parent's companion can still bind through `of_match_table`,
  when that companion has `data.of_compatible`, while its MODALIAS is
  `platform:`.
