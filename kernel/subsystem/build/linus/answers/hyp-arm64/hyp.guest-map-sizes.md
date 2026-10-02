- Donation to a protected guest: one page only.
  `__pkvm_host_donate_guest()` takes no page count and uses `PAGE_SIZE`.
- `pkvm_pgtable_stage2_map()` in `arch/arm64/kvm/pkvm.c`, protected VM:
  rejects any size but `PAGE_SIZE` and any prot but
  `KVM_PGTABLE_PROT_RWX`, with `WARN_ON_ONCE()` and `-EINVAL`.
- `pkvm_pgtable_stage2_map()`, non-protected VM: accepts `PAGE_SIZE` or
  `PMD_SIZE`.
- `pkvm_mem_abort()` in `arch/arm64/kvm/mmu.c`: always asks for
  `PAGE_SIZE`.
- EL2 size check: `__guest_check_transition_size()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `__guest_check_transition_size()` gets the real `phys` only from
  `__pkvm_host_share_guest()`. `__pkvm_host_unshare_guest()`,
  `__pkvm_host_wrprotect_guest()` and
  `__pkvm_host_test_clear_young_guest()` pass 0, so only the IPA alignment
  is tested there.
- `__pkvm_host_relax_perms_guest()` and `__pkvm_host_mkyoung_guest()`:
  take no size; they pass 0 to `assert_host_shared_guest()`, which accepts
  a leaf of any level.
- Host cap at PMD level: `fault_supports_stage2_huge_mapping()` in
  `arch/arm64/kvm/mmu.c` returns false under `is_protected_kvm_enabled()`
  for any size but `PAGE_SIZE` and `PMD_SIZE`.
- EL2 computes the block as `kvm_granule_size(KVM_PGTABLE_LAST_LEVEL - 1)`;
  the host tests `PMD_SIZE`.
