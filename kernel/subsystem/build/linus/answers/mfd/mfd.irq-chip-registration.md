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
