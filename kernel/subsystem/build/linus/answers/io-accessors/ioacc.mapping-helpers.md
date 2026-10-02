- There is no devm_ioremap_np() here; the offset/size siblings of
  `devm_ioremap()` are `devm_ioremap_uc()` and `devm_ioremap_wc()`.
- `DEVM_IOREMAP_NP`: chosen only inside `__devm_ioremap_resource()` in
  `lib/devres.c`, when the type passed in is `DEVM_IOREMAP` and `res->flags`
  has `IORESOURCE_MEM_NONPOSTED`.
- `devm_ioremap_resource_wc()` on a resource with `IORESOURCE_MEM_NONPOSTED`:
  ignores the flag and maps with `ioremap_wc()`.
- `IORESOURCE_MEM_NONPOSTED` set, `ioremap_np()` returns `NULL` (the generic
  stub): `devm_ioremap_resource()` releases the region and returns `-ENOMEM`;
  it does not retry with `ioremap()`.
- `pci_remap_cfgspace()` in `include/linux/io.h`: the form that does fall back,
  `ioremap_np() ?: ioremap()`.
- `of_mmio_is_nonposted()` in `drivers/of/address.c`: has no configuration
  test; true when `nonposted-mmio` is on the node or on its direct parent
  only, and `__of_address_to_resource()` then sets the flag.
- `devm_ioremap_resource()` errors: `-EINVAL` for a `NULL` or non-
  `IORESOURCE_MEM` resource, `-ENOMEM` when the region name cannot be
  allocated, `-EBUSY` when the region request fails, `-ENOMEM` when the mapping
  fails.
- `devm_ioremap_resource()` logging: goes through `dev_err_probe()`; the
  `-ENOMEM` cases print nothing, see `__dev_probe_failed()` in
  `drivers/base/core.c`.
- Without `CONFIG_HAS_IOMEM`: `devm_ioremap_resource()` is an inline stub in
  `include/linux/device/devres.h` that returns `IOMEM_ERR_PTR(-EINVAL)`.
- Without `CONFIG_HAS_IOMEM`: `devm_ioremap()` has no stub; `lib/devres.c` is
  not built, and the declaration in `include/linux/io.h` stays.
