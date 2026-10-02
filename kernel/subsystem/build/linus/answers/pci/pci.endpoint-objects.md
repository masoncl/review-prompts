- `struct pci_epf_driver` in `include/linux/pci-epf.h`: holds `probe`,
  `remove` and `ops`; `bind` and `unbind` are not its members.
- `struct pci_epf_ops`: has exactly `bind`, `unbind` and `add_cfs`.
- `pci_epf_register_driver()`: a macro over `__pci_epf_register_driver()`,
  which returns `-EINVAL` if `ops`, `ops->bind` or `ops->unbind` is NULL.
- `probe` is mandatory: `pci_epf_device_probe()` returns `-ENODEV` without it.
- Bind sequence, in each configfs function that links a function to a
  controller: `pci_epc_add_epf()`, then `pci_epf_bind()`, then
  `pci_epc_notify_pending_init()`.
- `pci_epc_add_epf()`: only links the function and picks its number; it does
  not call `pci_epf_bind()`.
- `pci_epc_notify_pending_init()`: calls `epc_init` at once if
  `epc->init_complete` is set, so a function bound after controller init still
  gets the event.
- Three link functions in `drivers/pci/endpoint/pci-ep-cfs.c` run that
  sequence: `pci_epc_epf_link()`, `pci_primary_epc_epf_link()` and
  `pci_secondary_epc_epf_link()`; the last passes `SECONDARY_INTERFACE`.
- Unlink order: `pci_epf_unbind()` first, then `pci_epc_remove_epf()`, so
  `unbind` runs with the `epf->epc` or `epf->sec_epc` that is being unlinked
  still set.
- `pci_epc_start()` and `pci_epc_stop()`: call the op under `epc->lock`, not
  `epc->list_lock`.
- `epc->lock`: taken by every wrapper in
  `drivers/pci/endpoint/pci-epc-core.c` that calls an op, including
  `pci_epc_get_features()` and `pci_epc_raise_irq()`, with one exception.
- `align_addr` op: `pci_epc_mem_map()` calls it with no lock held.
- Nesting: event callbacks called from the list walkers, such as
  `pci_epc_init_notify()` and `pci_epc_linkup()`, run under `epc->list_lock`
  then `epf->lock`; `pci_epc_notify_pending_init()` holds only `epf->lock`.
  The callbacks call wrappers that take `epc->lock`, as
  `pci_epf_test_epc_init()` does with `pci_epc_write_header()`.
