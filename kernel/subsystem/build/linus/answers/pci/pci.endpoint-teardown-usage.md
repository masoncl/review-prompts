| Function | Returns early for | Not checked |
|---|---|---|
| `pci_epf_destroy()` | nothing | `epf`; it calls `device_unregister()` |
| `pci_ep_cfs_remove_epc_group()` | NULL `group` | an error pointer is dereferenced |
| `pci_epf_remove_vepf()` | `IS_ERR_OR_NULL()` of either argument | whether `epf_vf` was added |
| `pci_epc_remove_epf()` | `IS_ERR_OR_NULL(epc)`, NULL `epf` | whether `epf` was added; `list_del()` is unconditional |
| `pci_epc_mem_free_addr()` | `phys_addr` in no window, after `pr_err()` | `epc`, `virt_addr` |
| `pci_epc_mem_exit()` | `epc->num_windows` of 0 | `epc` |
| `pci_epc_mem_unmap()` | invalid `epc` or function number, NULL `map`, NULL `map->virt_base` | whether the map succeeded |
| `pci_epf_free_doorbell()` | NULL `epf->db_msg` | `epf->epc`, dereferenced on the MSI path and, when `iova_size` is set, on the `PCI_EPF_DOORBELL_EMBEDDED` path |
| `pci_epf_unregister_driver()` | nothing | `driver` |

- `pci_epf_destroy()`: its only caller is `pci_epf_release()` in
  `drivers/pci/endpoint/pci-ep-cfs.c`; `pci_epf_drop()` only calls
  `config_item_put()`.
- There is no devm_pci_epc_destroy in this tree; `devm_pci_epc_release()`
  calls `pci_epc_destroy()` and is its only caller.
- `pci_epc_mem_exit()`: safe after a failed `pci_epc_multi_mem_init()` and
  when repeated, because both leave `epc->num_windows` at 0.
- `pci_epf_unregister_driver()` with `CONFIG_PCI_ENDPOINT_CONFIGFS`: walks
  `driver->epf_group`, which only `pci_epf_add_cfs()` initialises, so it needs
  a successful `__pci_epf_register_driver()` first.
- **Unsafe usage**: calling `pci_epc_destroy()` on an epc from
  `devm_pci_epc_create()`.
  - Unsafe: devres runs `devm_pci_epc_release()` later and unregisters the
    device a second time.
  - Safe: leave the epc to devres, as `dw_pcie_ep_init()` does.
- **Unsafe usage**: calling `pci_epc_mem_unmap()` on a map whose
  `pci_epc_mem_map()` failed.
  - Unsafe: after a failed `pci_epc_map_addr()` the memory is already freed
    and `map->virt_base` is still set, so it is freed twice.
  - Unsafe: on the `-EINVAL` return for a zero `pci_size`, `map` is not
    written, so an uninitialised `map` is used.
  - Safe: skip the unmap when the map call failed, as `pci_epf_test_read()`
    does.
- **Unsafe usage**: calling `pci_epf_free_space()` with a non-NULL `addr` once
  `pci_epc_remove_epf()` has cleared `epf->epc` or `epf->sec_epc`.
  - Unsafe: `pci_epf_free_space()` reads `epc->dev.parent` through the NULL
    pointer.
  - Safe: free in `unbind` the space of the interface whose epc pointer is
    still set; the configfs unlink functions call `pci_epf_unbind()` before
    `pci_epc_remove_epf()`, as `pci_epf_test_unbind()` relies on for
    `PRIMARY_INTERFACE`.
- **Unsafe usage**: calling `pci_epc_remove_epf()` for an epf that
  `pci_epc_add_epf()` did not add with the same `type`.
  - Unsafe: `list_del()` runs on a list entry that was never linked.
  - Safe: after `pci_epc_add_epf()` returned 0, as `pci_epc_epf_link()` does
    when `pci_epf_bind()` fails.
