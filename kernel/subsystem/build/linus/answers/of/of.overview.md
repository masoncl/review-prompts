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
