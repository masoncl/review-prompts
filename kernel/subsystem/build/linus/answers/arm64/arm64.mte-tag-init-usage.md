- `copy_highpage()` on a non-hugetlb source: ignores the result of
  `try_page_mte_tagging(to)`, has no warning there, and copies the tags
  whenever `page_mte_tagged(from)`.
- `memcmp_pages()`: reads no tags; with equal data and either page
  `page_mte_tagged()` it returns `addr1 != addr2`, so zero only for the same
  page.
- `tag_clear_highpages()`: takes `(page, numpages, clear_pages)`; there is no
  singular tag_clear_highpage in this tree.
- `tag_clear_highpages()` without `system_supports_mte()`: returns
  `clear_pages` unchanged; when that is `true`, `post_alloc_hook()` then
  zeroes the data itself.
- `tag_clear_highpages()` with MTE: returns `false`; uses
  `mte_zero_clear_page_tags()` if `clear_pages`, else `mte_clear_page_tags()`,
  which leaves the data alone.
- **Unsafe usage**: returning after `try_page_mte_tagging()` gave `true`
  without calling `set_page_mte_tagged()`.
  - Unsafe: every later caller of `try_page_mte_tagging()` on that page spins
    in `smp_cond_load_acquire()` with no timeout.
  - Safe: do every test that can bail out before taking the lock, as
    `mte_restore_tags()` in `arch/arm64/mm/mteswap.c` does with `xa_load()`.
- **Potentially unsafe usage**: writing a page's tags without calling
  `try_page_mte_tagging()` first.
  - Unsafe: while `PG_mte_lock` may still be clear; a later `mte_sync_tags()`
    wins the lock and zeroes the tags just written.
  - Safe: call it and ignore the result when overwriting is intended, as
    `copy_highpage()` and `kvm_vm_ioctl_mte_copy_tags()` do; once it returns,
    no other caller can win the lock.
  - Safe: the page already has `PG_mte_tagged`; `__access_remote_tags()` in
    `arch/arm64/kernel/mte.c` expects that and has a `WARN_ON_ONCE()` for it.
  - Safe: `empty_zero_page`, which `cpu_enable_mte()` clears once with
    `mte_clear_page_tags()`; its PTEs are made with `pte_mkspecial()`, for
    example in `do_anonymous_page()`, and `__sync_cache_and_tags()` calls
    `mte_sync_tags()` only for `!pte_special(pte)`.
- **Unsafe usage**: installing a tagged PTE for a swapped-in page before
  `arch_swap_restore()`.
  - Unsafe: `mte_sync_tags()` wins the lock and zeroes the tags;
    `mte_restore_tags()` then gets `false` and skips the restore.
  - Safe: restore first, as `do_swap_page()` does before `set_ptes()` and
    `shmem_swapin_folio()` does before `shmem_add_to_page_cache()`.
