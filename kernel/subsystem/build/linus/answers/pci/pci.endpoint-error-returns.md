| Function | On failure | Caller's test |
|---|---|---|
| `pci_epc_get()` | `ERR_PTR(-EINVAL)` only, for no such device and for a failed `try_module_get()` | `IS_ERR()` |
| `pci_epf_alloc_space()` | NULL on both failure paths, never an error pointer | `!ptr` |
| `pci_ep_cfs_add_epc_group()` | error pointer | `IS_ERR()` |
| `pci_ep_cfs_add_epf_group()` | error pointer | `IS_ERR()`, as `pci_epf_add_cfs()` does |
| `add_cfs` op of `struct pci_epf_ops` | error pointer; NULL means nothing to expose | both, as `pci_ep_cfs_add_type_group()` does |

- Without `CONFIG_PCI_ENDPOINT_CONFIGFS`: the two group functions are inline
  stubs in `include/linux/pci-ep-cfs.h` that return NULL.
- `__pci_epc_create()`: stores the result of `pci_ep_cfs_add_epc_group()` in
  `epc->group` untested and still returns the epc.
- `epc->group`: may therefore hold a group, NULL or an error pointer.
- `pci_epc_get_features()`: also returns NULL when the controller op itself
  returns NULL, as `dw_pcie_ep_get_features()` does when the glue driver has no
  `get_features`.
