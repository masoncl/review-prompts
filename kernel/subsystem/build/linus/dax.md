# DAX Subsystem Details

## Main structures

### Objects and how they relate

- `struct dax_device` of a `struct dev_dax`: created with NULL ops and killed at
  once by `__devm_create_dev_dax()`. It is alive only while device_dax or fsdev
  is bound (`run_dax()`), never under kmem.
- `struct dax_device` lifetime: the refcount of its embedded inode (`igrab()`,
  `put_dax()`). `dax_read_lock()` and `DAXDEV_ALIVE` only fence operations
  against `kill_dax()`; they do not keep the object.
- `struct dev_dax` ranges: a seed device has `nr_range` 0 and `ranges` NULL;
  `dax_bus_probe()` refuses to bind it, so no driver's probe sees that state.
- `struct dax_region`: has no lock of its own. The global `dax_region_rwsem`
  and `dax_dev_rwsem` in `drivers/dax/bus.c` cover every region and device.
- Memory failure with no holder ops: `memory_failure_dev_pagemap()` falls back
  to `mf_generic_kill_procs()`, which finds the file through `folio->mapping`
  and `folio->index`.
- `iomap->addr` under `IOMAP_DAX`: a byte offset into `iomap->dax_dev`, not a
  sector. `dax_iomap_pgoff()` adds no partition offset; the filesystem adds
  the `start_off` that `fs_dax_get_by_bdev()` returned.
- `dax_layout_busy_page()`: finds a busy page, does not wait for it.
  `dax_break_layout()` waits, when given a callback.
- `DAX_PMD` entry and its folio: `fs/dax.c` builds the PMD-order folio from
  order-0 pages when the entry is associated (`dax_folio_init()`) and splits it
  when the last association goes (`dax_folio_reset_order()`).
- device_dax folios: sized once at probe from `pgmap->vmemmap_shift`.
- device_dax folios and `folio->mapping`: `dax_set_mapping()` in
  `drivers/dax/device.c` points them at the mapping of the `struct dax_device`
  inode, with no `i_pages` entry. `dax_lock_folio()` tells them from
  filesystem folios by `S_ISCHR()` on the host inode and takes no entry lock.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| Third driver on the DAX bus | `drivers/dax/fsdev.c` (`fsdev_dax.o`, `CONFIG_DEV_DAX_FSDEV`) | type `DAXDRV_FSDEV_TYPE` |
| Region glue, persistent memory | `drivers/dax/pmem.c` | a `struct nd_device_driver` on the nvdimm bus, not a DAX-bus driver; its device comes from `drivers/nvdimm/dax_devs.c` |
| Region glue, CXL | `drivers/dax/cxl.c` | a `struct cxl_driver`; its device comes from `drivers/cxl/core/region_dax.c` |
| Region glue, firmware-reserved: driver | `drivers/dax/hmem/hmem.c` (`CONFIG_DEV_DAX_HMEM`) | two `struct platform_driver`, `dax_hmem_platform_driver` and `dax_hmem_driver`; neither calls `dax_driver_register()` |
| Region glue, firmware-reserved: resource list | `drivers/dax/hmem/device.c` (`CONFIG_DEV_DAX_HMEM_DEVICES`) | registers the `hmem_platform` device; `drivers/acpi/numa/hmat.c` feeds it through `hmem_register_resource()` |
| Private header for glue and drivers | `drivers/dax/bus.h` | the only private DAX header the glue files include; none includes `drivers/dax/dax-private.h` |
| Private header for core and bus drivers | `drivers/dax/dax-private.h` | also included by `tools/testing/nvdimm/dax-dev.c` |
| sysfs attribute outside `drivers/dax/bus.c` | `drivers/dax/kmem.c` | `state`, on devices bound to kmem |
| Tracepoints | `include/trace/events/fs_dax.h` | instantiated by `fs/dax.c` only; `drivers/dax/` has no trace events |
| Documentation, sysfs ABI | `Documentation/ABI/testing/sysfs-bus-dax` | |
| Documentation, CXL use of DAX | `Documentation/driver-api/cxl/linux/dax-driver.rst`, `Documentation/driver-api/cxl/allocation/dax.rst` | |
| Test build, nvdimm | `tools/testing/nvdimm/Kbuild` | rebuilds `super.c`, `bus.c`, `device.c` and `pmem.c` from `drivers/dax/`; does not rebuild `kmem.c`, `cxl.c` or `fsdev.c` |
| Test override of a DAX function | `tools/testing/nvdimm/dax-dev.c` | strong `dax_pgoff_to_phys()`; the one in `drivers/dax/bus.c` is `__weak` |
| Test resource and remap wrappers | `tools/testing/nvdimm/test/iomap.c` | targets of the `--wrap=` lines in the `Kbuild`, `devm_memremap_pages()` among them |
| Test build, CXL | `tools/testing/cxl/Kbuild` | rebuilds `drivers/dax/hmem/hmem.c` with `--wrap=walk_hmem_resources` |

**Kinds of DAX**

| Kind | `pgmap->type`, set in | VMA | Inode | Folio |
|---|---|---|---|---|
| fsdax | `MEMORY_DEVICE_FS_DAX`; `pmem_attach_disk()`, `fs/fuse/virtio_fs.c`, `drivers/s390/block/dcssblk.c` | `vma_is_fsdax()` | `IS_DAX()`, not `S_ISCHR()` | `folio_is_fsdax()` |
| device DAX, `DAXDRV_DEVICE_TYPE` | `MEMORY_DEVICE_GENERIC`; `dev_dax_probe()` | `vma_is_dax()` and not `vma_is_fsdax()` | `IS_DAX()` and `S_ISCHR()` | no helper; `folio_is_fsdax()` false |
| fsdev, `DAXDRV_FSDEV_TYPE` | `MEMORY_DEVICE_FS_DAX`; `fsdev_dax_probe()` in `drivers/dax/fsdev.c` | none on the char device: `fsdev_fops` has no mmap handler | char device; `fsdev_open()` does not set `S_DAX` | `folio_is_fsdax()` true |
| kmem, `DAXDRV_KMEM_TYPE` | no pgmap used; `__add_memory_driver_managed()` in `dax_kmem_do_hotplug()` | ordinary | none | ordinary |

- `enum dax_driver_type` in `drivers/dax/bus.h`: three values, not two.
- `pgmap->type` follows the bound driver, not the device: on a static region
  `dev_dax_probe()` and `fsdev_dax_probe()` write the type into the same
  bus-owned `dev_dax->pgmap`.
- `folio_is_fsdax()` true: does not prove a block-device filesystem owns the
  folio; an fsdev-bound DAX-bus device gives the same answer.
- `folio_is_fsdax()` and `is_fsdax_page()`: defined in
  `include/linux/memremap.h`, not gated on `CONFIG_FS_DAX`.
- Device-DAX folio: no helper exists, and `MEMORY_DEVICE_GENERIC` alone does
  not identify one; `drivers/xen/unpopulated-alloc.c` and
  `drivers/hv/mshv_vtl_main.c` use that type with no `struct dax_device`.
- Device-DAX inode: `dax_dev_get()` sets `S_IFCHR` and `S_DAX` on the
  pseudo-fs inode; `dax_open()` sets `S_DAX` on the opened inode and points
  its `i_mapping` at the mapping of the pseudo-fs inode.
- `vma_is_dax()`: calls `file_is_dax()`, which tests
  `file->f_mapping->host`; the `S_ISCHR()` test in `vma_is_fsdax()` uses
  `file_inode()` instead.
- Without `CONFIG_FS_DAX`: `S_DAX` is 0 in `include/linux/fs.h`, so
  `IS_DAX()`, `file_is_dax()`, `vma_is_dax()` and `dax_mapping()` are false
  for device DAX as well.

## Page cache entries

**Entry encoding**

- `dax_make_entry()`: takes `unsigned long pfn`; there is no pfn_t type in
  this tree.
- `dax_is_conflict()`: compares with `XA_RETRY_ENTRY`; there is no
  DAX_CONFLICT name here, and `fs/dax.c` never stores the value in `i_pages`.
- Zero entry: the pfn bits hold the pfn of the zero page (`zero_pfn()` in
  `dax_load_hole()`) or of the huge zero folio (`dax_pmd_load_hole()`), not 0.
- Zero and empty entries: test the flags before `dax_to_folio()`;
  `dax_associate_entry()`, `dax_disassociate_entry()` and `dax_busy_page()`
  return early for both, and `dax_entry_size()` returns 0.
- `DAX_EMPTY` entry: can be found unlocked; `dax_unlock_entry()` stores it
  back when a fault ends without `dax_insert_entry()`, for example the
  `pmd_trans_huge()` path of `dax_iomap_pte_fault()`.
- `PAGECACHE_TAG_TOWRITE`: set on a DAX mapping in two places,
  `tag_pages_for_writeback()` and `dax_insert_entry()` for an `IOMAP_WRITE`
  fault on an `IOMAP_F_SHARED` iomap.

**Entry locking**

- `dax_unlock_entry()`: the caller must not hold the `i_pages` lock; it
  takes the lock with `xas_lock_irq()`, stores, drops it, then wakes.
- `put_unlocked_entry()`: every call site in `fs/dax.c` holds the `i_pages`
  lock; the body reads only `xas->xa` and `xas->xa_index` and drops nothing.
- `wait_entry_unlocked()`: entered with the lock held, returns with it
  dropped; it waits non-exclusively and does not re-look-up the entry.
- `wait_entry_unlocked()` callers: `dax_lock_folio()` and
  `dax_lock_mapping_entry()`, which retake the lock and reload in their loop.
- `wait_table`: a file-scope static array in `fs/dax.c`, shared by all
  mappings; `struct exceptional_entry_key` tells entries on one queue apart.
- `dax_entry_waitqueue()`: decides PMD or PTE from the entry value passed
  in, not from the slot; a waker must pass an entry of the size the waiters
  saw.
- PMD downgrade in `grab_mapping_entry()`: passes the old PMD entry to
  `dax_wake_entry()` after the slot was set to NULL.
- `__dax_invalidate_entry()`: wakes with `WAKE_ALL` on every path that found
  an entry, also when it removed nothing because a mark was set.
- `dax_writeback_one()`: after the flush it wakes with `dax_wake_entry()` and
  `WAKE_NEXT` directly, while holding the `i_pages` lock.

**Entry unlock and wake rules**

- put_locked_mapping_entry() is not in this tree; `dax_unlock_entry()`
  unlocks an entry, also for `dax_unlock_folio()` and
  `dax_unlock_mapping_entry()`.
- `grab_mapping_entry()` and `dax_insert_entry()`: return the value without
  `DAX_LOCKED`; only the slot holds the locked form.
- Entry from `get_next_unlocked_entry()`: valid only while the `i_pages`
  lock is held; `dax_insert_pfn_mkwrite()` calls `dax_lock_entry()` before
  `xas_unlock_irq()`.
- `wait_entry_unlocked_exclusive()`: its result carries the same lock-or-put
  duty; it returns NULL when the entry is gone, and then no wake is needed.
- `wait_entry_unlocked_exclusive()` use: inside `xas_for_each()` walks on an
  entry already loaded, as in `dax_delete_mapping_range()`.
- `dax_unlock_entry()`: accepts a fresh `XA_STATE` at the index, as
  `dax_unlock_folio()` and `dax_unlock_mapping_entry()` build one.
- **Unsafe usage**: passing `dax_unlock_entry()` a value that has
  `DAX_LOCKED` set, or the value from before `dax_insert_entry()` replaced it.
  - Unsafe: `BUG_ON(dax_is_locked(entry))` fires for a locked value; a stale
    value is stored as-is over the new entry.
  - Safe: unlock with what `dax_insert_entry()` returned, as
    `dax_fault_iter()` writes it through `void **entry` for
    `dax_iomap_pte_fault()`.
- **Potentially unsafe usage**: a lookup or store through an `xa_state` again
  after the `i_pages` lock was dropped, with no explicit `xas_reset()`.
  - Unsafe: when `xas->xa_node` still points at a node from before the drop;
    `xas_start()` in `lib/xarray.c` continues from it.
  - Safe: `xas_reset()` before relocking, as `dax_insert_entry()` and
    `dax_unlock_entry()` do; it sets `XAS_RESTART`, which `xas_start()` tests.
  - Safe: `xas_reset()` after the zero-entry unmap in `grab_mapping_entry()`,
    then `xas_set()` back to the fault index after the downgrade.
  - Safe: `xas_set()` after relocking, as `dax_lock_folio()` and
    `dax_lock_mapping_entry()` do after `wait_entry_unlocked()`; `xas_set()`
    sets `XAS_RESTART`.
  - Safe: `xas_pause()` before the drop inside a walk, as
    `dax_layout_busy_page_range()` does every `XA_CHECK_SCHED` entries;
    `xas_pause()` in `lib/xarray.c` sets `XAS_RESTART`.
  - Safe: `goto retry` in `grab_mapping_entry()` after `xas_nomem()` returned
    true; `xas_nomem()` in `lib/xarray.c` sets `XAS_RESTART`.
  - Safe: after `get_next_unlocked_entry()` or
    `wait_entry_unlocked_exclusive()` slept; both call `xas_reset()` and look
    up again before they return.

**PMD and PTE entry conflicts**

- PTE fault, real PMD entry: `grab_mapping_entry()` locks and returns the
  PMD entry; nothing is removed or split.
- PTE fault, real PMD entry: `dax_insert_entry()` leaves it in place when the
  iomap lacks `IOMAP_F_SHARED`, and only sets marks.
- PTE fault, empty PMD entry: removed without `unmap_mapping_pages()`; only a
  zero PMD entry is unmapped first.
- PTE fault, locked PMD entry of any kind: `get_next_unlocked_entry()` waits
  for the unlock before the kind is looked at.
- PMD fault, any PTE entry in range: conflict, also for a zero or an empty
  PTE entry; nothing is removed and no PMD entry is installed.
- PMD fault, locked PTE entry: no wait; `get_next_unlocked_entry()` tests the
  order before the lock bit.
- `dax_is_conflict()`: true only for `XA_RETRY_ENTRY`, which
  `get_next_unlocked_entry()` returns; it is not a fault code.
- `grab_mapping_entry()`: turns the conflict into
  `xa_mk_internal(VM_FAULT_FALLBACK)`; `XA_RETRY_ENTRY` never reaches its
  caller.
- `grab_mapping_entry()` errors: `xa_mk_internal(VM_FAULT_OOM)` or
  `xa_mk_internal(VM_FAULT_SIGBUS)`; callers test `xa_is_internal()` and
  decode with `xa_to_internal()`.
- `dax_insert_pfn_mkwrite()`: does not go through `grab_mapping_entry()`; at
  order 0 it treats any PMD entry, real ones too, as a race.
- `dax_insert_pfn_mkwrite()` on a race or conflict: calls
  `put_unlocked_entry()` with `WAKE_NEXT` and returns `VM_FAULT_NOPAGE`.

**Entry invariants and their checks**

- `dax_insert_entry()`: entered with the entry lock held and the `i_pages`
  lock not held; it takes the `i_pages` lock itself.
- `__dax_invalidate_entry()`: takes the `i_pages` lock itself.
- `dax_lock_entry()`: has no assertion.
- Slot still holds the caller's locked entry: checked by the `WARN_ON_ONCE`
  in `dax_insert_entry()`, on the replace branch only.
- `dax_insert_entry()` non-replace branch: discards the `xas_load()` result,
  so nothing checks the slot there.
- `dax_disassociate_entry()`: has no `WARN_ON_ONCE` of its own and does not
  use its `mapping` or `trunc` argument.
- Folio belongs to the mapping it is removed from: nothing checks.
- `dax_disassociate_entry()` on a shared folio: only decrements
  `folio->share`; `->mapping` is cleared when the folio is not shared or the
  count reaches 0, in `dax_folio_reset_order()`.
- Pages idle when the last association goes: `dax_folio_put()` has
  `WARN_ON_ONCE(folio_ref_count())` per page, for order 0 too, whatever
  `trunc` was.
- Folio is order 0 when associated on the non-shared path: checked by
  `WARN_ON_ONCE(folio_order(folio))` in `dax_folio_init()`.
- Folio has no references when made compound: checked in `dax_folio_init()`
  for an order above 0.
- Marks on removal: `xas_store()` of NULL clears them through
  `xas_init_marks()`; `fs/dax.c` removal paths clear none explicitly.
- `dax_delete_mapping_range()`: a removal path with no mark test and no
  `WARN_ON_ONCE` of its own; `dax_break_layout()` calls it only when no busy
  page was found.
- `dax_delete_mapping_entry()`: `WARN_ON_ONCE(!ret)` checks that an entry was
  found and removed.
- Removal sites: search for callers of `dax_disassociate_entry()`; each calls
  it under the `i_pages` lock before its `xas_store()`, which in
  `dax_insert_entry()` is inside `dax_lock_entry()`.

## Faults

**Fault entry points**

- `ext4_dax_huge_fault()` in `fs/ext4/file.c`: takes
  `filemap_invalidate_lock_shared()` itself, for reads and writes, before it
  calls `dax_iomap_fault()`.
- `ext4_dax_vm_ops`: all four members reach `ext4_dax_huge_fault()`,
  `.page_mkwrite` included; `ext4_dax_fault()` passes order 0.
- Write test in the handler: `ext4_dax_huge_fault()` and
  `xfs_is_write_fault()` test `FAULT_FLAG_WRITE` and `VM_SHARED`, not
  `vmf->cow_page`, because `cow_page` is unset for a huge fault.
- `vmf->cow_page` is tested in `dax_iomap_pte_fault()` (to set
  `IOMAP_WRITE`) and in `xfs_dax_fault_locked()` (to pick the iomap ops).
- XFS `.map_pages`: there is no xfs_filemap_map_pages() here;
  `xfs_file_vm_ops` installs `filemap_map_pages()`.
- `dax_iomap_pte_fault()` order: i_size test, `grab_mapping_entry()`,
  `pmd_trans_huge()` test, `iomap_iter()` loop around `dax_fault_iter()`,
  store `*iomap_errp`, `dax_unlock_entry()`.
- i_size test: runs before the entry is taken and is not repeated; only the
  caller's lock keeps it true.
- `dax_insert_entry()`: called before every page-table insert of
  `dax_fault_iter()`, `dax_load_hole()` and `dax_pmd_load_hole()`, and before
  the synchronous return; the `cow_page` path and the error returns that come
  before it skip it.
- **Unsafe usage**: reading the `iomap_errp` value after `dax_iomap_fault()`
  without having initialised it.
  - Unsafe: `dax_iomap_pmd_fault()` has no such parameter, and
    `dax_iomap_pte_fault()` returns before the store on the i_size,
    `grab_mapping_entry()` and `pmd_trans_huge()` exits.
  - Safe: set it to 0 before every call, as `__fuse_dax_fault()` does at its
    declaration and again before its retry, or pass NULL, as
    `xfs_dax_fault_locked()` does.

**VMA flags and insert helpers**

- ext4, XFS, erofs: set one flag, with
  `vma_desc_set_flags(desc, VMA_HUGEPAGE_BIT)`, in
  `ext4_file_mmap_prepare()`, `xfs_file_mmap_prepare()` and
  `erofs_file_mmap_prepare()`.
- There is no ext4_file_mmap() or xfs_file_mmap() here; both filesystems
  install `.mmap_prepare` only.
- `struct vm_area_desc`: the flags field is `vma_flags`; it has no `vm_flags`
  field.
- `VMA_HUGEPAGE_BIT`: generated by `DECLARE_VMA_BIT()` in
  `include/linux/mm.h`; `VM_HUGEPAGE` is the same bit as a mask.
- `fuse_dax_mmap()` in `fs/fuse/dax.c`: sets `VM_MIXEDMAP | VM_HUGEPAGE` with
  `vm_flags_set()`; fuse is the one filesystem calling `dax_iomap_fault()`
  that sets `VM_MIXEDMAP`.
- PTE insert: `vmf_insert_page_mkwrite()`, in `dax_fault_iter()`,
  `dax_load_hole()` and `dax_insert_pfn_mkwrite()`.
- PMD insert: `vmf_insert_folio_pmd()`, in `dax_fault_iter()`,
  `dax_pmd_load_hole()` and `dax_insert_pfn_mkwrite()`.
- There is no vmf_insert_folio_pte() in this tree.
- `fs/dax.c` does not call `vmf_insert_mixed()`, `vmf_insert_mixed_mkwrite()`
  or `vmf_insert_pfn_pmd()`.
- `VM_MIXEDMAP`: neither insert helper tests it.
- Reference in `dax_fault_iter()`: `folio_ref_inc()` on
  `dax_to_folio(*entry)` before the insert, `folio_put()` after.
- Reason for the reference: `validate_page_before_insert()` in `mm/memory.c`
  returns `-EINVAL` for a folio with reference count 0, which
  `vmf_insert_page_mkwrite()` turns into `VM_FAULT_SIGBUS`.
- Mapping's own reference: taken with `folio_get()` in
  `insert_page_into_pte_locked()` and `insert_pmd()`, not for a zero folio.
- Reference not taken: on the synchronous return, which leaves
  `dax_fault_iter()` before `folio_ref_inc()`, and on the hole paths.
- **Potentially unsafe usage**: `vm_ops` of a file that faults through
  `dax_iomap_fault()`, without `.pfn_mkwrite`.
  - Unsafe: on a shared mapping with `VM_WRITE` or `VM_MAYWRITE`;
    `vm_mixed_zeropage_allowed()` in `mm/memory.c` returns false and
    `dax_load_hole()` gets `VM_FAULT_SIGBUS` from the insert.
  - Safe: when the filesystem refuses shared mappings that have
    `VMA_MAYWRITE_BIT`, as `erofs_file_mmap_prepare()` does;
    `vm_mixed_zeropage_allowed()` accepts COW and non-writable mappings.
- `Documentation/filesystems/dax.rst`: says to set `VM_MIXEDMAP` and
  `VM_HUGEPAGE` and to supply "fault, pmd_fault, page_mkwrite, pfn_mkwrite".
- pmd_fault: no such member in this tree; the member is `.huge_fault` and
  takes an order.
- `Documentation/filesystems/dax.rst` names no insert helper.
- `Documentation/filesystems/dax.rst` points to ext2 as an example; `fs/ext2`
  has no DAX fault path, and `fs/ext2/super.c` ignores the `dax` option with
  a warning.

**Huge fault fallback**

- COW test in `dax_fault_check_fallback()`: `FAULT_FLAG_WRITE` set and
  `VM_SHARED` clear; `vmf->cow_page` is not read.
- Extent shorter than `PMD_SIZE`: tested with `iomap_length()` in the loop of
  `dax_iomap_pmd_fault()`, not in `dax_fault_iter()`.
- `dax_pmd_load_hole()`: falls back only when `mm_get_huge_zero_folio()`
  returns NULL; a PMD that is no longer none gives `VM_FAULT_NOPAGE` from
  `insert_pmd()`.
- `*vmf->pmd` neither none nor huge: `dax_iomap_pmd_fault()` returns 0 after
  `dax_unlock_entry()`; this is not a fallback.
- `fallback:` label: calls `split_huge_pmd()` and
  `count_vm_event(THP_FAULT_FALLBACK)` only when `ret` is
  `VM_FAULT_FALLBACK`; nothing else touches the page table.
- `grab_mapping_entry()` returning `VM_FAULT_OOM` or `VM_FAULT_SIGBUS`: jumps
  to `fallback:` too, and the split is skipped.
- `split_huge_pmd()` on a DAX VMA: does nothing unless `*vmf->pmd` is huge;
  then `__split_huge_pmd_locked()` in `mm/huge_memory.c` clears the PMD and,
  unless it mapped the huge zero folio, drops the folio's rmap and reference.
  It builds no PTE table.
- `CONFIG_FS_DAX_PMD` off: `dax_iomap_pmd_fault()` is a stub that returns
  `VM_FAULT_FALLBACK`, and `dax_fault_check_fallback()` is not compiled.
- `CONFIG_FS_DAX_PMD`: has no prompt; see `fs/Kconfig` for what it depends
  on.

**Synchronous faults**

- `dax_fault_is_synchronous()`: tests `IOMAP_WRITE`, `VM_SYNC` and
  `IOMAP_F_DIRTY` only; it does not call `dax_synchronous()`.
- `dax_synchronous()`: not tested at fault time; `daxdev_mapping_supported()`
  tests it at mmap time.
- Entry when `dax_iomap_fault()` returns `VM_FAULT_NEEDDSYNC`:
  `dax_insert_entry()` computed `dirty` as false, so it set no
  `PAGECACHE_TAG_DIRTY` and skipped `__mark_inode_dirty()`.
- `dax_finish_sync_fault()`: calls `vfs_fsync_range()` itself, then
  `dax_insert_pfn_mkwrite()`; the filesystem does not fsync first.
- Locks around `dax_finish_sync_fault()`: in-tree callers hold the fault lock
  across it. `ext4_dax_huge_fault()` calls it after `ext4_journal_stop()` and
  before `filemap_invalidate_unlock_shared()`; `xfs_dax_fault_locked()` runs
  under the caller's `XFS_MMAPLOCK_SHARED` or `XFS_MMAPLOCK_EXCL`.
- `dax_insert_pfn_mkwrite()`: returns `VM_FAULT_NOPAGE` when the entry is
  gone, is of a smaller order than asked, or is a PMD entry at order 0.
- `dax_insert_pfn_mkwrite()`: does not test for a zero or empty entry, and
  does not compare the entry with the `pfn` it is given.
- `daxdev_mapping_supported()` in `include/linux/dax.h`: takes a
  `const struct vm_area_desc *`, the inode and the `struct dax_device`, and
  tests `VMA_SYNC_BIT` with `vma_desc_test()`.
- `daxdev_mapping_supported()` caller: the filesystem's `mmap_prepare`
  handler, not `mm/mmap.c`; see `ext4_file_mmap_prepare()`.
- Without `CONFIG_DAX`: `daxdev_mapping_supported()` is a stub that refuses
  every mapping with `VMA_SYNC_BIT`.
- Gate in `do_mmap()`: `MAP_SHARED_VALIDATE` with `MAP_SYNC` returns
  `-EOPNOTSUPP` unless `f_op->fop_flags` has `FOP_MMAP_SYNC`.
- There is no mmap_supported_flags member in this tree.

**Holes, COW and shared extents**

- `dax_load_hole()`: takes the pfn from `zero_pfn()` and maps it with
  `vmf_insert_page_mkwrite(vmf, pfn_to_page(pfn), false)`; there is no
  my_zero_pfn() here.
- `dax_pmd_load_hole()`: maps the huge zero folio with
  `vmf_insert_folio_pmd(vmf, zero_folio, false)`; it does not call
  `set_pmd_at()` itself.
- Hole read path: taken for `IOMAP_UNWRITTEN` as well as `IOMAP_HOLE`, when
  `IOMAP_WRITE` is clear and a PTE fault has no `vmf->cow_page`.
- `dax_fault_cow_page()`: returns `VM_FAULT_DONE_COW` when `finish_fault()`
  returns 0, otherwise what `finish_fault()` returned.
- Entry after the `cow_page` path: the entry `grab_mapping_entry()` locked,
  unlocked again; an existing entry is unchanged, a new one is `DAX_EMPTY`
  and stays in the xarray. No mark is set.
- `grab_mapping_entry()` at order 0: removes a zero or empty PMD entry before
  it makes the PTE-sized entry; this holds for every PTE fault, the
  `cow_page` path included.
- `IOMAP_F_SHARED` in `dax_insert_entry()`: always calls
  `unmap_mapping_pages()` and always replaces the entry, even over a normal
  pfn entry.
- `PAGECACHE_TAG_TOWRITE` in `dax_insert_entry()`: set when `IOMAP_WRITE` and
  `IOMAP_F_SHARED` are both set, synchronous faults included.
- Order in `dax_fault_iter()`: `dax_insert_entry()` runs before
  `dax_iomap_copy_around()`, so the entry and its marks remain when the copy
  fails.
- `dax_iomap_copy_around()` from the fault path: gets `size` as both length
  and alignment, so it copies or zeroes the whole page or PMD, not head and
  tail.
- Zero test in `dax_iomap_copy_around()`: `IOMAP_F_SHARED` set on the map from
  `iomap_iter_srcmap()`, or type `IOMAP_UNWRITTEN`; it does not test
  `IOMAP_HOLE`.
- `iomap_iter_srcmap()` in `include/linux/iomap.h`: returns `iter->iomap` when
  the filesystem filled no `srcmap`, which is how a hole source shows up as
  `IOMAP_F_SHARED`.
- **Unsafe usage**: a filesystem setting `IOMAP_F_SHARED` on the `srcmap` it
  fills for a DAX write.
  - Unsafe: `dax_iomap_copy_around()` tests `srcmap->flags` and zeroes the
    destination instead of copying the old data.
  - Safe: flag only `iomap`, and fill `srcmap` without `IOMAP_F_SHARED`, as
    `xfs_direct_write_iomap_begin()` does in `fs/xfs/xfs_iomap.c`.

## Page references and breaking layouts

**Idle and busy pages**

- Device DAX idle count depends on the driver: `drivers/dax/device.c` uses
  `MEMORY_DEVICE_GENERIC` (idle at 1); `drivers/dax/fsdev.c` uses
  `MEMORY_DEVICE_FS_DAX`, so its pages idle at 0 and take the fsdax wake-up
  path.
- Initial count per type: see `__init_zone_device_page()` in `mm/mm_init.c`.
- Page-table mapping of an fsdax folio: takes one folio reference and one
  mapcount, see `insert_page_into_pte_locked()` in `mm/memory.c`.
- `dax_busy_page()`: does not call `dax_page_is_idle()`; it reports
  `&folio->page` busy when `folio_ref_count(folio) - folio_mapcount(folio)` is
  non-zero.
- `dax_page_is_idle()`: used only as the sleep condition in `wait_page_idle()`
  and `wait_page_idle_uninterruptible()`; it needs the count at 0, so a
  mapping reference keeps a waiter asleep too.
- `free_zone_device_folio()` for `MEMORY_DEVICE_FS_DAX`: leaves
  `folio->mapping` set; the only type-specific step is
  `wake_up_var(&folio->page)`.
- Idle fsdax folio (count 0): can still be large and still carry
  `folio->mapping` or `folio->share`; those go in `dax_folio_put()` when the
  last entry is removed, not at the last put.
- `free_zone_device_folio()` for `MEMORY_DEVICE_GENERIC`: calls no callback and
  leaves `folio->mapping` set; `struct dev_pagemap_ops` has `folio_free`, and
  there is no page_free member.

**Folio association and sharing**

- Shared marker: there is no PAGE_MAPPING_DAX_SHARED here; a shared folio has
  `folio->mapping == NULL` and `folio->share != 0`, see `dax_folio_is_shared()`
  in `fs/dax.c`.
- First association of a shared extent: takes the non-shared branch and sets
  `folio->mapping` and `folio->index`; only the second association calls
  `dax_folio_make_shared()`, so a non-NULL `folio->mapping` does not prove a
  single owner.
- Shared branch of `dax_associate_entry()`: increments `folio->share`, which
  counts associations; when the folio still had a mapping it first calls
  `dax_folio_make_shared()`, which clears `folio->mapping` and sets
  `folio->share` to 1. It does not call `dax_folio_init()`, and warns when the
  entry order differs from `folio_order()`.
- Device DAX: `dax_associate_entry()` has no device-DAX test; it skips only
  zero and empty entries. `drivers/dax/device.c` never reaches it and writes
  `folio->mapping` and `folio->index` in `dax_set_mapping()`.
- `dax_folio_reset_order()` in `fs/dax.c`: does the final reset; it also
  zeroes `folio->share`, which is `folio->index`. It is exported, and
  `fsdev_clear_folio_state()` in `drivers/dax/fsdev.c` calls it on probe and
  unbind.
- Shared folio and the generic memory-failure fallback: `dax_lock_folio()`
  returns 0 when `folio->mapping` is NULL, so `mf_generic_kill_procs()` returns
  `-EBUSY`; only the holder's `notify_failure` can find the owners.

**Breaking layouts**

- NULL callback: `dax_break_layout()` returns `-ERESTARTSYS` at the first busy
  page without waiting for it, and leaves the entries in place.
- NULL callback, in-tree use: `xfs_mmaplock_two_inodes_and_break_dax_layout()`
  in `fs/xfs/xfs_inode.c` for the second inode; on error it drops both
  `XFS_MMAPLOCK_EXCL` locks and starts again.
- Entries on return: deleted only when the return value is 0; on any error
  they all stay, although the range has already been unmapped from page
  tables.
- `dax_delete_mapping_range()`: removes entries without testing
  `PAGECACHE_TAG_DIRTY` or `PAGECACHE_TAG_TOWRITE` and flushes nothing.
- `dax_layout_busy_page_range()`: does not lock entries; it waits for a locked
  entry and releases it, so only the caller's lock keeps new faults out.
- Callback: drops only the lock that blocks faults, calls `schedule()`, and
  retakes it; `xfs_wait_dax_page()` drops `XFS_MMAPLOCK_EXCL` and keeps the
  IOLOCK.
- `dax_break_layout_final()` callers: search for the name; `ext4_evict_inode()`
  calls it without an `IS_DAX()` test, and `erofs_evict_inode()` calls it too.
- Order at eviction: each caller runs `dax_break_layout_final()` before
  `truncate_inode_pages_final()`.

**Freeing and remapping blocks**

- `dax_break_layout()`: asserts no lock itself; `xfs_break_dax_layouts()` and
  `ext4_break_layouts()` check only the fault-blocking lock, and
  `fuse_dax_break_layouts()` checks none.
- `xfs_break_dax_layouts()`: defined in `fs/xfs/xfs_inode.c`; asserts
  `XFS_MMAPLOCK_EXCL`.
- `ext4_break_layouts()`: returns `-EINVAL` with a warning when
  `mapping->invalidate_lock` is not locked; the test is `rwsem_is_locked()`,
  which does not tell shared from exclusive.
- `i_rwsem`: held by the truncate and fallocate callers, but not everywhere;
  `xfs_break_layouts()` asserts the IOLOCK in either mode, and
  `lookup_and_reclaim_dmap()` in `fs/fuse/dax.c` holds only
  `mapping->invalidate_lock` across the call and takes `fi->dax->sem` for
  write afterwards, around the reclaim.
- ext4 call sites: `ext4_break_layouts()` is called in `ext4_fallocate()` once,
  under `filemap_invalidate_lock()`, before the mode switch, and in
  `ext4_setattr()`; `ext4_punch_hole()`, `ext4_collapse_range()`,
  `ext4_insert_range()` and `ext4_zero_range()` rely on that caller.
- ext4 scope: every fallocate mode except `FALLOC_FL_ALLOCATE_RANGE`, and every
  `ATTR_SIZE` change, growing included.
- XFS scope: `__xfs_file_fallocate()` breaks layouts for every mode, and
  `xfs_vn_setattr()` for every `ATTR_SIZE`; `xfs_zone_gc_finish_chunk()` does
  it before remapping garbage-collected blocks.
- XFS two-inode operations: `xfs_ilock2_io_mmap()` breaks DAX layouts only when
  both inodes are DAX; otherwise it takes the two invalidate locks with
  `filemap_invalidate_lock_two()` and breaks no DAX layout. Its callers are
  found by searching for the name.
- fuse scope: `fuse_do_setattr()` on `ATTR_SIZE`, `fuse_open()` on an atomic
  `O_TRUNC`, `fuse_file_fallocate()` when its `block_faults` is set, and dmap
  reclaim, which passes one dmap's byte range instead of the whole file.

**Truncate and invalidate usage**

- `truncate_folio_batch_exceptionals()`: treats any value entry found in a DAX
  mapping as an error; it does `WARN_ON_ONCE(1)` and then calls
  `dax_delete_mapping_entry()`.
- Comment in `truncate_folio_batch_exceptionals()`: names
  dax_break_layout_entry(), which is defined nowhere; `dax_break_layout()` is
  the function meant.
- `invalidate_inode_pages2_range()`: calls
  `dax_invalidate_mapping_entry_sync()` directly; there is no
  invalidate_exceptional_entry2() in this tree.
- `invalidate_inode_pages2_range()` on a DAX mapping: removes entries first and
  calls `unmap_mapping_pages()` on the whole range only after the loop, also
  when it returns `-EBUSY`.
- **Unsafe usage**: `truncate_inode_pages_range()` on a DAX range that still
  holds entries; it warns and removes them without waiting for references.
  - Safe: after `dax_break_layout()` returned 0, with the fault-blocking lock
    still held, as `fuse_open()` does before `truncate_pagecache()`;
    `truncate_folio_batch_exceptionals()` defines the requirement.
  - Safe: at eviction after `dax_break_layout_final()`, as
    `xfs_fs_evict_inode()` does before `truncate_inode_pages_final()`.
- **Potentially unsafe usage**: `invalidate_inode_pages2_range()` on a DAX
  range.
  - Unsafe: when a clean entry that is neither zero nor empty has a folio
    that still has a reference, from a page table or a pin; the entry is
    disassociated while the folio is in use and `dax_folio_put()` warns on the
    non-zero refcount.
  - Safe: after `dax_break_layout()` returned 0 on the range under
    `mapping->invalidate_lock`, as `lookup_and_reclaim_dmap()` in
    `fs/fuse/dax.c` does before `dmap_writeback_invalidate()`; no entry is
    left to invalidate.

## Reads, writes and writeback

**Read and write path**

- `IOCB_ATOMIC` in `iocb->ki_flags`: `dax_iomap_rw()` hits `WARN_ON_ONCE()` and
  returns `-EIO`; this is its first test, ahead of the zero-length return.
- Lock assertions: `lockdep_assert_held_write()` for a write and
  `lockdep_assert_held()` for a read, on `inode->i_rwsem`; there is no
  `WARN_ON_ONCE()` on `inode_is_locked()`, and without `CONFIG_LOCKDEP` nothing
  is tested.
- Read on a read-only superblock: `sb_rdonly()` true skips the read assertion;
  `erofs_file_read_iter()` in `fs/erofs/data.c` calls with no `i_rwsem` held.
- `IOCB_NOWAIT`: `dax_iomap_rw()` turns it into `IOMAP_NOWAIT` itself.
- Type test in `dax_iomap_iter()`: passes `IOMAP_MAPPED`, and any type whose
  `iomap->flags` has `IOMAP_F_SHARED`; everything else is `WARN_ON_ONCE()` and
  `-EIO`.
- `IOMAP_UNWRITTEN` without `IOMAP_F_SHARED`: rejected for a write.
- The type test is not limited to writes: a read of a type other than
  `IOMAP_HOLE`, `IOMAP_UNWRITTEN` or `IOMAP_MAPPED` reaches it too.
- `DAX_RECOVERY_WRITE`: no iocb or iomap flag selects it (there is no
  IOMAP_DAX_RECOVERY here); it is used only for the second
  `dax_direct_access()` call, made when the first returned `-EHWPOISON` and the
  iter is a write.
- Recovery copy: `dax_recovery_write()` replaces `dax_copy_from_iter()` only
  when that second call returned a positive count; a negative result goes
  through `dax_mem2blk_err()` like any other.
- Recovery write that copies nothing: the loop ends with `-EFAULT`, not `-EIO`.
  `dax_recovery_write()` returns 0 when the driver has no `recovery_write` op;
  `pmem_recovery_write()` returns 0 for a poisoned range that is not
  page-aligned.
- Width of the poison test: the request passed to `dax_direct_access()` is the
  rest of the I/O inside this iomap, `ALIGN(length + offset, PAGE_SIZE)`, and
  `__pmem_direct_access()` in `drivers/nvdimm/pmem.c` returns `-EHWPOISON` under
  `DAX_ACCESS` when any bad block lies in it, so a read fails with `-EIO` even
  when the page at `pos` is good.

**Invalidation before a write**

- Condition in `dax_iomap_iter()`: `IOMAP_F_NEW` set in `iomap->flags`, or a
  write with `IOMAP_F_SHARED` set; `iomap->type` plays no part, so
  `IOMAP_UNWRITTEN` alone does not trigger it.
- `IOMAP_F_NEW` half of the condition: not combined with the direction of the
  iter; only the `IOMAP_F_SHARED` half requires a write.
- Function: `invalidate_inode_pages2_range()` on `inode->i_mapping`; for a DAX
  mapping it calls `dax_invalidate_mapping_entry_sync()` on each value entry
  (`mm/truncate.c`). Its return value is ignored.
- CoW write only: `__dax_clear_dirty_range()` runs first on the same range and
  clears both `PAGECACHE_TAG_DIRTY` and `PAGECACHE_TAG_TOWRITE`.
- `IOMAP_F_NEW` without `IOMAP_F_SHARED`: no mark is cleared, and
  `__dax_invalidate_entry()` with `trunc` false leaves an entry that has either
  mark in place.

**Dirty tracking and writeback**

- `dax_insert_entry()`: has no `dirty` parameter; it computes
  `write && !dax_fault_is_synchronous()` from `iter->flags` and the vma.
- `dax_fault_is_synchronous()`: needs `IOMAP_WRITE`, `VM_SYNC` and
  `IOMAP_F_DIRTY` together, so a `MAP_SYNC` write fault on an iomap without
  `IOMAP_F_DIRTY` is marked `PAGECACHE_TAG_DIRTY` at fault time.
- Synchronous fault: the entry is marked dirty later, not by
  `dax_insert_entry()`; `dax_finish_sync_fault()` calls `vfs_fsync_range()` and
  then `dax_insert_pfn_mkwrite()`, which sets `PAGECACHE_TAG_DIRTY`.
- write(2) through `dax_iomap_rw()`: sets no mark, and `dax_copy_from_iter()`
  uses `_copy_from_iter_flushcache()` only when the device has `DAXDEV_NOCACHE`;
  otherwise it is a plain `_copy_from_iter()`.
- `dax_writeback_one()` does not call `dax_direct_access()`: the pfn is
  `dax_to_pfn(entry)` and the flushed address is
  `page_address(pfn_to_page(pfn))`.
- Write-protect step: between clearing `PAGECACHE_TAG_TOWRITE` and
  `dax_flush()`, it calls `pfn_mkclean_range()` on every vma found by
  `mapping_rmap_tree_foreach()`, under `i_mmap_lock_read()`; there is no
  vma_interval_tree_foreach in this tree.
- Entry found locked: `dax_writeback_one()` calls `get_next_unlocked_entry()`
  (there is no get_unlocked_entry here); the pfn comparison and the test that
  `PAGECACHE_TAG_TOWRITE` is still set are made only in this branch.
- Final unlock: open-coded as `xas_store()`, `xas_clear_mark()` of
  `PAGECACHE_TAG_DIRTY`, `dax_wake_entry()`; it does not call
  `dax_unlock_entry()`.
- `i_pages` lock: `dax_writeback_one()` is entered and returns with it held, on
  the skip path too; it drops it around the write-protect and flush, and
  `get_next_unlocked_entry()` drops it if it sleeps.
- `dax_writeback_mapping_range()` returns without writing in three cases:
  `inode->i_blkbits != PAGE_SHIFT` (`WARN_ON_ONCE()`, `-EIO`), `mapping_empty()`
  (0), `wbc->sync_mode != WB_SYNC_ALL` (0, no warning).
- `dax_writeback_mapping_range()` has no early return on
  `dax_write_cache_enabled()`, `mapping_tagged()` or `wbc->nr_to_write`; with
  `CONFIG_ARCH_HAS_PMEM_API`, `dax_flush()` tests `dax_write_cache_enabled()`
  for each entry.

**Cache flush conditions**

- Without `CONFIG_ARCH_HAS_PMEM_API`: `dax_flush()` itself is the empty second
  definition in `drivers/dax/super.c`; it tests no flag and calls nothing.
- `DAXDEV_WRITE_CACHE` clear: `dax_flush()` returns before
  `arch_wb_cache_pmem()`; the flag is written only by `dax_write_cache()`, and
  the enum is private to `drivers/dax/super.c`.
- Callers of `dax_write_cache()`: search for the name; the one that is easy to
  miss is `write_cache_store()` in `drivers/nvdimm/pmem.c`, which lets
  userspace set or clear the flag at run time through sysfs.

## The dax_device core

**Device lifetime**

- `run_dax()`: revives a device that `kill_dax()` killed. Declared in
  `drivers/dax/dax-private.h`, called from `dev_dax_probe()` and
  `fsdev_dax_probe()`.
- `DAXDEV_ALIVE` is not one-way: `__devm_create_dev_dax()` calls `kill_dax()`
  right after `alloc_dax()`, probe sets the bit, `kill_dev_dax()` clears it on
  unbind and again from `unregister_dev_dax()`.
- `kill_dax()` on every call: clears `holder_ops` and `holder_data` with plain
  stores after `synchronize_srcu()`; there is no holder lock.
- `dax_get_private()`: returns NULL while `DAXDEV_ALIVE` is clear, and has no
  lock assertion.
- `dax_alive()`: the `lockdep_assert_held()` on `dax_srcu` compiles to no check
  without lockdep; see `include/linux/lockdep.h`.
- `dax_srcu`: one domain for all devices, and sections nest. A
  `dax_direct_access()` call with no `dax_read_lock()` in the same function
  relies on the caller's section, as `dax_memzero()` and, through
  `dax_zero_page_range()`, `virtio_fs_zero_page_range()` do under the section
  that `dax_zero_iter()` opens.
- **Unsafe usage**: dereferencing a `kaddr` from `dax_direct_access()` after
  the `dax_read_unlock()` that ends the section it was obtained in;
  `kill_dax()` waits only for sections still open before the driver unmaps.
  - Safe: one section across the lookup and every access, as
    `copy_cow_page_dax()` and `dax_iomap_iter()` in `fs/dax.c` do.
  - Safe: `dax_iomap_direct_access()` unlocks before it returns `*kaddr`; the
    caller takes its own section around the call and the access, as
    `dax_unshare_iter()` and `dax_range_compare_iter()` do.
  - Safe: using only the returned page count after unlock, with NULL `kaddr`
    and NULL `pfn`, as `fuse_dax_mem_range_init()` does.

**Allocation and references**

- `alloc_dax()`: returns the device alive; `dax_dev_get()` sets `DAXDEV_ALIVE`
  when `iget5_locked()` hands back an `I_NEW` inode.
- Filesystem lookups that take a reference: `fs_dax_get_by_bdev()`
  (`xa_load()` on `dax_hosts`, then `igrab()`) and `fs_dax_get()` (`igrab()`);
  there is no dax_get_by_host here.
- `kill_dax()` and `put_dax()`: test only for NULL, while `alloc_dax()` fails
  with `ERR_PTR()`. `pmem_attach_disk()` stores the pointer only on success, so
  `pmem_release_disk()` passes NULL when DAX was refused with `-EOPNOTSUPP`.

**Holders and failure notification**

- `fs_dax_get_by_bdev()` with a NULL holder: takes the reference, claims
  nothing, ignores `ops`; `ext4_alloc_sbi()` and `open_table_device()` in
  `drivers/md/dm.c` do this.
- `fs_dax_get_by_bdev()` with a non-NULL holder when a holder is already set:
  returns NULL, the same value as for a queue without DAX.
- Holder with NULL ops: allowed; `xfs_alloc_buftarg()` passes its mount, the
  `struct xfs_mount`, as the holder, with NULL ops without
  `CONFIG_MEMORY_FAILURE`, and `dax_holder_notify_failure()` returns
  `-EOPNOTSUPP` for NULL `holder_ops`.
- Non-NULL ops: `notify_failure` must be set; `dax_holder_notify_failure()`
  calls it unchecked.
- `fs_dax_get()`: defined in `drivers/dax/super.c` under `CONFIG_FS_DAX`, with
  no caller in this tree. See its body for the returns; easy to miss is that
  `-EOPNOTSUPP` means the bound driver is not `DAXDRV_FSDEV_TYPE`, and that the
  claim is made after `dax_read_unlock()`.
- **Unsafe usage**: `fs_dax_get()` with a NULL holder; it has no holder test,
  stores `hops` with `holder_data` still NULL, and `fs_put_dax()` with NULL
  never clears it.
  - Safe: NULL holder with NULL ops to `fs_dax_get_by_bdev()`, which skips the
    claim, as `ext4_alloc_sbi()` does.
- **Unsafe usage**: `fs_dax_get()` on a device whose private data is not a
  `struct dev_dax`; it casts `dax_get_private()` and locks `dev_dax->dev`.
  - Safe: a device made by `__devm_create_dev_dax()` in `drivers/dax/bus.c`,
    which passes the `struct dev_dax` to `alloc_dax()`.
- `fs_put_dax()` `holder` argument: the holder that was claimed, or NULL if
  none was; with NULL it only calls `put_dax()`, which is why
  `close_table_device()` can call `put_dax()` directly.
- Pagemap operations that reach `dax_holder_notify_failure()`:
  `pmem_pagemap_memory_failure()` in `fsdax_pagemap_ops`
  (`drivers/nvdimm/pmem.c`) and `fsdev_pagemap_memory_failure()` in
  `fsdev_pagemap_ops` (`drivers/dax/fsdev.c`); none is in `drivers/dax/super.c`.
- `dax_holder_notify_failure()`: runs `notify_failure` inside its own
  `dax_read_lock()` section; there is no holder lock, and nothing named
  dax_holder_lock.

**Holder release order**

- `fs_put_dax()` with non-NULL `dax_dev` and `holder`: first
  `WRITE_ONCE(dax_dev->holder_ops, NULL)`, unconditionally; then
  `cmpxchg(&dax_dev->holder_data, holder, NULL)`; then
  `WARN_ON(prev && prev != holder)`; no lock is held across these steps.
- `fs_put_dax()` has no test of `holder_data` before it clears `holder_ops`, so
  a mismatched caller removes the real holder's operations.
- `dax_holder_notify_failure()`: never reads `holder_data`; it reads
  `holder_ops` once with `READ_ONCE()` and returns `-EOPNOTSUPP` if NULL, which
  is what a call racing with `fs_put_dax()` gets.
- `kill_dax()` with a holder whose ops are NULL: the holder is told nothing;
  the `-EOPNOTSUPP` is ignored and the holder is cleared all the same.

**Device operations**

- `struct dax_operations`: three members, `direct_access`, `zero_page_range`,
  `recovery_write`; it has no copy operations, and `dax_copy_from_iter()` and
  `dax_copy_to_iter()` never call the driver.
- `DAXDEV_NOCACHE` and `DAXDEV_NOMC`: the copy helpers test them on every
  device, with or without `ops`.
- NULL `dax_dev->ops`: `dax_direct_access()` and `dax_zero_page_range()` return
  `-EOPNOTSUPP`, tested after the alive test; `dax_recovery_write()` returns 0.
- `dax_recovery_write()`: no `dax_alive()` test; returns 0 for NULL
  `recovery_write`, and has no fallback copy.
- `dax_direct_access()`: a negative return from the driver comes back
  unconverted, for example `-EHWPOISON` from pmem; `dax_mem2blk_err()` is the
  caller's job, as in `dax_iomap_iter()`.
- `direct_access`: required whenever `ops` is non-NULL; nothing checks it and
  `dax_direct_access()` calls it unchecked.
- `zero_page_range`: checked only by `alloc_dax()`; `dax_set_ops()` installs
  `ops` without that check.
- `dax_set_ops()`: sets `ops` after allocation, `-EBUSY` if already set; NULL
  clears. `fsdev_dax_probe()` uses it on a device allocated with NULL `ops`.
- **Unsafe usage**: `dax_set_ops()` with NULL on a live device;
  `dax_direct_access()` and `dax_zero_page_range()` test `dax_dev->ops` and
  then read it again for the call.
  - Safe: clear after `kill_dax()` has returned; `fsdev_dax_probe()` registers
    `fsdev_clear_ops()` before `fsdev_kill()`, so devres runs the kill first.
- `_copy_from_iter_flushcache`: a macro for `_copy_from_iter_nocache` without
  `CONFIG_ARCH_HAS_UACCESS_FLUSHCACHE`; see `include/linux/uio.h`.
- `_copy_mc_to_iter`: a macro for `_copy_to_iter` without
  `CONFIG_ARCH_HAS_COPY_MC`, so `DAXDEV_NOMC` then changes nothing.

## The DAX bus and its drivers

**Regions and devices**

- Static `dev_dax->pgmap`: a `kmemdup()` copy made in
  `__devm_create_dev_dax()`, owned by the `struct dev_dax` and freed in
  `dev_dax_release()`; the caller's `data->pgmap` is not kept (in
  `drivers/dax/pmem.c` it is a stack variable).
- Static `dev_dax->pgmap` across bindings: the same copy is handed to every
  driver that binds, so whatever one driver writes into it is seen by the
  next; `fsdev_acquire_pgmap()` resets `vmemmap_shift` and
  `fsdev_clear_pgmap_ops()` clears `ops` and `owner` on unbind.
- Dynamic `dev_dax->pgmap`: `devm_kzalloc()`ed by the driver that binds, in
  `dev_dax_probe()` or `fsdev_acquire_pgmap()`, and freed by devres on unbind.
- **Unsafe usage**: leaving `dev_dax->pgmap` pointing at a `devm_kzalloc()`ed
  pagemap of a dynamic device after probe has failed or the driver has
  unbound.
  - Unsafe: `dev_dax_probe()` and `fsdev_acquire_pgmap()` return `-EINVAL`
    for a dynamic device whose `pgmap` is not NULL, so the device cannot be
    bound again.
  - Safe: `fsdev_dax_probe()` assigns `dev_dax->pgmap` after its last step
    that can fail, and registers `fsdev_kill()` so that `kill_dev_dax()`
    clears it on unbind.
- `dev_dax->ranges[0]` at creation: `__devm_create_dev_dax()` calls
  `alloc_dev_dax_range()` with `data->size` for static and dynamic devices
  alike; a `data->size` of 0 makes no range.
- Lock helpers: there are no dax_region_lock or dax_dev_lock guard helpers;
  callers use `down_write_killable()`, `down_read_interruptible()` and
  `down_write()` directly on `dax_region_rwsem` and `dax_dev_rwsem`.
- `dax_bus_lock`: a mutex, guards only the per-driver `ids` list used by
  `do_id_store()` and `dax_match_id()`.
- `dax_region_rwsem` held for write: asserted by `alloc_dev_dax_range()`,
  `trim_dev_dax_range()`, `adjust_dev_dax_range()` and
  `devm_register_dax_mapping()`, so it is the lock for `dev_dax->ranges`,
  `dev_dax->nr_range` and the children of `dax_region->res`.
- `dax_dev_rwsem`: asserted by `dev_dax_size()` and, for write, by
  `__free_dev_dax_id()`; also taken for write to change `dev_dax->align` and
  `dev_dax->memmap_on_memory`.
- Ranges changed under `dax_region_rwsem` alone: `__devm_create_dev_dax()`
  before `device_add()`, and `unregister_dev_dax()` after `device_del()`;
  `size_store()` and `mapping_store()`, on a registered device, hold both.
- `get_dax_range()`: takes `dax_region_rwsem` for write, so the mapping
  `start`, `end` and `page_offset` show functions hold the write lock.
- `delete_store()`: takes `device_lock()` on the region device, then on the
  victim, then `dax_dev_rwsem` for write, and not `dax_region_rwsem`;
  `unregister_dev_dax()` takes that later, after `dax_dev_rwsem` and the
  victim's device lock are dropped.
- `unregister_dev_dax()`: holds `dax_region_rwsem` for write across
  `device_del()`, so the bound driver's `remove` and devm actions run with it
  held.
- `dax_bus_probe()`: takes `dax_dev_rwsem` for read under the device lock of
  the `struct dev_dax`.

**Character device mappings**

- Shared-mapping test: `__check_vma()` tests `VMA_MAYSHARE_BIT` with
  `vma_flags_test_any()`, not `VM_SHARED`.
- Fourth check: `__check_vma()` returns `-EINVAL` when `file_is_dax()` is
  false for the file; it does not call `vma_is_dax()`.
- mmap hook: there is no dax_mmap() here; `dax_mmap_prepare()` works on a
  `struct vm_area_desc`, calls `__check_vma()` under `dax_read_lock()` and
  sets `VMA_HUGEPAGE_BIT` with `vma_desc_set_flags()`.
- `check_vma()`: a wrapper that feeds a VMA to `__check_vma()`; each of
  `__dev_dax_pte_fault()`, `__dev_dax_pmd_fault()` and the real
  `__dev_dax_pud_fault()` calls it first and turns any error into
  `VM_FAULT_SIGBUS`.
- Order other than 0, `PMD_ORDER` or `PUD_ORDER`: `dev_dax_huge_fault()`
  returns `VM_FAULT_SIGBUS`, not `VM_FAULT_FALLBACK`.
- PMD or PUD range not fully inside the VMA: `VM_FAULT_SIGBUS`, not
  `VM_FAULT_FALLBACK`.
- Stub returning `VM_FAULT_FALLBACK`: only `__dev_dax_pud_fault()` without
  `CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD`; `__dev_dax_pmd_fault()` has no
  stub.
- `dax_set_mapping()`: writes `folio->mapping` and `folio->index` and nothing
  else; it does not touch the folio order.
- `dax_set_mapping()` with `dev_dax->pgmap->vmemmap_shift` set: writes only
  the head folio; `dev_dax_probe()` sets `vmemmap_shift` whenever
  `dev_dax->align` is larger than `PAGE_SIZE`.
- Inserts: `vmf_insert_page_mkwrite()`, `vmf_insert_folio_pmd()` and
  `vmf_insert_folio_pud()`; `drivers/dax/device.c` inserts no raw pfn.

**Memory hotplug driver**

- `dev_dax->target_node < 0`: `dev_dax_kmem_probe()` returns `-EINVAL`; there
  is no fallback node.
- Range trimming: `dax_kmem_range()` uses `memory_block_aligned_range()` from
  `include/linux/memory.h`.
- Two passes, not one per range: `dax_kmem_init_resources()` reserves every
  range with `request_mem_region()` first, then `dax_kmem_do_hotplug()` adds
  every range whose `data->res[i]` is set.
- Add call: `__add_memory_driver_managed()`, which takes the online type as
  an argument; `dax_kmem_do_hotplug()` does not call
  `add_memory_driver_managed()`.
- Online type at probe: `dev_dax_kmem_probe()` reads
  `mhp_get_default_online_type()` and passes it down;
  `__add_memory_resource()` onlines the blocks when it is not `MMOP_OFFLINE`.
- `data->state`: set to that online type after probe, `DAX_KMEM_UNPLUGGED`
  before; see `struct dax_kmem_data`.
- `state` attribute of the dax device: `state_store()` lets user space pick
  the online type per device; it accepts "unplugged", "online",
  "online_kernel" and "online_movable".
- `state` write of "offline": `dax_kmem_parse_state()` rejects it with
  `-EINVAL`.
- `state` write of an online type: allowed only from `DAX_KMEM_UNPLUGGED`,
  else `-EBUSY`, unless it is the state already held, which succeeds; a
  device probed with `MMOP_OFFLINE` must be written "unplugged" first.
- `state` write of "unplugged": `dax_kmem_do_hotremove()` offlines and removes
  every added range with `offline_and_remove_memory_ranges()`; on failure
  nothing is removed and the state is unchanged.
- `dax_kmem_do_hotremove()` without `CONFIG_MEMORY_HOTREMOVE`: returns
  `-EBUSY`.
- `dev_dax_kmem_remove()`: never offlines; with `CONFIG_MEMORY_HOTREMOVE`,
  `dax_kmem_remove_ranges()` calls only `remove_memory()`, which returns
  `-EBUSY` for a range with an online block; without it
  `dev_dax_kmem_remove()` removes nothing.
- `dev_dax_kmem_remove()` does not read `data->state`; memory block `state`
  files can change blocks without updating it.
- Mixed result in `dax_kmem_remove_ranges()`: ranges that are offline are
  removed and their `data->res[i]` freed, even when another range is online
  and the rest of the driver data is then leaked.

**Filesystem-facing driver**

- The driver exists: `fsdev_dax_driver` in `drivers/dax/fsdev.c`, type
  `DAXDRV_FSDEV_TYPE`, module `fsdev_dax`, built with `CONFIG_DEV_DAX_FSDEV`
  (no prompt, depends on `DEV_DAX` and `FS_DAX`).
- Filesystem entry point: `fs_dax_get()` in `drivers/dax/super.c` takes a
  `struct dax_device` with no block device; `fs_put_dax()` releases it.
- `fs_dax_get()` returns: `-ENODEV` if the device is dead or unbound,
  `-EOPNOTSUPP` if the bound driver is not `DAXDRV_FSDEV_TYPE`, `-EBUSY` if
  another holder is set.
- `fs_dax_get()` has no caller in this tree.

| | `dev_dax_probe()` | `fsdev_dax_probe()` |
|---|---|---|
| `pgmap->type` | `MEMORY_DEVICE_GENERIC` | `MEMORY_DEVICE_FS_DAX` |
| `pgmap->vmemmap_shift` | set when `dev_dax->align` > `PAGE_SIZE` | left 0, reset to 0 on a static pgmap |
| `pgmap->ops`, `pgmap->owner` | not set | `fsdev_pagemap_ops`, the `struct dev_dax`; cleared on unbind |
| `struct dax_operations` | none | `dev_dax_ops`, installed with `dax_set_ops()`, cleared on unbind |
| character device | `dax_fops`, with `dax_mmap_prepare()` | `fsdev_fops`, no mmap handler |

- Folio reset: `fsdev_clear_folio_state()` runs `dax_folio_reset_order()` on
  every folio of every range at probe, and again on unbind as a devm action.
- `dev_dax->cached_size`: written by `fsdev_dax_probe()`, read by
  `__fsdev_dax_direct_access()` to bound the returned page count.
- `fsdev_pagemap_memory_failure()`: forwards to `dax_holder_notify_failure()`,
  so the holder set by `fs_dax_get()` receives it.
- Binding is never automatic: `dax_match_type()` only ever selects
  `DAXDRV_DEVICE_TYPE` or `DAXDRV_KMEM_TYPE`, so `dax_bus_match()` matches
  this driver only through `dax_match_id()`.
- To bind: unbind the device from its current driver, then write its name
  (form "dax%d.%d") to the `new_id` attribute of `fsdev_dax`; `do_id_store()`
  adds the name and calls `driver_attach()`.
- Driver `bind` attribute: `bind_store()` requires `dax_bus_match()` to
  succeed, so it works only after the name is in `new_id`.
- `dax_bus_type` does not set `driver_override`.

## Model gaps

### Other mistakes models make

- Models take a DAX filesystem's `struct iomap_ops` to be an `iomap_begin` and
  `iomap_end` pair. Here it has a third member `iomap_next`, which
  `iomap_iter()` in `fs/iomap/iter.c` calls when set; for example
  `fuse_iomap_ops` in `fs/fuse/dax.c` sets only `.iomap_next`, built with
  `DEFINE_IOMAP_ITER_NEXT_END()`.
- Models take the loop body of `iomap_iter()` to report progress through a
  processed count. Here the body sets `iter.status` and moves on with
  `iomap_iter_advance()`, which takes a byte count by value; see
  `dax_iomap_pte_fault()` in `fs/dax.c`.
- Models take `.pfn_mkwrite` to be all that `vm_mixed_zeropage_allowed()` in
  `mm/memory.c` needs on a shared mapping that may be written. It also
  requires `vma_is_fsdax()` or `VM_IO`.
- Models take a DAX PTE to be a special devmap pfn mapping. Nothing named
  pte_devmap is in this tree.
- Models take a hmem or CXL `struct dev_dax` to bind to the character device
  driver by default. `dax_hmem_probe()` and `cxl_dax_region_probe()` pass
  `IORESOURCE_DAX_KMEM`, so with `CONFIG_DEV_DAX_KMEM` `dax_match_type()`
  picks kmem; hmem drops the flag only when its `region_idle` parameter is
  set.
- Models take dax_hmem to create a device for every soft-reserved range. With
  `CONFIG_DEV_DAX_CXL`, `hmem_register_device()` in `drivers/dax/hmem/hmem.c`
  skips a range that intersects `IORES_DESC_CXL`; `process_defer_work()` later
  registers it only if `cxl_region_contains_resource()` is false.
- Models do not know `kzalloc_obj()`, `kzalloc_flex()` and `kmalloc_objs()`.
  They are defined in `include/linux/slab.h` and used in
  `drivers/dax/bus.c` and `drivers/dax/kmem.c`.
