- Before the first fault the table also holds valid mappings: for each hyp
  text page `fix_host_ownership_walker()` in
  `arch/arm64/kvm/hyp/nvhe/setup.c` installs a page-level
  `KVM_PGTABLE_PROT_R` idmap and sets the host state to `PKVM_NOPAGE`.
- Hyp text is therefore the one case of host state `PKVM_NOPAGE` with a valid
  host PTE instead of an annotation; `check_page_ownership()` in
  `arch/arm64/kvm/hyp/nvhe/mm.c` accepts it when the PTE is not writable.
- `fix_host_ownership()`: walks the hyp linear map of every `hyp_memory`
  region and the per-CPU stacks in the private VA range.
- `KVM_HOST_S2_FLAGS`: `KVM_PGTABLE_S2_AS_S1 | KVM_PGTABLE_S2_IDMAP`; there is
  no KVM_PGTABLE_S2_NOFWB in this tree.
- MMIO is not mapped as device memory at stage-2: `PKVM_HOST_MMIO_PROT` lacks
  `KVM_PGTABLE_PROT_DEVICE`, and with `KVM_PGTABLE_S2_AS_S1`
  `KVM_S2_MEMATTR()` gives `PAGE_S2_MEMATTR(AS_S1)` for every host leaf; MMIO
  differs from memory only in having no execute permission.
- `host_stage2_force_pte_cb()`: MMIO mapped with `PKVM_HOST_MMIO_PROT` is not
  forced to pages and may be a block.
- `host_stage2_force_pte_cb()` on a range that is not wholly inside one
  `hyp_memory` region: compares against `PKVM_HOST_MMIO_PROT`, so
  `PKVM_HOST_MEM_PROT` is forced to pages there.
- Shared and borrowed host pages: mapped with plain `PKVM_HOST_MEM_PROT`, no
  SW bits, state only in `struct hyp_page`; the callback does not force them
  and a `PKVM_PAGE_SHARED_OWNED` page may sit inside a block.
- Annotations: do not consult the callback; `kvm_pgtable_stage2_annotate()`
  sets `force_pte` itself.
- The only prot other than `PKVM_HOST_MEM_PROT` and `PKVM_HOST_MMIO_PROT`
  passed to `host_stage2_idmap_locked()` in this tree is
  `KVM_PGTABLE_PROT_R` for hyp text.
