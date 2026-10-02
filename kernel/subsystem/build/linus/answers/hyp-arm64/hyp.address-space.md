- Hyp image sections (`__hyp_text_start`, `__hyp_rodata_start`,
  `__hyp_data_start`, `__hyp_bss_start`): part of the linear map, not a
  region of their own. `__hyp_pa()` and `hyp_virt_to_phys()` are valid on a
  hyp symbol; `hyp_create_idmap()` uses that on `__hyp_idmap_text_start`.
- There is no hyp_symbol_addr() and no hyp_create_pcpu_fixmap() here;
  `hyp_create_fixmap()` in `arch/arm64/kvm/hyp/nvhe/mm.c` makes the fixmap
  slots.
- vmemmap: not allocated from the private range. `hyp_create_idmap()` fixes
  `__hyp_vmemmap`, and that address is the upper limit of the private range.
- `__io_map_base`: written once, in `hyp_create_idmap()`. `__io_map_next` is
  the allocation cursor. `pkvm_check_host_ownership()` relies on
  `__io_map_base` staying at the start of the quarter.
- Private range, by who owns the hyp stage-1:

| Owner | Base | Grows | Allocator | Fails with `-ENOMEM` when |
|---|---|---|---|---|
| EL2 (pKVM) | `__io_map_base` | up | `pkvm_alloc_private_va_range()` | end passes `__hyp_vmemmap` |
| host | `io_map_base = hyp_idmap_start` in `kvm_mmu_init()` | down | `hyp_alloc_private_va_range()` in `arch/arm64/kvm/mmu.c` | `BIT(VA_BITS - 1)` flips |

- `hyp_create_idmap()`, `hyp_back_vmemmap()`, `hyp_create_fixmap()`: called
  only on the `__pkvm_init()` path in `arch/arm64/kvm/hyp/nvhe/setup.c`.
- Without pKVM: `__hyp_vmemmap` is never set, so no `struct hyp_page`
  conversion is valid; the host maps the idmap in `kvm_map_idmap_text()`.
- `__hyp_va()` and `hyp_phys_to_virt()`: return an address for any PA. The
  address can be dereferenced only if the hyp stage-1 (`pkvm_pgtable` under
  pKVM) maps that page.
- Unmapped linear VA used as a handle: `__apply_guest_page()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` gets one for a guest page and turns
  it back into a PA with `__hyp_pa()`.
