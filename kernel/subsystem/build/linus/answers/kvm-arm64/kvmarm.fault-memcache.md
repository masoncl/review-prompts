- `get_mmu_memcache()` and `topup_mmu_memcache()` are in
  `arch/arm64/kvm/mmu.c`; there is no prepare_mmu_memcache().
- `get_mmu_memcache()`: tests `is_protected_kvm_enabled()` only, so a
  non-protected VM on a pKVM host also gets `vcpu->arch.pkvm_memcache`.
- Top-up conditions differ per handler:

| Handler | Tops up when |
|---|---|
| `user_mem_abort()` | `!perm_fault`, or `memslot_is_logging()`, or `is_protected_kvm_enabled()` |
| `gmem_abort()` | `!perm_fault` only; otherwise `memcache` stays NULL |
| `pkvm_mem_abort()` | always; any failure is returned as `-ENOMEM` |

- `user_mem_abort()`: the dirty-logging term has no write-fault test.
- `topup_hyp_memcache()`: also allocates `mc->mapping`, a
  `struct pkvm_mapping`, if it is NULL.
- `pkvm_pgtable_stage2_map()` in `arch/arm64/kvm/pkvm.c`: takes
  `cache->mapping` with `swap()` and writes through it, so a map call under
  pKVM needs a top-up since the previous successful map.
- EL2 minimum: `__guest_check_pgtable_memcache()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` returns `-ENOMEM` when the vCPU's
  cache holds fewer than `kvm_mmu_cache_min_pages()` pages, even if the map
  would allocate nothing.
- `topup_hyp_memcache()` and `free_hyp_memcache()`: return at once when
  `!is_protected_kvm_enabled()`.
- Host-side `vcpu->arch.pkvm_memcache`: freed only in
  `kvm_arch_vcpu_destroy()`; `free_hyp_memcache()` also frees `mc->mapping`.
- Pages already moved to EL2: `__pkvm_finalize_teardown_vm()` pushes them to
  `kvm->arch.pkvm.stage2_teardown_mc`, which `__pkvm_destroy_hyp_vm()` frees
  with `free_hyp_memcache()`.
