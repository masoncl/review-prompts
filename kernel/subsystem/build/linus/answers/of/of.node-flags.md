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
