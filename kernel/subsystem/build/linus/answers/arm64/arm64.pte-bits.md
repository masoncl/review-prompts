- `PTE_PRESENT_INVALID`: is `PTE_NG`, bit 11, and has that meaning only while
  `PTE_VALID` is clear; see `arch/arm64/include/asm/pgtable-prot.h`.
- `pte_write()`: tests `PTE_WRITE` alone; hardware dirty is
  `pte_write() && !pte_rdonly()`.
- Userfaultfd bits: `PTE_UFFD` (bit 58, present entries) and `PTE_SWP_UFFD`
  (bit 3, swap entries); there is no PTE_UFFD_WP or PTE_SWP_UFFD_WP here.
- Userfaultfd accessors: for example `pte_uffd()`, `pte_mkuffd()`,
  `pte_clear_uffd()`, `pte_swp_uffd()`; there is no pte_uffd_wp() in this
  tree.
- Without `CONFIG_HAVE_ARCH_USERFAULTFD_WP`: `PTE_UFFD` and `PTE_SWP_UFFD` are
  both 0 and arm64 defines no accessors; the stubs in
  `include/asm-generic/pgtable_uffd.h` are used.
- Table above `__check_safe_pte_update()`: gives the dirty/writable encoding,
  not a list of safe transitions.
- Present-invalid is not the same as PROT_NONE: `pte_protnone()` also requires
  `!pte_user()` and `!pte_user_exec()`.
- Present-invalid kernel entries exist: `set_memory_valid()` and
  `set_direct_map_invalid_noflush()` in `arch/arm64/mm/pageattr.c` set
  `PTE_PRESENT_INVALID` on linear-map entries, so `pte_present()` stays true
  for them.
- Making a kernel entry valid again: clear `PTE_PRESENT_INVALID`, then set
  `PTE_PRESENT_VALID_KERNEL`, which re-adds nG only through `PTE_MAYBE_NG`;
  see `pte_mkvalid_k()`.
- `set_pageattr_masks()` in `arch/arm64/mm/pageattr.c`: clears before it sets,
  because some callers pass the aliasing bits in both masks.
