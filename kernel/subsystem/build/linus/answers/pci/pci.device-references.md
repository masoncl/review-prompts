- `DEFINE_FREE(pci_dev_put, ...)` in `include/linux/pci.h`: sits inside
  `#ifdef CONFIG_PCI`. The other branch defines `pci_dev_put()` as an empty
  macro and has no `DEFINE_FREE()`, so `__free(pci_dev_put)` is usable only in
  code that is built with `CONFIG_PCI`.
- `pci_get_dev_by_id()` in `drivers/pci/search.c`: drops the reference on
  `from` after `bus_find_device()` has returned, so `from` is valid during the
  search and must not be used once the lookup returns, unless the caller
  holds another reference.
- `pci_get_slot()`: takes no starting device and drops no reference.
- Reverse forms: `pci_get_device_reverse()` and `for_each_pci_dev_reverse`
  follow the same reference rules as `pci_get_device()` and
  `for_each_pci_dev`.
