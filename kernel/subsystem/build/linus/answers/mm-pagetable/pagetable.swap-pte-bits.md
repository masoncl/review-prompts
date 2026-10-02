- Without `CONFIG_HAVE_ARCH_USERFAULTFD_WP`: the `pte_` and `pmd_` uffd
  accessors are stubs in `include/asm-generic/pgtable_uffd.h`; tests return
  0, setters return the entry unchanged.
- PMD exclusive bit: none; PMDs have only soft-dirty and uffd.
- **Potentially unsafe usage**: a swap-bit accessor on a present entry, or a
  present-entry accessor on a swap-format entry.
  - Unsafe: when the bit read is acted on or copied into a new entry; on
    x86-64 the swap bits alias present-entry bits (`_PAGE_SWP_SOFT_DIRTY` is
    `_PAGE_RW`, `_PAGE_SWP_UFFD` is `_PAGE_USER`, `_PAGE_SWP_EXCLUSIVE` is
    `_PAGE_PWT`).
  - Safe: branch on `pte_present()` first, as `swp_pte_prepare()` in
    `mm/rmap.c` does.
  - Safe: `pte_swp_uffd_any()` in `include/linux/userfaultfd_k.h`, which
    returns false for a present PTE before it looks at the bit.
  - Safe: clearing the swap bits of a possibly-present PTE only to compare
    it with a swap-format value, as `pte_same_as_swp()` does for
    `unuse_pte()` in `mm/swapfile.c`; the other side is
    `swp_entry_to_pte(entry)`, which a present PTE never equals.

| Helper | Ignores the soft-dirty, uffd and exclusive bits |
|---|---|
| `softleaf_from_pte()`, then compare `.val` | yes |
| `pte_same_as_swp()` (static in `mm/swapfile.c`) | yes, on its first argument |
| `pte_same()` | no |
| `swap_pte_batch()` in `mm/internal.h` | no; batch ends where a bit differs |

- `pte_move_swp_offset()` in `mm/internal.h`: re-applies all three bits to
  the entry it builds.
