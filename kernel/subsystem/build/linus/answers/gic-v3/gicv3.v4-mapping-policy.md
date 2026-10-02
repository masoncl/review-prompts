- Eager: when `its_list_map` is zero or `has_rvpeid` is set. Lazy: only when
  `its_list_map` is non-zero and `has_rvpeid` is clear.
- Eager mapping is done by `its_vpe_irq_domain_activate()`, on every
  `is_v4()` ITS; `its_map_vm()` returns at once when mapping is eager.
- Lazy mapping is done by `its_map_vm()`; `its_vpe_irq_domain_activate()`
  then only sets `col_idx` and the effective affinity.
- `its_vlpi_map()` on an irq that is already forwarded: sends VMOVI and does
  not call `its_map_vm()`, so under lazy mapping `vlpi_count[]` counts
  forwarded irqs, not `MAP_VLPI` requests; under eager mapping it stays 0.
- Two fields are named `vlpi_count`:
  - `vlpi_count[]` in `struct its_vm`, indexed by `list_nr`: drives the lazy
    case.
  - `vlpi_count` in `struct its_vpe`, an `atomic_t`: written and read only
    under `arch/arm64/kvm/`; the ITS driver does not use it.
- `vmapp_count`: every unmap sends VMAPP with V=0; reaching zero only sets
  ALLOC in that command, on a GICv4.1 ITS.
- PTZ: `its_build_vmapp_cmd()` always encodes it as false.
