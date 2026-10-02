| Pool | Backs | Pages come from |
|---|---|---|
| `hpool`, static in `arch/arm64/kvm/hyp/nvhe/setup.c` | hyp stage-1 table pages of `pkvm_pgtable`, nothing else | `hyp_pgt_base`, `hyp_s1_pgtable_pages()` pages; pages the early allocator already used are `reserved_pages` |
| `host_s2_pool`, static in `arch/arm64/kvm/hyp/nvhe/mem_protect.c` | host stage-2 table pages of `host_mmu.pgt` | `host_s2_pgt_base`, `host_s2_pgtable_pages()` pages |
| `pool` in `struct pkvm_hyp_vm` | that VM's stage-2 table pages, for protected and non-protected VMs | the PGD donated in `__pkvm_init_vm()`; later, memcache pages freed into it |

- There is no hyp_s1_pool, and `struct host_mmu` has no pool member.
- VM and vCPU structures: host-donated memory from `map_donated_memory()`
  in `arch/arm64/kvm/hyp/nvhe/pkvm.c`, not from `hpool`.
- Guest callbacks such as `guest_s2_get_page()`: find the pool through the
  per-CPU `current_vm`, which is set only between `guest_lock_component()`
  and `guest_unlock_component()`.
- Host stage-2 callers pass `&host_s2_pool` as the memcache argument of
  `kvm_pgtable_stage2_map()`; `host_s2_zalloc_page()` allocates from that
  argument.
- With `CONFIG_NVHE_EL2_DEBUG`: `selftest_vm` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` has a fourth pool, seeded from
  `selftest_base` by `init_selftest_vm()`.
- With `CONFIG_NVHE_EL2_DEBUG`: `pkvm_ownership_selftest()` takes one page
  from `host_s2_pool` that is not a table page.
