- `ptep_modify_prot_start()` does not always clear the entry: Xen PV
  (`xen_ptep_modify_prot_start()`) returns `*ptep` and leaves it present; the
  commit preserves accessed and dirty with `MMU_PT_UPDATE_PRESERVE_AD`.
- Code between start and commit must not assume the entry is non-present.
- arm64 hardware dirty: the CPU clears `PTE_RDONLY` on an entry with
  `PTE_WRITE`; `pte_write()` does not change.
- mprotect start/commit user: `change_present_ptes()`, through
  `prot_commit_flush_ptes()`.
