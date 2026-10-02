- There is no KVM_PGTABLE_WALK_HANDLE_FAULT here; the flag is
  `KVM_PGTABLE_WALK_IGNORE_EAGAIN` and its sense is the opposite.

| Flag | Effect when set |
|---|---|
| `KVM_PGTABLE_WALK_SHARED` | as in "Shared walks"; also `stage2_map_walker_try_leaf()` skips its shortcut for a change of software bits only, and `kvm_pgtable_visitor_cb()` warns if the RCU read lock is not held |
| `KVM_PGTABLE_WALK_IGNORE_EAGAIN` | `-EAGAIN` from a visitor counts as success: the walk goes on and returns 0 |
| `KVM_PGTABLE_WALK_SKIP_BBM_TLBI` | `stage2_try_break_pte()` does no TLB invalidation; nothing else tests it |
| `KVM_PGTABLE_WALK_SKIP_CMO` | `stage2_map_walker_try_leaf()` does no cache maintenance for the new entry; nothing else tests it |

- Without `KVM_PGTABLE_WALK_IGNORE_EAGAIN`: the first `-EAGAIN` ends the walk
  and is returned, whether or not the walk is in a fault handler.
- `KVM_PGTABLE_WALK_IGNORE_EAGAIN` is set by `kvm_pgtable_stage2_wrprotect()`
  and by `__host_stage2_idmap()` in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `stage2_unmap_walker()` tests neither skip flag.
- `stage2_unmap_defer_tlb_flush()` reads no walk flag; it tests
  `system_supports_tlb_range()` and `ARM64_HAS_STAGE2_FWB`.
- `KVM_PGTABLE_WALK_SKIP_BBM_TLBI`: its one user,
  `kvm_pgtable_stage2_create_unlinked()`, builds a table that is not linked
  yet; `stage2_split_walker()` then does the TLBI when it breaks the block
  entry.
