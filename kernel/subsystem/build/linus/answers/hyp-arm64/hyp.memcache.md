- Per-vCPU memcache: `pkvm_memcache` in `struct kvm_vcpu_arch`. It exists
  twice: the host's `vcpu->arch.pkvm_memcache` and EL2's
  `hyp_vcpu->vcpu.arch.pkvm_memcache`.
- No field is named `stage2_mc`; that name is only a local variable in
  `__pkvm_finalize_teardown_vm()`.
- `get_mmu_memcache()` in `arch/arm64/kvm/mmu.c`: selects `pkvm_memcache` for
  every VM when `is_protected_kvm_enabled()`, protected or not.
- Helpers: there is no __push_hyp_memcache() or __pop_hyp_memcache(); the
  inline helpers in `arch/arm64/include/asm/kvm_host.h` are
  `push_hyp_memcache()`, `pop_hyp_memcache()`, `__topup_hyp_memcache()` and
  `__free_hyp_memcache()`.
- Per-VM memcaches: `teardown_mc` and `stage2_teardown_mc`, both in
  `struct kvm_protected_vm` (host `kvm->arch.pkvm`). There is no hyp_donations.
- `struct pkvm_hyp_vm` has no memcache member of its own, and EL2 does not use
  the `teardown_mc` and `stage2_teardown_mc` copies in
  `hyp_vm->kvm.arch.pkvm`; EL2 writes the host's headers through
  `hyp_vm->host_kvm` in `__pkvm_finalize_teardown_vm()`.
- There is no __pkvm_teardown_vm() and no reclaim_hyp_memcache(); teardown is
  `__pkvm_start_teardown_vm()` then `__pkvm_finalize_teardown_vm()`.

| Memcache | Filled by | Drained by |
|---|---|---|
| host `vcpu->arch.pkvm_memcache` | host, `topup_hyp_memcache()` | EL2, `refill_memcache()`; rest freed by host, `free_hyp_memcache()` in `kvm_arch_vcpu_destroy()` |
| hyp `hyp_vcpu->vcpu.arch.pkvm_memcache` | EL2, `refill_memcache()` | `guest_s2_zalloc_page()`; rest popped at teardown |
| `teardown_mc` | EL2, `teardown_donated_memory()`: pages of each `struct pkvm_hyp_vcpu` and of `struct pkvm_hyp_vm` | host, `free_hyp_memcache()` |
| `stage2_teardown_mc` | EL2: PGD and stage-2 table pages (`reclaim_pgtable_pages()`), unused hyp vCPU memcache pages | host, `free_hyp_memcache()` |

- `stage2_teardown_mc` and the host vCPU memcache carry
  `HYP_MEMCACHE_ACCOUNT_STAGE2`: `hyp_mc_free_fn()` then calls
  `kvm_account_pgtable_pages()` with -1 per page. A page pushed on
  `teardown_mc` is freed without that.
- Pages popped from the hyp vCPU memcache never return to a memcache while the
  VM lives: a freed table page goes to `hyp_vm->pool` through `hyp_put_page()`.
- `guest_s2_zalloc_page()`: tries `current_vm->pool` first and pops the memcache
  only when the pool is empty.
