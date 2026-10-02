- `gic_v5_its_msi_parent_ops`: has no prepare member; its only callback is
  `.init_dev_msi_info`. `gicv5_its_msi_prepare()` is `.msi_prepare` of
  `gicv5_its_msi_domain_ops` in `drivers/irqchip/irq-gic-v5-its.c`; both
  child prepares reach it through
  `msi_get_domain_info(domain->parent)->ops->msi_prepare`.
- PCI device ID and controller node: `pci_msi_map_rid_ctlr_node()` in
  `drivers/pci/msi/irqdomain.c`. It calls `of_msi_xlate()` when the ITS
  domain has an OF node and `iort_msi_xlate()` otherwise.
- `pci_msi_domain_get_msi_rid()` and `iort_msi_map_id()`: used by the GICv3
  `its_pci_msi_prepare()`; the v5 path does not call them.
- Platform lookup: `of_pmsi_get_msi_info()` when `dev->of_node` is set,
  else `iort_pmsi_get_msi_info()` in `drivers/acpi/arm64/iort.c`. Both are
  shared with GICv3; a non-NULL `pa` argument selects the v5 behaviour.
- There is no iort_pmsi_get_dev_id() and no of_v5_pmsi_get_msi_info() in
  this tree.
- `of_pmsi_get_msi_info()` with `pa` set: the `msi-parent` phandle must
  target a child of the ITS domain's node (the translate frame
  `msi-controller` node). The match compares `of_get_parent()` of the target
  with the domain node, and the address is read from the target.
- DT PCI: the node `of_msi_xlate()` returns must also be the frame node,
  because `its_translate_frame_address()` looks for `"ns-translate"` in that
  node's `reg-names`; the ITS node's own entry is `"ns-config"`.
- ACPI frame address: `iort_its_translate_pa()` searches
  `iort_msi_chip_list` for the fwnode. `gic_acpi_parse_madt_its_translate()`
  fills that list from each MADT translate frame (`base_address`, keyed by
  `translate_frame_id`).
- `iort_msi_xlate()`: takes the fwnode from `its->identifiers[0]`, the first
  identifier of the IORT ITS group only.
- Prepare runs once per per-device domain: `msi_create_device_irq_domain()`
  passes `hwsize` as `nvec` and keeps the result in `info->alloc_data`.
  `populate_alloc_info()` copies it into every later allocation, so
  `num_events` is `roundup_pow_of_two()` of `hwsize`.
- **Unsafe usage**: using the `pa` output of `of_pmsi_get_msi_info()` when
  the `msi-parent` walk did not match.
  - Unsafe: when the device node has `msi-map`, the `of_map_msi_id()`
    fallback can return 0 with `*dev_id` set and `*pa` never written.
  - Safe: when the `msi-parent` walk matched; that branch calls
    `its_translate_frame_address()` before it returns 0.
