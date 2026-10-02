- `hyp_fixmap_map()`: returns the slot address plus `offset_in_page(phys)`.
  The PA need not be page-aligned; `__tracing_enable_event()` in
  `arch/arm64/kvm/hyp/nvhe/events.c` passes the PA of a field.
- `fixmap_map_slot()`: makes no test of the old PTE. A map over a live mapping
  retargets the slot with no invalidation and no error.
- `fixmap_map_slot()`: writes the PTE, then `dsb(ishst)`. No TLBI, no `isb()`.
- `fixmap_clear_slot()`: clears `KVM_PTE_VALID`, then `dsb(ishst)`,
  `__tlbi_level(vale2is, addr, level)`, `__tlbi_sync_s1ish_hyp()`, `isb()`.
- `__tlbi_sync_s1ish_hyp()` in `arch/arm64/include/asm/tlbflush.h`: `dsb(ish)`
  plus a repeated TLBI under `ARM64_WORKAROUND_REPEAT_TLBI_SYNC`. A bare
  `dsb(ish)` in its place loses the workaround.
- Attributes: `fixmap_map_slot()` changes only the address bits and
  `KVM_PTE_VALID`. Every mapping has the `PAGE_HYP` attributes that
  `hyp_create_fixmap()` gave the slot, whatever the page is elsewhere.
- Writing a read-only page: `__tracing_enable_event()` uses the fixmap to
  write to hyp rodata, which the linear map has as `PAGE_HYP_RO`.
