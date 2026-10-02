- Supply aliases: registered right after `dev.parent` and `dev.type` are set,
  before the OF match, `mfd_acpi_add_device()`, platform data, software node
  and resources. That is why `fail_alias` sits below `fail_of_entry` and
  `fail_res_conflict`.
- `fail_res_conflict`: the only label that removes the software node. It is
  also the target when `platform_device_add_resources()` or
  `platform_device_add()` fails.
- A new step placed before the OF match: must be undone at `fail_alias` or
  below, because the path that drops a cell for a disabled node (see
  "Disabled and missing nodes") jumps to `fail_alias`.
- `mfd_remove_devices_fn()`: repeats the software node, OF entry and supply
  alias undo steps. A new per-device step needs its undo in both places.
- `pdev->mfd_cell` and `dev.type`: both must be set before
  `platform_device_add()`. `mfd_remove_devices_fn()` reads `cell->level` with
  no NULL test for every child that has the type.
- The cell copy is shallow: `mfd_remove_devices_fn()` reads
  `cell->parent_supplies` and `cell->swnode` at removal, and
  `isp_user_buffer_alloc()` reads `mfd_cell->platform_data`. What these point
  to must outlive the child.
- Type name `"mfd_device"`: compared as a string by `isp_genpd_add_device()`
  in `drivers/gpu/drm/amd/amdgpu/isp_v4_1_1.c`, and sent as `DEVTYPE=` by
  `dev_uevent()`.
