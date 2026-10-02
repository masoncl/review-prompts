# KHO (Kexec Handover) Subsystem

## Main structures

### Objects and how they relate

- Location: core is `kernel/liveupdate/kexec_handover.c`, with
  `kernel/liveupdate/kexec_handover_debugfs.c` and
  `kernel/liveupdate/kho_block.c`; there is no kernel/kexec_handover.c.
  Handed-over layouts are in `include/linux/kho/abi/`.
- No finalize step: there is no kho_finalize(), kho_abort(),
  struct kho_serialization, notifier chain or debugfs finalize file.
- debugfs under `kho/`: read-only blobs plus `scratch_phys` and
  `scratch_len`; it controls nothing.
- Preserved-memory tracker: `struct kho_radix_tree`
  (`include/linux/kho_radix_tree.h`), one tree for all orders; a key
  from `kho_encode_radix_key()` carries both physical address and order.
- There is no struct kho_mem_track, struct khoser_mem_chunk or
  struct kho_mem_phys, and no per-order xarray.
- `struct kho_radix_node` and `struct kho_radix_leaf`: one page each, linked
  by physical address, so the tree is handed over in place with no
  flattening.
- Tracker node pages: not keys in the tracker themselves; they stay intact
  until walked because early allocation is confined to scratch, and
  `kho_extend_scratch()` counts them as busy.
- `struct kho_out` and `struct kho_in`: each embeds its own
  `struct kho_radix_tree`; the incoming one wraps the previous kernel's root
  page (`kho_memory_init_early()`) and is used only by `__init` code.
- `struct kho_out`: `lock` protects the root FDT, not the tracker; each tree
  has its own `lock`; there is no finalized flag.
- `union kho_page_info`: magic plus order, stamped into `page->private` of
  the first page of each preserved block (one tracker key) by
  `kho_preserved_memory_reserve()` during the boot-time walk.
- `kho_restore_folio()` and `kho_restore_pages()`: read only that stamp; they
  do not consult `struct kho_in` or the tracker.
- Order-0 runs: `kho_preserve_pages()` and `kho_restore_pages()`; there is
  no kho_preserve_phys() or kho_restore_phys().
- `struct kho_kexec_metadata`: KHO's own sub-blob, `KHO_METADATA_NODE_NAME`,
  registered in `kho_init()`; the next kernel copies it into `struct kho_in`.
- `struct kho_block_set`: chain of preserved pages, each headed by
  `struct kho_block_header_ser`, holding fixed-size entries; LUO sessions and
  files use it. It is linked into `luo.o`, so it needs `CONFIG_LIVEUPDATE`,
  not only `CONFIG_KEXEC_HANDOVER`.
- Clients: no IOMMU or vfio user in this tree; search callers of
  `kho_add_subtree()` and `kho_preserve_folio()`. `mm/memfd_luo.c` calls the
  preserve functions itself, hands the result to LUO as `serialized_data`,
  and registers no sub-blob of its own.
- Passing to the next kernel: never the command line. `kho_fill_kimage()`
  fills `kho` in `struct kimage`; x86 sends `struct kho_data` as
  `SETUP_KEXEC_KHO` setup data, devicetree arches send `linux,kho-fdt` and
  `linux,kho-scratch` under `/chosen` (`drivers/of/kexec.c`); both reach
  `kho_populate()`.
- Two meanings of scratch on a KHO boot: the `kho_scratch` array of
  `struct kho_scratch`, and memblock regions flagged `MEMBLOCK_KHO_SCRATCH`.
  `kho_extend_scratch()` also flags every range outside the
  `KHO_SCRATCH_EXT_BLKSIZE` blocks that hold preserved memory or tracker
  nodes.
- `kho_scratch` array only: `kho_scratch_overlap()` (hence `MIGRATE_CMA`) and
  kexec image placement in `kho_locate_mem_hole()` ignore the extended
  ranges.

## Where to look

**Source files**

| Job | File | Easy to miss |
|---|---|---|
| KHO core | `kernel/liveupdate/kexec_handover.c` | also holds the radix tree, vmalloc preservation and kexec metadata code; none has a file of its own |
| KHO debug checks | `kernel/liveupdate/kexec_handover.c` | there is no kexec_handover_debug.c; `CONFIG_KEXEC_HANDOVER_DEBUG` builds no object and is tested with `IS_ENABLED()` |
| KHO debugfs | `kernel/liveupdate/kexec_handover_debugfs.c` | `CONFIG_KEXEC_HANDOVER_DEBUGFS`; stubs in `kernel/liveupdate/kexec_handover_internal.h` |
| Serialization blocks | `kernel/liveupdate/kho_block.c` | listed in `luo-y`, so built under `CONFIG_LIVEUPDATE`, not under `CONFIG_KEXEC_HANDOVER` alone; `include/linux/kho_block.h` has no stubs; users are `kernel/liveupdate/luo_file.c` and `kernel/liveupdate/luo_session.c` |
| LUO | `kernel/liveupdate/luo_core.c`, `kernel/liveupdate/luo_session.c`, `kernel/liveupdate/luo_file.c`, `kernel/liveupdate/luo_flb.c`, `kernel/liveupdate/luo_internal.h` | the four `.c` files are linked into `luo.o` together with `kho_block.o` |
| Public headers | `include/linux/kexec_handover.h`, `include/asm-generic/kexec_handover.h`, `include/linux/kho_radix_tree.h`, `include/linux/kho_block.h`, `include/linux/liveupdate.h`, `include/uapi/linux/liveupdate.h` | the radix tree and the blocks each have their own header; `struct kho_scratch` is in `include/asm-generic/kexec_handover.h` |
| ABI between kernels | `include/linux/kho/abi/kexec_handover.h`, `include/linux/kho/abi/kexec_metadata.h`, `include/linux/kho/abi/block.h`, `include/linux/kho/abi/luo.h`, `include/linux/kho/abi/memfd.h`, `include/linux/kho/abi/memblock.h` | six headers; `include/linux/kho/abi/memblock.h` is used by `mm/memblock.c`, `include/linux/kho/abi/kexec_metadata.h` by `kernel/liveupdate/kexec_handover.c` |
| memfd handler | `mm/memfd_luo.c` | `CONFIG_LIVEUPDATE_MEMFD` |
| In-kernel test, KHO | `lib/test_kho.c` | symbol is `CONFIG_TEST_KEXEC_HANDOVER`; there is no CONFIG_TEST_KHO; plain `module_init()`, not KUnit |
| In-kernel test, LUO | `lib/tests/liveupdate.c` | `CONFIG_LIVEUPDATE_TEST`; not KUnit and no initcall; `liveupdate_register_file_handler()` calls `liveupdate_test_register()` |
| Selftests, KHO | `tools/testing/selftests/kho/` | no Makefile and not in `TARGETS`; run through `tools/testing/selftests/kho/vmtest.sh` |
| Selftests, LUO | `tools/testing/selftests/liveupdate/` | in `TARGETS` of `tools/testing/selftests/Makefile` |

## Enabling and boot

**Boot sequence**

- Order; the first three steps run on the boot CPU before any initcall:

| Step | Called from | Runs when |
|---|---|---|
| `kho_populate()` | x86: `add_kho()` from `parse_setup_data()`; DT: `early_init_dt_check_kho()`, last call in `early_init_dt_scan_nodes()` | inside `setup_arch()`, only if the previous kernel passed KHO data |
| `kho_memory_init_early()` | first call in `mm_core_init_early()` in `mm/mm_init.c` | `start_kernel()`, right after `setup_arch()`, before `free_area_init()` |
| `kho_memory_init()` | `mm_core_init()` | immediately before `memblock_free_all()` |
| `kho_init()` | `fs_initcall` | `do_initcalls()` |

- `kho_populate()` on x86: runs before `parse_early_param()`, and neither it nor
  its callers read `kho_enable`.
- `kho_memory_init_early()`: returns at once unless `is_kho_boot()`; otherwise
  sets `kho_scratch`, initialises `kho_in.radix_tree` from the incoming FDT and
  calls `kho_extend_scratch()`.
- `kho_memory_init()`: calls `kho_mem_retrieve()` when `kho_in.scratch_phys` is
  set, else `kho_reserve_scratch()`; there is no kho_release_scratch() here.
- `kho_init()`: the only place that creates outgoing state
  (`kho_out.radix_tree.root`, `kho_out.fdt`).
- First safe call:

| Functions | First usable after | Called earlier |
|---|---|---|
| `kho_retrieve_subtree()` | `kho_populate()`, once `phys_to_virt()` of the FDT is mapped (`kho_populate()` itself uses `early_memremap()`); `reserve_mem()` in `mm/memblock.c` (`__setup`) calls it before `kho_memory_init()` | `-ENOENT` |
| `kho_restore_folio()`, `kho_restore_pages()`, `kho_restore_free()` | `kho_memory_init()`; first in-tree use is `luo_early_startup()` at `early_initcall` | `kho_restore_page()` returns NULL; the magic it tests is written by `kho_preserved_memory_reserve()` |
| `kho_restore_vmalloc()` | as above, plus `vmalloc_init()`, which runs later in `mm_core_init()` | — |
| `kho_preserve_folio()`, `kho_preserve_pages()`, `kho_preserve_vmalloc()`, `kho_alloc_preserve()`, the unpreserve functions | a successful `kho_init()` | `WARN_ON_ONCE(!tree->root)`; preserve fails |
| `kho_add_subtree()`, `kho_remove_subtree()` | a successful `kho_init()` | NULL `kho_out.fdt` is dereferenced in `fdt_open_into()` |

- Outside `kho_init()`, in-tree outgoing users run at `late_initcall`,
  `module_init` or runtime, for example `luo_late_startup()` and
  `reserve_mem_init()`.

**Finalize and abort**

- No finalize or abort step, notifier chain or debugfs control file exists;
  there is no kho_finalize() or register_kho_notifier() in this tree.
- Stale text: the help of `CONFIG_KEXEC_HANDOVER_DEBUGFS` and a comment in
  `kernel/liveupdate/luo_flb.c` still mention finalize; no code implements it.
- Debugfs in `kernel/liveupdate/kexec_handover_debugfs.c`: every file is
  created with mode 0400.
- Root FDT: built once by `kho_out_fdt_setup()` in `kho_init()`, with the
  physical address of `kho_out.radix_tree.root` in it, then edited in place.
- `kho_fill_kimage()`: generates nothing; it stores `virt_to_phys(kho_out.fdt)`
  in `image->kho.fdt` and adds the `kho_scratch` array as a kexec buffer.
- The root FDT and the radix tree are not copied at load or at
  `kernel_kexec()`; the next kernel reads the root FDT page and radix tree
  pages as they are in memory at the jump.
- Precondition for any handover: the image was loaded through
  `kernel/kexec_file.c`, the only caller of `kho_fill_kimage()`, with
  `kho_enable` true and a non-crash image; otherwise `image->kho.fdt` stays 0
  and `setup_kho()` in `arch/x86/kernel/kexec-bzimage64.c` adds nothing.

**Enabled and handover-boot checks**

- `kho_enable`: `__ro_after_init`, so it cannot change once init memory is
  sealed; every function that writes it is `__init`.
- `kho_is_enabled()` true to false: `kho_reserve_scratch()` on allocation
  failure, and the error path of `kho_init()`; besides the `kho=` parser
  `kho_parse_enable()`, nothing else writes `kho_enable`, `kho_populate()`
  included.
- `kho_reserve_scratch()`: reached only when `kho_in.scratch_phys` is 0, so on
  a handover boot whose `kho_memory_init_early()` succeeded only `kho_init()`
  can clear `kho_enable`.
- `kho_is_enabled()` is final only after `kho_init()` (`fs_initcall`); a true
  read at `early_initcall`, as in `luo_early_startup()`, can be overtaken.
- `is_kho_boot()`: independent of `kho_enable`; with `kho=off` on a handover
  boot it is still true.
- `is_kho_boot()` true to false: `kho_in.fdt_phys = 0` in the error path of
  `kho_memory_init_early()` and in the error path of `kho_mem_retrieve()`
  (called by `kho_memory_init()`); final once `kho_memory_init()` returns.
- `is_kho_boot()` read between `kho_populate()` and
  `kho_memory_init_early()`: done by `reserve_regions()` in
  `drivers/firmware/efi/efi-init.c`; the value can still be withdrawn.

**Calling the API when disabled**

- State when disabled: `kho_init()` returns before creating anything, so
  `kho_out.radix_tree.root` and `kho_out.fdt` are NULL; the same holds before
  `kho_init()` runs and after it fails.
- No function in the table tests `kho_enable`:

| Function | With `kho_out` state NULL |
|---|---|
| `kho_preserve_folio()`, `kho_preserve_pages()` | `-EINVAL` after `WARN_ON_ONCE(!tree->root)` in `kho_radix_add_key()` |
| `kho_preserve_vmalloc()` | `-ENOMEM` for a valid area, because `new_vmalloc_chunk()` fails |
| `kho_alloc_preserve()` | `ERR_PTR(-EINVAL)`; the folio is freed |
| `kho_unpreserve_folio()`, `kho_unpreserve_pages()` | `WARN_ON_ONCE()` in `kho_radix_del_key()`, then return |
| `kho_unpreserve_free()` | same warning, then still drops the folio |
| `kho_add_subtree()`, `kho_remove_subtree()` | NULL pointer dereference in `fdt_open_into()` |
| `kho_retrieve_subtree()`, restore functions | unaffected; work on a handover boot with `kho=off` |

- **Potentially unsafe usage**: calling `kho_add_subtree()` or
  `kho_remove_subtree()`.
  - Unsafe: when nothing on the path proves `kho_init()` set up
    `kho_out.fdt`: `kho=off`, a call before `fs_initcall`, or a
    `kho_is_enabled()` test made before `kho_init()` ran; `fdt_open_into()`
    reads the header through NULL.
  - Safe: after `kho_is_enabled()` read true at `late_initcall` or later, as
    `reserve_mem_init()` in `mm/memblock.c` does; `kho_init()` clears
    `kho_enable` on every failure.
  - Safe: after a preserve call on the same path succeeded, as
    `luo_state_setup()` does with `kho_alloc_preserve()`; `kho_init()` sets the
    radix root and `kho_out.fdt` together and tears both down on failure.
  - Safe: inside `kho_init()` after `kho_out_fdt_setup()` returned 0, as
    `kho_out_kexec_metadata()` does.
  - Safe: `kho_remove_subtree()` for a blob whose `kho_add_subtree()` returned
    0, as the error path of `prepare_kho_fdt()` does.
- `luo_late_startup()`: tests only `liveupdate_enabled()`, decided at
  `early_initcall`; after a later `kho_init()` failure it is the failing
  `kho_alloc_preserve()` that keeps it from `kho_add_subtree()`.
- Unpreserve functions: call only for a preservation that succeeded;
  otherwise, while `kho_out.radix_tree.root` is NULL, they hit
  `WARN_ON_ONCE()`.
- Incoming side: `luo_early_startup()` and `kho_test_init()` skip retrieval
  when `kho_is_enabled()` is false; `reserve_mem_kho_revive()` does not test it.
- `mm/memblock.c`: calls no restore function; `reserve_mem_kho_revive()` only
  re-registers the range with `reserved_mem_add()`.
- Callers of `kho_add_subtree()`: the only one that runs at `fs_initcall` is
  `kho_out_kexec_metadata()`, inside `kho_init()` after `kho_out_fdt_setup()`;
  nothing under `kernel/` outside `kernel/liveupdate/` calls it.

## Preserving and restoring memory

**Preserved memory tracker**

- Names: there is no kho_radix_encode_key(), kho_radix_add_page(),
  kho_radix_del_page(), KHO_ORDER_0_LOG2 or struct kho_mem_track in this tree.
- Key: built by `kho_encode_radix_key()` and decoded by
  `kho_decode_radix_key()`, both static in
  `kernel/liveupdate/kexec_handover.c`.
- Order bit: `1UL << (64 - (PAGE_SHIFT + order))`, OR-ed with
  `phys >> (PAGE_SHIFT + order)`.
- Lock: `struct kho_radix_tree` holds a `struct mutex lock`, not an
  rw_semaphore.
- `kho_radix_add_key()`, `kho_radix_del_key()` and `kho_radix_walk_tree()`:
  each takes `tree->lock`; add and del call `might_sleep()` before taking it.
- `kho_radix_walk_tree()`: holds the mutex across every callback, so a
  callback cannot add or delete in the tree being walked;
  `kho_extend_scratch()` adds to a second tree with its own lockdep class.
- `kho_radix_add_key()` errors: `-EINVAL` with `WARN_ON_ONCE()` when
  `tree->root` is NULL, `-ERANGE` for a key wider than `KHO_RADIX_KEY_WIDTH`,
  `-ENOMEM`.
- `kho_radix_del_key()`: returns void.
- `kho_radix_alloc_node()`: `get_zeroed_page(GFP_KERNEL)` once
  `slab_is_available()`, `memblock_alloc()` before that.

**Folio preserve and restore**

- `kho_preserve_folio()`: no address or alignment check; its errors are those
  of `kho_radix_add_key()`.
- Scratch overlap: `WARN_ON()` and `-EINVAL` only under
  `CONFIG_KEXEC_HANDOVER_DEBUG`.
- `kho_preserve_folio()`: takes no reference; the caller keeps the folio
  allocated, as `memfd_luo_preserve_folios()` does with `memfd_pin_folios()`.
- `kho_restore_page()`: looks the page up with `pfn_to_online_page()`, not
  `pfn_valid()`; a NULL there returns NULL with no warning.
- Magic mismatch (never preserved, already restored, tail page):
  `WARN_ON_ONCE()` and NULL, nothing written.
- Unaligned `phys`: `PHYS_PFN()` drops the offset, so an address inside the
  head page restores the folio.

**Page ranges**

- Block order: `__kho_preserve_pages_order()` takes
  `min(count_trailing_zeros(pfn), ilog2(end_pfn - pfn))`, then lowers it until
  the first and last pfn of the block give the same `pfn_to_nid()`.
- `MAX_PAGE_ORDER`: no cap in `kho_preserve_pages()` or in
  `kho_restore_pages()`.
- Scratch overlap: `WARN_ON()` and `-EINVAL` only under
  `CONFIG_KEXEC_HANDOVER_DEBUG`.
- `kho_restore_pages()`: does not call `__kho_preserve_pages_order()`; it
  advances by its own `min(count_trailing_zeros(pfn), ilog2(end_pfn - pfn))`.
- Pages initialised per step: `1 << info.order` from the stored order in
  `kho_restore_page()`; the step and the stored order are never compared.
- Wrong `nr_pages` on restore: fails only when the walk lands on a pfn that
  is not online or whose `page->private` lacks `KHO_PAGE_MAGIC`; otherwise it
  returns the first page.
- `kho_restore_pages()` failure: returns NULL with no undo; blocks already
  restored stay restored.

**Allocate and preserve**

- Sizes: 0 gives `ERR_PTR(-EINVAL)`; `get_order(size) > MAX_PAGE_ORDER` gives
  `ERR_PTR(-E2BIG)`.
- Without `CONFIG_KEXEC_HANDOVER`: the stub returns `ERR_PTR(-EOPNOTSUPP)`.
- Finalize: KHO has no finalize or freeze state here; kho_finalize() is not
  defined, and `kho_unpreserve_free()` has no state check.
- luo_fdt_setup() is not in this tree; `luo_state_setup()` in
  `kernel/liveupdate/luo_core.c` allocates a `struct luo_ser` this way.
- **Unsafe usage**: passing the `ERR_PTR()` result to `kho_unpreserve_free()`
  or `kho_restore_free()`; both filter only NULL.
  - Safe: jump past the free on `IS_ERR()`, as `memfd_luo_preserve()` in
    `mm/memfd_luo.c` does.
- `kho_restore_free()` argument: `phys_to_virt()` of the handed-over physical
  address; the function applies `__pa()` to it.
- One in-tree caller of `kho_restore_free()`: `luo_early_startup()` reads
  `struct luo_ser` through `phys_to_virt()` and, once the size and compatible
  checks pass, calls `kho_restore_free()` on it last. That blob is a
  retrieved subtree, so "Retrieving a subtree" applies: under
  `CONFIG_KEXEC_HANDOVER_DEBUGFS`, `kho_in_debugfs_init()` later points a
  debugfs file at it.
- `kho_restore_free()` on a block already restored: `kho_restore_folio()`
  returns NULL, `WARN_ON()` fires, and no `folio_put()` runs.

**Unpreserve calls**

- Never-preserved memory, table entry missing on the path:
  `kho_radix_del_key()` hits `WARN_ON()`, not `WARN_ON_ONCE()`, and returns.
- Never-preserved memory, leaf exists: the clear bit is cleared again, with no
  warning.
- Counting: the tracker holds one bit per key; preserving a block twice and
  unpreserving it once leaves it not preserved.
- `kho_unpreserve_folio()`: builds the key from `folio_order()` at the call,
  so the folio must still have the order it had when preserved.

**Incoming preserved pages**

- Deferred init: supported; `CONFIG_KEXEC_HANDOVER` has no dependency on
  `CONFIG_DEFERRED_STRUCT_PAGE_INIT` in `kernel/liveupdate/Kconfig`.
- `kho_get_preserved_page()`: under `CONFIG_DEFERRED_STRUCT_PAGE_INIT` it calls
  `init_deferred_page()` for every page of the block before
  `kho_preserved_memory_reserve()` writes `page->private`.
- `memblock_reserved_mark_noinit()`: sets `MEMBLOCK_RSRV_NOINIT`, so
  `memmap_init_reserved_pages()` skips the block and the write survives.
- Deferred pass: `deferred_init_memmap_chunk()` walks
  `for_each_free_mem_range()`, which leaves reserved ranges out.
- Page flags: preserved pages are not marked reserved; the skipped
  `memmap_init_reserved_range()` is what calls `__SetPageReserved()`.
- `kho_init_pages()` and `kho_init_folio()`: run at restore, not at reserve
  time.
- Before the reserve: `kho_populate()` calls
  `memblock_set_kho_scratch_only()`; `memblock_free_all()` clears it.
- `kho_extend_scratch()`: called from `kho_memory_init_early()`; marks as
  scratch every `KHO_SCRATCH_EXT_BLKSIZE` block that holds no preserved memory
  and no node of the incoming radix tree.
- Comment in `kho_restore_page()`: names deserialize_bitmap(), which is not
  defined in this tree; `kho_preserved_memory_reserve()` writes the magic.

**Matching restore to preserve**

- Order: `kho_restore_page()` makes no order check of any kind; only
  `info.magic` is tested.
- Caller-side check: `kho_test_restore_data()` in `lib/test_kho.c` compares
  `folio_order()` of the result with the order it recorded itself.
- Reading before restore: preserved data is readable through `phys_to_virt()`
  before any restore call, as `memfd_luo_retrieve()` does with
  `struct memfd_luo_ser`.
- `kho_alloc_preserve()` memory: `kho_restore_folio()` also fits, since
  `kho_restore_free()` calls it and then `folio_put()`.
- **Unsafe usage**: `kho_restore_folio()` on a range from
  `kho_preserve_pages()`; it restores only the first block, as a compound page
  of that block's stored order, with no `MAX_PAGE_ORDER` check.
  - Safe: `kho_restore_pages()` with the preserved count, as
    `kho_restore_vmalloc()` does for blocks from `kho_preserve_vmalloc()`;
    `kho_restore_page()` picks `kho_init_pages()` from `is_folio`.
- **Unsafe usage**: `kho_restore_pages()` on a folio from
  `kho_preserve_folio()`; `kho_init_pages()` gives every page refcount 1 and
  sets up no compound page.
  - Safe: `kho_restore_folio()`, as `memfd_luo_retrieve_folios()` does;
    `kho_init_folio()` sets tail counts to 0 and calls `prep_compound_page()`.

**Unwinding a failed setup**

- Required order: `kho_remove_subtree()` before the blob is unpreserved or
  freed, and each unpreserve before its free.
- Blob versus data: no order is required; `kho_test_cleanup()` and
  `memfd_luo_unpreserve()` unpreserve the data first and the blob last.
- Full sequence: `prepare_kho_fdt()` in `mm/memblock.c` preserves the blob,
  adds it, preserves data, and unwinds with `kho_remove_subtree()`,
  `kho_unpreserve_pages()`, `put_page()`.
- Second full sequence, in source only: `kho_test_exit()` in `lib/test_kho.c`
  calls `kho_remove_subtree()`, then `kho_test_cleanup()`. It never runs,
  because `TEST_KEXEC_HANDOVER` is bool and the function is `__exit`, and it
  does not test whether `kho_test_save()` ran, so it does not show how to
  meet the rule in "Calling the API when disabled".
- `kho_test_preserve()` error path: has no `kho_remove_subtree()`, because
  `kho_add_subtree()` is its last step.
- luo_fdt_setup() is not in this tree; `luo_state_setup()` in
  `kernel/liveupdate/luo_core.c` has no `kho_remove_subtree()` either, because
  `kho_add_subtree()` is its last step that can fail.
- Failed `kho_add_subtree()`: it deletes its own node, so the caller only
  unpreserves and frees, as `kho_out_kexec_metadata()` does.
- `kho_remove_subtree()`: finds the node by the blob's physical address;
  returns void and does nothing when no node matches.
- debugfs: `kho_debugfs_blob_add()` keeps the blob pointer only under
  `CONFIG_KEXEC_HANDOVER_DEBUGFS`; otherwise it is a stub that returns 0.

## Subtrees, root FDT and ABI

**Adding a subtree**

- `kho_add_subtree()`: takes three arguments, `(const char *name, void *blob,
  size_t size)`; see `kernel/liveupdate/kexec_handover.c`.
- `blob`: any format; nothing checks that it is an FDT. `luo_state_setup()`
  adds a `struct luo_ser`, `kho_out_kexec_metadata()` a
  `struct kho_kexec_metadata`.
- `size`: stored as a `u64` for the next kernel and, under
  `CONFIG_KEXEC_HANDOVER_DEBUGFS`, used as the length of the debugfs file, so
  it must not exceed the preserved allocation.
- `name`: copied by `fdt_add_subnode()` and by `debugfs_create_blob()`; needed
  only for the duration of the call.
- Blob contents: may be rewritten in place until kexec; only the address and
  `size` are captured. `luo_session_serialize()` writes
  `luo_ser->sessions_pa` after the add.
- Return values: 0, `-EEXIST` (name already a child of the root),
  `-ENOMEM` (every other libfdt failure, including either `fdt_setprop()`;
  the new node is deleted first).
- `-EOPNOTSUPP`: returned by the stub in `include/linux/kexec_handover.h`
  without `CONFIG_KEXEC_HANDOVER`.
- No other errno: the body has no test for KHO being enabled and there is no
  finalized state.
- **Unsafe usage**: adding a blob whose pages are not preserved.
  - Unsafe: `kho_add_subtree()` preserves nothing; the next kernel reserves
    only what the radix tree lists, in `kho_mem_retrieve()`.
  - Safe: `kho_alloc_preserve()` first, as `luo_state_setup()` does.
  - Safe: `alloc_page()` then `kho_preserve_pages()`, as `prepare_kho_fdt()`
    does; `kho_preserve_folio()`, as `kho_test_preserve()` does.

**Retrieving a subtree**

- `kho_retrieve_subtree()`: takes `(const char *name, phys_addr_t *phys,
  size_t *size)`; `size` may be NULL, as `reserve_mem_kho_retrieve_fdt()`
  passes.
- `-EINVAL`: also returned when `KHO_SUB_TREE_SIZE_PROP_NAME` is missing or
  not 8 bytes long, even if `size` is NULL; `*phys` is already written then.
- `-ENOENT` for no incoming FDT is tested before the NULL test on `phys`.
- `-EOPNOTSUPP`: returned by the stub in `include/linux/kexec_handover.h`
  without `CONFIG_KEXEC_HANDOVER`.
- Mapping: every in-tree consumer uses `phys_to_virt()`; none calls
  `fdt_check_header()` on a sub-blob, only `kho_populate()` does, on the root.
- Struct blobs: check the returned size, then the version, before reading
  fields; see `luo_early_startup()` and `kho_in_kexec_metadata()`.
- FDT blobs: `fdt_node_check_compatible()` then a length test on each
  `fdt_getprop()`; see `reserve_mem_kho_revive()` and `kho_test_restore()`.
- Earliest read: once `kho_populate()` has run; `reserve_mem_kho_revive()`
  reads its blob from the `reserve_mem=` handler, before `kho_memory_init()`.
  `memblock_set_kho_scratch_only()` keeps early allocations off it.
- A consumer need not restore the blob: `reserve_mem_kho_retrieve_fdt()` and
  `kho_in_kexec_metadata()` leave it reserved.
- **Potentially unsafe usage**: freeing a retrieved blob.
  - Unsafe: with `CONFIG_KEXEC_HANDOVER_DEBUGFS`; `kho_in_debugfs_init()`
    creates a file for every incoming subnode that points at the blob, and no
    code removes entries from `kho_in.dbg`.
  - Safe: without `CONFIG_KEXEC_HANDOVER_DEBUGFS`, where
    `kho_in_debugfs_init()` is an empty stub in
    `kernel/liveupdate/kexec_handover_internal.h`.
  - Safe: copying the fields out and leaving the blob reserved, as
    `kho_in_kexec_metadata()` does.

**Root FDT**

- `KHO_FDT_COMPATIBLE`: `"kho-v4"`.
- Each subtree: one child node of the root, named by the caller, with two
  properties.

| Macro | Name | Written as | Reader requires |
|---|---|---|---|
| `KHO_SUB_TREE_PROP_NAME` | `"preserved-data"` | `phys_addr_t` | 8 bytes |
| `KHO_SUB_TREE_SIZE_PROP_NAME` | `"blob-size"` | `u64` | 8 bytes |

- `KHO_FDT_MEMORY_MAP_PROP_NAME`: one `u64`, the physical address of
  `kho_out.radix_tree.root`, a `struct kho_radix_node`; written once in
  `kho_out_fdt_setup()`.
- There is no struct khoser_mem_chunk and no KHO_FDT_SUB_TREE_PROP_NAME here.
- Byte order: CPU-native in the root FDT and in both in-tree sub-FDTs; values
  go in as raw bytes through `fdt_property()` and `fdt_setprop()`. None of
  this code calls `cpu_to_fdt64()`.
- Reads: `kho_get_mem_map_phys()` uses `get_unaligned()`;
  `kho_retrieve_subtree()`, `kho_remove_subtree()`, `kho_in_debugfs_init()`
  and `reserve_mem_kho_revive()` dereference the `fdt_getprop()` pointer.
- In-tree sub-FDTs: only `MEMBLOCK_KHO_FDT` (`prepare_kho_fdt()`) and
  `KHO_TEST_FDT` (`lib/test_kho.c`). The `LUO_KHO_ENTRY_NAME` and
  `KHO_METADATA_NODE_NAME` blobs are packed structs, not FDTs.
- memblock sub-FDT: one node per `reserve_mem` entry, named after it, with
  `"start"` and `"size"` written raw from `struct reserve_mem_table`
  (`phys_addr_t`); `include/linux/kho/abi/memblock.h` documents them as u64.
- Size limit: one page, and not only in the core. `setup_kho()` in
  `arch/x86/kernel/kexec-bzimage64.c` and `kho_add_chosen()` in
  `drivers/of/kexec.c` pass `PAGE_SIZE` as the FDT length to the next kernel.
- Root FDT full: `kho_add_subtree()` returns `-ENOMEM`.

**ABI versions and compatible strings**

- Macro to bump with each definition, and what a mismatch does:

| Header in `include/linux/kho/abi/` | Macro | Value | Checked in | On mismatch |
|---|---|---|---|---|
| `kexec_handover.h` | `KHO_FDT_COMPATIBLE` | `"kho-v4"` | `kho_populate()` | boots as a non-KHO boot |
| `block.h` | `KHO_FDT_COMPATIBLE` | `"kho-v4"` | `kho_populate()` | boots as a non-KHO boot |
| `luo.h` | `LUO_ABI_COMPATIBLE` | `"luo-v5"` | `luo_early_startup()` | `panic()` via `luo_restore_fail()` |
| `memfd.h` | `MEMFD_LUO_FH_COMPATIBLE` | `"memfd-v2"` | `luo_file_deserialize_one()` | `-ENOENT`; `luo_open()` then fails with `-EIO` |
| `memblock.h` | `MEMBLOCK_KHO_NODE_COMPATIBLE` | `"memblock-v1"` | `reserve_mem_kho_retrieve_fdt()` | region allocated afresh |
| `memblock.h` | `RESERVE_MEM_KHO_NODE_COMPATIBLE` | `"reserve-mem-v1"` | `reserve_mem_kho_revive()` | region allocated afresh |
| `kexec_metadata.h` | `KHO_KEXEC_METADATA_VERSION` | 1 | `kho_in_kexec_metadata()` | warning, metadata ignored |

- `luo.h`: one macro covers every struct in the file. There is no
  LUO_FDT_COMPATIBLE, LUO_FDT_SESSION_COMPATIBLE or LUO_FDT_FLB_COMPATIBLE.
- `LUO_ABI_COMPATIBLE`: stored in `luo_ser->compatible` and compared with
  `strncmp()`, not `fdt_node_check_compatible()`.
- `LUO_ABI_COMPAT_LEN`: derived from the string, so a longer string can
  change the layout of `struct luo_ser`.
- `KHO_KEXEC_METADATA_VERSION`: a `u32` in the struct, compared with `!=`; it
  is not a compatible string.
- `block.h`: the pairing with `KHO_FDT_COMPATIBLE` is stated only in its
  header comment; the only user of the blocks is LUO.
- `KHO_FDT_COMPATIBLE`: the `DOC:` comment in the same header shows "kho-v3"
  twice; the definition is `"kho-v4"`.
- `MEMFD_LUO_FH_COMPATIBLE`: the example in a comment in
  `include/linux/liveupdate.h` shows "memfd-v1"; the definition is
  `"memfd-v2"`.
- `__packed`: used by the structs in `luo.h`, `memfd.h`, `block.h` and
  `kexec_metadata.h`. The structs in `kexec_handover.h` are not `__packed`,
  and `DECLARE_KHOSER_PTR()` is a union of a `u64` and a pointer.
- `Documentation/core-api/kho/abi.rst` renders the header `DOC:` comments, so
  a stale value in a comment reaches the published ABI text.

**Changing the core**

- `CONFIG_KEXEC_HANDOVER=n`: stubs also live in
  `include/linux/kho_radix_tree.h` and `kernel/kexec_internal.h`, besides
  `include/linux/kexec_handover.h`.
- KHO options: `kernel/liveupdate/Kconfig`; `TEST_KEXEC_HANDOVER` and
  `LIVEUPDATE_TEST` are in `lib/Kconfig.debug`.
- Userspace memblock tests: `tools/testing/memblock/` compiles
  `mm/memblock.c` with empty `linux/kexec_handover.h` and
  `linux/kho/abi/memblock.h` and a `kho_scratch_overlap()` stub in
  `tools/testing/memblock/internal.h`. A new KHO call outside
  `#ifdef CONFIG_KEXEC_HANDOVER` needs a stub there.
- Documentation build: kernel-doc directives under `Documentation/` name
  `DOC:` titles and source files, for example in
  `Documentation/core-api/kho/abi.rst`,
  `Documentation/core-api/kho/index.rst` and
  `Documentation/core-api/liveupdate.rst`; renaming either breaks them.
- x86 decompressor: `process_kho_entries()` in
  `arch/x86/boot/compressed/kaslr.c` reads `struct kho_scratch` from
  `include/asm-generic/kexec_handover.h` and `struct kho_data` from
  `arch/x86/include/uapi/asm/setup_data.h`.
- EFI boot: `drivers/firmware/efi/efi-init.c` keeps only scratch regions when
  `is_kho_boot()` is true.
- Crash images: `kho_fill_kimage()` and `kho_locate_mem_hole()` skip
  `KEXEC_TYPE_CRASH`.
- Selftests: both `tools/testing/selftests/kho/` and
  `tools/testing/selftests/liveupdate/` exist; `vmtest.sh` in the first
  embeds its own kernel config.

## Scratch regions

**Count, size and pageblock type**

- Count: `nodes_weight(node_states[N_MEMORY]) + 2`, not the number of online
  nodes; the per-node loop is `for_each_node_state(nid, N_MEMORY)`, so a
  memoryless node gets no region.
- `kho_reserve_scratch()` runs only when `kho_in.scratch_phys` is 0, that is
  with no handover data or with handover data that was rejected:
  `kho_memory_init()` calls it then, and it returns at once when `kho_enable`
  is false.
- KHO boot: `kho_scratch` and `kho_scratch_cnt` are inherited from the
  previous kernel in `kho_populate()` and `kho_memory_init_early()`; the
  `kho_scratch=` sizes are then not used.
- Alignment and size rounding: `SCRATCH_ALIGNMENT_BYTES`
  (`PAGE_SIZE * MAX_ORDER_NR_PAGES`) in `kernel/liveupdate/kexec_handover.c`,
  not `CMA_MIN_ALIGNMENT_BYTES`; a `static_assert()` only requires it to be at
  least that.
- Default size: `scratch_scale` is 200 (percent), applied to
  `memblock_reserved_kern_size()` minus `memblock_reserved_hugetlb_size()`;
  see `scratch_size_update()` and `scratch_size_node()`.
- Default global size: the scaled total minus the lowmem size, not the scaled
  total.
- `kho_scratch=` explicit form: three comma-separated sizes, in the order
  lowmem, global, per-node; see `kho_parse_scratch_size()`.
- `kho_reserve_scratch()` does not call `memblock_mark_kho_scratch()`; the
  `MEMBLOCK_KHO_SCRATCH` flag is set by `kho_populate()` in the next kernel.
- Migrate type on a cold boot: `kho_init()` calls
  `init_cma_reserved_pageblock()` on every scratch pageblock, which sets
  `MIGRATE_CMA` and frees the pages to the buddy allocator; there is no
  kho_init_scratch_pages() and KHO does not call
  `set_pageblock_migratetype()`.
- `kho_init()` is an `fs_initcall`: on a cold boot, until it runs the regions
  are memblock-reserved and nothing is allocated from them.
- Migrate type on a KHO boot: `kho_init()` returns before that loop when a
  handover FDT exists; `kho_scratch_migratetype()` in
  `include/linux/kexec_handover.h` returns `MIGRATE_CMA` for scratch
  pageblocks when `mm/mm_init.c` initialises the memmap.

**Preserving memory inside scratch**

- `kho_scratch_overlap()`: defined in `kernel/liveupdate/kexec_handover.c`
  and built whenever `CONFIG_KEXEC_HANDOVER` is on; there is no
  kernel/liveupdate/kexec_handover_debug.c in this tree.
- Stub that returns `false`: in `include/linux/kexec_handover.h`, for
  `CONFIG_KEXEC_HANDOVER` off, not for `CONFIG_KEXEC_HANDOVER_DEBUG` off.
- Debug gate: `IS_ENABLED(CONFIG_KEXEC_HANDOVER_DEBUG)` in front of the call,
  in `kho_preserve_folio()` and `kho_preserve_pages()` only; without the
  option nothing rejects an overlapping preserve.
- On overlap both return `-EINVAL`; `kho_preserve_pages()` tests the whole
  range once, before the first key is added.
- There is no __kho_preserve_order(), xa_load_or_alloc() or new_chunk() here;
  `kho_radix_alloc_node()`, which allocates the tracking tree pages, does not
  call `kho_scratch_overlap()`.
- `kho_preserve_vmalloc()`: no check of its own; each `kho_preserve_pages()`
  call inside it checks, under the same gate.
  - Data page in scratch: returns `-EINVAL`.
  - Chunk page in scratch: `new_vmalloc_chunk()` returns `NULL`, so the caller
    sees `-ENOMEM`.
- `kho_alloc_preserve()` on overlap, with the option: `ERR_PTR(-EINVAL)`,
  passed up from `kho_preserve_folio()`.
- Callers outside the debug gate: `kho_scratch_migratetype()` (memmap init)
  and `memblock_alloc_hugetlb()` in `mm/memblock.c`; a change to
  `kho_scratch_overlap()` changes both.
- Regions covered: only the entries of `kho_scratch[]`; ranges that
  `kho_extend_scratch()` marks with `memblock_mark_kho_scratch()` are not in
  the array and are not tested.
- **Potentially unsafe usage**: preserving a folio that came from a movable
  allocation.
  - Unsafe: when nothing has moved the folio out of `MIGRATE_CMA` pageblocks;
    `alloc_flags_cma()` in `mm/page_alloc.c` lets movable allocations take
    scratch pages, and the next kernel overwrites scratch.
  - Safe: after `memfd_pin_folios()`, as `memfd_luo_preserve_folios()` in
    `mm/memfd_luo.c` does; `folio_is_longterm_pinnable()` rejects
    `MIGRATE_CMA`, so the pin migrates such folios first.
- **Potentially unsafe usage**: preserving memory that was allocated from
  memblock during boot.
  - Unsafe: on a KHO boot, when the allocation was made without testing
    `kho_scratch_overlap()`; `choose_memblock_flags()` limits memblock to
    `MEMBLOCK_KHO_SCRATCH` ranges until `memblock_free_all()`.
  - Safe: when the allocator retries while `kho_scratch_overlap()` is true,
    as `memblock_alloc_hugetlb()` does.

## Live Update Orchestrator

**Orchestrator overview**

- LUO state: a raw `struct luo_ser` (`include/linux/kho/abi/luo.h`), not an
  FDT; `luo_state_setup()` hands it to `kho_add_subtree()` under
  `LUO_KHO_ENTRY_NAME`.
- There is no LUO_FDT_KHO_ENTRY_NAME, LUO_FDT_COMPATIBLE, luo_fdt_setup() or
  struct luo_session_header_ser in this tree.
- ABI version: the `compatible` member of `struct luo_ser`, compared with
  `LUO_ABI_COMPATIBLE` in `luo_early_startup()`, which also rejects a blob
  shorter than `struct luo_ser`.
- `sessions_pa`: physical address of the first `struct kho_block_header_ser`
  in a chain of blocks of `struct luo_session_ser`; each session's files
  hang off `struct luo_file_set_ser` the same way
  (`kernel/liveupdate/kho_block.c`).
- `sessions_pa` is written only by `luo_session_serialize()`, and is 0 when
  there are no sessions; `luo_session_setup_outgoing()` at boot only records
  where to write it.
- `flbs_pa`: one preserved page, allocated at boot by
  `luo_flb_setup_outgoing()`.
- `liveupdate_enabled()`: false unless the `liveupdate` early parameter set
  `luo_global.enabled`; KHO being enabled is not enough.
- `luo_early_startup()`: clears `luo_global.enabled` when `kho_is_enabled()`
  is false.
- Disabled LUO: `liveupdate_ioctl_init()` does not register `/dev/liveupdate`.
- Incoming state: `liveupdate_early_init()`, an `early_initcall()`, calls
  `luo_early_startup()`.
- Any non-zero return of `luo_early_startup()` reaches `luo_restore_fail()`,
  which is `panic()`; this includes a compatible mismatch and a
  `kho_retrieve_subtree()` error other than `-ENOENT`.
- Sessions and files are not deserialized at boot: `luo_open()` calls
  `luo_session_deserialize()`, which does the work once and caches the
  result; on failure every open of `/dev/liveupdate` returns `-EIO`.
- Outgoing state: `luo_late_startup()`, a `late_initcall()`, calls
  `luo_state_setup()` only when `liveupdate_enabled()`; a failure clears
  `luo_global.enabled`.

**LUO sessions**

- Name length constant: `LIVEUPDATE_SESSION_NAME_LENGTH` in
  `include/uapi/linux/liveupdate.h`.
- `luo_session_create()`: returns `-EINVAL` for an empty name and for a name
  with no NUL within `LIVEUPDATE_SESSION_NAME_LENGTH` bytes.
- `luo_session_retrieve()`: validates nothing; it compares with `strncmp()`
  over the size of the name array, and a name that matches no incoming
  session returns `-ENOENT`.
- Session count: no LUO_SESSION_MAX in this tree; the bound is
  `KHO_MAX_BLOCKS` blocks per `struct kho_block_set`, past which
  `kho_block_add()` returns `-ENOSPC` and `kho_block_set_grow()` passes it
  up.
- `luo_session_insert()`: for the outgoing list it returns whatever
  `kho_block_set_grow()` returns, and grows before it checks for a duplicate
  name.
- Second retrieve of the same session: `-EINVAL`, from the test of
  `session->retrieved` in `luo_session_retrieve()`.
- Close after the update when `luo_session_finish_one()` fails:
  `luo_session_release()` returns the error without removing or freeing the
  session.
- That session stays on the incoming list with `retrieved` true and no file
  descriptor, so a later retrieve returns `-EINVAL` and nothing can finish
  it.

**Reboot hook**

- `kernel_kexec()` in `kernel/kexec_core.c`: calls `liveupdate_reboot()` when
  it holds the kexec lock, `kexec_image` is set and
  `kexec_image->preserve_context` is false.
- `kernel_kexec()` does not test `liveupdate_enabled()`; `liveupdate_reboot()`
  returns 0 itself when LUO is disabled.
- The call is before `kernel_restart_prepare()`; an error goes to the caller
  of `kernel_kexec()` and no shutdown step has run.
- Steps of `liveupdate_reboot()`: `luo_session_serialize()`, then
  `luo_flb_serialize()`, which returns void.
- kho_finalize is defined nowhere in this tree, and `liveupdate_reboot()`
  rewrites no error to `-EAGAIN`.
- Undo: `liveupdate_reboot()` undoes nothing itself; `luo_session_serialize()`
  is the only step that can fail and rolls back before it returns.
- `luo_session_serialize()` rollback: unfreezes the sessions frozen before
  the failing one, zeroes their serialized names, and releases both rwsems;
  `luo_session_deserialize()` takes no part.
- Locks on success: `luo_session_serialize_rwsem` stays write-held and is
  never released; the outgoing `rwsem` is released, and each
  `session->mutex` is dropped inside `luo_session_freeze_one()`.
- After a successful `liveupdate_reboot()`: `luo_session_create()`,
  `luo_session_retrieve()`, `luo_session_ioctl()` and
  `luo_session_release()` block on the read side of
  `luo_session_serialize_rwsem`.

**File handler callbacks:** The table lists what is easy to miss; see
`struct liveupdate_file_ops` in `include/linux/liveupdate.h` for the rest.

| Callback | Required | Kernel, caller | Easy to miss |
|---|---|---|---|
| `can_preserve` | yes | old, `luo_preserve_file()` | Handlers are tried in registration order; the first that returns true is used and no other is tried. |
| `get_id` | no | both, `luo_get_id()` | Key in `luo_preserved_files`; without it the key is the `struct file` pointer. A key already present makes `luo_preserve_file()` fail with `-EBUSY`. |
| `preserve` | yes | old, `luo_preserve_file()` | On failure LUO does not call `unpreserve`; `preserve` must undo its own partial work. |
| `unpreserve` | yes | old, `luo_file_unpreserve_files()` | Reached only from `luo_session_release()`; there is no per-file unpreserve ioctl. Newest file first. |
| `freeze` | no | old, `luo_file_freeze_one()` | Oldest file first. `kernel_kexec()` does not call `freeze_processes()` on this path, so other tasks still run. |
| `unfreeze` | no | old, `luo_file_unfreeze_one()` | Not called for the file whose `freeze` failed; that `freeze` must undo its own work. |
| `retrieve` | yes | new, `luo_retrieve_file()` | Called at most once per file, whether it succeeds or fails; `luo_file_finish()` does not call it. |
| `finish` | yes | new, `luo_file_finish_one()` | Newest file first. |

- `liveupdate_register_file_handler()`: does not test `owner`; returns
  `-EOPNOTSUPP` when `liveupdate_enabled()` is false and `-EEXIST` for a
  `compatible` already registered.
- Locks: `can_preserve`, `preserve` and `unpreserve` run under
  `session->mutex` without the mutex of the `struct luo_file`; `freeze`,
  `unfreeze`, `retrieve`, `can_finish` and `finish` hold both.
- New kernel: a handler must be registered before `/dev/liveupdate` is first
  opened; `luo_file_deserialize_one()` returns `-ENOENT` for an unknown
  `compatible`, and that fails the whole deserialization.

**Callback arguments**

- `struct liveupdate_file_op_args` in `include/linux/liveupdate.h`: the
  retrieve result is the member `retrieve_status`; it has no member named
  `retrieved`.
- Writes LUO keeps: `serialized_data` and `private_data` after `preserve`
  returns 0, `serialized_data` after `freeze` returns 0, `file` after
  `retrieve` returns 0; a write in any other callback is discarded.
- `retrieve` returning 0 with `file` unset: `luo_retrieve_file()` calls
  `get_file()` on it without a test.
- `retrieve` input: only `handler` and `serialized_data` are set.
- `serialized_data`: LUO carries only the u64 and passes the same value to
  `can_finish` and `finish`; it never frees or reads what the value names.
- Memory named by `serialized_data`: owned by the handler, and may be gone
  before `finish`; `memfd_luo_retrieve()` in `mm/memfd_luo.c` frees it on
  success and on failure.
- `retrieve_status`: set for `can_finish` and `finish` only, 0 in every other
  callback; the success value is 1.
- `file` in `can_finish` and `finish`: NULL unless `retrieve` succeeded.

**Retrieve and finish:** Models have this right; see `luo_retrieve_file()` in
`kernel/liveupdate/luo_file.c`.

**Finishing a file set**

- Never-retrieved file: `can_finish` and `finish` get `retrieve_status` 0 and
  `file` NULL.
- `luo_file_finish()` failure: `-EBUSY` from the first `can_finish` that
  returns false is the only error; `finish` returns void.
- File reference count: `luo_file_finish()` does not look at it.
- After `-EBUSY`: nothing was finished, and `LIVEUPDATE_SESSION_FINISH` can
  be tried again while the session file descriptor is open.
- Serialized file entries: freed through `kho_block_set_shrink()` and
  `kho_block_set_destroy()`, not by a direct `kho_restore_free()` call in
  `luo_file_finish()`.

## Model gaps

### Other mistakes models make

- Models take an incompatible incoming blob to be rejected cleanly. For LUO
  it is a `panic()`. `liveupdate_early_init()` does not call
  `liveupdate_enabled()`, and `luo_early_startup()` calls it only in the
  branch where `kho_is_enabled()` is false, so with KHO enabled the panic
  does not need `liveupdate=`.
- Models do not know that LUO has no exported symbols:
  `kernel/liveupdate/luo_file.c`, `kernel/liveupdate/luo_flb.c` and
  `kernel/liveupdate/kho_block.c` contain no `EXPORT_SYMBOL`, and
  `CONFIG_LIVEUPDATE_MEMFD` is bool, so a file handler has to be built in.
- Models do not know that the `struct kho_block_set` code in
  `kernel/liveupdate/kho_block.c` does no locking of its own, and that
  `kho_block_set_shrink()` frees blocks from the end of the chain.
- Models do not know that a failure to register the `KHO_METADATA_NODE_NAME`
  subtree fails `kho_init()` and clears `kho_enable`; see
  `kho_kexec_metadata_init()`.
- Models do not know the limits of `kho_preserve_vmalloc()`: it returns
  `-EOPNOTSUPP` for an area with flags outside
  `KHO_VMALLOC_SUPPORTED_FLAGS` and `-EINVAL` when `find_vm_area()` fails.
  `kho_unpreserve_vmalloc()` frees the chunk pages, not the area.
- Models do not know that `luo_preserved_files` is one xarray for all
  sessions, so the `-EBUSY` of `luo_preserve_file()` applies to a file
  preserved in any session; `memfd_luo_get_id()` uses the inode.
- Models do not know the FLB rules in `liveupdate_register_flb()`: all four
  `struct liveupdate_flb_ops` callbacks are required, the file handler must
  already be registered, and at most `LUO_FLB_MAX` FLBs exist.
  `liveupdate_flb_get_incoming()` takes a count that
  `liveupdate_flb_put_incoming()` drops; the last drop runs `finish`.
- Models take incoming sessions to be deserialized in early boot. Early boot
  only runs `kho_block_set_restore()` in `luo_session_setup_incoming()`;
  `luo_open()` returns `-EBUSY` to a second opener while the first still
  holds `/dev/liveupdate` open.
- Models take LUO to be on whenever Kexec HandOver is on. `memfd_luo_init()`
  ignores the `-EOPNOTSUPP` that `liveupdate_register_file_handler()` returns
  when `liveupdate_enabled()` is false.
- Models do not know that `kexec_calculate_store_digests()` in
  `kernel/kexec_file.c` skips the purgatory checksum for a non-crash image
  whenever `kho_is_enabled()`.
- Models trust comments that name things this tree does not define, for
  example LIVEUPDATE_IOCTL_PREPARE and LIVEUPDATE_STATE_UPDATED in
  `include/uapi/linux/liveupdate.h`.
