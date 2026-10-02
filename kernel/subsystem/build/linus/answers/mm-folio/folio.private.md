- Owner by folio kind:

| Folio | What the word holds | Where |
|---|---|---|
| page cache | filesystem data; not always a pointer | for example `(void *)EXTENT_FOLIO_PRIVATE` in btrfs, `NETFS_FOLIO_COPY_TO_CACHE` |
| swap cache | `folio->swap` | `__folio_migrate_mapping()` copies it |
| hugetlb | bitmap of `enum hugetlb_page_flags` | `include/linux/hugetlb.h` |
| migration destination | `folio->migrate_info` | `__migrate_folio_record()` in `mm/migrate.c` |

- hugetlb folios from a hugetlbfs lookup: the field holds flag bits, not a
  pointer, with `PG_private` clear; `folio_migrate_flags()` leaves it alone
  on hugetlb and sets it to NULL on every other source folio.
- Release is keyed on flags, not on the field: `folio_needs_release()` in
  `mm/internal.h` is true for `PG_private`, `PG_private_2` or a mapping with
  `AS_RELEASE_ALWAYS`.
- A value stored without `PG_private` is invisible to `folio_needs_release()`,
  `folio_expected_ref_count()` and `folio_detach_private()`; in-tree code
  does this for values that need no release, for example
  `erofs_onlinefolio_init()` (a counter, valid only while the folio is
  locked).
- `PG_private` without `folio_attach_private()`: `nfs_inode_add_request()`
  sets the flag and the field by hand under `mapping->i_private_lock`.
- Attach reference accounting: `folio_expected_ref_count()` adds one for
  `PG_private` only, and only for non-anon folios; `mapping_evict_folio()`
  adds one for `folio_has_private()`, which also covers `PG_private_2`.
- `PG_private` can remain set on a folio whose `mapping` is NULL;
  `migrate_folio_unmap()` and `try_to_free_buffers()` handle that case.
- Migration moves the data rather than freeing it: `filemap_migrate_folio()`
  detaches from the source and attaches to the destination with both folios
  locked; in `mm/migrate.c` only `fallback_migrate_folio()` calls
  `filemap_release_folio()`.
- Large-folio split of a non-anon folio: calls `filemap_release_folio()` on
  the locked folio first and fails with `-EBUSY` if that fails; see
  `mm/huge_memory.c`.
- `mapping->i_private_lock` excludes `try_to_free_buffers()` and the attach
  in `create_empty_buffers()` and `grow_dev_folio()`; it does not exclude
  migration, which detaches without it.
- **Potentially unsafe usage**: reading `folio->private` of a folio returned
  by a page-cache lookup and dereferencing it.
  - Unsafe: with only a reference; `filemap_release_folio()` or truncation
    can detach or free the data.
  - Safe: folio locked and `folio->mapping` equal to the mapping searched, in
    a filesystem that detaches only under the folio lock; a lookup with
    `FGP_LOCK` gives both, as `iomap_get_folio()` does.
    `filemap_release_folio()` and `try_to_free_buffers()` assert the folio
    lock; `nfs_inode_remove_request()` clears the field under
    `mapping->i_private_lock` alone.
  - Safe: `PG_writeback` set, in a filesystem that keeps the data attached
    until it ends writeback, as `iomap_finish_folio_write()`;
    `filemap_release_folio()` and `try_to_free_buffers()` return false under
    writeback, and truncation waits for it.
  - Safe: buffer heads under `mapping->i_private_lock` when the caller also
    excludes truncation and migration, as `block_dirty_folio()` requires of
    its callers (folio lock, or a mapped page with the page table lock).
  - Safe: buffer heads under `mapping->i_private_lock` with a test of
    `BH_Migrate` on the head, as the atomic path of
    `__find_get_block_slow()` in `fs/buffer.c` does; this pairs with
    `buffer_migrate_folio_norefs()`.
