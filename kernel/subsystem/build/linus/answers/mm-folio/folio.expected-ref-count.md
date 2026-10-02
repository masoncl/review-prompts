- Swap cache term: added for any folio with `folio_test_swapcache()` true,
  anon or not; it sits outside the `!folio_test_anon()` block.
- shmem folio in the swap cache: counted by the swap cache term;
  `shmem_delete_from_page_cache()` in `mm/shmem.c` has set `folio->mapping`
  to NULL, so the page cache term is 0.
- `PG_private_2`: no term for it, although `folio_start_private_2()` in
  `include/linux/netfs.h` takes a reference; such a folio compares as having
  one extra reference until `folio_end_private_2()`.
- Typed pages: `WARN_ON_ONCE()` and return 0 when `page_has_type()` is true,
  except for hugetlb folios.
- GUP pins held by others: not a precondition; they are what a mismatch
  detects.
- Caller's own pin: added by the caller; `collect_longterm_unpinnable_folios()`
  in `mm/gup.c` passes 1 when `folio_has_pincount()` is true, otherwise
  `GUP_PIN_COUNTING_BIAS`.
- `folio_migrate_mapping()`: the addend is `extra_count + 1`; `extra_count`
  is for extra references the caller knows of, for example 1 in `fs/aio.c`.
- **Potentially unsafe usage**: comparing `folio_ref_count()` with
  `folio_expected_ref_count()` and no addend.
  - Unsafe: when the caller holds its own reference (from `folio_try_get()`,
    `folio_get()`, GUP or LRU isolation); the function has no term for it, so
    the comparison always reports an extra reference.
  - Safe: when the caller holds no reference and found the folio through a
    present PTE under the page table lock, as `collapse_scan_pmd()` in
    `mm/khugepaged.c` does.
  - Safe: when the caller holds no reference and walks the page cache under
    the xarray lock, as `memfd_tag_pins()` in `mm/memfd.c` does.
- Per-CPU LRU batch reference: no term for it;
  `__folio_batch_add_and_move()` in `mm/folio.c` takes it with `folio_get()`.
- `lru_add_drain()`: drains the calling CPU only; a batch on another CPU
  keeps its reference until that CPU drains, which `lru_add_drain_all()` or
  `lru_cache_disable()` forces.
- `folio_isolate_lru()`: does not drain; a batch that took its reference
  while `PG_lru` was set, for example through `folio_activate()` (with
  `CONFIG_SMP`), keeps it after isolation.
- Freeze value in migration: `__folio_migrate_mapping()` in `mm/migrate.c`
  freezes on the same `expected_count` that was compared.
- Freeze value in split: `__folio_freeze_and_split_unmapped()` in
  `mm/huge_memory.c` freezes on `folio_cache_ref_count(folio) + 1`, which has
  no mapcount or `PG_private` term; in `__folio_split()`
  `folio_expected_ref_count()` is only the racy check before
  `unmap_folio()`.
