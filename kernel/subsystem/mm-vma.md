# MM VMA Operations

## SLAB_TYPESAFE_BY_RCU and VMA Recycling

Dereferencing a parent/owner pointer from a `SLAB_TYPESAFE_BY_RCU` object
after dropping the object's refcount causes use-after-free when the object has
been recycled to a different owner. The owner can exit and free its backing
structure in the window between the refcount drop and the dereference.

The VMA cache is created with `SLAB_TYPESAFE_BY_RCU` (see `vma_state_init()`
in `mm/vma_init.c`), which means a VMA's slab memory remains valid through an
RCU read-side critical section even after `vm_area_free()`, but the VMA can be
reallocated to a completely different `struct mm_struct` during that window.

**Per-VMA lock lookup protocol** (see `lock_vma_under_rcu()` and
`vma_start_read()` in `mm/mmap_lock.c`):
1. `mas_walk()` under `rcu_read_lock()` finds a VMA in the maple tree
2. `vma_start_read()` increments `vma->vm_refcnt`
3. If `vma->vm_mm != mm` (VMA was recycled), the refcount must be dropped --
   but `vma_refcount_put()` dereferences `vma->vm_mm` for `rcuwait_wake_up()`
4. The foreign `mm` must be stabilized with `mmgrab()` before calling
   `vma_refcount_put()`, then released with `mmdrop()` afterward

**REPORT as bugs**: Code paths in `lock_vma_under_rcu()`, `lock_next_vma()`,
or `vma_start_read()` that call `vma_refcount_put()` on a VMA whose `vm_mm`
does not match the caller's `mm` without first stabilizing the foreign `mm`
via `mmgrab()`.

## VMA Anonymous vs File-backed Classification

Using `vma->vm_file` to determine whether a VMA is file-backed causes
incorrect dispatch for VMAs that have a `vm_file` but are treated as
anonymous (e.g., private mappings of `/dev/zero`). This leads to BUG_ON
crashes, unaligned page offsets, or wrong code paths being taken.

**How VMA classification works** (see `include/linux/mm.h`):
- `vma_is_anonymous(vma)` returns `!vma->vm_ops` -- this is the canonical
  test for anonymous VMAs
- `vma_set_anonymous(vma)` sets `vma->vm_ops = NULL` but does NOT clear
  `vma->vm_file`
- A VMA can have `vma->vm_file != NULL` AND be anonymous (`vm_ops == NULL`)

**VMAs where `vm_file` is set but the VMA is anonymous:**
- Private mappings of `/dev/zero`: `mmap_zero_prepare()` in
  `drivers/char/mem.c` calls `vma_desc_set_anonymous(desc)` for private
  mappings, leaving `vm_file` pointing to the `/dev/zero` file. Shared
  mappings take a different path via `shmem_zero_setup_desc()` which sets
  `vm_ops = &shmem_anon_vm_ops`
- Any future caller of `vma_set_anonymous()` / `vma_desc_set_anonymous()` on a
  VMA created with a file reference (today nothing else does this;
  `set_vma_user_defined_fields()` says "Only /dev/zero should do this")

**Correct usage:**
- To choose between the anonymous and file fault, collapse or THP paths (that
  is, anything that depends on `vm_ops`): use `vma_is_anonymous(vma)`, NOT
  `vma->vm_file`
- To ask whether the VMA holds a file reference or is linked into
  `mapping->i_mmap` (rmap locking, uprobes, `fput()`): test `vma->vm_file`.
  That is the right test, and the private `/dev/zero` VMA *is* linked into the
  file's `i_mmap`. See `vma_prepare()` in `mm/vma.c`, `take_rmap_locks()` in
  `mm/mremap.c`, `copy_vma()` and `__zap_vma_range()`
- `!vma_is_anonymous(vma)` does not imply `vma->vm_file != NULL`: special
  mappings installed by `__install_special_mapping()` (vdso, vvar) have
  `vm_ops` set and no file. Check `vma->vm_file` before dereferencing it

**REPORT as bugs**: Code that uses `vma->vm_file` (or `!vma->vm_file`) to
decide something that really depends on `vm_ops`: which fault, collapse or THP
path to take, how to interpret `vm_pgoff`, or whether madvise or userfaultfd
treats the VMA as anonymous. The correct test there is `vma_is_anonymous()`.
Testing `vma->vm_file` to find out whether there is a file reference or an
`i_mmap` linkage is correct and must not be reported.

## VMA Split/Merge Critical Section

Page table structural changes performed outside the `vma_prepare()`/
`vma_complete()` critical section race with concurrent page faults (via VMA
lock) and rmap walks (via file/anon rmap locks). The result is use-after-free,
page table corruption, or re-establishment of state that was just torn down.

The VMA-modifying paths -- `__split_vma()`, `commit_merge()`, and
`vma_shrink()` in `mm/vma.c` -- share a critical section:

1. `vma_start_write()` (acquire per-VMA lock, before or at entry)
2. `vma_prepare()` (acquire file rmap `i_mmap_lock_write()` and anon_vma lock)
3. Page table structural changes: `vma_adjust_trans_huge()` in all three, and
   `hugetlb_split()` in `__split_vma()` only
4. VMA range update (`vm_start`/`vm_end`/`vm_pgoff`)
5. `vma_complete()` (release locks acquired in step 2)

`__split_vma()` additionally calls `vm_ops->may_split()` before this sequence.

**Rules:**
- `vm_ops->may_split()` must only validate whether the split is permitted
  (e.g., alignment checks). It must not modify page tables or other shared
  state, because it runs before the VMA and rmap locks are acquired
- Any page table unsharing, splitting, or teardown required by a VMA split
  must happen between `vma_prepare()` and `vma_complete()`, where the VMA
  write lock and file/anon rmap write locks prevent concurrent page table
  walks (except hardware walks and `gup_fast()`)
- When calling helpers that normally acquire their own locks (e.g.,
  `hugetlb_unshare_pmds()`), use a `take_locks=false` path and assert
  that the needed locks are already held (see `hugetlb_split()` in
  `mm/hugetlb.c`)

## Per-VMA Lock Exclusion via vma_start_write()

`mmap_write_lock()` alone excludes neither existing nor new per-VMA read
lockers. It only bumps `mm->mm_lock_seq`, and with only that done
`vma_start_read()` still succeeds: its sequence check fails only once
`vma_start_write(vma)` has copied `mm_lock_seq` into `vma->vm_lock_seq`.
`vma_start_write()` both waits for existing readers (the `vm_refcnt` wait in
`__vma_start_exclude_readers()`, during which `VM_REFCNT_EXCLUDE_READERS_FLAG`
refuses new ones) and makes later `vma_start_read()` attempts fail until
`mmap_write_unlock()` or downgrade. `Documentation/mm/process_addrs.rst` puts
it as "without a VMA write lock, page faults will run concurrent with whatever
you are doing". Page faults populate page tables at all levels, and
per-VMA-locked `MADV_DONTNEED` can clear PMDs and free PTE pages through
`CONFIG_PT_RECLAIM` (`pmd_clear()` in `zap_empty_pte_table()` /
`zap_pte_table_if_empty()`, then `pte_free_tlb()` in `zap_pte_range()`), so any
`mmap_write_lock()` holder that relies on page table state before
`vma_start_write()` races with per-VMA locked paths.

**`check_pmd_still_valid()` / `find_pmd_or_thp_or_none()`**: These functions
walk page tables (`mm_find_pmd()` → PGD→P4D→PUD→PMD) and then read the PMD
value via `pmdp_get_lockless(pmd)` in `check_pmd_state()`. A concurrent per-VMA
locked `MADV_DONTNEED` can reach `pmd_clear()` (in `zap_empty_pte_table()` or
`zap_pte_table_if_empty()`) and then `pte_free_tlb()` in `zap_pte_range()`
between the PMD read and subsequent use of the result — the check succeeds, the
caller proceeds assuming a valid PMD, but the PMD has been cleared and the PTE
page freed underneath it. Code that calls these functions before
`vma_start_write()` and then acts on the result (e.g., proceeding to
`pmd_lock()` + `pmdp_collapse_flush()` on the assumption the PMD is still
populated) is a bug — even though the PMD *pointer* remains valid (it points
into the PMD table page, which PT_RECLAIM does not free), the *value* and the
PTE page it pointed to are gone.

**REPORT as bugs**: Functions holding `mmap_write_lock()` that read page table
state (e.g. `check_pmd_still_valid()`, lockless PMD reads) and then act on it
as if it were stable or exclusive before calling `vma_start_write(vma)`. Access
that takes the page table lock and revalidates, tolerating concurrent faults as
it would under `mmap_read_lock()`, is fine (`register_for_each_vma()` in
`kernel/events/uprobes.c`). A read-only debug walk that takes no page table
lock but tolerates concurrent change is also not a bug (`ptdump_walk_pgd()` →
`walk_page_range_debug()`, which relies on the RCU protection in
`pte_offset_map()`). When a patch adds new per-VMA lock users (e.g., converting
a path from `mmap_read_lock()` to per-VMA lock), search with semcode
(grep_functions, find_callers) for `mmap_write_lock()` holders that access page
tables for the same VMA and verify each either calls `vma_start_write()` before
the access or falls under one of the exemptions above.

## VMA Flags Modification API

Key distinction: `vm_flags_set()` ORs (adds bits, never clears),
`vm_flags_reset()` replaces (sets to exact value); it only asserts the VMA
write lock, so the caller must take it. `vm_flags_init()` replaces without
locking (VMA not yet in tree). `vm_flags_clear()` removes specific bits.
`vm_flags_mod()` adds and removes in one operation. Only `vm_flags_set()`,
`vm_flags_clear()` and `vm_flags_mod()` call `vma_start_write()` themselves.
See `include/linux/mm.h`.

**Common mistake:** `vm_flags_set(vma, new_flags)` to replace flags -- because
it ORs, stale flags silently survive. Use `vm_flags_reset()` for exact
replacement. Stale `VM_WRITE`/`VM_MAYWRITE` creates security holes.

## File Reference Ownership During mmap Callbacks

mmap uses split ownership: `ksys_mmap_pgoff()` holds one file reference
(fput at end), VMA gets its own via `get_file()` in `__mmap_new_file_vma()`.
When a callback replaces the file (`f_op->mmap_prepare()` replacing
`desc->vm_file`, or legacy `f_op->mmap()` replacing `vma->vm_file`), the
replacement already carries its own reference.

**REPORT as bugs**: unconditional `get_file()` on a file that may have been
swapped by a callback -- the replacement gets a leaked extra reference. See
`map->file_doesnt_need_get` in `call_mmap_prepare()` in `mm/vma.c` and
`shmem_zero_setup()` in `mm/shmem.c`.

## Quick Checks

- **mmap_lock ordering**: Taking the wrong lock type deadlocks or corrupts the
  VMA tree. Write lock (`mmap_write_lock()`) for VMA structural changes
  (insert/delete/split/merge, modifying vm_flags/vm_page_prot; the one
  exception is `vma_set_atomic_flag()` for `VM_ATOMIC_SET_ALLOWED` flags, which
  needs only the mmap or per-VMA read lock). Read lock (`mmap_read_lock()`) for
  VMA lookup and read-only traversal; page faults run under it or under only
  the per-VMA read lock. See the "Lock ordering in mm" comment block at the top
  of `mm/rmap.c`
- **Failable mmap lock reacquisition**: `mmap_write_lock_killable()` /
  `mmap_read_lock_killable()` return `-EINTR` on kill. Ignoring the return
  means continuing without the lock. Check in retry loops and lock upgrade
  sequences. See `__get_user_pages_locked()` in `mm/gup.c`
- **VMA merge anon_vma propagation**: merging an unfaulted VMA with a faulted
  one requires `dup_anon_vma()` (see `vma_expand()` in `mm/vma.c`). Merge-time
  `anon_vma` property checks (e.g., `list_is_singular()` in
  `vma_is_fork_child()`, called from `is_mergeable_anon_vma()`) must apply to
  the VMA that **has** the `anon_vma`, not unconditionally to the destination
  -- the three cases (dst unfaulted/src faulted, dst faulted/src unfaulted,
  both faulted) are asymmetric. See `vma_is_fork_child()` in `mm/vma.c`
- **VMA interval tree uses pgoff, not PFN**: `mapping->i_mmap` is keyed by
  `vm_pgoff`; `vma_filebacked_address()` and `vma_anon_address()` in
  `mm/internal.h` expect a `pgoff_t` (file pgoff and anonymous pgoff
  respectively). Passing a raw PFN searches the wrong coordinate space.
  **REPORT as bugs**: raw PFN to `mapping_rmap_tree_foreach()`,
  `vma_filebacked_address()` or `vma_anon_address()`
- **VMA merge/modify error handling**: `vma_modify*()` return `ERR_PTR()` on
  failure; `vma_merge_new_range()` never does, it returns NULL and reports OOM
  only through `vmg_nomem()`. Either may return a different VMA, and the
  original VMA may be freed on success. On failure, `vmg->start/end/pgoff` may
  be mutated and not restored — save originals or check `vmg_nomem()`. See
  `madvise_update_vma()` in `mm/madvise.c` and `vma_modify()` in `mm/vma.c`
- **VMA flag ordering vs merging**: flags not in `VMA_IGNORE_MERGE_FLAGS` must
  be set in proposed `vm_flags` *before* `vma_merge_new_range()`. Setting flags
  post-merge via `vm_flags_set()` silently breaks future merges
  (`is_mergeable_vma()` compares the two flag sets with
  `vma_flags_diff_pair()`). See `ksm_vma_flags()` in `mm/ksm.c`
- **VMA merge side effects vs page table operations**: `vma_complete()`
  triggers `uprobe_mmap()` which installs PTEs. Callers that subsequently
  move/overwrite page tables must set `skip_vma_uprobe` in
  `struct vma_merge_struct` (see `mm/vma.h`), or orphaned PTEs leak memory
- **Fork-time VMA flag divergence**: `dup_mmap()` clears `VMA_LOCKED_MASK` (the
  `VM_LOCKED_MASK` bits) on the child VMA, and `dup_userfaultfd()` clears
  `__VM_UFFD_FLAGS` on it unless the parent's uffd context has
  `UFFD_FEATURE_EVENT_FORK`. Fork-time flag checks (e.g., `vma_needs_copy()`
  checking `VM_UFFD_WP`) must use the destination VMA, not the source. Combined
  mask checks must verify all flags have the same source-vs-destination
  semantics
- **VM_ACCOUNT preservation during VMA manipulation**: clearing `VM_ACCOUNT` on
  a surviving VMA (e.g., `MREMAP_DONTUNMAP`, partial unmap) leaks committed
  memory permanently — `do_vmi_munmap()` only uncharges VMAs with `VM_ACCOUNT`.
  Review `vm_flags_clear()` calls including `VM_ACCOUNT`, and the new-API
  spelling `vma_clear_flags(vma, VMA_ACCOUNT_BIT)` (see `mm/mremap.c`, which
  restores the bit afterwards)
- **VMA iteration on external mm_struct**: call
  `check_stable_address_space(mm)` after mmap lock, before traversal. When
  `dup_mmap()` fails after the tree was duplicated, the new mm's VMA tree is
  destroyed with `__mt_destroy()`, leaving it empty, and the mm is flagged
  `MMF_UNSTABLE` (an earlier failure leaves an empty tree without the flag).
  OOM reaper also sets `MMF_UNSTABLE`. See `unuse_mm()` in `mm/swapfile.c`
- **VMA operation results assigned to struct members**: `vma_merge_extend()`,
  `vma_merge_new_range()`, `copy_vma()` return NULL on failure. Assigning
  directly to a struct member (e.g., `vrm->vma = vma_merge_extend(...)`)
  clobbers the original VMA pointer before the NULL check. Assign to a local
  first, NULL-check, then update the struct member on success
- **VMA merge functions invalidate input on success**: `vma_merge_new_range()`,
  `vma_merge_existing_range()`, `vma_modify()` may free the original VMA on
  success. Callers must use the returned VMA, not the original. Discarding the
  return value and using the original is use-after-free
- **`vma_modify*()` error returns in VMA iteration loops**:
  `vma_modify_flags()` etc. return an `ERR_PTR()` on merge/split failure
  (`-ENOMEM`, or another errno such as `-EINVAL` from `may_split()`). Assigning
  back to a VMA loop variable without `IS_ERR()` check dereferences the error
  pointer. Even when the merge is best-effort (VMA unchanged on failure), the
  error return corrupts iteration. Check `IS_ERR()`. The only exemption is
  `give_up_on_oom`, settable only through `vma_modify_flags_uffd()`: when the
  range covers the whole VMA no split happens and a merge OOM is swallowed, so
  the call cannot fail. `userfaultfd_release_all()` relies on this through
  `userfaultfd_clear_vma()` and does not check. If a split is needed the error
  is still returned
- **VMA lock refcount balance on error paths**:
  `__vma_start_exclude_readers()` adds `VM_REFCNT_EXCLUDE_READERS_FLAG` to
  `vm_refcnt` then waits for readers. With `TASK_KILLABLE`
  (`vma_start_write_killable()`), the `-EINTR` path must call
  `__vma_end_exclude_readers()` to subtract the flag back. A leaked flag
  permanently blocks VMA detach/free
- **VMA addresses used as boolean flags**: `vm_start` can legitimately be zero,
  so `if (addr)` to mean "was this set" silently fails for zero-address VMAs.
  Use an explicit `bool` flag or direct comparisons. Same for any
  `unsigned long` address/offset that can be zero
- **Maple state RCU lifetime**: `struct ma_state` caches RCU-protected node
  pointers. After `rcu_read_unlock()`, invalidate with `mas_set()` or
  `mas_reset()` before reuse. Easy to miss when `vma_start_read()` drops RCU
  internally on failure. See `lock_vma_under_rcu()` in `mm/mmap_lock.c`
- **`struct mm_struct` flexible array sizing**: trailing flexible array packs
  cpumask and mm_cid regions. Static definitions whose cpumask or mm_cid area
  is ever accessed (`init_mm`, `efi_mm`) must use
  `MM_STRUCT_FLEXIBLE_ARRAY_INIT`; `tboot_mm` legitimately does not. Adding a
  new region requires updating `mm_cache_init()` (dynamic),
  `MM_STRUCT_FLEXIBLE_ARRAY_INIT` (static), and all static `struct mm_struct`
  definitions
- **Memfd file creation API layering**: calling `shmem_file_setup()` or
  `hugetlb_file_setup()` directly for memfd produces files missing
  `O_LARGEFILE`, fmode flags, and security init. Use `memfd_alloc_file()`.
  **REPORT as bugs**: memfd creation via direct `shmem_file_setup()` /
  `hugetlb_file_setup()` (non-memfd callers like DRM/SGX/SysV are fine)
- **VMA lock vs mmap_lock assertions**: `mmap_assert_locked(mm)` fires when
  only a VMA lock is held. Paths reachable under either lock should use
  `vma_assert_stabilised(vma)` unless they know which lock they hold
  (`assert_fault_locked()` branches on `FAULT_FLAG_VMA_LOCK`). With
  `CONFIG_PER_VMA_LOCK` it accepts the mmap lock (held by us under lockdep, by
  anyone otherwise) and otherwise falls back to `vma_assert_locked(vma)`, which
  asserts a VMA read or write lock and fires when only `mmap_read_lock()` is
  held. Without `CONFIG_PER_VMA_LOCK` both are `mmap_assert_locked()`. Legacy
  `mmap_assert_locked()` in page table walk/zap paths is likely incorrect
- **VM Committed Memory Accounting**: `security_vm_enough_memory_mm()` is not
  just a check -- on success it increments `vm_committed_as` via
  `vm_acct_memory()` (an inline in `include/linux/mman.h`), called from
  `__vm_enough_memory()` in `mm/util.c`. Every error path after a successful
  call must invoke `vm_unacct_memory()`. A leaked charge permanently inflates
  `vm_committed_as`, causing `-ENOMEM` under strict overcommit
  (`vm.overcommit_memory=2`)
