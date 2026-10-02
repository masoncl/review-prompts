# Multi-Function Devices (MFD)

## Main structures

### Objects and how they relate

- One cell yields at most one child: `struct mfd_cell` has no num_devices
  member; several children of one kind need several cells or several calls.
- Child id: `id + cell->id` (the cell's `id` member, not its array index);
  with `PLATFORM_DEVID_AUTO` the cell's `id` is ignored. See
  `mfd_add_device()`.
- `struct resource` in a cell, as translated by `mfd_add_device()`:

  | Cell resource | Child resource |
  |---|---|
  | `flags` has the `IORESOURCE_MEM` bit (`IORESOURCE_REG` has it too), `mem_base` non-NULL | offset by `mem_base->start`, parented to `mem_base` |
  | `IORESOURCE_IRQ`, `domain` non-NULL | `irq_create_mapping()` of `start`; a range triggers `WARN_ON()` |
  | `IORESOURCE_IRQ`, `domain` NULL | offset by `irq_base` |
  | anything else, including `IORESOURCE_IO` and `IORESOURCE_MEM` with NULL `mem_base` | copied unchanged, with the cell's `parent` |

- `mfd_dev_type`: the private `struct device_type` stamped on every child
  (there is no mfd_devtype).
- OF node lookup in `mfd_add_device()`: runs only for a cell with
  `of_compatible` under a parent that has an `of_node`; for a parent without
  an `of_node` the core gives the child no DT node and prints no
  "Failed to locate of_node" warning.
- `struct mfd_of_node_entry`: one entry per DT node handed to a child, on
  `mfd_of_node_list`, which is global rather than per parent; without
  `use_of_reg`, cells with the same compatible take the nodes in DT order.
- `swnode` is the only software-node member of the cell; there is no
  property-entry member.
- `drivers/mfd/mfd-core.c` sets no driver data and no regmap on a child;
  reaching the regmap or driver data through `dev.parent` is a convention
  between the two drivers, which the core neither sets up nor enforces.
- DMA: the child's `dev.dma_mask` and `dev.dma_parms` point at the parent's
  objects (not copies); `coherent_dma_mask` is copied by value.
- `parent_supplies`: regulator supply names that the child requests are
  aliased to the parent device, so the lookup happens on the parent.
- `drivers/mfd/simple-mfd-i2c.c`: `simple_mfd_i2c_probe()` uses
  `devm_mfd_add_devices()` when the match data carries cells, and
  `devm_of_platform_populate()` only when it carries none.
- Children created from DT nodes rather than cells: `mfd_get_cell()` returns
  NULL and `dev.type` is not `mfd_dev_type`, so `mfd_remove_devices()` skips
  them.
- `keyboard_led_is_mfd_device()` in
  `drivers/platform/chrome/cros_kbd_led_backlight.c`: uses
  `IS_ENABLED(CONFIG_MFD_CROS_EC_DEV)` and a non-NULL `mfd_get_cell()` to tell
  an MFD child from a device that firmware enumerated.
- `struct syscon` in `drivers/mfd/syscon.c`: unrelated to cells; it has no
  `struct device`, is keyed by `struct device_node` on the global
  `syscon_list`, and nothing in that file removes an entry.

## Where to look

**Core files**

- `drivers/mfd/mfd-core.c` exports four functions: `mfd_add_devices()`,
  `devm_mfd_add_devices()`, `mfd_remove_devices()` and
  `mfd_remove_devices_late()`.
- `mfd_add_hotplug_devices()` and `mfd_get_cell()`: `static inline` in
  `include/linux/mfd/core.h`, not in `drivers/mfd/mfd-core.c`.
- Children of a `simple-mfd` node: created by `of_platform_default_populate()`
  in `drivers/of/platform.c`; "simple-mfd" is an entry of its function-local
  `match_table[]`. No file under `drivers/mfd/` matches that string.
- `drivers/bus/simple-pm-bus.c`: for a node whose best match in
  `simple_pm_bus_of_match` is "simple-mfd", `simple_pm_bus_probe()` returns 0
  and binds when that string is the first `compatible` entry of the node, and
  `-ENODEV` otherwise. It creates no children in either case.
- `include/linux/mfd/core.h`: its header comment names
  drivers/mfd/mfd-core.h; no such file exists.

**Documentation files**

- `Documentation/devicetree/bindings/mfd/mfd.txt`: exists, as plain text; it
  has no YAML replacement.
- `Documentation/devicetree/bindings/mfd/syscon.yaml`: does not contain the
  string "simple-mfd". The rule for `syscon` combined with `simple-mfd` (at
  least three `compatible` entries) is in
  `Documentation/devicetree/bindings/mfd/syscon-common.yaml`.
- `Documentation/devicetree/bindings/writing-bindings.rst`: holds the rules on
  when `simple-mfd` and `syscon` may be used.
- ACPI handling of children: section "MFD devices" in
  `Documentation/firmware-guide/acpi/enumeration.rst`.
- The example in that section sets both `pnpid` and `adr` of
  `struct mfd_cell_acpi_match`; `mfd_acpi_add_device()` in
  `drivers/mfd/mfd-core.c` reads `adr` only when `pnpid` is `NULL`.
- `Documentation/driver-api/`: has no document for the MFD core. The only
  mention of the API there is `devm_mfd_add_devices()` in the list in
  `Documentation/driver-api/driver-model/devres.rst`.
- Kernel-doc for the core: only on `mfd_add_devices()` and
  `devm_mfd_add_devices()` in `drivers/mfd/mfd-core.c`, and no `.rst` file
  includes it. `include/linux/mfd/core.h` has plain comments only.
- `Documentation/devicetree/usage-model.rst`: the document that
  `include/linux/mfd/core.h` cites for `of_compatible`. Its
  `of_platform_populate()` example passes of_default_bus_match_table, a table
  that no source file defines.

**Kconfig symbols**

- Menu dependency: `if HAS_IOMEM` in `drivers/mfd/Kconfig` encloses the whole
  menu, `MFD_CORE` and `MFD_SYSCON` included.
- `MFD_CORE`: selects `IRQ_DOMAIN` and nothing else.
- `MFD_CORE`: no Kconfig file has `depends on MFD_CORE`; every reference
  outside its definition is `select MFD_CORE`.
- `MFD_SYSCON`: users get it either way; both `select MFD_SYSCON` and
  `depends on MFD_SYSCON` are common in the tree.
- `MFD_SYSCON` with neither `select` nor `depends on`: the driver still builds.
  `include/linux/mfd/syscon.h` has inline stubs for `!CONFIG_MFD_SYSCON`; the
  lookups return `ERR_PTR(-ENOTSUPP)`, except that
  `syscon_regmap_lookup_by_phandle_optional()` returns `NULL` and
  `of_syscon_register_regmap()` returns `-EOPNOTSUPP`.
- `MFD_SIMPLE_MFD_I2C`: `tristate` with no prompt. A driver gets it with
  `select MFD_SIMPLE_MFD_I2C`, as `MFD_SL28CPLD` does.
- `drivers/mfd/bcm2835-pm.c`: built by `CONFIG_ARCH_BCM2835`, not by a symbol
  in `drivers/mfd/Kconfig`. Its `select MFD_CORE` is in
  `arch/arm/mach-bcm/Kconfig` and `arch/arm64/Kconfig.platforms`.

**Callers outside the directory**

- Outside callers: found by searching for `mfd_add_devices()`,
  `devm_mfd_add_devices()` and `mfd_add_hotplug_devices()` outside
  `drivers/mfd/`. For example `drivers/misc/cardreader/rtsx_pcr.c`,
  `drivers/soc/samsung/exynos-pmu.c` and
  `drivers/gpu/drm/amd/amdgpu/amdgpu_acp.c`.
- No file under `sound/`, `drivers/pci/`, `drivers/gpio/` or
  `drivers/platform/chrome/` calls any of those three functions.
- `select MFD_CORE` outside `drivers/mfd/Kconfig` does not mark a caller. For
  example `GPIO_VX855` and `GPIO_RDC321X` in `drivers/gpio/Kconfig` select it
  for child drivers that register nothing.
- `mfd_get_cell()`: inline, so a child driver that only calls it, such as
  `drivers/platform/chrome/cros_kbd_led_backlight.c`, links without
  `MFD_CORE`.
- The select belongs on the symbol that builds the calling file: the `bool`
  sub-options `DRM_AMD_ACP` and `DRM_AMD_ISP` of the amdgpu module for the
  amdgpu files, `POLARFIRE_SOC_SYSCONS` for the two files in
  `drivers/soc/microchip/`.
- `MFD_NVEC`: defined in `drivers/staging/nvec/Kconfig`, not in
  `drivers/mfd/Kconfig`, despite its name.

**Shared headers**

- Private headers: the files matched by `drivers/mfd/*.h`. None of them has a
  name that starts with "tps".
- `include/linux/mfd/tps6594.h` and `include/linux/mfd/tps65010.h`: shared
  headers, not private ones.
- No source file or Makefile outside `drivers/mfd/` reaches a header in
  `drivers/mfd/`: there is no `../mfd/` include and no include path that names
  the directory. A child driver in another directory can only use what is
  under `include/`.

**Tests of the core**

- MFD core: no KUnit test and no selftest. No file under `drivers/mfd/`
  mentions KUnit, and no file with "test" or "kunit" in its name calls
  `mfd_add_devices()`.
- System controller helper: no KUnit test and no selftest; no such file calls
  a lookup function of `drivers/mfd/syscon.c`.
- Regmap interrupt controller: no test. `drivers/base/regmap/regmap-kunit.c`
  has no reference to `regmap_add_irq_chip()` or `struct regmap_irq_chip`.
- `REGMAP_KUNIT` in `drivers/base/regmap/Kconfig`: selects `REGMAP_RAM` only,
  so a KUnit run does not even build `drivers/base/regmap/regmap-irq.c` unless
  something else selects `REGMAP_IRQ`.
- `tools/testing/selftests/`: has no directory for MFD.

## Cells

**Cell initialiser macros**

- `MFD_CELL_ALL()` argument order: `_name, _res, _pdata, _pdsize, _id, _compat,
  _of_reg, _use_of_reg, _match`; see `include/linux/mfd/core.h`.
- `_pdsize`: follows `_pdata` in `MFD_CELL_ALL()`, `MFD_CELL_OF_REG()`,
  `MFD_CELL_OF()`, `MFD_CELL_ACPI()` and `MFD_CELL_BASIC()`; the caller
  supplies it, nothing derives it from `_pdata`.
- `MFD_CELL_OF_REG()`: the only wrapper that sets `use_of_reg`; every other
  wrapper passes `false` and `of_reg` 0.
- `num_resources`: computed by `MFD_RES_SIZE()`, a `sizeof` division, not by
  `ARRAY_SIZE()`.
- `_res` given as `NULL` or as a pointer: compiles and yields `num_resources`
  0, so a pointer to resources silently registers a child with none.
- `MFD_CELL_OF()` with `_compat` `NULL`: same cell as `MFD_CELL_BASIC()`;
  `mfd_add_device()` skips the OF lookup when `of_compatible` is `NULL`.
- Members no macro sets: `level`, `swnode`, `suspend`, `resume`,
  `ignore_resource_conflicts`, `pm_runtime_no_callbacks`, `parent_supplies`,
  `num_parent_supplies`; a cell that needs one sets it by name, for example
  with a designated initialiser.
- `MFD_DEP_LEVEL_NORMAL` and `MFD_DEP_LEVEL_HIGH`: defined in the same header;
  they are values for `level`, not initialisers.

**Cell lookup from a child**

- `mfd_get_cell()`: returns `pdev->mfd_cell`; it does not read
  `dev_get_platdata()`.
- Platform device not created by `mfd_add_device()`: the result is `NULL`,
  never a pointer to some other structure.
- Main use in this tree: a boolean "is this an MFD child" test, as in
  `mipi_i3c_hci_pci_is_mfd()` and `keyboard_led_is_mfd_device()`; neither
  dereferences the result.
- Reading a member: only `id` is read through the accessor outside the core,
  in `drivers/regulator/da9052-regulator.c`.
- `platform_data`, `name`, `of_compatible`: no caller reads them through
  `mfd_get_cell()`.
- `pdev->mfd_cell` is also read directly, without the accessor, and those
  reads do take `name` and `platform_data`; search for `->mfd_cell` as well as
  for `mfd_get_cell` when looking for users.

**Cell storage and lifetime**

- The copy: `pdev->mfd_cell`, made by `kmemdup()` in `mfd_add_device()`; it is
  not `pdev->dev.platform_data` and `platform_device_add_data()` plays no part
  in it.
- Comment above `struct mfd_cell` in `include/linux/mfd/core.h`: says the copy
  becomes the platform data of the child; the code does not do that.
- Free: `kfree(pa->pdev.mfd_cell)` in `platform_device_release()`;
  `struct platform_object` has no pdata member.
- Members the core reads from the copy after `mfd_add_devices()` returns:
  `level`, `swnode` (tested only), `parent_supplies` and
  `num_parent_supplies`, all in `mfd_remove_devices_fn()`.
- **Potentially unsafe usage**: a cell member that points at storage which
  ends before the child is removed.
  - Unsafe: `swnode`; `swnode_register()` stores the pointer and copies
    neither the node nor its properties.
  - Unsafe: `parent_supplies`; `regulator_register_supply_alias()` stores each
    string pointer, and `mfd_remove_devices_fn()` reads the array again
    through the copy.
  - Unsafe: `resources[i].name`; the copied `struct resource` keeps the
    pointer.
  - Unsafe: any member that code reads later through `mfd_get_cell()` or
    `pdev->mfd_cell`; the copy then holds a dangling pointer.
  - Safe: the `resources` array, `name`, and `platform_data` with nonzero
    `pdata_size`; `mfd_add_device()` copies them with
    `platform_device_add_resources()`, `platform_device_alloc()` and
    `platform_device_add_data()` before it returns. For example
    `ti_tscadc_probe()` points `platform_data` at a local variable.
  - Safe: `of_compatible` and `acpi_match`; `mfd_add_device()` and
    `mfd_acpi_add_device()` are the only core readers, and both finish before
    `mfd_add_devices()` returns.

**Platform data of a child**

- Condition for the copy: `mfd_add_device()` tests `cell->pdata_size`, not
  `cell->platform_data`.
- `pdata_size` zero: `dev_get_platdata()` in the child returns `NULL`; it does
  not return the cell copy.
- `pdata_size` nonzero with `platform_data` `NULL`:
  `platform_device_add_data()` stores `NULL` and returns 0, so the child gets
  `NULL` and the add does not fail.
- **Potentially unsafe usage**: `platform_data = &ptr` with
  `pdata_size = sizeof(ptr)`, which copies the pointer value and not the
  object.
  - Unsafe: when the child casts `dev_get_platdata()` to the object type;
    `platform_device_add_data()` allocated only `pdata_size` bytes, so the
    child reads past the allocation.
  - Unsafe: when the object `ptr` refers to is freed before the child is
    removed.
  - Safe: when the child reads one pointer back, as `ti_tscadc_dev_get()` in
    `include/linux/mfd/ti_am335x_tscadc.h` does, and the object is devm memory
    of the parent whose remove calls `mfd_remove_devices()`, as
    `ti_tscadc_probe()` and `ti_tscadc_remove()` do.

**Cells written at probe**

- `drivers/mfd/88pm800.c`: `onkey_devs` and `regulator_devs` are
  `static const`; `rtc_devs` is the only cell array there that is not.
- `drivers/mfd/intel-lpss.c`: the per-device copy is made in
  `intel_lpss_assign_devs()`; `intel_lpss_probe()` then writes only `swnode`
  and `ignore_resource_conflicts` into it.
- `intel_lpss_idma64_cell`: not copied by the driver; `intel_lpss_probe()`
  registers it straight from the `static const` object.
- **Unsafe usage**: writing a member of a file-scope cell on only some paths
  of probe; the cell keeps what an earlier probe wrote, and
  `platform_device_add_data()` then copies `pdata_size` bytes from the old
  `platform_data` pointer.
  - Safe: write every member that probe can set on every path, including the
    value that clears it, as `as3711_i2c_probe()` does.
  - Safe: copy a `static const` template for each device and write the copy,
    as `intel_lpss_assign_devs()` does with `devm_kmemdup()`.
  - Safe: build the cells for each probe on the stack, as `sky81452_probe()`
    does, or on the heap and free them after the add, as
    `skl_int3472_tps68470_probe()` does; `mfd_add_device()` has taken its own
    copy by then.

**Variant selection**

- Backends of `device_get_match_data()`: only `of_fwnode_ops` and the ACPI
  fwnode ops implement `device_get_match_data`; it never reads a
  `struct platform_device_id`, `struct i2c_device_id` or
  `struct spi_device_id` table.
- Device whose primary fwnode is a software node, or that has no fwnode: the
  result is `NULL`; `software_node_ops` has no `device_get_match_data`.
- ACPI backend: `acpi_device_get_match_data()` returns
  `acpi_device_id.driver_data`, or `of_device_id.data` when the match came
  through the OF table, so both tables must hold the same kind of value.
- Legacy-table fallback: not in `device_get_match_data()`; the bus helpers
  `i2c_get_match_data()` and `spi_get_device_match_data()` add it, and it runs
  whenever the firmware result is `NULL`, which includes a matched entry whose
  data is 0.
- `dev->driver`: `of_device_get_match_data()` and
  `acpi_device_get_match_data()` dereference it without a test; it must be
  set, as it is from the start of probe, and the tables searched are those of
  that driver.
- **Potentially unsafe usage**: a valid variant stored as 0 in an id table.
  - Unsafe: when probe tests the result to reject an unmatched device; the
    variant and "no match" both read as 0.
  - Unsafe: with `i2c_get_match_data()` or `spi_get_device_match_data()` when
    the legacy table can match the same device with another value; the
    fallback replaces the 0.
  - Safe: variants start at 1 and probe rejects 0, as `adp5585_i2c_probe()`
    does with `enum adp5585_variant`.

## Child names and driver binding

**Platform device id**

- `PLATFORM_DEVID_AUTO` name: `<name>.<N>.auto`, not `<name>.<N>`; see
  `platform_device_add()` in `drivers/base/platform.c`.
- N under `PLATFORM_DEVID_AUTO`: comes from `platform_devid_ida`, one IDA for
  every platform device in the system, so N is neither per name nor per
  parent.
- `PLATFORM_DEVID_NONE` base with `cell->id` k > 0: plain addition, the name is
  `<name>.<k-1>`; nothing rejects it.
- Negative `cell->id`: `platform_device_add()` tests the sum, not the base.
  - Sum of -1 (base 0, `cell->id` -1): bare `<name>`; for example `rtc_devs`
    in `drivers/mfd/max8925-core.c`.
  - Sum of -2 (base -1, `cell->id` -1): treated as `PLATFORM_DEVID_AUTO`.

**Child driver binding**

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

**Order among children**

- Models have the order and the lookup rules right; see `mfd_add_devices()` in
  `drivers/mfd/mfd-core.c` and `__device_attach()` in `drivers/base/dd.c`.
- Cell whose `of_compatible` matches only a disabled child node of
  `parent->of_node`: `mfd_add_device()` returns 0 and registers nothing, so a
  consumer may wait for a sibling that never exists.

**Unique child names**

- Scope of uniqueness: the whole platform bus, including platform devices that
  no MFD parent created.
- Duplicate under the same parent: `kobject_add()` in `device_add()` fails.
- Duplicate under different parents: `sysfs_create_link()` in
  `bus_add_device()` fails; both cases return `-EEXIST` and log through
  `sysfs_warn_dup()`.
- `insert_resource()` in `platform_device_add()`: fails when a range partly
  overlaps one already inserted, whatever the names are; an identical or
  nested range is accepted.
- `mfd_add_devices()` on failure: calls `mfd_remove_devices(parent)`, which
  removes every MFD child of the parent, also those added by earlier calls.
  - Cells with `level` `MFD_DEP_LEVEL_HIGH` are left in place.
  - When the failing cell is the first of the call, nothing is removed.
- **Potentially unsafe usage**: a constant `id` argument, such as 0 or
  `PLATFORM_DEVID_NONE`.
  - Unsafe: with a constant other than `PLATFORM_DEVID_AUTO`, when a second
    instance of the parent is registered; its first child fails with
    `-EEXIST` in `bus_add_device()`.
  - Safe: `PLATFORM_DEVID_AUTO`, as `mfd_add_hotplug_devices()` in
    `include/linux/mfd/core.h` passes; `platform_devid_ida` makes each name
    unique.
  - Safe: a base allocated per instance, as from `intel_lpss_devid_ida` in
    `drivers/mfd/intel-lpss.c`, and freed only after the children are
    removed, as `intel_lpss_remove()` does; the sums `base + cell->id` of two
    instances must differ for cells of the same `name`, since
    `platform_device_add()` builds the name from the sum.
- **Potentially unsafe usage**: two cells of one parent with the same `name`.
  - Unsafe: with a base other than `PLATFORM_DEVID_AUTO` and equal `cell->id`;
    the second cell fails with `-EEXIST` in `kobject_add()`.
  - Safe: distinct `cell->id` values, as in `lm3533_bl_devs` in
    `drivers/mfd/lm3533-core.c`; `platform_device_add()` puts the sum in the
    name. This holds with a `PLATFORM_DEVID_NONE` base too, where the names
    are `<name>` and `<name>.<k-1>`.
  - Safe: `PLATFORM_DEVID_AUTO`, where `platform_device_add()` allocates a
    separate number for each cell, as for `vexpress_sysreg_cells` in
    `drivers/mfd/vexpress-sysreg.c`.

## Resources of a child

**Memory resources**

- Without `mem_base`: the cell's `parent` is copied to the child together with
  `start` and `end`; it is not forced to NULL.
- `platform_device_add()`: calls `insert_resource()`, not
  `request_resource()`, for every resource that has a `parent` or whose
  `resource_type()` is `IORESOURCE_MEM` or `IORESOURCE_IO`.
- `insert_resource()` under `mem_base`: does not need `mem_base` itself to be
  in the `iomem_resource` tree.
- Failed insert: happens when the range lies outside `mem_base` or partly
  overlaps a resource already under it; see `__insert_resource()` in
  `kernel/resource.c`.
- Temporary array in `mfd_add_device()`: allocated with `kzalloc_objs()`; the
  function does not call `kcalloc()`.
- **Unsafe usage**: a child requests its range while the parent holds a busy
  region that covers it, including one that encloses the whole `mem_base`;
  the child's request fails with `-EBUSY`.
  - Safe: the parent maps without requesting, as `vexpress_sysreg_probe()` in
    `drivers/mfd/vexpress-sysreg.c` does with `devm_ioremap()`, and each child
    requests its own range. `__request_region_locked()` defines the
    requirement: it descends only through resources without
    `IORESOURCE_BUSY`.

**Interrupt resources**

- Range with a domain: `WARN_ON()`, then one `irq_create_mapping()` of the
  cell's `start`; `start` and `end` of the child both get that number. There
  is no loop over the range.
- `DEFINE_RES_IRQ()` and `DEFINE_RES_IRQ_NAMED()`: always describe one
  interrupt; a range needs explicit `.start` and `.end`, or
  `DEFINE_RES_NAMED()` with a size.
- Failed mapping: `irq_create_mapping()` returns 0 and the core stores it
  unchecked; the child's `platform_get_irq()`, when it takes the number from
  that resource, then warns and returns `-EINVAL`.
- No domain and `irq_base` 0: the numbers pass through unchanged, and they
  need not be Linux irq numbers.
  - For example, `drivers/mfd/wm831x-core.c` passes chip-relative numbers,
    and its children map them with `wm831x_irq()`.

**Register and other resources**

- **Unsafe usage**: `IORESOURCE_REG` cells together with a non-NULL
  `mem_base`. The core tests `flags & IORESOURCE_MEM`, and `IORESOURCE_REG`
  contains that bit. The resource is offset by `mem_base->start`, gets
  `mem_base` as parent and is inserted under it.
  - Safe: pass NULL as `mem_base`, as `ocelot_core_init()` does; the resource
    then takes the last `else` branch of `mfd_add_device()`.
- `IORESOURCE_IO`: does not contain the `IORESOURCE_MEM` bit, so it is copied
  unchanged whether or not `mem_base` is set.
- `platform_get_resource()` and `platform_get_resource_byname()`: compare
  `resource_type()` exactly, unlike the bit test in the core.
  - A lookup for `IORESOURCE_MEM` never returns an `IORESOURCE_REG` resource;
    `ocelot_regmap_from_resource_optional()` relies on that.
- Ocelot child, for an `IORESOURCE_REG` resource: uses only `res->name`, never
  `res->start`.
  - `ocelot_spi_init_regmap()` on the parent side turns `start` and the size
    into `reg_base` and `max_register` of the named regmap.
- Other children: use `res->start` as the register address on the parent's
  bus; for example `drivers/regulator/wm831x-dcdc.c`.
- `ocelot_core_try_add_regmap()` in `drivers/mfd/ocelot-core.c`: skips a name
  that already has a regmap on the parent, and discards the result of
  `ocelot_spi_init_regmap()`.
  - A failed regmap shows up only in the child, for example as `-ENOENT` from
    `ocelot_regmap_from_resource()`.

**Interrupt lookup in a child**

- Call chain: `platform_get_irq()` calls `platform_get_irq_optional()`, which
  calls `platform_get_irq_affinity()` with a NULL affinity pointer.
- Affinity: filled by `get_irq_affinity()` in `drivers/base/platform.c`, only
  when the result is > 0 and the pointer is non-NULL.
- By name: `__platform_get_irq_byname()` does not call `of_irq_get_byname()`;
  it calls `fwnode_irq_get_byname()` on `dev_fwnode()`.
  - An ACPI node whose `interrupt-names` holds the name therefore also wins
    over the cell resource.
- Child with both an OF node and an ACPI node: `dev_fwnode()` returns the OF
  node whenever `dev->of_node` is set, so the lookup takes the OF path.
- ACPI node, by index: the cell resource wins.
  - `acpi_irq_get()`: runs only when that resource has `IORESOURCE_DISABLED`.
  - `acpi_dev_gpio_irq_get()`: the last step, only for index 0 and only when
    there is no IRQ resource at that index.
- Result 0: `WARN()` and `-EINVAL`, not `-ENXIO`, in both the index path and
  the name path.

**DMA settings of children**

- `dma_mask`: assigned in `mfd_add_device()` as a shared pointer to the
  parent's storage.
- The three assignments (`dma_mask`, `dma_parms`, `coherent_dma_mask`) are
  unconditional and replace the defaults that `setup_pdev_dma_masks()` set in
  `platform_device_alloc()`.
- Parent with NULL `dma_mask` or `dma_parms`: the child gets NULL.
  - For example an I2C or SPI parent; `drivers/i2c/i2c-core-base.c` and
    `drivers/spi/spi.c` set neither.
  - `dma_set_mask()` on a child with NULL `dma_mask` returns `-EIO`.
  - `dma_set_max_seg_size()` on a child with NULL `dma_parms` hits
    `WARN_ON_ONCE()` and does nothing.
- Child with an OF node, at probe: `platform_dma_configure()` calls
  `of_dma_configure()`, the inline wrapper of `of_dma_configure_id()`, which
  narrows `*dev->dma_mask` in place, so it writes the parent's mask.
  - With a NULL `dma_mask` it warns "DMA mask not set" and points `dma_mask`
    at the child's own `coherent_dma_mask`.

## Firmware nodes of a child

**Global state and locks**

- `mfd_of_node_mutex`: a `DEFINE_MUTEX()` in `drivers/mfd/mfd-core.c`; every
  walk, `list_add_tail()` and `list_del()` on `mfd_of_node_list` runs under
  `scoped_guard(mutex, &mfd_of_node_mutex)`.
- Lookup and insert in `mfd_match_of_node_to_dev()`: two separate critical
  sections; the mutex is released between the "already claimed" walk and
  the `list_add_tail()`.
- `mfd_of_node_list`, `mfd_of_node_mutex` and `struct mfd_of_node_entry`:
  defined unconditionally; only the block in `mfd_add_device()` that adds
  entries is gated by `IS_ENABLED(CONFIG_OF)`.
- Entry removal (`fail_of_entry` in `mfd_add_device()`, and
  `mfd_remove_devices_fn()`): frees the entry only and does not call
  `of_node_put()` on `np`.
- `mfd_remove_devices()`: skips children whose `cell->level` is
  `MFD_DEP_LEVEL_HIGH`, so their entries stay until
  `mfd_remove_devices_late()`; `devm_mfd_add_devices()` unwinds with
  `mfd_remove_devices()`.
- `PLATFORM_DEVID_AUTO`: the MFD core keeps no id counter; it passes the
  value to `platform_device_alloc()`, and `platform_devid_ida` lives in
  `drivers/base/platform.c`.

**Device tree node matching**

- `mfd_match_of_node_to_dev()`: takes `(pdev, np, cell)` and tests one
  candidate node; it does not read the parent.
- `mfd_add_device()`: holds the loop over the children of
  `parent->of_node` and the `of_device_is_compatible()` and
  `of_device_is_available()` tests, in that order, before each call.
- Loop iterator: `for_each_child_of_node_scoped()`; the `continue` and
  `goto` exits need no `of_node_put()`, and adding one is a double put.
- Accepted node: set with `device_set_node(&pdev->dev,
  of_fwnode_handle(np))`, which writes both `dev.fwnode` and `dev.of_node`.
- References: one `of_node_get()` per accepted node; the entry's `np` and
  the child's `dev.fwnode` share it.

**Matching by address**

- Value compared: `of_property_read_reg(np, 0, &of_node_addr, NULL)` in
  `drivers/of/address.c`, the first `reg` address, untranslated.
- `mfd_match_of_node_to_dev()` does not call `of_translate_address()` or
  `of_address_to_resource()`.
- Without `CONFIG_OF_ADDRESS`: `of_property_read_reg()` is a stub in
  `include/linux/of_address.h` that returns `-ENOSYS`; a `use_of_reg` cell
  then gets `-EAGAIN` for every node.

**Disabled and missing nodes**

- No node accepted and no compatible node disabled: `pr_warn()` with
  "Failed to locate of_node", the child is registered with
  `dev.of_node == NULL`, and `mfd_add_device()` returns 0.
- `disabled` in `mfd_add_device()`: set by any compatible node that fails
  `of_device_is_available()`, before the claimed test and the `of_reg` test
  run.
- Cell dropped without a message: whenever no node is accepted and at
  least one compatible node is disabled, even if that node has a different
  `reg` or the cell's own node is absent or already claimed.
- Disabled sibling plus an accepted node: the child is registered
  normally; `disabled` is only read after the loop ends without a match.
- Dropped cell: `mfd_add_device()` returns 0 through `fail_alias`, adds
  nothing to `mfd_of_node_list`, and `mfd_add_devices()` goes on to the
  next cell.

**ACPI companion of a child**

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

**Software nodes**

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

**Parent node reuse**

- `struct device` has no `of_node_reused` member; the state is bit
  `DEV_FLAG_OF_NODE_REUSED` in `dev->flags`.
- Accessors: `dev_of_node_reused()` and `dev_set_of_node_reused()`,
  generated by `__create_dev_flag_accessors()` in `include/linux/device.h`.
- `struct platform_device_info` still has a member `of_node_reused`;
  `platform_device_register_full()` copies it into the flag.
- `device_set_of_node_from_dev()`: leaves `dev->fwnode` unchanged.
- Property reads on the child, for example `device_property_present()`,
  still read the adopted node, because `__dev_fwnode()` returns
  `of_fwnode_handle(dev->of_node)` whenever `dev->of_node` is set.
- `platform_device_release()`: puts `dev.fwnode` with
  `fwnode_handle_put()`, unless `dev_fwnode()` returns a software node; it
  does not put `dev.of_node`.
- `platform_device_set_of_node_from_dev()` in `drivers/base/platform.c`:
  the variant that also sets `dev.fwnode` to the adopted node.
- `device_set_node()` with the parent's fwnode: sets `dev->fwnode` and
  `dev->of_node`, takes no reference and does not set the flag.
- **Unsafe usage**: a child that binds to a driver takes its parent's node
  and `DEV_FLAG_OF_NODE_REUSED` stays clear; on the next probe
  `pinctrl_bind_pins()` looks up pin states for the child through the
  parent's node, and `of_match_device()` matches the child against the
  parent's compatible.
  - Safe: `device_set_of_node_from_dev()` in probe, which sets the flag, as
    `adp5585_gpio_probe()` in `drivers/gpio/gpio-adp5585.c` does;
    `pinctrl_bind_pins()` and `of_match_device()` test
    `dev_of_node_reused()`.
  - Safe: reading through the parent without adopting, as
    `max7360_keypad_parse_fw()` in
    `drivers/input/keyboard/max7360-keypad.c` does with
    `device_property_read_bool(dev->parent, ...)`; `pinctrl_bind_pins()`
    and `of_match_device()` read only the child's own `dev->of_node`.
- **Potentially unsafe usage**: `device_set_of_node_from_dev()` in the
  probe of an MFD child.
  - Unsafe: when the cell's `of_compatible` already gave the child a node;
    the call puts that node while `dev->fwnode` still points at it, and
    `platform_device_release()` puts it again.
  - Safe: guarded by `!dev->of_node`, as `max77650_regulator_probe()` in
    `drivers/regulator/max77650-regulator.c` does.
  - Safe: a cell with no `of_compatible`, as the `MFD_CELL_NAME()` cells in
    `drivers/mfd/adp5585.c`; the child then has no node to put.
- **Unsafe usage**: `device_set_of_node_from_dev()` on a child whose only
  fwnode is the software node from `cell->swnode`; `dev_fwnode()` then
  returns the parent's node, and `dev_to_swnode()` in
  `drivers/base/swnode.c` no longer finds the child's software node.
  - Safe: a child without `swnode` in its cell, as `adp5585_gpio_probe()`
    is for the `MFD_CELL_NAME()` cells in `drivers/mfd/adp5585.c`;
    `platform_device_set_of_node_from_dev()` warns on the software-node
    case with `WARN_ON()`.

## Parent data and regmaps

**Parent data in children**

- `simple_mfd_i2c_probe()` in `drivers/mfd/simple-mfd-i2c.c`: creates the
  regmap and adds the children, but sets no driver data; its children get NULL
  from `dev_get_drvdata()` on the parent and reach the regmap through
  `dev_get_regmap()`.
- `rk8xx_probe()` in `drivers/mfd/rk8xx-core.c`: receives a regmap that the bus
  glue (`drivers/mfd/rk8xx-i2c.c`, `drivers/mfd/rk8xx-spi.c`) already created,
  then sets driver data, adds the irq chip, and only then adds the cells.
- Children of a syscon parent: call `syscon_node_to_regmap()` or
  `device_node_to_regmap()` on `dev->parent->of_node`; these return `ERR_PTR()`
  and are checked with `IS_ERR()`, while `dev_get_regmap()` is checked for NULL.
- `regulator_register()` in `drivers/regulator/core.c`: when `config->regmap`
  is NULL and the child has no regmap of its own, uses
  `dev_get_regmap(dev->parent, NULL)`; `devm_clk_register_regmap()` in
  `drivers/clk/qcom/clk-regmap.c` has the same fallback.
- Earliest point: `really_probe()` in `drivers/base/dd.c` returns `-EBUSY` if
  the device's devres list is not empty when probing starts, so on a device
  that binds to a driver a regmap can be attached only from inside that
  device's own probe or later.
- Parent unbind and parent probe failure: both run `device_unbind_cleanup()`,
  which calls `devres_release_all()` and then `dev_set_drvdata(dev, NULL)`.
- Parent probe failure after plain `mfd_add_devices()`: the driver core does
  not remove the children; the parent's error path must call
  `mfd_remove_devices()`, or the children stay registered with NULL parent
  driver data. For example, `da9052_device_init()` in
  `drivers/mfd/da9052-core.c` calls it when its second `mfd_add_devices()` call
  fails.
- **Unsafe usage**: a child calling `dev_get_regmap()` on its parent from its
  remove callback, or from any path that can run while the parent unbinds.
  - Unsafe: when the parent's devres removes the children, as after
    `devm_mfd_add_devices()`; `devres_release_all()` unlinks every devres entry
    of the parent before it runs any release callback, so the lookup returns
    NULL while `devm_mfd_dev_release()` is removing the children;
    `dev_get_drvdata()` on the parent is still set at that point.
  - Safe: look the regmap up once in probe and keep the pointer, as
    `rk808_clkout_probe()` in `drivers/clk/clk-rk808.c` does; `release_nodes()`
    in `drivers/base/devres.c` runs the newest release first, so a regmap
    created with a devm initializer such as `devm_regmap_init_i2c()` before
    `devm_mfd_add_devices()` is freed after the children are gone.

**Several regmaps per parent**

- NULL `name`: returns the most recently attached regmap, named or unnamed;
  `find_dr()` in `drivers/base/devres.c` walks the list newest first.
- Parent with several regmaps whose children pass NULL: the default regmap must
  be attached last, as `pm8008_probe()` in `drivers/mfd/qcom-pm8008.c` does.
- Unmanaged regmaps are found too: `__regmap_init()` calls
  `regmap_attach_dev()` for any non-NULL `dev`, so `regmap_init()` and
  `devm_regmap_init()` both add the lookup entry.
- `regmap_attach_dev()` called directly: publishes a regmap that was created on
  another device (for example a dummy I2C client) on the parent; see
  `max77759_create_i2c_subdev()` in `drivers/mfd/max77759.c`.
- Lookup name after `regmap_attach_dev()`: it is `name` from the
  `struct regmap_config` passed to that call, which replaces the name given at
  init when it is not NULL; `pm8008_probe()` creates with "primary" and attaches
  with "secondary".
- `regmap_attach_dev()` also sets `map->dev` to the new device; the entry on the
  device the regmap was created on stays in place.
- `dev_get_regmap_match()`: compares only the name, never the regmap pointer, so
  two regmaps with the same name on one device cannot be told apart and the
  newest is returned.
- `regmap_exit()`: `regmap_detach_dev()` removes the newest entry on `map->dev`
  whose name equals `map->name`, and any newest entry when `map->name` is NULL;
  with several regmaps on one device the entry removed can belong to another
  regmap, unless every regmap there has a distinct, non-NULL name.

## Suspend and runtime PM

**Cell suspend and resume**

- `suspend` and `resume` in `struct mfd_cell`: both are declared in
  `include/linux/mfd/core.h`, as `int (*)(struct platform_device *)`.
- No cell in this tree sets either member, and nothing reads or calls them;
  `drivers/mfd/mfd-core.c` only copies them with the rest of the cell.
- **Unsafe usage**: setting `suspend` or `resume` in a `struct mfd_cell` and
  expecting it to run over system sleep.
  - Safe: put the callbacks in the child driver's `dev_pm_ops`, as
    `dln2_spi_pm` in `drivers/spi/spi-dln2.c` does; `platform_pm_suspend()`
    and `platform_pm_resume()` in `drivers/base/platform.c` call those.
- Child callbacks come from the platform bus when the child has no
  `pm_domain`: `mfd_dev_type` has no `pm`, so `device_suspend()` falls
  through to `platform_dev_pm_ops`. A child with `dev->pm_domain` set gets
  the callbacks of the domain instead.
- A child driver with no `dev_pm_ops` gets the legacy `suspend` and `resume`
  of `struct platform_driver` instead, see `platform_legacy_suspend()`.

| Phase | Order | Where |
|---|---|---|
| `prepare` | parent, then children | `dpm_prepare()` |
| `suspend`, `suspend_late`, `suspend_noirq` | children, then parent | `dpm_suspend()`, `dpm_suspend_late()`, `dpm_noirq_suspend_devices()` |
| `resume_noirq`, `resume_early`, `resume` | parent, then children | `dpm_noirq_resume_devices()`, `dpm_resume_early()`, `dpm_resume()` |
| `complete` | children, then parent | `dpm_complete()` |

- Sibling order in `dpm_list`: starts as cell array order, but a child whose
  probe is retried after deferral is moved to the tail of `dpm_list` by
  `device_pm_move_to_tail()`, called from `deferred_probe_work_func()`.
- Async: neither `mfd_add_device()` nor `platform_device_add()` calls
  `device_enable_async_suspend()`, so a child is handled synchronously unless
  its driver calls it or, with `CONFIG_PM_ADVANCED_DEBUG`, the `async` sysfs
  attribute enables it.
- With async enabled the parent/child order still holds, through
  `dpm_wait_for_subordinate()` on suspend and `dpm_wait_for_superior()` on
  resume; sibling order does not.

**Runtime PM of children**

- Step: when the cell sets `pm_runtime_no_callbacks`, `mfd_add_device()`
  calls `pm_runtime_no_callbacks()` after `platform_device_add()` has
  returned 0, as its last action on the device.
- Child probe: can run inside `platform_device_add()`, so the child driver's
  probe may see `power.no_callbacks` still 0.
- Sysfs: the device is already registered, so `dpm_sysfs_add()` has created
  the runtime attributes and `rpm_sysfs_remove()` then removes them.
- `rpm_sysfs_remove()`: unmerges all of `pm_runtime_attr_group`, which
  includes `control`; see `runtime_attrs` in `drivers/base/power/sysfs.c`.
- Enabling: `mfd_add_device()` makes no other runtime PM call; the child
  stays disabled until its driver calls `pm_runtime_enable()`.
- Flag on a disabled child: no effect on transitions; `rpm_resume()` and
  `rpm_check_suspend_allowed()` return on `power.disable_depth` before any
  test of `power.no_callbacks`.
- `rpm_resume()` of a flagged child: skips the parent only when the parent is
  `RPM_ACTIVE`, disabled, or has `power.ignore_children`; otherwise it resumes
  the parent first and returns `-EBUSY` if the parent does not become active.
- `power.child_count` of the parent: follows the child's `runtime_status`,
  not whether the child's runtime PM is enabled.
- `pm_runtime_set_active()` on a disabled child: on success increments the
  parent's `child_count`, so the child blocks parent suspend unless the
  parent has `power.ignore_children`; see `__pm_runtime_set_status()` in
  `drivers/base/power/runtime.c`.
- `pm_runtime_disable()` on an active child: leaves `child_count` unchanged,
  so the parent stays blocked until the child's status becomes
  `RPM_SUSPENDED`.
- **Potentially unsafe usage**: `pm_runtime_set_active()` in a child's probe.
  - Unsafe: when the parent has runtime PM enabled, is not `RPM_ACTIVE` and
    has not set `power.ignore_children`, which during probe means the
    parent's runtime resume failed; `__pm_runtime_set_status()` returns
    `-EBUSY` and leaves the child `RPM_SUSPENDED`.
  - Safe: when the parent has runtime PM enabled and its runtime resume
    succeeds; `__driver_probe_device()` in `drivers/base/dd.c` calls
    `pm_runtime_get_sync()` on the parent before the probe and
    `pm_runtime_put()` after it, so the parent is `RPM_ACTIVE` for the test
    in `__pm_runtime_set_status()`.
  - Safe: when the parent is `RPM_ACTIVE` or has runtime PM disabled at that
    point, which is what `__pm_runtime_set_status()` tests; for example
    `dln2_spi_probe()` in `drivers/spi/spi-dln2.c`, whose parent never
    enables runtime PM because `dln2_driver` does not set
    `supports_autosuspend`.

## Registration and removal

**Add and remove functions**

- mfd_cell_enable() and mfd_cell_disable(): not in this tree. `struct
  mfd_cell` in `include/linux/mfd/core.h` has no enable or disable hook and
  no usage count field.
- Exports: `mfd_add_devices()`, `mfd_remove_devices()`,
  `mfd_remove_devices_late()` and `devm_mfd_add_devices()` all use plain
  `EXPORT_SYMBOL()`.

**Device type of children**

- Models have this right; see `mfd_remove_devices_fn()` in
  `drivers/mfd/mfd-core.c`, the only code in the core that tests
  `mfd_dev_type`.

**Failure while adding**

- Failing cell is cell 0 of the call: `mfd_add_devices()` removes nothing;
  the cleanup is under `if (i)`. Children from earlier calls stay registered.
- Failing cell is a later one: the cleanup is `mfd_remove_devices()`, so
  children with `MFD_DEP_LEVEL_HIGH` stay registered, from this call and from
  earlier ones.
- **Potentially unsafe usage**: returning the error of `mfd_add_devices()`
  with no removal call in the error path.
  - Unsafe: when an earlier plain `mfd_add_devices()` call added children to
    the same parent, which stay registered when the failing cell is cell 0,
    or when a cell already registered has `MFD_DEP_LEVEL_HIGH`; those
    children stay registered while the driver core releases the parent's
    devres.
  - Safe: when it is the only call on the parent and no cell sets `level`,
    as in `dln2_probe()`; the `if (i)` branch already removed what the call
    added.
  - Safe: when the earlier children were added with `devm_mfd_add_devices()`,
    as in `bcm2835_pm_probe()`; `devm_mfd_dev_release()` removes them when
    the probe fails.

**Scope of removal**

- Reference from `of_node_get()` in `mfd_match_of_node_to_dev()`: dropped
  when `platform_device_release()` calls `fwnode_handle_put()` on
  `dev.fwnode`, while `dev.fwnode` is still the OF node.
- Software node: removed with `device_remove_software_node()` when
  `cell->swnode` is set.
- IRQ mappings made by `irq_create_mapping()` in `mfd_add_device()`: not
  disposed. `drivers/mfd/mfd-core.c` does not call `irq_dispose_mapping()`,
  and neither do `platform_device_del()` and `platform_device_release()`.

**Dependency levels**

- `level`: read only by `mfd_remove_devices_fn()`, which skips a cell when
  `cell->level > *level`.

| Caller | Level passed | Removes |
|---|---|---|
| `mfd_remove_devices()` | `MFD_DEP_LEVEL_NORMAL` | normal cells only |
| `mfd_remove_devices_late()` | `MFD_DEP_LEVEL_HIGH` | every MFD child still registered, normal cells too |
| `devm_mfd_dev_release()` | calls `mfd_remove_devices()` | normal cells only |
| failure path of `mfd_add_devices()` | calls `mfd_remove_devices()` | normal cells only |

- `MFD_DEP_LEVEL_HIGH` in this tree: set by one cell, `madera-ldo1` in
  `madera_ldo1_devs`. It is a regulator that can supply DCVDD, which the
  parent holds through `regulator_get()`.
- `drivers/mfd/arizona-core.c`: sets no `level` and does not call
  `mfd_remove_devices_late()`.
- `mfd_remove_devices_late()`: its only caller is `madera_dev_exit()`.
- **Unsafe usage**: a cell with `MFD_DEP_LEVEL_HIGH` on a path that removes
  children only through `mfd_remove_devices()`, the devres release or the
  failure path of `mfd_add_devices()`; the child stays registered after the
  parent driver is gone.
  - Safe: call `mfd_remove_devices()`, release what the parent took from the
    HIGH child, then call `mfd_remove_devices_late()`, as `madera_dev_exit()`
    does. The level test in `mfd_remove_devices_fn()` defines the
    requirement.

**Managed registration**

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

**Manual removal with devres**

- Models have this right; see `__device_release_driver()` and `really_probe()`
  in `drivers/base/dd.c`.

**Hot-pluggable parents**

- `drivers/mfd/mfd-core.c`: has no hotplug handling; the wrapper differs from
  `mfd_add_devices()` only in its arguments.
- Callers of `mfd_add_hotplug_devices()`: include parents on the platform
  bus that want automatic ids, for example `ec_device_probe()` in
  `drivers/mfd/cros_ec_dev.c`.
- `cell->id` with `PLATFORM_DEVID_AUTO`: ignored by `mfd_add_device()`;
  `pdev->id` is the allocated id, `mfd_get_cell(pdev)->id` is the cell's.
- `_dln2_transfer()` after `dln2_stop()`, while `disconnect` is set: returns
  `-ENODEV`. `-ESHUTDOWN` appears in `drivers/mfd/dln2.c` only as a URB
  status in the RX completion.
- `dln2_free()`: frees only the RX URBs. `struct dln2_dev` comes from
  `devm_kzalloc()` on the interface device, so it outlives
  `dln2_disconnect()`.
- Child `remove()` callbacks in `dln2_disconnect()`: run inside
  `mfd_remove_devices()`, after `dln2_stop()`, and call back into the parent.
  `dln2_i2c_remove()` and `dln2_spi_remove()` call `dln2_transfer()` and get
  `-ENODEV`; `dln2_gpio_remove()` calls `dln2_unregister_event_cb()`.

**Changes to registration**

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

## Regmap interrupt controller

**Interrupt chip registration**

- Domain creation: `regmap_irq_create_domain()` makes one
  `irq_domain_instantiate()` call with `.virq_base = irq_base`, whether
  `irq_base` is zero or not. It calls neither `irq_domain_create_legacy()`
  nor `irq_domain_create_linear()`; there is no irq_domain_add_legacy()
  function in this tree.
- Negative `irq_base` (for example the -1 that `da9063_device_init()` in
  `drivers/mfd/da9063-core.c` sets): `irq_alloc_descs()` picks any free
  contiguous range of `chip->num_irqs` descriptors. Registration continues
  with the returned base, so all indices are mapped at once, as for a
  positive `irq_base`.
- Positive `irq_base`: the range must be free at exactly that number;
  `__irq_alloc_descs()` returns `-EEXIST` otherwise.
- NULL `fwnode`: the domain is still created, named by `alloc_unknown_name()`
  in `kernel/irq/irqdomain.c`, with `domain->fwnode` NULL.
  `irq_find_matching_fwspec()` never matches it, so no firmware interrupt
  specifier reaches it; callers use `regmap_irq_get_domain()` or
  `regmap_irq_get_virq()`.
- Several chips registered with one `fwnode`: `irq_find_matching_fwspec()`
  returns the first match in `irq_domain_list`, so a firmware `interrupts`
  property reaches one of the domains only. `chip->domain_suffix` changes the
  name, not the lookup.

**Interrupts for children**

- What `platform_get_irq()` returns to a child is decided by the last two
  arguments the parent gives `mfd_add_devices()`; the cell resource holds the
  chip index in every case:

| Parent passes | Resource after `mfd_add_device()` | Child |
|---|---|---|
| `domain` from `regmap_irq_get_domain()` | Linux interrupt number | requests it directly |
| `irq_base` from `regmap_irq_chip_get_base()`, `domain` NULL | `irq_base` + index | requests it directly |
| `irq_base` 0, `domain` NULL | chip index, unchanged | converts with `regmap_irq_get_virq()` |

- `irq_base` row: correct only for a chip registered with a non-zero
  `irq_base`; `regmap_irq_chip_get_base()` does `WARN_ON()` and returns 0
  otherwise. Example: `da9063_device_init()` in `drivers/mfd/da9063-core.c`.
- Index row: `axp20x_usb_power_probe()` in
  `drivers/power/supply/axp20x_usb_power.c` feeds the result of
  `platform_get_irq_byname()` to `regmap_irq_get_virq()`; its parent in
  `drivers/mfd/axp20x.c` passes `0, NULL`.
- `regmap_irq_get_virq()` with a constant: used when the cell has no IRQ
  resource and the child reaches the parent's `struct regmap_irq_chip_data`,
  and by a parent that needs a child interrupt itself, for example
  `sec_irq_init_s2mpg1x()` through `s2mpg1x_add_chained_pmic()` in
  `drivers/mfd/sec-irq.c`.
- Child with an OF node: `platform_get_irq_affinity()` in
  `drivers/base/platform.c` tries `of_irq_get()` first and
  `__platform_get_irq_byname()` tries `fwnode_irq_get_byname()` first. The cell
  resource is used only when firmware gives no interrupt.

**Interrupt chip description**

- `regmap_add_irq_chip_fwnode()` has five `-EINVAL` tests of the chip, all
  before any allocation:
  - `num_regs <= 0`
  - `clear_on_unmask` with `ack_base` or `use_ack`
  - `mask_base` and `unmask_base` both set without `mask_unmask_non_inverted`
  - an `irqs[i].reg_offset` that is not a multiple of `map->reg_stride`
  - an `irqs[i].reg_offset / map->reg_stride` that is `>= num_regs`
- Not tested at registration: `type_in_mask` layouts, a zero `status_base`,
  `clear_on_unmask` with `status_invert`, `clear_ack` without `ack_base`.
- `mask_unmask_non_inverted`: read only by the registration test. It changes
  no written value; the kerneldoc in `include/linux/regmap.h` that describes
  an inverted mode does not match the code.
- `mask_base` and `unmask_base` both set (with the flag): to mask, the bit is
  set in the `mask_base` register and cleared in the `unmask_base` register,
  on every sync. Examples: `drivers/mfd/stpmic1.c`,
  `drivers/mfd/qcom-pm8008.c`.
- There is no mask_invert member in `struct regmap_irq_chip`; a register where
  0 means masked is described with `unmask_base` alone.
- `handle_mask_sync` set: neither `mask_base` nor `unmask_base` is written, at
  registration or in `regmap_irq_sync_unlock()`.

**Interrupt index lookup**

- `regmap_irq_get_virq()` has no bounds test: it reads
  `data->chip->irqs[irq].mask` for any `irq`, including negative values and
  values `>= chip->num_irqs`.
- Return on mapping failure: 0 from `irq_create_mapping()`, not a negative
  errno. `-EINVAL` is returned only for a table entry whose `mask` is 0.
- `irq_create_mapping()` on the domain is bounds-checked by
  `irq_domain_associate_locked()` against `hwirq_max` (`chip->num_irqs`), but
  `regmap_irq_get_virq()` reads the table before it gets there.
- **Potentially unsafe usage**: passing `regmap_irq_get_virq()` an index that
  is not a constant.
  - Unsafe: when nothing limits the value to `0 .. chip->num_irqs - 1` of the
    chip behind `data`, for example a value from firmware, a negative errno,
    or an enum that belongs to another chip variant; the read goes outside
    `chip->irqs[]`.
  - Safe: an index the parent itself placed in the cell resource from the enum
    that indexes `chip->irqs[]`, read back after the `< 0` test, as
    `axp20x_usb_power_probe()` does; only while the child's firmware node
    gives no interrupt of that name, since `__platform_get_irq_byname()` asks
    firmware first.
  - Safe: a loop bounded by the driver's own table of indices from the enum
    that indexes `chip->irqs[]` of that chip, as `max77693_muic_probe()` in
    `drivers/extcon/extcon-max77693.c` does with `enum max77693_irq_muic`.

**Child handler context**

- `regmap_irq_map()` installs no flow handler: it calls `irq_set_chip()`,
  `irq_set_nested_thread()`, `irq_set_parent()` and `irq_set_noprobe()`. It
  does not call `handle_edge_irq()` or set it.
- `IRQF_ONESHOT` on the child request: not required. `__setup_irq()` replaces
  the handler with `irq_nested_primary_handler()` before its test for a NULL
  handler without `IRQF_ONESHOT`, so that test never fires for a nested
  interrupt.
- **Potentially unsafe usage**: `request_threaded_irq()` with a NULL handler
  and no `IRQF_ONESHOT`.
  - Unsafe: on an interrupt that is not nested and whose chip lacks
    `IRQCHIP_ONESHOT_SAFE`; `__setup_irq()` returns `-EINVAL`.
  - Safe: on a child of a regmap interrupt chip, which `regmap_irq_map()`
    marks nested; `axp20x_usb_power_probe()` requests with flags 0 through
    `devm_request_any_context_irq()`.
- `request_any_context_irq()` and `devm_request_any_context_irq()`: return
  `IRQC_IS_NESTED`, which is 1, on success for such a child. The caller must
  test `< 0`; a test for non-zero treats success as failure.
- Trigger flags in the child request: `regmap_irq_set_type()` returns 0
  without doing anything when the type is not in
  `irqs[i].type.types_supported`, so an unsupported trigger is accepted
  silently.

**Interrupts across system sleep**

- `drivers/base/regmap/regmap-irq.c` has no suspend or resume hook. Mask and
  wake registers are written only at registration and in
  `regmap_irq_sync_unlock()`; a parent whose device loses register state must
  restore them itself.
- `suspend_device_irqs()` and `resume_irqs()` in `kernel/irq/pm.c` skip
  nested-thread descriptors. Child interrupts are never disabled or armed by
  the core; only the primary is.
- `dpm_suspend_noirq()` calls `suspend_device_irqs()` before the noirq
  callbacks; `dpm_resume_noirq()` calls `resume_device_irqs()` after them.
- **Potentially unsafe usage**: leaving the primary interrupt enabled across
  the parent's suspend and resume callbacks.
  - Unsafe: when the bus controller suspends before `suspend_device_irqs()`
    or resumes after `resume_device_irqs()`. `regmap_irq_thread()` then fails
    in `read_irq_data()`, acks nothing, calls no child handler and returns
    `IRQ_NONE`. On an adapter marked by `i2c_mark_adapter_suspended()`,
    `__i2c_check_suspended()` returns `-ESHUTDOWN` and warns.
  - Safe: `disable_irq()` on the primary in the parent's suspend callback and
    `enable_irq()` in resume, as `max77686_suspend()` and `max77686_resume()`
    in `drivers/mfd/max77686.c` do; `regmap_irq_thread()` then cannot run
    while the bus is suspended.
  - Safe: when the bus controller suspends and resumes in its noirq
    callbacks, as `exynos5_i2c_suspend_noirq()` does, and the primary was
    requested without `IRQF_NO_SUSPEND`; the callbacks run inside the window
    set by `dpm_suspend_noirq()` and `dpm_resume_noirq()`, and
    `suspend_device_irq()` skips a descriptor with `no_suspend_depth`.
- Wake and masking: `regmap_irq_set_wake()` and the wake part of
  `regmap_irq_sync_unlock()` never change `mask_buf`. Child interrupts without
  wake stay unmasked in the chip during suspend.
- `wake_base` polarity: a 1 in the register means wake disabled; with
  `wake_invert` a 1 means wake enabled.
- Failure on the primary: `regmap_irq_sync_unlock()` drops the return value of
  `enable_irq_wake(d->irq)` and `regmap_irq_set_wake()` returns 0 always. The
  child's `enable_irq_wake()` succeeds even when `set_irq_wake_real()` returns
  `-ENXIO` for the primary's chip.

## System controllers

**Syscon regmap creation**

- `drivers/mfd/syscon.c`: defines no `struct platform_driver`, no probe
  function, no OF match table and no platform id table; there is no
  syscon_driver or syscon_probe() in this tree.
- `syscon` compatible: nothing binds to it; the file holds only the lookup
  functions and `of_syscon_register_regmap()`.
- `CONFIG_MFD_SYSCON`: a `bool` in `drivers/mfd/Kconfig`; the file has no
  initcall and no exit function.
- `of_syscon_register()`: maps `reg` index 0 with `of_iomap()`, not through a
  device resource, so nothing claims the memory region.

**Syscon lookup functions**

- `syscon_node_to_regmap()`: returns the entry of any node already on
  `syscon_list`, whatever its compatible; the `syscon` compatible only decides
  whether a missing entry is created.
- Entries reach the list without `syscon` in two ways:
  `of_syscon_register_regmap()` and an earlier `device_node_to_regmap()`.
- `syscon_node_to_regmap()` on creation: takes only clock index 0 with
  `of_clk_get()` and one reset with
  `of_reset_control_get_optional_exclusive()`, then deasserts the reset.
- `regmap_mmio_attach_clk()`: only prepares the clock;
  `drivers/base/regmap/regmap-mmio.c` enables and disables it around each
  register access.
- `device_node_to_regmap()`: touches no clock and no reset.
- Clock error other than `-ENOENT`, or any reset error: the lookup fails with
  that code (for example `-EPROBE_DEFER`) and no entry is added, so the next
  lookup tries again.
- First creator wins: clock and reset are handled only when the entry is
  created, so `syscon_node_to_regmap()` after `device_node_to_regmap()` on the
  same node returns the regmap with no clock attached and the reset untouched.
- `syscon_regmap_lookup_by_phandle()` with a NULL `property`: looks up `np`
  itself.

**Syscon lookup results**

| Case | Result |
|---|---|
| node has no `syscon` compatible and no entry on `syscon_list`, any lookup except `device_node_to_regmap()` | `ERR_PTR(-EPROBE_DEFER)` |
| `syscon_node_to_regmap()` with a NULL node | `ERR_PTR(-EPROBE_DEFER)` |
| `syscon_regmap_lookup_by_phandle()`, `of_parse_phandle()` returns NULL | `ERR_PTR(-ENODEV)` |
| `syscon_regmap_lookup_by_phandle_args()`, property missing | code of `of_parse_phandle_with_fixed_args()`, `-ENOENT` |
| `reg` missing or `of_iomap()` fails, on creation | `ERR_PTR(-ENOMEM)` |
| `syscon_regmap_lookup_by_phandle_optional()` with `CONFIG_MFD_SYSCON` off | NULL |

- `-EINVAL` is not returned for a node that lacks `syscon`; see
  `device_node_get_regmap()`.
- `syscon_regmap_lookup_by_phandle_optional()`: turns only `-ENODEV` into
  NULL; every other error, `-EPROBE_DEFER` included, comes back as an
  `ERR_PTR()`.
- `-ENODEV` to NULL covers a property that is present but whose phandle does
  not resolve, since `of_parse_phandle()` returns NULL for both.
- **Unsafe usage**: using the result of
  `syscon_regmap_lookup_by_phandle_optional()` after only one of the two
  tests, `IS_ERR()` or NULL; with only `IS_ERR()` a NULL reaches the regmap
  calls, with only a NULL test an `ERR_PTR(-EPROBE_DEFER)` does.
  - Safe: `IS_ERR()` at the lookup with the error returned from probe, and a
    NULL test at each use, as `rockchip_pinctrl_probe()` does for
    `regmap_ioc`.

**Syscon regmap configuration**

- `reg-io-width`: sets both `reg_stride` and `val_bits`; `reg_bits` stays 32
  from `syscon_regmap_config`.
- Width check: `of_syscon_register()` has none; `regmap_mmio_get_min_stride()`
  in `drivers/base/regmap/regmap-mmio.c` accepts `val_bits` 8, 16 and 32 only.
- `reg-io-width = <8>`: allowed by the enum in
  `Documentation/devicetree/bindings/mfd/syscon-common.yaml`, fails in
  `regmap_init_mmio()` with `-EINVAL`.
- Resource smaller than the width: `of_syscon_register()` fails with
  `-EFAULT`.
- `max_register` of 0 (resource exactly one register): `max_register_is_0` is
  set, so the limit is still enforced.
- Hardware spinlock: `of_syscon_register()` only sets `use_hwlock`,
  `hwlock_id` and `hwlock_mode = HWLOCK_IRQSTATE`; it does not call
  `hwspin_lock_request_specific()` and sets no `lock` or `unlock` callback.
- `__regmap_init()` in `drivers/base/regmap/regmap.c`: requests the lock and
  fails with `-ENXIO` if it gets none.
- `of_hwspin_lock_get_id()` errors: `-ENOENT` is ignored; `-EPROBE_DEFER`
  fails the lookup silently; any other error fails it with a `pr_err()`.
- `CONFIG_HWSPINLOCK` off: the `of_hwspin_lock_get_id()` stub returns 0, so a
  `hwlocks` property is ignored and the regmap is created without it.
- Without a hardware spinlock: the regmap locks with a spinlock because the
  `regmap_mmio` bus sets `fast_io`; `syscon_regmap_config` does not set it.

**Syscon list locking**

- `syscon_list_lock`: a mutex, not a spinlock; there is no syscon_list_slock
  in this tree.
- `device_node_get_regmap()`: holds the mutex across the list search and
  `of_syscon_register()`, so two first lookups of one node create one regmap.
- Lookups need no `struct device`, so they also run from early init code, for
  example `at91sam9rl_pmc_setup()` declared with `CLK_OF_DECLARE()`.

**Children of a syscon node**

- Parent without the `syscon` compatible, two forms in this tree:
  - `device_node_to_regmap()` on the parent node, as `jz4740_wdt_probe()`
    does; creates a plain MMIO regmap.
  - `syscon_node_to_regmap()` on the parent node, when the parent driver
    registers its own regmap, as `sun20i_regulator_get_regmap()` does with
    `sunxi_sram_probe()`; returns `-EPROBE_DEFER` until the registration.
- `dev_get_regmap()` on the parent device: finds no regmap made by
  `of_syscon_register()`, because `__regmap_init()` calls
  `regmap_attach_dev()` only for a non-NULL device; it returns NULL unless a
  driver created a regmap on that device.
- `of_get_parent()` form: the lookup keeps no node reference, so
  `of_node_put()` directly after the lookup is right, as in
  `berlin2_reset_probe()`.

**Syscon binding rules**

- `Documentation/devicetree/bindings/mfd/syscon.yaml`: has no `select:` block
  and no `simple-mfd` entry; a new plain compatible is added in one place, the
  first `enum` of the `oneOf` under `properties: compatible`.
- Compatible with a fallback (specific, fallback, `syscon`): a new `items`
  entry in that `oneOf`; three such entries exist.
- `syscon.yaml` properties: only `compatible`, `reg` and `resets`, plus
  `reg-io-width` through the `$ref` to `syscon-common.yaml`, with
  `unevaluatedProperties: false`; a node with `simple-mfd`, children or other
  properties gets its own binding file.
- Own binding files: list `const: syscon` in their own `compatible` and do not
  reference `syscon-common.yaml`; only `syscon.yaml` has that `$ref`.
- `Documentation/devicetree/bindings/mfd/syscon-common.yaml`: applies to every
  node whose `compatible` contains `syscon`, through its own `select:`.
- Order: `syscon-common.yaml` checks only `contains`, `minItems` and
  `maxItems`; the position of `syscon` and `simple-mfd` comes from the `items`
  list of each device schema.
- `maxItems: 5`: applies to `compatible` with and without `simple-mfd`.
- `syscon` together with `simple-bus`: rejected, except for a closed list of
  compatibles in `syscon-common.yaml` marked as not allowed to grow.

**Registering a regmap**

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

## Children from the device tree

**The simple-mfd compatible**

- Match table: there is no of_default_bus_match_table symbol in the C code;
  the table is the function-local `match_table` in
  `of_platform_default_populate()`, `drivers/of/platform.c`.
- Code that tests the string `simple-mfd`: only that table and
  `simple_pm_bus_of_match` in `drivers/bus/simple-pm-bus.c`.
- `of_platform_default_populate()`: not a boot-only path; it is exported and
  drivers call it on their own node, for example `drivers/bus/imx-weim.c`.
- `of_platform_default_populate_init()` with `CONFIG_PPC`: does not call
  `of_platform_default_populate()`; platform code does, for example
  `arch/powerpc/platforms/microwatt/setup.c`.
- `of_platform_populate()` with `matches == NULL`: creates devices for the
  direct children of `root` and recurses into none of them;
  `__of_match_node()` returns NULL for a NULL table. The kerneldoc "NULL to
  use the default" does not describe the code.
- `devm_of_platform_populate()`: passes `matches == NULL`, so a `simple-mfd`
  child node gets a platform device and that node's children get none.
- Driver that needs recursion into `simple-mfd` children: calls
  `of_platform_default_populate()`.
- `of_platform_bus_create()` recurses only after
  `of_platform_device_create_pdata()` returned a device for the `simple-mfd`
  node itself; a disabled node or one with `OF_POPULATED` already set gets no
  device and its children are not walked.
- `OF_POPULATED` and `of_device_is_available()`: tested in
  `of_platform_device_create_pdata()`; `of_platform_bus_create()` tests
  `OF_POPULATED_BUS`.
- `of_clk_init()` and `of_irq_init()`: set `OF_POPULATED` on each node they
  initialise, so a `simple-mfd` node that is also such a provider loses its
  children.
- `CLK_OF_DECLARE_DRIVER()`: clears `OF_POPULATED` again, `CLK_OF_DECLARE()`
  does not; see `drivers/clk/ingenic/x1000-cgu.c`.
- Children that get no platform device even when walked, in addition to the
  flag and availability tests above: nodes without a `compatible` property;
  nodes matching `of_skipped_node_table`; nodes compatible with
  `arm,primecell`, which go to `of_amba_device_create()` and are not recursed
  into.

**Driver for simple-mfd nodes**

- `simple_pm_bus_of_match` in `drivers/bus/simple-pm-bus.c`: contains
  `simple-mfd` with `.data = ONLY_BUS`, so the `simple-pm-bus` platform driver
  matches a platform device whose compatible list contains `simple-mfd` at any
  position.
- Decline test in `simple_pm_bus_probe()`: only whether the matched string is
  at index 0 of `compatible`; it does not look for another driver.
- `"syscon", "simple-mfd"`: declined with `-ENODEV`, like any list where
  `simple-mfd` is not first.
- `of_match_device()` returns the entry that matches earliest in the node's
  compatible list; the index test runs only when that entry has `.data` set.
- Entries without `.data`: `simple-pm-bus` and six `fsl,` entries; a node whose
  best match is one of them takes the full clock, runtime PM and
  `of_platform_populate()` path even with `simple-mfd` later in its list.
- Driver override: tested with `device_has_driver_override()` from
  `include/linux/device.h`; `struct platform_device` has no `driver_override`
  member in this tree.
- Probe with a driver override set: returns 0 before any match lookup and
  calls neither `of_platform_populate()` nor `pm_runtime_enable()`.
- Build: `obj-$(CONFIG_OF) += simple-pm-bus.o` in `drivers/bus/Makefile`;
  there is no Kconfig symbol for the driver, and `CONFIG_OF` is bool, so the
  driver is built in whenever `CONFIG_OF` is set.

**Binding conventions**

- `Documentation/devicetree/bindings/mfd/mfd.txt`: does not require a
  device-specific compatible in front of `simple-mfd`, and says nothing about
  fallback order.
- Example in `mfd.txt`: `compatible = "syscon", "simple-mfd"`, no `ranges`,
  and a child `led@8.0` with `offset` and `mask` and no `reg`.
- `Documentation/devicetree/bindings/mfd/syscon-common.yaml`: holds the
  specific-compatible rule; when the list contains `simple-mfd` it sets
  `minItems: 3`. The schema selects only nodes whose list contains `syscon`.
- The `mfd.txt` example does not satisfy `syscon-common.yaml`; a new binding
  follows the schema.
- `Documentation/devicetree/bindings/writing-bindings.rst`: has the explicit
  rule "DON'T use 'simple-mfd' compatible for non-trivial devices, where
  children depend on some resources from the parent".
- `writing-bindings.rst` also has "DON'T use 'syscon' alone without a specific
  compatible string".
- `mfd.txt` gives two conditions for `simple-mfd`: the subnodes are separate
  and independent, "not needing any resources to be provided by the parent
  device"; and the nexus driver does not have to probe registers to find the
  children.
- `mfd.txt` has no sentence about using `simple-mfd` to avoid writing a
  driver; the nearest text is "DON'T create nodes just for the sake of
  instantiating drivers" in `writing-bindings.rst`.
- `ranges` in `mfd.txt`: listed under optional properties; the file does not
  mention empty `ranges`, regmap children, or when `ranges` is expected.
- `#address-cells` and `#size-cells` in `mfd.txt`: listed as optional, each
  with "Must be present if ranges is used".

## Conventions

**Conventions for new code**

These are conventions that the maintainers of the MFD subsystem ask of new
code. Existing code may differ. No code in a kernel tree states them, so they
are kept by hand and inserted as they are.

- Commit subjects: always capitalise the description after the subsystem
  prefix, for the MFD, LED and Backlight subsystems. The format is
  "mfd: <driver>: <Capitalised description>", as in
  "mfd: max77650: Remove useless type_invert flag".
- Do not hard-code implementation details in driver, struct or device names.
  Avoid the string "mfd" and the driver's own file name in names.
- Prefer to name the private data structure after the device (for example
  `struct kb3930`) and to name the variable that holds it `ddata`, rather than
  a generic name such as `info` or `priv`.
- MFD is an API in Linux, not just a physical layout. New core drivers that
  register multiple children belong in `drivers/mfd/`, and so do new calls to
  `mfd_add_devices()` or `devm_mfd_add_devices()`.
- Do not use the MFD API for a simple device with a single function. Use it
  only for a device that registers multiple children in different subsystems,
  through the MFD API or `of_platform_populate()`.
- For a simple MFD, consider whether a standard device tree compatible such as
  "simple-mfd" or "simple-pm-bus" can be used instead of a custom driver.
- The core MFD driver should handle only core resources, such as interrupts
  and the regmap.
- A child driver must reach the data of its parent with a standard API, such
  as `dev_get_drvdata()` on `pdev->dev.parent`. Avoid bespoke accessors or
  helper functions in the parent that pass state to child devices.
- Initialise a private resource, such as a regmap or a clock handle, in the
  child driver that consumes it, not in the parent, unless several child
  devices share the resource.
- Define `struct mfd_cell` arrays as `static const`.
- Do not pass platform data for child devices, such as `struct mfd_cell`
  arrays, through the match data of a device id table, such as `data` in
  `struct of_device_id`. To pass which variant a device is, store an enum or
  an integer id in the match data, and select the `static const` cell array
  with a `switch` in the probe code.
- Do not create local copies of cells in order to amend them at run time.
  Always use static references.
- Sibling child drivers, such as the RTC driver and the regulator driver under
  one MFD parent, must not call functions of each other directly. Do not
  expose driver-level callbacks that bypass the standard kernel subsystem
  APIs.
- Prefer `PLATFORM_DEVID_AUTO` for automatic cell indexing.

## Model gaps

### Other mistakes models make

- Models take firmware lookups on a child to follow `dev->fwnode`. After
  `device_set_of_node_from_dev()`, `platform_get_irq()` on the child asks the
  parent's node, through `dev_fwnode()`, before the cell's interrupt
  resources; it does not test `dev_of_node_reused()`.
- Models expect `kzalloc()` for a structure in this code.
  `mfd_match_of_node_to_dev()`, `of_syscon_register()` and
  `regmap_add_irq_chip_fwnode()` use `kzalloc_obj()` from
  `include/linux/slab.h`.
- Models expect an explicit `kfree()` on each early exit of
  `of_syscon_register()`. It holds `syscon` under `__free(kfree)` and returns
  it with `return_ptr()`.
- Models name irq_domain_add_linear() for the domain of a regmap interrupt
  chip. No source file in this tree defines it.
- Models do not know `platform_device_set_of_node()` and
  `platform_device_set_fwnode()` in `drivers/base/platform.c`.
