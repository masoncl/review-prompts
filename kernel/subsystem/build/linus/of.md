# Open Firmware (Device Tree) Subsystem

## Main structures

### Objects and how they relate

- `of_node_get()` and `of_node_put()`: no-op inlines in `include/linux/of.h`
  unless `CONFIG_OF_DYNAMIC`; without it no node is counted or freed.
- `CONFIG_OF_KOBJ` without `CONFIG_OF_DYNAMIC`: the node still embeds a
  kobject, for sysfs only; `of_node_release()` in `drivers/of/kobj.c` is empty.
- Leaked node reference (a missing `of_node_put()`) under `CONFIG_OF_DYNAMIC`:
  stays silent, except for an `OF_OVERLAY` node, whose count
  `__of_changeset_entry_destroy()` tests.
- `struct device_node` has no `allnext` member and there is no global node
  list; `for_each_of_allnodes()` walks child, sibling and parent links through
  `__of_find_all_nodes()` in `drivers/of/base.c`.
- `struct property` from an unflattened FDT: the struct lives in the unflatten
  chunk, but `name` and `value` point into the FDT blob, so the blob must
  outlive the tree; see `populate_properties()` in `drivers/of/fdt.c`.
- Overlay FDT: `of_overlay_fdt_apply()` copies it into `new_fdt` of
  `struct overlay_changeset` for that reason.
- `deadprops` of a node: also holds properties queued in a changeset and not
  yet applied, put there by `of_changeset_add_prop_helper()` and, for a node
  that the overlay itself adds, by `add_changeset_property()`;
  `__of_add_property()` and `__of_update_property()` take them off again.
- `struct of_changeset`: serialised against other writers by `of_mutex`, not
  atomic for readers; `__of_changeset_apply_entries()` applies entries one at a
  time, each edit taking `devtree_lock` on its own, and undo after a failure
  is best effort.
- Overlays have a second notifier chain: `overlay_notify_chain` in
  `drivers/of/overlay.c`, called once per fragment with
  `struct of_overlay_notify_data` and an `enum of_overlay_notify_action`
  value; `of_reconfig_chain` is called once per changeset entry with
  `struct of_reconfig_data`.
- `struct platform_device` is not created for every node:
  `of_platform_populate()` takes children of its root that have `compatible`
  and descends only below nodes that match the bus table; see
  `of_platform_bus_create()` in `drivers/of/platform.c`.
- Node compatible with "arm,primecell", under `CONFIG_ARM_AMBA`: becomes a
  `struct amba_device`, also marked `OF_POPULATED`.
- There is no struct of_reserved_mem here; the type is `struct reserved_mem`
  in `include/linux/of_reserved_mem.h`.
- `struct reserved_mem` holds no node pointer: `of_reserved_mem_lookup()`
  matches the node's basename against `name`, and the early callbacks in
  `struct reserved_mem_ops` take an FDT offset, not a `struct device_node`.
- Live tree with no FDT at all: under `CONFIG_OF_PROMTREE`,
  `of_pdt_build_devicetree()` in `drivers/of/pdt.c` builds the nodes from
  firmware calls, so no property points into a blob.
- `of_range_parser` and `of_range` are `#define` aliases in
  `include/linux/of_address.h`; the struct tags are
  `struct of_pci_range_parser` and `struct of_pci_range`.

## Where to look

**Core files**

| Job | File under `drivers/of/` |
|---|---|
| MSI parsing: `of_msi_xlate()`, `of_msi_get_domain()`, `of_msi_configure()` | `irq.c`; there is no MSI file |
| `msi-map` id translation: `of_map_msi_id()` | `base.c` |
| Boot-time self-test, `CONFIG_OF_UNITTEST` | `unittest.c`, data in `unittest-data/` |
| KUnit tests, `CONFIG_OF_KUNIT_TEST` and `CONFIG_OF_OVERLAY_KUNIT_TEST` | `of_test.c`, `overlay_test.c` |
| KUnit helpers, built on `CONFIG_KUNIT` alone | `of_kunit_helpers.c` |

**Compiled-out stubs and unit tests**

- Stub return values are not all errors: without `CONFIG_OF`, for example,
  `of_add_property()`, `of_remove_property()` and `of_dma_configure()`
  return 0.
- `of_iomap()` and `of_address_to_resource()`: their stubs (NULL, `-EINVAL`)
  are selected by `CONFIG_OF`, not `CONFIG_OF_ADDRESS`; see the second
  `#ifdef` block in `include/linux/of_address.h`.
- With `CONFIG_OF` on and `CONFIG_OF_ADDRESS` off, those two are plain
  externs; SPARC defines them in `arch/sparc/kernel/of_device_common.c`.
- `of_irq_get()`, `of_irq_get_byname()` and `of_irq_count()` without
  `CONFIG_OF_IRQ`: return 0, not an error; `of_irq_parse_one()` returns
  `-EINVAL`.
- There is no of_msi_map_id() here; the `of_msi_xlate()` stub returns
  `id_in` unchanged, and the `!CONFIG_OF` stub of `of_map_msi_id()` returns
  `-EINVAL`.
- `CONFIG_OF_DYNAMIC` off: besides the `of_node_get()` and `of_node_put()`
  inlines, only `of_reconfig_notifier_register()`,
  `of_reconfig_notifier_unregister()`, `of_reconfig_notify()` and
  `of_reconfig_get_state_change()` have stubs in `include/linux/of.h`, all
  four returning `-EINVAL`.
- No stub exists for the changeset functions (for example
  `of_changeset_init()`, `of_changeset_apply()`), `of_attach_node()`,
  `of_detach_node()` or `of_resolve_phandles()`; a caller fails to build
  unless its Kconfig entry requires the option or the calls sit under an
  `#if` on it, as in `drivers/media/platform/qcom/venus/core.c`.
- `CONFIG_OF_EARLY_FLATTREE` off: stubs exist only for the functions in the
  `#else` branch of `include/linux/of_fdt.h`; `of_scan_flat_dt()` and
  `early_init_dt_scan()`, for example, have none.
- `early_init_dt_scan_chosen_stdout()` stub: returns `-ENODEV`;
  `of_flat_dt_get_machine_name()` stub: returns NULL.
- `CONFIG_OF_FLATTREE` and `CONFIG_OF_RESOLVE`: select no stubs; without
  `CONFIG_OF_FLATTREE`, `initial_boot_params` is not even declared.
- `of_dma_get_range()` in `drivers/of/of_private.h`: returns `-ENODEV`
  unless both `CONFIG_OF_ADDRESS` and `CONFIG_HAS_DMA` are set.
- `of_platform_register_reconfig_notifier()`: empty unless both
  `CONFIG_OF_DYNAMIC` and `CONFIG_OF_ADDRESS` are set.
- `CONFIG_OF_ADDRESS` depends on `!SPARC && (HAS_IOMEM || UML)` and
  `CONFIG_OF_IRQ` on `!SPARC && IRQ_DOMAIN`, so their stubs apply on SPARC
  and on any other `CONFIG_OF` build that fails those tests.
- `CONFIG_OF_PROMTREE`: selected only by `arch/sparc/Kconfig` and by
  `config OLPC` in `arch/x86/Kconfig`; `arch/powerpc/Kconfig` selects
  `OF_EARLY_FLATTREE` instead.
- x86 with `CONFIG_OLPC`: `CONFIG_OF_EARLY_FLATTREE` is also on, so
  `drivers/of/fdt.c` is built next to `drivers/of/pdt.c`.
- SPARC: `CONFIG_OF_EARLY_FLATTREE` defaults to off; `fdt.c` is built only
  if something selects `CONFIG_OF_FLATTREE`, for example
  `CONFIG_OF_OVERLAY`.
- `CONFIG_OF_UNITTEST` depends on `OF_EARLY_FLATTREE`, which defaults to off
  on SPARC; x86 with `CONFIG_OF` always has `OF_EARLY_FLATTREE`.
- No blob from the bootloader: `unflatten_device_tree()` in
  `drivers/of/fdt.c` unflattens the built-in `drivers/of/empty_root.dts`;
  `of_have_populated_dt()` tells that case apart.
- Checker for expected messages: `scripts/dtc/of_unittest_expect`, run on a
  saved console log; the kernel compares nothing.
- `EXPECT_NOT_BEGIN()` and `EXPECT_NOT_END()`: mark a message that must not
  appear between them.
- Match rule, `compare()` in the script: the console line, timestamp
  removed, must begin with the expected text; anything after it is ignored.
- Expected text of a message printed with `pr_err()`, `pr_warn()` or
  `pr_info()` therefore starts with the `pr_fmt` prefix of the printing
  file, for example `"OF: overlay: "`; a patch that changes a `pr_fmt` in
  `drivers/of/` changes every such message of that file.
- Expected strings are formatted output, with node paths and errno numbers
  already expanded; search `drivers/of/unittest.c` for a fixed fragment of
  the message, not for the format string.
- A message printed by several tests has one pair per test; all pairs need
  the new text.
- Placeholders in expected text: `<<int>>`, `<<hex>>`, and `<<all>>`, which
  matches the rest of the line.
- `level` argument of the four macros: the level the marker line is printed
  at; the script compares text only.

## Node references

**Iterator macros**

- Macros that declare the loop variable themselves, as `struct device_node *`
  with `__free(device_node)`: `for_each_child_of_node_scoped()`,
  `for_each_available_child_of_node_scoped()`,
  `for_each_compatible_node_scoped()`,
  `for_each_child_of_node_with_prefix()`, `for_each_of_graph_port()`,
  `for_each_of_graph_port_endpoint()`. No other node iterator in
  `include/linux/of.h` or `include/linux/of_graph.h` does.
- `for_each_child_of_node_with_prefix()`, `for_each_of_graph_port()`,
  `for_each_of_graph_port_endpoint()`: no "_scoped" in the name, yet they
  declare the variable; a variable of that name declared by the caller is
  shadowed and never set.
- There is no for_each_endpoint_of_node_scoped in this tree;
  `for_each_endpoint_of_node()` uses a caller-declared variable and the caller
  puts it on early exit.
- `for_each_reserved_child_of_node()` and `for_each_node_with_property()`:
  counted, caller-declared, same rule as `for_each_child_of_node()`.
- `of_property_for_each_u32()`: takes three arguments and declares its own
  cursor `_it` in the `for`; only the `u32` is the caller's.
- `of_property_for_each_string()`: declares nothing; the caller supplies
  both the `struct property *` and the `const char *`.
- `for_each_of_allnodes()`, `for_each_of_allnodes_from()`: usable only by
  built-in code; `__of_find_all_nodes()` is not exported, `of_mutex` is
  declared only in `drivers/of/of_private.h`, and `devtree_lock` only there
  and in `arch/sparc/include/asm/prom.h`.
- `for_each_of_allnodes()` and `for_each_of_allnodes_from()`: take no
  reference; in-tree callers hold `devtree_lock` (for example the `of_find_`
  functions in `drivers/of/base.c`), hold `of_mutex` (`of_core_init()`), or
  run from `__init` code.

**Node reference counts**

- `of_node_release()` on a node without `OF_DETACHED`: prints "ERROR:
  of_node_release() detected bad of_node_put() on" plus the parent path and
  `full_name`; no "Bad of_node_put()" string exists in this tree.
- Stack dump and the second error line: skipped when `CONFIG_OF_UNITTEST` is
  set and the parent's `full_name` is "testcase-data".
- Order of checks in `of_node_release()`: `OF_DETACHED`, then `OF_DYNAMIC`,
  then `OF_OVERLAY` with `OF_OVERLAY_FREE_CSET`.
- Detached node without `OF_DYNAMIC` (a boot node after `of_detach_node()`):
  release returns silently, nothing printed, nothing freed.
- Freed nodes: `OF_DETACHED` and `OF_DYNAMIC`, and either no `OF_OVERLAY` or
  `OF_OVERLAY_FREE_CSET` set.
- Overlay node with children, or with properties left: release prints an
  error and frees the node anyway.
- Count reaching zero on an attached node (boot or overlay):
  `kobject_cleanup()` in `lib/kobject.c` removes the node from
  `/sys/firmware/devicetree`, frees the kobject name and puts the parent
  kobject; the `struct device_node` memory stays.
- Overlay node, missing put: `__of_changeset_entry_destroy()` sees a count
  above 1, prints "ERROR: memory leak, expected refcount 1 instead of", and
  does not set `OF_OVERLAY_FREE_CSET`.
- Overlay node after that message: never freed, even if the late put arrives;
  release then prints "ERROR: memory leak before free overlay changeset".
- Overlay removal does not fail on a bad count; nothing in
  `drivers/of/overlay.c` reads the count.
- Overlay node, extra put, no other holder: the count reaches zero before
  `OF_OVERLAY_FREE_CSET` is set; error printed, node leaked, and the changeset's
  own put then gives a `refcount_t` underflow warning.
- Overlay node, extra put, another holder present: the count is 1 at
  changeset destroy, the node is freed, and the holder has a use-after-free.

**Borrowed pointers and device of_node**

- `device_set_node()`: assigns `dev->fwnode` and `dev->of_node`, takes no
  reference.
- `device_add()` and `device_release()` in `drivers/base/core.c`: neither
  gets nor puts `dev->of_node`; whoever creates the device owns the reference
  and must drop it itself.
- Core helpers that do take and drop it: `device_add_of_node()` and
  `device_remove_of_node()`, `device_set_of_node_from_dev()`,
  `platform_device_set_of_node()`, `platform_device_set_fwnode()`,
  `platform_device_set_of_node_from_dev()`.
- `of_device_alloc()`: calls `platform_device_set_of_node()`, which takes the
  reference with `fwnode_handle_get()`.
- `platform_device_release()`: drops the node with `fwnode_handle_put()` on
  `dev.fwnode`; it does not call `of_node_put()` on `dev.of_node`.
- Platform device whose `dev.of_node` is assigned by hand with
  `of_node_get()` while `dev.fwnode` is left unset: the release does not drop
  that reference; use `platform_device_set_of_node()`.
- `platform_device_register_full()`: takes `fwnode_handle_get()` on
  `pdevinfo->fwnode` itself.
- `device_set_of_node_from_dev()`: marks reuse with
  `dev_set_of_node_reused()`, a bit `DEV_FLAG_OF_NODE_REUSED`; `struct device`
  has no `of_node_reused` field, only `struct platform_device_info` has.
- `device_add_of_node()`: returns `-EBUSY` and takes nothing if the device
  already has an `of_node`.
- `__of_find_node_by_path()` and `__of_find_node_by_full_path()` in
  `drivers/of/base.c`: return a counted node.
- `__of_find_all_nodes()`: borrowed; `of_find_all_nodes()` is the counted
  form.
- `dev_of_node()` and `to_of_node()`: borrowed, plain accessors.
- Bus code that sets the node with `device_set_node()` and wants it counted
  takes the reference itself, for example `of_register_spi_device()` with
  `of_node_get()`.

**Lookups that consume an argument**

- Rule: a function with a `prev`, `previous` or `from` parameter puts that
  node, except `__of_find_all_nodes()`; search `include/linux/of.h` and
  `include/linux/of_graph.h` for "next" and for `from`.
- Consumers whose name or parameter does not show it:
  `of_get_next_parent()` (parameter `node`), `of_find_all_nodes()`,
  `of_phandle_iterator_next()` (puts `it->node`),
  `__of_find_node_by_full_path()` (parameter `node`).
- Steppers also covered by the rule: `of_get_next_reserved_child()`,
  `of_get_next_child_with_prefix()`, `of_get_next_cpu_node()`,
  `of_graph_get_next_endpoint()`, `of_graph_get_next_port()`,
  `of_graph_get_next_port_endpoint()`.
- NULL parent: `of_get_next_child()`, `of_get_next_child_with_prefix()`,
  `of_get_next_available_child()`, `of_get_next_reserved_child()`,
  `of_graph_get_next_port()`, `of_graph_get_next_port_endpoint()` and
  `of_graph_get_next_endpoint()` return NULL before the put, so `prev` keeps
  its reference.
- `of_irq_find_parent()`: leaves the argument's count alone; it takes its own
  reference first and puts that one while walking up.
- Get-before-consume in a driver: `gsc_hwmon_get_devtree_pdata()` in
  `drivers/hwmon/gsc-hwmon.c` calls `of_node_get()` on the borrowed
  `of_node` on the line before `of_find_compatible_node()`.

**Phandle lists and references**

- Unresolved phandle with `cells_name` NULL (`of_parse_phandle()`,
  `of_parse_phandle_with_fixed_args()`, `of_parse_phandle_with_args()` with
  NULL `cells_name`): `__of_parse_phandle_with_args()` returns 0 with
  `out_args->np` NULL; the caller must test `np`.
- Unresolved phandle with `cells_name` set: `-EINVAL` after "could not find
  phandle".
- Any error return from `__of_parse_phandle_with_args()`: `out_args` is not
  written, so `out_args->np` holds whatever the caller left there.
- Empty entry in the iterator: `of_phandle_iterator_next()` returns 0 with
  `it->phandle` 0 and `it->node` NULL; the body of `of_for_each_phandle()`
  runs for it and must not dereference `it->node`.
- Empty entry at the requested index: `__of_parse_phandle_with_args()`
  returns `-ENOENT`.
- `of_for_each_phandle()`: discards the return of
  `of_phandle_iterator_init()`; a missing property, and the case of no
  `cells_name` with a negative `cell_count`, both end the loop with `-ENOENT`.
- `out_args` NULL on success: `__of_parse_phandle_with_args()` puts the node
  itself; the caller has nothing to drop.

**Puts inside iterator loops**

- Non-scoped, leave early and hand the reference out:
  `of_get_child_by_name()` (`break`, then returns the child) and
  `of_graph_get_endpoint_by_regs()` (`return node` inside
  `for_each_endpoint_of_node()`).
- Scoped, leave early with no put: `of_platform_populate()` and
  `of_platform_bus_probe()` in `drivers/of/platform.c` use
  `for_each_child_of_node_scoped()` with a bare `break`.
- Scoped, hand the loop's own reference out: `return_ptr()` in
  `of_graph_get_port_by_id()`; no `of_node_get()` is needed for that.
- Scoped, keep the node while the loop goes on: store `of_node_get()` of it;
  the loop's reference is put at the next step.

**Automatic cleanup of nodes**

- **Potentially unsafe usage**: `of_node_put()` on a `__free(device_node)`
  variable.
  - Unsafe: when the variable still holds the put pointer at any scope exit;
    the `DEFINE_FREE` body in `include/linux/of.h` puts it a second time.
  - Safe: when the variable is overwritten with a counted pointer or NULL
    before any exit, as `__of_translate_address()` in `drivers/of/address.c`
    does with `dev`.
- **Potentially unsafe usage**: passing a `__free(device_node)` variable as
  the consumed argument of `of_get_next_parent()` or an `of_find_` function.
  - Unsafe: when the result goes to another variable; the callee has put the
    node and the cleanup puts it again.
  - Safe: when the result is assigned back to the same variable, as
    `of_link_to_phandle()` in `drivers/of/property.c` does with
    `of_get_next_parent()`.
- **Unsafe usage**: storing an `ERR_PTR()` value in a
  `__free(device_node)` variable; the `DEFINE_FREE` body tests only for NULL
  and calls `of_node_put()` on it.
  - Safe: NULL, as `opp_np` in `_bandwidth_supported()` in
    `drivers/opp/of.c` holds until a lookup is assigned.
- `of_graph_get_port_by_id()`: its `__free(device_node)` variable `node` is
  never handed out; `return_ptr()` is applied to the loop variable of
  `for_each_child_of_node_scoped()`.
- Storing instead of returning: `*host = no_free_ptr(dev)` in
  `__of_translate_address()`.

## Reading properties

**Typed property reads**

- Empty property from `populate_properties()`: `length` 0 with a non-NULL
  `value`, so the integer and index readers, and the array readers asked for
  one or more elements, return `-EOVERFLOW`, not `-ENODATA`.
- `-ENODATA` from an integer read: only when `value` is NULL, which
  `of_find_property_value_of_size()` tests before the length.
- `of_pdt_build_one_prop()` in `drivers/of/pdt.c`: sets `length` to 0 and
  does not assign `value` when the firmware reports a property length of 0
  or less.
- Variable forms with `sz_min` 0 and nonzero `sz_max`: an empty property with
  a non-NULL `value` passes both size tests and the call returns 0 elements.
- Variable forms, property longer than a nonzero `sz_max` elements:
  `-EOVERFLOW`; nothing is truncated or copied.
- `of_property_read_string()`: tests `!prop->length` for `-ENODATA`.
- `of_property_read_string_helper()` and `of_property_match_string()`: test
  `!prop->value`; an empty property with non-NULL `value` still gives
  `-ENODATA`, from the fall-through after the loop.
- `of_property_read_string_array()` returning `-EILSEQ`:
  `of_property_read_string_helper()` has already stored the pointers to the
  strings before the unterminated one, so the output array is partly
  written.
- The integer, array and index readers, `of_property_read_string()` and
  `of_property_read_string_index()`: every error return comes before the
  first store, so the output is unchanged on failure.

**Boolean and presence tests**

- `of_property_read_bool()` on a property with nonzero `length`: prints with
  plain `pr_warn()` on every call; not `WARN()`, not once-only, not rate
  limited.
- `fwnode_property_read_bool()` and `device_property_read_bool()` on an OF
  node: reach `of_property_read_bool()` through
  `of_fwnode_property_read_bool()` in `drivers/of/property.c`, so they print
  the same warning.
- `fwnode_property_present()` and `device_property_present()` on an OF node:
  reach `of_property_present()` through `of_fwnode_property_present()`; no
  warning.

**Lifetime of property values**

- Removal or replacement: never frees; the pointer stays valid after the
  property has left `np->properties`.
- `of_node_release()` in `drivers/of/dynamic.c`: the only place the core frees
  `properties` and `deadprops`; it runs when the last node reference drops.
- `of_node_release()` returns without freeing when `OF_DETACHED` is clear,
  when `OF_DYNAMIC` is clear, or when the node has `OF_OVERLAY` without
  `OF_OVERLAY_FREE_CSET`.
- Without `CONFIG_OF_DYNAMIC`: `of_node_release()` is an empty function in
  `drivers/of/kobj.c` and `of_node_put()` is an empty inline; the core frees
  no property.
- `__of_prop_free()`: calls `kfree()` on `name`, `value` and the
  `struct property` separately, for every entry of both lists; the property's
  own `OF_DYNAMIC` flag is not tested.
- `__of_add_property()` and `__of_update_property()`: first take the incoming
  property off `np->deadprops`, so that list is walked long after a removal.
- **Unsafe usage**: freeing a `struct property`, or its `name` or `value`,
  while it is on `np->properties` or `np->deadprops`; the next walk of the
  list and `of_node_release()` touch freed memory.
  - Safe: freeing a property that was never linked to the node, as
    `of_changeset_add_prop_helper()` does when `of_changeset_add_property()`
    fails.
  - Safe: leaving a removed property allocated, as `ima_free_kexec_buffer()`
    in `drivers/of/kexec.c` does after `of_remove_property()`.

**Status property**

- There is no of_device_is_fail and no of_device_is_reserved in this tree;
  `__of_device_is_fail()` and `__of_device_is_reserved()` are static in
  `drivers/of/base.c`.
- Outside `drivers/of/base.c`: the only exported test for reserved is
  `of_get_next_reserved_child()`; fail and disabled have none, a caller reads
  `status` itself, for example with `of_property_read_string()`.
- `"disabled"`: compared against nowhere in `drivers/of/`; any `status` other
  than `"okay"` or `"ok"` makes the node not available.
- `status` present but empty (non-NULL `value`) or not NUL-terminated:
  `__of_device_is_status()` returns false, so the node is not available, not
  reserved and not fail.
- `of_get_next_cpu_node()` and `for_each_of_cpu_node()`: skip only fail
  nodes; disabled and reserved CPU nodes are returned.
- `of_get_next_reserved_child()` and `for_each_reserved_child_of_node()`:
  return only reserved children; the kerneldoc line about skipping disabled
  nodes describes a different function.
- `of_get_available_child_by_name()`: tests only the first child with that
  name; if it is not available the result is NULL, with no look at later
  children of the same name.
- `of_fwnode_get_next_child_node()` and `of_fwnode_get_named_child_node()` in
  `drivers/of/property.c`: use the available-only iterators, so fwnode child
  walks over OF nodes skip every child that is not available.
- `of_get_next_status_child()`: static worker behind the available and
  reserved child iterators; it takes the status test as a callback.
- `of_fdt_device_is_available()` in `drivers/of/fdt.c` and
  `of_property_status_ok()` in `drivers/of/dynamic.c`: separate parsers that
  know only `"okay"` and `"ok"`; they do not call `__of_device_is_status()`.

## Translating IDs, addresses and interrupts

**ID map translation**

- `of_map_id()` signature here: `(np, id, map_name, cells_name, map_mask_name,
  filter_np, arg)`; there is no `u32` ID out-pointer and no node out-pointer.
- Result: a `struct of_phandle_args` filled through `arg`; the node is
  `arg->np`, the translated ID is `arg->args[0]`.
- Wrappers: `of_map_iommu_id()` and `of_map_msi_id()` in `drivers/of/base.c`
  are the only callers of `of_map_id()`; `of_map_iommu_id()` passes a NULL
  `filter_np`.
- `filter_np` is `struct device_node * const *` and is never written.
- `filter_np` non-NULL: the map property must exist; `*filter_np` non-NULL
  as well: only entries that target that node match.

| Case | Return | `arg->np` | `arg->args[]` |
|---|---|---|---|
| `np`, `map_name`, `cells_name` or `arg` NULL | `-EINVAL` | not written | not written |
| property absent, `filter_np` NULL | 0 | NULL | `args[0]` = input ID, `args_count` 1 |
| property absent, `filter_np` non-NULL | `-ENODEV` | NULL | not written |
| no entry matches, or none targets `*filter_np` | 0 | NULL | `args[0]` = unmasked input ID, `args_count` 1 |
| an entry matches | 0 | target node | each output cell plus (masked ID − id-base) |

- Match versus bypass: only `arg->np` tells them apart; both return 0. See
  `imx_pcie_add_lut_by_rid()` in `drivers/pci/controller/dwc/pci-imx6.c`.
- Ownership: on a match `arg->np` holds a reference from
  `of_find_node_by_phandle()`, with or without a filter; the caller calls
  `of_node_put()`.
- **Unsafe usage**: `of_node_put(arg->np)` after a failed call when `arg` was
  not zero-initialised.
  - Unsafe: `of_map_id()` sets `arg->np = NULL` only after its argument
    check, so on that `-EINVAL` return, for example for a NULL `np`,
    `arg->np` is stack garbage; under `CONFIG_OF_DYNAMIC` `of_node_put()`
    passes it to `kobject_put()`.
  - Safe: `struct of_phandle_args spec = {};` then an unconditional
    `of_node_put(spec.np)`, as `of_pmsi_get_msi_info()` in
    `drivers/irqchip/irq-gic-its-msi-parent.c` does.

**Map entry output cells**

- Cell count: read per entry from the entry's target node with
  `of_property_read_u32(phandle_node, cells_name, &cells)`.
- `cells_name`: passed by the caller (`"#iommu-cells"` or `"#msi-cells"` in
  the wrappers); it is not derived from the map name.
- Entry layout: id-base, phandle, `cells` output cells, length; `3 + cells`
  cells, so entries in one map can differ in size.
- Target lacks the property: `cells` is 1.
- Largest count: `MAX_PHANDLE_ARGS`; a larger one returns `-EINVAL` after a
  `pr_err()`.
- Count of 0: accepted; a match sets `args_count` to 0 and writes no
  `args[]`.
- Length check: the property must be a whole number of cells and every entry
  walked must fit; otherwise `-EINVAL`.
- Unresolvable phandle: `-ENODEV` for any entry reached before the match, not
  only the matching one, because the target is needed to size the entry.
- `of_check_bad_map()`: when the first entry's target says 2 cells and the
  whole map parses as 4-cell entries with one phandle and length 1, every
  entry is read as 1-cell, with a `pr_warn_once()`.
- More than one output cell with an entry length above 1: `-EINVAL` when the
  ID falls in that entry.

**MSI controller lookup**

- Properties read: `msi-map` with `msi-map-mask`, and `msi-parent`; no file
  under `drivers/of/` reads `msi-controller`.
- Walk: `of_msi_xlate()` follows `dev->parent`, not device tree parents.
- Return: `u32`; `id_in` unchanged when nothing translates; there is no
  error return.
- Order at each level: `of_map_msi_id()` on `parent_dev->of_node`; only on a
  non-zero return, `of_check_msi_parent()`.
- `msi-map` present with no matching entry: `of_map_msi_id()` returns 0, so
  the walk ends there with the ID unchanged; `msi-parent` on that node is
  not tried.
- Non-zero from `of_map_msi_id()`: any error, for example a NULL `of_node`
  or a malformed map, moves on to `msi-parent` and then up.
- `msi-parent`: accepted only when entry 0 has zero argument cells; with
  cells `of_check_msi_parent()` returns `-EINVAL` and the walk continues up.
- `msi-parent` never changes the ID.
- `msi_np` NULL: `msi-parent` is not read, and a node without `msi-map` also
  ends the walk; the walk goes up only past a device for which
  `of_map_msi_id()` returns an error, for example a NULL `of_node`.
- `of_msi_get_domain()`: no walk and no `msi-map`; it iterates every
  `msi-parent` entry of the given node and returns the first domain
  `irq_find_matching_host()` finds for the token.

**MSI controller node argument**

- `msi_np` NULL: accepted; the caller gets the ID only, as
  `fsl_mc_get_msi_id()` in `drivers/bus/fsl-mc/fsl-mc-msi.c` does.
- `*msi_np` non-NULL on entry, match through `msi-map`: `of_msi_xlate()`
  drops the lookup reference; the caller's count is unchanged.
- `msi-parent`: absent `#msi-cells` means 0 cells, so the same controller
  node counts as 1 cell under `msi-map` and 0 under `msi-parent`.
- `msi-map` result: `of_msi_xlate()` uses `args[0]` only, and only when
  `args_count > 0`; with 0 cells the node is still handed back and the ID
  stays `id_in`.

**Address translation**

- Node read: `of_translate_one()` reads the property on the node being
  crossed, starting at the device's parent; the last node of the walk, the
  one with no parent, is never read.
- Missing `ranges`: failure, except where `of_empty_ranges_quirk()` is true;
  that needs `CONFIG_PPC` and either a `"1682m-sdc"` node or a
  `"Power Macintosh"` or `"MacRISC"` machine.
- Missing `dma-ranges`: 1:1, the same as an empty one.
- Logic PIO: a node registered as a non-`LOGIC_PIO_CPU_MMIO` range ends the
  walk before `ranges` is read, and `of_translate_address()` returns
  `OF_BAD_ADDR`.
- `of_translate_dma_address()`: steps with `__of_get_dma_parent()` at every
  level, the first included.
- `__of_get_dma_parent()`: takes the `interconnects` entry at the index of
  `"dma-mem"` in `interconnect-names`; without that name, or if the entry
  does not parse, it uses `of_get_parent()`.
- Without `CONFIG_HAS_DMA` or without `CONFIG_OF_ADDRESS`:
  `__of_get_dma_parent()` is a stub in `drivers/of/of_private.h` that calls
  `of_get_parent()`.

**Interrupt parsing**

- `interrupts-extended`: wins per index, when `of_parse_phandle_with_args()`
  returns 0; any other return falls back to `interrupts`, including an index
  past its last entry.
- Node with both `interrupt-controller` and `interrupt-map`: the map wins and
  the walk goes on through it.
- Map ignored: only on a node that has `interrupt-controller` and matches
  `of_irq_imap_abusers[]` in `drivers/of/irq.c`.
- `of_irq_imap_abusers[]`: holds `"CBEA,platform-spider-pic"` and
  `"sti,platform-spider-pic"`, not platform-open-pic strings, and also
  `"pasemi,rootbus"`, among others.
- Map entry whose parent is the node itself: `of_irq_parse_raw()` returns 0
  there, with the specifier taken from the map.
- `of_irq_parse_raw()` called directly: it takes its own reference on the
  input `out_irq->np`; the caller's reference is not consumed, and
  `of_irq_parse_pci()` in `drivers/pci/of.c` passes a borrowed pointer.

**Interrupt lookup results**

- No interrupt at that index: `of_irq_get()` returns `-EINVAL` when the node
  has no `interrupts` property or no interrupt parent, `-EOVERFLOW` when the
  index is past the end of `interrupts`.
- `-ENOENT`: comes from `of_irq_parse_raw()` when the walk runs out of
  parents without reaching a controller; it does not mean "property absent".
- `platform_get_irq_affinity()` in `drivers/base/platform.c`: passes on only
  a positive value or `-EPROBE_DEFER` from `of_irq_get()`; anything else
  falls back to the resource table and, with no IRQ resource there, ends as
  `-ENXIO`.
- `platform_get_irq_optional()` and `platform_get_irq()`: wrappers around
  `platform_get_irq_affinity()`, which turns a final 0 into `-EINVAL` with a
  `WARN()`.
- `fwnode_irq_get()` in `drivers/base/property.c`: turns 0 from
  `of_irq_get()` into `-EINVAL`.

## Locks and live tree changes

**devtree_lock and of_mutex**

- `of_overlay_phandle_mutex`: third lock, a static `struct mutex` in
  `drivers/of/overlay.c`, taken only through `of_overlay_mutex_lock()`; there
  is no object named of_overlay_mutex.
- `of_mutex`: taken with `mutex_lock(&of_mutex)` directly; there is no
  of_mutex_lock() helper.
- Order in `of_overlay_fdt_apply()`: `of_overlay_phandle_mutex`, then
  `of_mutex`, then `devtree_lock`; `of_fdt_unflatten_mutex` in
  `drivers/of/fdt.c` is also taken while `of_mutex` is held.
- `of_overlay_remove()`: takes `of_mutex` only, not
  `of_overlay_phandle_mutex`.
- Reconfig notifiers do not run under `of_mutex`: `of_attach_node()`,
  `of_detach_node()`, `of_add_property()`, `of_remove_property()` and
  `of_update_property()` notify after the change and after
  `mutex_unlock(&of_mutex)`, and discard the notifier's return value, so a
  notifier cannot veto.
- `of_alias_get_id()` and `of_alias_get_highest_id()`: take `of_mutex`, so
  they may sleep, unlike the node and property lookups.
- `__of_find_property()`, `__of_get_next_child()`,
  `__of_device_is_compatible()`, `__of_device_is_available()` are `static` in
  `drivers/of/base.c`, and `__of_attach_node()` is `static` in
  `drivers/of/dynamic.c`; the `__` forms with a locking rule that other files
  can call are those declared in `drivers/of/of_private.h`, plus
  `__of_find_all_nodes()` and the macro `for_each_of_allnodes()` in
  `include/linux/of.h`.
- The `__` prefix does not mean one locking rule; for example:

| Kind | For example | Caller must |
|---|---|---|
| read-only | `__of_get_property()`, `__of_find_node_by_path()`, `__of_find_all_nodes()` | hold `devtree_lock` or `of_mutex`, or own the tree |
| modifying | `__of_add_property()`, `__of_remove_property()`, `__of_update_property()`, `__of_detach_node()` | hold `of_mutex` unless no other task can reach the node, not hold `devtree_lock`, be able to sleep |
| changeset notify | `__of_changeset_apply_notify()`, `__of_changeset_revert_notify()` | hold `of_mutex` on entry; they unlock and relock it |

- Modifying `__` forms: take `devtree_lock` themselves for the list change,
  release it, then call the sysfs helpers in `drivers/of/kobj.c`.
- **Unsafe usage**: calling a modifying `__` form with `devtree_lock` held;
  the raw spinlock is taken again and the sysfs step may sleep.
  - Safe: hold `of_mutex` only, as `of_add_property()` does.
- **Potentially unsafe usage**: calling a read-only `__` form without
  `devtree_lock`.
  - Unsafe: on a node reachable from `of_root`, with `of_mutex` not held
    either; `__of_add_property()`, `__of_remove_property()`,
    `__of_update_property()` and `__of_detach_node()` relink `properties`,
    `deadprops`, `child` and `sibling` under `devtree_lock`.
  - Safe: with `devtree_lock` held, as `of_find_compatible_node()` does.
  - Safe: with `of_mutex` held, as `of_core_init()` does with
    `for_each_of_allnodes()`; every caller of a modifying `__` form on the
    live tree holds `of_mutex`.
  - Safe: on a tree that is not attached to the live tree, as
    `add_changeset_node()` does with `__of_get_property()` on the overlay's
    own unflattened tree.
- **Potentially unsafe usage**: calling a modifying `__` form without
  `of_mutex`.
  - Unsafe: on a node in the live tree; the sysfs update runs after
    `devtree_lock` is dropped and only `of_mutex` orders it against another
    writer.
  - Safe: on a newly allocated node that no other task can reach, as
    `__of_node_dup()` does with `__of_add_property()`.

**Node flags**

| Flag | What the core does with it | Who sets and clears it |
|---|---|---|
| `OF_DYNAMIC` | `of_node_release()` frees a node only if set | `__of_node_dup()`; pseries on nodes it allocates, e.g. `dlpar_parse_cc_node()`; never cleared |
| `OF_DETACHED` | `of_node_release()` logs an error and returns without freeing if clear; the tree scan in `of_find_node_by_phandle()` skips nodes that have it; `of_resolve_phandles()` returns `-EINVAL` if the overlay root lacks it; `__of_detach_node()` warns and returns if already set | core only: `__of_node_dup()`, `__of_detach_node()`, `__unflatten_device_tree()` on the root node only and only when its `detached` argument is true; cleared by `__of_attach_node()` |
| `OF_POPULATED` | `of_platform_device_create_pdata()` refuses a node that has it; `of_platform_notify()` skips add if set and remove if clear | buses with `of_node_test_and_set_flag()`; also set with no device by `of_irq_init()` and `of_clk_init()` |
| `OF_POPULATED_BUS` | `of_platform_bus_create()` skips the node; `of_platform_notify()` creates a device for a new node only if the parent is the root or has it | `of_platform_populate()` on the root passed in, `of_platform_bus_create()`; cleared by `of_platform_depopulate()` and `of_platform_device_destroy()`; also `drivers/nvmem/layouts.c` |
| `OF_OVERLAY` | `__of_attach_node()` does not derive `name` and `phandle` from properties; `of_node_release()` and `__of_changeset_entry_destroy()` apply the overlay checks | core only: `add_changeset_node()` in `drivers/of/overlay.c`; never cleared |
| `OF_OVERLAY_FREE_CSET` | `of_node_release()` refuses to free an `OF_OVERLAY` node without it | core only: `__of_changeset_entry_destroy()`, unless the refcount is above 1; never cleared |

- `drivers/of/fdt.c` never sets `OF_DYNAMIC`: nodes of the boot tree and of an
  overlay's own unflattened tree are never freed by `of_node_release()`.
- `OF_DYNAMIC` outside the core: `of_pci_remove_node()` and
  `of_pci_remove_host_bridge_node()` test it to recognise a node that PCI
  created with a changeset.
- `OF_OVERLAY` is set only on nodes that `add_changeset_node()` allocates,
  not on a target node that already exists; `add_changeset_property()` logs
  "memory leak will occur" for a property it adds to or updates on a node
  without the flag.
- `OF_DETACHED`, `OF_OVERLAY`, `OF_OVERLAY_FREE_CSET`: no code outside
  `drivers/of/` writes them; `lib/vsprintf.c` reads `OF_DETACHED` for
  printing.

**Changesets**

- `of_changeset_destroy()`: never reverts; an applied changeset stays in the
  tree for good, and only the entries and their node references go.
- Destroy after apply is the normal way to make a change permanent, as
  `dlpar_hp_dt_add()` does; to undo, call `of_changeset_revert()` first, as
  `of_pci_remove_node()` does.
- `of_changeset_destroy()`: calls `device_link_wait_removal()` first, which
  flushes a workqueue, so it may sleep.
- References: `of_changeset_action()` takes one `of_node_get()` on the
  entry's node; none on the parent, none on the property.
- Properties: `__of_changeset_entry_destroy()` frees no property.
- `of_changeset_add_prop_helper()`: links the new property on `deadprops`
  when it is queued, so that it is freed with the node even if never applied;
  `__of_add_property()` unlinks it from `deadprops` on apply.
- Rollback result is lost: `__of_changeset_apply()` passes a local
  `ret_revert` and discards it, and `__of_changeset_revert()` does the same
  with `ret_reply`; the caller of `of_changeset_apply()` or
  `of_changeset_revert()` gets the entry's error and cannot tell whether the
  tree was restored.
- Actions that can fail in `__of_changeset_entry_apply()`, which revert also
  uses with the inverted action: of the five `OF_RECONFIG_` actions only
  `OF_RECONFIG_ADD_PROPERTY` (`-EEXIST`, name already on the node) and
  `OF_RECONFIG_REMOVE_PROPERTY` (`-ENODEV`, property not on the node's list);
  `__of_attach_node()` and `__of_detach_node()` return void and
  `__of_update_property()` returns 0.

**Changeset notifiers**

- Timing: `__of_changeset_apply()` applies every entry first, then
  `__of_changeset_apply_notify()` sends one notification per entry in list
  order; a callback sees the whole changeset applied, not only its entry.
- `of_changeset_revert()`: same shape; `__of_changeset_revert_notify()` walks
  the entries in reverse and sends the inverted action.
- Locks: `__of_changeset_apply_notify()` unlocks `of_mutex` before the loop
  and relocks it after; callbacks run with neither `of_mutex` nor
  `devtree_lock` held.
- During an overlay apply the callbacks still run under
  `of_overlay_phandle_mutex`.
- Notifier error: logged by `__of_changeset_entry_notify()`, the remaining
  entries are still notified, and the last non-zero error becomes the return
  value of `of_changeset_apply()`.
- A non-zero return from `of_changeset_apply()` can therefore mean "every
  entry applied, a notifier failed"; nothing is rolled back in that case.
- Property entries: `of_property_notify()` sends nothing when the node is not
  in sysfs (`of_node_is_attached()` in `drivers/of/kobj.c`).

**Applying an overlay**

- `of_overlay_fdt_apply()`: has a fourth parameter, `base`, the node that a
  fragment's `target-path` is resolved against; NULL for the root.
- `*ret_ovcs_id`: 0 on entry, set to the id after every call to
  `of_overlay_apply()`, whatever it returned.
- Non-zero id after an error: says only that the overlay is still registered
  in `ovcs_idr` and holds its memory, not that the tree changed.
- Cases with a non-zero id: every error from `of_overlay_apply()`, for
  example `of_resolve_phandles()` or `init_overlay_changeset()` failed, an
  `OF_OVERLAY_PRE_APPLY` notifier refused, `build_changeset()` failed, the
  entries were applied and rolled back, or a notifier failed with the overlay
  fully applied.
- Zero id after an error: `free_overlay_changeset()` already ran, or nothing
  was allocated.
- **Unsafe usage**: returning from an `of_overlay_fdt_apply()` error without
  calling `of_overlay_remove()` on the id; the error path skips
  `free_overlay_changeset()`, so the overlay stays registered and possibly
  applied.
  - Safe: call `of_overlay_remove()` on every error, as
    `imx8mp_hdmi_tx_connector_fixup_init()` does; with an id of 0 it returns
    0 and does nothing.
- `OF_OVERLAY_PRE_APPLY` and `OF_OVERLAY_POST_APPLY` notifiers: run from
  `overlay_notify()` with `of_overlay_phandle_mutex` and `of_mutex` both
  held.
- Refusal state: `devicetree_corrupt()` tests the static
  `devicetree_state_flags` in `drivers/of/overlay.c`; there is no
  devicetree_state_flags_corrupt().
- `DTSF_APPLY_FAIL`: set in `of_overlay_apply()` when
  `__of_changeset_apply_entries()` fails and reports a rollback error in
  `ret_revert`.
- `DTSF_REVERT_FAIL`: set in `of_overlay_remove()` when
  `__of_changeset_revert_entries()` fails and reports a re-apply error.
- Plain `of_changeset_apply()` and `of_changeset_revert()` never set either
  bit.
- After `DTSF_APPLY_FAIL`: the `of_overlay_remove()` that the caller owes
  returns `-EBUSY` as well, so that overlay stays registered and its memory
  is never freed.

**Removing an overlay**

- `*ovcs_id == 0`: `of_overlay_remove()` returns 0 at once.
- Refusals that leave the overlay registered and `*ovcs_id` unchanged:
  `devicetree_corrupt()` (`-EBUSY`, tested before `of_mutex` is taken), id
  not in `ovcs_idr` (`-ENODEV`), `overlay_removal_is_ok()` fails (`-EBUSY`),
  an `OF_OVERLAY_PRE_REMOVE` notifier error, an entry revert error (the
  entries already reverted are re-applied, best effort); there is no other
  state test.
- `overlay_removal_is_ok()`: tests overlap, not order; it refuses when a
  node in this overlay's changeset is the same as, an ancestor of, or a
  descendant of a node in the changeset of a later-applied overlay (see
  `node_overlaps_later_cs()`); an older overlay with no such overlap can be
  removed.
- Once the entries are reverted nothing refuses: `*ovcs_id` is zeroed and
  `free_overlay_changeset()` runs even if a reconfig or
  `OF_OVERLAY_POST_REMOVE` notifier returns an error.
- An overlay has two kinds of memory with different lifetimes:

| Memory | Allocated by | Freed |
|---|---|---|
| overlay's own tree, `overlay_mem` and `new_fdt`; `nd.overlay` in an overlay notifier points here | `of_overlay_fdt_apply()` | `kfree()` in `free_overlay_changeset()`, right after the `OF_OVERLAY_POST_REMOVE` notifiers; no refcount is looked at |
| nodes added to the live tree, and their properties | `__of_node_dup()` and `__of_prop_dup()` | `of_node_release()`, on the last `of_node_put()` |

- `free_overlay_changeset()`: both of its callers reach it with
  `notify_state` at `OF_OVERLAY_INIT` or `OF_OVERLAY_POST_REMOVE`, so the
  "do not free" branch is not taken.
- Pointer into the overlay's own tree: must be gone when the
  `OF_OVERLAY_POST_REMOVE` notifier returns; nothing checks it.
- `np->name` of a node the overlay added: `add_changeset_node()` points it at
  the "name" property of the overlay's own tree, so it dangles after removal
  even if the node itself is still referenced.
- Properties the overlay added to a pre-existing node: moved to that node's
  `deadprops` on removal, and freed only if that node is ever released.
- Refcount check: in `__of_changeset_entry_destroy()`, only for
  `OF_RECONFIG_ATTACH_NODE` entries on `OF_OVERLAY` nodes; the expected count
  is 1, the entry's own reference.
- `of_overlay_remove()` still returns success on a mismatch, and
  `overlay_mem` and `new_fdt` are freed anyway.
- Reference on an added node: must be dropped before
  `__of_changeset_entry_destroy()` reads the count, that is by the time the
  `OF_OVERLAY_POST_REMOVE` notifiers have returned and
  `device_link_wait_removal()` has finished.

## Devices from nodes

**Creating platform devices**

- `of_platform_populate()`: makes no availability test on `root`; availability
  is tested per node, inside `of_platform_device_create_pdata()` and
  `of_amba_device_create()`.
- `of_platform_bus_create()`: every return path yields 0, so
  `of_platform_populate()` returns `-EINVAL` (no root node) or 0, and 0 says
  nothing about which devices exist; the `of_platform_populate()` stub
  without `CONFIG_OF_ADDRESS` returns `-ENODEV`.
- `OF_POPULATED_BUS` on `root`: set by `of_platform_populate()` unconditionally
  after the walk, not only on success.
- `strict`: the no-"compatible" skip applies only when it is true;
  `of_platform_populate()` always passes true, `of_platform_bus_probe()`
  passes false.
- `of_skipped_node_table`: one entry, "operating-points-v2"; nothing about
  reserved memory is skipped by table.
- `reserved_mem_matches`: the opposite of a skip list;
  `of_platform_default_populate_init()` creates a device for each matching
  child of `/reserved-memory` with `of_platform_device_create()`, except
  under `CONFIG_PPC`.
- There is no of_default_bus_match_table definition here; the default table
  is the static `match_table` inside `of_platform_default_populate()`, and its
  "arm,amba-bus" entry exists only under `CONFIG_ARM_AMBA`.
- `matches` NULL: `__of_match_node()` returns NULL, so only the direct
  children of `root` get devices; the kerneldoc "NULL to use the default" is
  not what the code does. `devm_of_platform_populate()` passes NULL.
- "arm,primecell" node without `CONFIG_ARM_AMBA`: `of_amba_device_create()` is
  a stub returning NULL and `of_platform_bus_create()` still returns before
  the platform path, so the node gets no device of either kind.
- `OF_POPULATED_BUS` test in `of_platform_bus_create()`: this is the
  `of_node_check_flag()` skip; `OF_POPULATED` is not checked there, it is
  test-and-set inside the two create helpers.
- `OF_POPULATED_BUS` is also set by `of_platform_bus_create()` on a node it
  descended into, whatever the children returned.
- Second `of_platform_populate()` on the same `root`: the flag on `root` is
  not tested, the children are walked again; per-node flags are what stop
  duplicates.
- `OF_POPULATED` set by other code: `of_irq_init()` in `drivers/of/irq.c` and
  `of_clk_init()` in `drivers/clk/clk.c` set it on nodes they initialise, so
  populate makes no platform device for them and does not descend.
  - A driver that needs both clears it by hand, for example
    `CLK_OF_DECLARE_DRIVER()` and `imx_gpcv2_irqchip_init()`.
- `of_platform_depopulate()`: the `OF_POPULATED_BUS` test is on
  `parent->of_node` only; each child platform device is then destroyed if its
  own node has `OF_POPULATED`, including one made by hand with
  `of_platform_device_create()`.
- `of_platform_depopulate()` after populating a different node:
  `of_platform_populate()` flags `root`, depopulate tests `parent->of_node`;
  if they differ and `parent->of_node` lacks the flag, depopulate does nothing.
  `devm_of_platform_populate()` passes `dev->of_node` and `dev`, so they match.
- `of_platform_device_destroy()`: clears both flags before it unregisters the
  device, not after.
- **Unsafe usage**: unregistering a device that `of_platform_device_create()`
  or `of_platform_populate()` made, with `platform_device_unregister()` or
  `of_device_unregister()`, and leaving `OF_POPULATED` set;
  `platform_device_release()` clears no flag, so
  `of_platform_device_create_pdata()` returns NULL for that node from then on.
  - Safe: remove it with `of_platform_device_destroy()`, as
    `of_platform_notify()` does.
  - Safe: clear `OF_POPULATED` on `dev->of_node` first, then unregister, as
    `ssi_remove_ports()` in `drivers/hsi/controllers/omap_ssi_core.c` does.
  - Safe: a device built with `of_device_alloc()` and `of_device_add()`, which
    never set `OF_POPULATED`, as `ibmebus_create_device()` in
    `arch/powerpc/platforms/pseries/ibmebus.c` does.
- `of_find_device_by_node()`: searches `platform_bus_type` only, so it returns
  NULL for a node whose device is on `amba_bustype`.
- Releasing the lookup result: `platform_device_put()` accepts NULL and
  `of_platform_notify()` relies on that; `put_device(&pdev->dev)` needs a
  NULL test first, because `dev` is not the first member of
  `struct platform_device`.

## Model gaps

### Other mistakes models make

- Models take `of_device_alloc()` to store the node with `of_node_get()`.
  `platform_device_set_of_node()`, which it calls, sets both `dev.fwnode` and
  `dev.of_node`.
- Models take `of_node_reused` to be a member of `struct device`. The bit is
  read with `dev_of_node_reused()`, which `__create_dev_flag_accessors()`
  generates in `include/linux/device.h`.
- Models take `RESERVEDMEM_OF_DECLARE()` to register an init function. Its
  third argument is a `struct reserved_mem_ops *`; see
  `include/linux/of_reserved_mem.h`.
- Models take `node_init` in `struct reserved_mem_ops` to be optional like the
  other callbacks. `__reserved_mem_init_node()` in
  `drivers/of/of_reserved_mem.c` calls it without a NULL test.
- Models name of_node_alloc() as a way to create a dynamic node.
  `of_changeset_create_node()` in `drivers/of/dynamic.c` creates one, through
  `__of_node_dup()`.
- Models do not know `kzalloc_obj()`, `kzalloc_objs()` and `kmalloc_obj()`,
  which `drivers/of/` uses for struct allocations. The GFP argument is
  optional and defaults to `GFP_KERNEL`; see `include/linux/slab.h`.
- Models take a missing `#address-cells` or `#size-cells` to fall back
  silently to the parent or the default. `of_bus_n_addr_cells()` and
  `of_bus_n_size_cells()` in `drivers/of/base.c` `WARN_ONCE()` for a level
  that lacks the property, except with `CONFIG_SPARC` or when the tree has a
  node compatible with "coreboot".
- Models take `of_root` to be NULL when the bootloader passed no blob.
  `of_have_populated_dt()` tells that case by testing `of_root` for a
  "compatible" property; see `include/linux/of.h`.
- Models take `early_init_dt_scan()` and `early_init_dt_verify()` to take one
  pointer. Both take `(void *dt_virt, phys_addr_t dt_phys)`; the physical
  address is kept in `initial_boot_params_pa`.
- Models do not know `of_imap_parser_init()` and `for_each_of_imap_item()` in
  `include/linux/of_irq.h`, which walk `interrupt-map`. Leaving the loop early
  owes `of_node_put()` on `item.parent_args.np`.
- Models do not know the root-node helpers `of_machine_get_match()`,
  `of_machine_get_match_data()`, `of_machine_device_match()`,
  `of_machine_read_compatible()` and `of_machine_read_model()`; see
  `include/linux/of.h`.
- Models look for `of_get_cpu_node()` and `of_cpu_device_node_get()` in
  `drivers/of/base.c` and for `of_modalias()` in `drivers/of/device.c`. They
  are in `drivers/of/cpu.c` and `drivers/of/module.c`.
- Models look for `struct of_device_id` in `include/linux/mod_devicetable.h`.
  It is defined in `include/linux/device-id/of.h`, which that header includes.
