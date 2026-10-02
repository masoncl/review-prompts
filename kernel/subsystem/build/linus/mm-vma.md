# MM VMA Operations

## Main structures

### Objects and how they relate

- VMA linked list: none in this tree; `mm->mm_mt` is the only per-mm index of
  VMAs, and prev/next come from the `struct vma_iterator`.
- Build scope: `mm/vma.c` and `mm/vma_exec.c` are built only under
  `CONFIG_MMU`; `mm/vma_init.c` (allocation, duplication, freeing) is built
  for nommu too. See `mm/Makefile`.
- Two page offsets per `struct vm_area_struct`: `vm_pgoff`, and an anonymous
  page offset read with `vma_start_anon_pgoff()` (`include/linux/mm.h`) and
  written with `vma_set_anon_pgoff()` (`mm/vma.h`).
  - Pure anonymous VMA, under `CONFIG_MMU`: the two are equal; `do_mmap()` in
    `mm/nommu.c` sets only `vm_pgoff`.
- `vma_flags_t`: a bitmap type. `vma->flags` holds it, in a union with
  `const vm_flags_t vm_flags`, so both name the same storage.
  `struct vma_merge_struct` and `struct mmap_state` have a like union, but
  the bitmap member is named `vma_flags` and `vm_flags` is not const;
  `struct vm_area_desc` has only `vma_flags`.
- Attached and detached: the state of `vm_refcnt`, not tree membership.
  - `vms_gather_munmap_vmas()` marks VMAs detached while they are still in
    `mm->mm_mt`; they leave the tree later.
  - Without `CONFIG_PER_VMA_LOCK`: `vma_mark_attached()` and
    `vma_mark_detached()` are empty, `vma_is_attached()` returns true.
- `struct vma_munmap_struct` side tree: indexed by a counter, 0 to
  `vma_count` - 1, not by address.
- `struct vma_munmap_struct` on the `munmap()` path
  (`do_vmi_align_munmap()`): gather, clear the range in `mm->mm_mt`, then
  `vms_complete_munmap_vmas()` clears page tables and frees the VMAs.
- `struct vma_munmap_struct` on the `mmap()` path: `vms_clean_up_area()`,
  called from `__mmap_setup()`, clears page tables and calls `vma_close()`
  before any new VMA exists.
  - `vms_complete_munmap_vmas()`, called from `__mmap_complete()`, then only
    does the accounting and frees the old VMAs.
  - `vms->clear_ptes` records which side of that point the unmap is on;
    `vms_abort_munmap_vmas()` reattaches only while it is still true.
- `struct mmap_state`: embeds the `struct vma_munmap_struct` and its side
  tree (`vms`, `mas_detach`, `mt_detach`). It holds no
  `struct vma_merge_struct`; `VMG_MMAP_STATE()` builds one from it.
- `struct unmap_desc` (`mm/vma.h`): the range argument of `unmap_region()`,
  `unmap_vmas()` and `free_pgtables()`. It holds three separate limits: the
  VMA range to zap, the page table floor and ceiling to free, and the bound
  of the tree walk. Build it with `UNMAP_STATE()` or `unmap_all_init()`;
  `unmap_pgtable_init()` only re-aims an existing one, as `exit_mmap()` does
  before `free_pgtables()`.
- `struct vma_prepare`: not used by every bounds change.
  `expand_upwards()` and `expand_downwards()` take the anon_vma lock and
  call `anon_rmap_tree_pre_update_vma()` and
  `anon_rmap_tree_post_update_vma()` themselves.
- `struct unlink_vma_file_batch`: used by `free_pgtables()` in `mm/memory.c`
  to remove up to eight consecutive VMAs of one file from `i_mmap` under a
  single `i_mmap_lock_write()`.

## Where to look

**Core files**

| Job | File | Not where expected |
|---|---|---|
| Allocate, duplicate, free a VMA | `mm/vma_init.c` | `kernel/fork.c` holds none of it; built as `obj-y`, so `mm/nommu.c` uses it too |
| Split, merge, unmap, body of mmap | `mm/vma.c`, API in `mm/vma.h` | built only with `CONFIG_MMU`; `mmap_region()`, `__mmap_region()` and `do_brk_flags()` are here, not in `mm/mmap.c`; `mm/nommu.c` has its own static `split_vma()` |
| Stack setup for exec | `mm/vma_exec.c` | `relocate_vma_down()`, `create_init_stack_vma()`; `fs/exec.c` keeps the callers `setup_arg_pages()` and `bprm_mm_init()`; no shift_arg_pages() exists |
| mmap and brk syscalls, fork and exit of an mm | `mm/mmap.c` | `vm_mmap_pgoff()` is in `mm/util.c` |
| mmap lock, per-VMA lock | `include/linux/mmap_lock.h`, `mm/mmap_lock.c` | `vma_start_read()` is `static inline` in `mm/mmap_lock.c`, not in the header; `lock_mm_and_find_vma()` is in `mm/mmap_lock.c` |
| Userland tests | `tools/testing/vma/` | there is no tools/testing/vma/vma.c; see `main.c`, `shared.c`, `tests/merge.c`, `tests/mmap.c`, `tests/vma.c` |

**Entry points**

| Job | Start from | Easy to miss |
|---|---|---|
| Split | `vma_modify()` or `vms_gather_munmap_vmas()` in `mm/vma.c` | `split_vma()` and `__split_vma()` are both `static` in `mm/vma.c`; code outside that file gets a split only through the `vma_modify_flags()` family or an unmap, including the one `mmap_region()` does over existing mappings |
| Merge, existing VMA | `vma_modify()` | `vma_merge_existing_range()` is `static`; `vma_modify()` is its only caller in `mm/` |
| Merge, mremap copy | `vma_merge_copied_range()` in `mm/vma.c`, called from `copy_vma()` | moves `vmg->middle` to `vmg->copied_from`, then calls `vma_merge_new_range()` |
| Move a mapping | `do_mremap()` in `mm/mremap.c` | then `remap_move()`, `mremap_to()` or `mremap_at()`; `move_vma()` calls `copy_vma_and_data()`, which calls `copy_vma()` in `mm/vma.c` |

**State structures**

| Job | Structure | Easy to miss |
|---|---|---|
| What the hook asks the core to do after the VMA exists | `struct mmap_action` in `include/linux/mm_types.h` | embedded as `action` in `struct vm_area_desc`; `__mmap_region()` passes `&desc.action` to `__mmap_new_vma()` and `mmap_action_complete()` |
| An unmap: which VMAs go and the accounting | `struct vma_munmap_struct` in `mm/vma.h` | holds no tree; the detached VMAs are in a side tree reached through a separate `struct ma_state *mas_detach` passed beside it, on the stack in `do_vmi_align_munmap()` and in `struct mmap_state` for mmap |
| An unmap: page-table teardown range | `struct unmap_desc` in `mm/vma.h` | argument of `unmap_region()`, `unmap_vmas()` and `free_pgtables()`; set up by `UNMAP_STATE()`, `unmap_all_init()` or by hand in `vms_clear_ptes()` |

**Userland tests**

- `tools/testing/vma/main.c`: includes `mm/vma_init.c`, `mm/vma_exec.c` and
  `mm/vma.c` textually, then `tests/merge.c`, `tests/mmap.c`, `tests/vma.c`.
- `#include "vma_internal.h"` in a core file: still resolves to
  `mm/vma_internal.h`; its body is skipped because
  `tools/testing/vma/vma_internal.h`, included first through `shared.h`,
  defines the same guard `__MM_VMA_INTERNAL_H`.
- New include in `mm/vma_internal.h`: the test build never reads it; every
  symbol the core then uses must be supplied on the test side.
- Where test-side definitions go, under `tools/testing/vma/include/`:

| File | Holds |
|---|---|
| `stubs.h` | no-op versions, for example the mmap lock calls and `uprobe_mmap()` |
| `dup.h` | copies of kernel types and helpers that must match the kernel, for example `struct vm_area_struct` and `struct vm_area_desc`; `struct mm_struct` is a cut-down version |
| `custom.h` | versions altered for testing, for example `vma_start_write()` increments `vm_lock_seq`, and `struct anon_vma` has test fields |

- New field the core touches: add it to the test's copy of the struct, in
  `dup.h` for example for `struct vm_area_struct`; `struct anon_vma` is in
  `custom.h`.
- `mm/vma.h`: included unmodified by `shared.h` and has no `#include`;
  every type and helper it uses must be defined by the shim before it.
- New core `.c` file: add an `#include` to `main.c` and add the file to the
  prerequisites of the `main.o` rule in `tools/testing/vma/Makefile`.
- Kernel globals the core reads: defined by the test, for example
  `sysctl_max_map_count` in `main.c` and `stack_guard_gap` in `shared.c`.
- `CONFIG_` symbols: the shim defines `CONFIG_MMU` and
  `CONFIG_PER_VMA_LOCK`; `tools/testing/shared/shared.mk` generates a header
  that defines `CONFIG_64BIT` on a 64-bit build; the `Makefile` sets
  `NUM_VMA_FLAG_BITS` and `NUM_MM_FLAG_BITS` to 64; core code under a symbol
  the test build does not define is not compiled by the test.

## Flags

**Flag representation**

- Union in `struct vm_area_struct` (`include/linux/mm_types.h`): exactly two
  members, `const vm_flags_t vm_flags` and `vma_flags_t flags`.
- There is no __vm_flags member here, and no `ACCESS_PRIVATE()` on VMA flags
  outside `tools/testing/vma/`; the `vm_flags_set()` family writes through
  `&vma->flags`.
- `vma->flags` is not const: `vma->flags = x` compiles, and `mm/` does it (for
  example `__mmap_new_vma()` in `mm/vma.c`).
- `struct vm_area_desc`: has only `vma_flags_t vma_flags`; it has no
  `vm_flags` member, so `desc->vm_flags` does not compile.
- Bit numbers: type `vma_flag_t`, spelled only with the prefix `VMA_` and the
  suffix `_BIT`, for example `VMA_READ_BIT`; there is no VM_READ_BIT.
- `VM_PKEY_BIT0` to `VM_PKEY_BIT4`: masks, despite the name.
- Helper names, by the object they take (bits are a variadic list of
  `vma_flag_t` bit numbers such as `VMA_READ_BIT`, except the one-bit test):

| Object | one bit | any of | all of | set | clear |
|---|---|---|---|---|---|
| `vma_flags_t *` | `vma_flags_test()` | `vma_flags_test_any()` | `vma_flags_test_all()` | `vma_flags_set()` | `vma_flags_clear()` |
| `struct vm_area_struct *` | `vma_test()` | `vma_test_any()` | `vma_test_all()` | `vma_set_flags()` | `vma_clear_flags()` |
| `struct vm_area_desc *` | `vma_desc_test()` | `vma_desc_test_any()` | `vma_desc_test_all()` | `vma_desc_set_flags()` | `vma_desc_clear_flags()` |

- There is no vma_test_flags(), vma_test_all_flags() or vma_desc_test_flags().
- `_mask` suffix: every any/all/set/clear name above has a function with
  `_mask` appended that takes a `vma_flags_t` by value, for example
  `vma_set_flags_mask(vma, VMA_REMAP_FLAGS)`.
- Converters: `legacy_to_vma_flags()` and `vma_flags_to_legacy()` in
  `include/linux/mm_types.h`; the second returns word 0 only.
- Composite masks: some exist in both spellings, and the legacy one may be
  derived, as `VM_SPECIAL` is `vma_flags_to_legacy(VMA_SPECIAL_FLAGS)`; others
  have only the bitmap spelling, for example `VMA_REMAP_FLAGS`.
- Atomic single-bit access: `vma_set_atomic_flag()` and
  `vma_test_atomic_flag()`.
- Flag configured out: the legacy mask is `VM_NONE`, for example
  `VM_DROPPABLE`; some flags also have a bitmap mask macro that becomes
  `EMPTY_VMA_FLAGS`, for example `VMA_DROPPABLE`, tested with
  `vma_test_single_mask()`.
- **Potentially unsafe usage**: passing a `vma_flag_t` bit number of 32 or
  more to `mk_vma_flags()`.
  - Unsafe: in code that is also built for 32-bit; `NUM_VMA_FLAG_BITS` is
    `BITS_PER_LONG`, `vma_flags_set_flag()` does no range check, and for
    example `VMA_SEALED_BIT` is declared in every configuration.
  - Safe: in code built only for 64-bit, as `__mseal_range()` in
    `mm/mseal.c`; `mm/Makefile` builds it only under `CONFIG_64BIT`.
  - Safe: through the mask macro that is `EMPTY_VMA_FLAGS` when the flag is
    unavailable, as `VMA_UFFD_MINOR` in `include/linux/mm.h`;
    `CONFIG_HAVE_ARCH_USERFAULTFD_MINOR` is selected only on 64-bit.

**Flag helpers**

- Rows for `vm_flags_init()`, `vm_flags_reset()`, `vm_flags_set()`,
  `vm_flags_clear()`, `vm_flags_mod()` and `__vm_flags_mod()`: models have
  these right; see `include/linux/mm.h`. The rows below are the rest.

| Helper | Bits already set | VMA write lock |
|---|---|---|
| `vma_flags_reset_once()` | replaced; word 0 with `WRITE_ONCE()` | neither |
| `vma_set_flags()`, `vma_set_flags_mask()` | kept, new bits ORed in | neither |
| `vma_clear_flags()`, `vma_clear_flags_mask()` | kept, except those named | neither |
| direct `vma->flags = x` | replaced | neither |
| `vma_set_atomic_flag()` | kept, one bit set with `set_bit()` | neither; `vma_assert_stabilised()` |
| `vma_desc_set_flags()`, `vma_desc_clear_flags()` | kept, set or cleared in `desc->vma_flags` | neither; only the desc changes |

- There is no vm_flags_reset_once() here; `vma_flags_reset_once()` does that
  job, takes a `vma_flags_t *`, and has no assertion.
- Bitmap spelling of `vm_flags_reset()`: none that asserts; `mm/` assigns
  `vma->flags` after `vma_start_write()`, as `madvise_update_vma()` does.
- `vma_set_atomic_flag()`: accepts only bits in `VM_ATOMIC_SET_ALLOWED`
  (`VM_MAYBE_GUARD`); any other bit hits `WARN_ON_ONCE()` and is not set.
- Without `CONFIG_PER_VMA_LOCK`: `vma_start_write()` is an empty stub, so
  `vm_flags_set()`, `vm_flags_clear()` and `vm_flags_mod()` make no lock check
  at all; `vma_assert_write_locked()` becomes `mmap_assert_write_locked()`.
- With `CONFIG_PER_VMA_LOCK`: the mmap write lock assertions inside
  `vma_start_write()` are in `__vma_raw_mm_seqnum()` in
  `include/linux/mmap_lock.h` and in `__vma_start_exclude_readers()` in
  `mm/mmap_lock.c`.

**Changing flags**

- **Potentially unsafe usage**: changing flags with a helper that neither
  locks nor asserts: `vma_set_flags()`, `vma_set_flags_mask()`,
  `vma_clear_flags()`, `vma_clear_flags_mask()`, `vma_flags_reset_once()`, or
  a direct `vma->flags = x`.
  - Unsafe: on a VMA that is in the tree and that the caller has not
    write-locked; `vm_flags_reset()` asserts the same requirement with
    `vma_assert_write_locked()`.
  - Safe: after `vma_start_write()` under the mmap write lock, as
    `mprotect_fixup()`, `madvise_update_vma()` and `__mseal_range()` do.
  - Safe: on a VMA not yet inserted, as `create_init_stack_vma()` in
    `mm/vma_exec.c` and `__install_special_mapping()` do.
  - Safe: inside an `->mmap` hook called from `__mmap_new_file_vma()`, where
    the VMA is still detached, as `hugetlbfs_file_mmap()` does;
    `__mmap_new_vma()` calls `vma_iter_store_new()` only after the hook.
- **Unsafe usage**: `vm_flags_reset()` in an `->mmap` hook with no earlier
  write lock.
  - Unsafe: `__mmap_new_vma()` calls `vma_start_write()` only after the hook
    returns, so `vma_assert_write_locked()` warns, with `CONFIG_PER_VMA_LOCK`
    and `CONFIG_DEBUG_VM`.
  - Safe: `vm_flags_mod()`, `vm_flags_set()` or `vm_flags_clear()`, which lock
    first, as `mmap_vmcore()` in `fs/proc/vmcore.c` does.
  - Safe: `vma_start_write()` and then `vm_flags_reset()`, as
    `userfaultfd_set_ctx()` in `mm/userfaultfd.c` does.
- `remap_pfn_range()`: sets `VMA_REMAP_FLAGS` through `vma_set_flags_mask()` in
  `remap_pfn_range_prepare_vma()`; it does not call `vm_flags_set()` and for
  that write neither takes nor asserts the VMA write lock.
- `vma_modify_flags()`: takes a `vma_flags_t *` and, on a successful merge,
  writes the merged VMA's flags back through it, so sticky flags can be added;
  store the value from the pointer afterwards, not the value passed in.
- After `vma_modify_flags()`: callers lock and store themselves;
  `mprotect_fixup()` and `mlock_vma_pages_range()` use
  `vma_flags_reset_once()`, `madvise_update_vma()` assigns `vma->flags`. None
  of them calls `vm_flags_reset()`.
- New VMA in `mm/`: `__mmap_new_vma()` assigns `vma->flags`; `vma_init()`
  leaves the flags zero from its `memset()`. `vm_flags_init()` is used when
  copying, by `vm_area_init_from()` in `mm/vma_init.c`.
- `->mmap` hook and merging: after the hook `__mmap_new_file_vma()` copies
  `vma->flags` into `map->vma_flags`; no merge is attempted afterwards.
- `->mmap_prepare` hook: change `desc->vma_flags` with `vma_desc_set_flags()`
  or `vma_desc_clear_flags()`, as `secretmem_mmap_prepare()` does;
  `call_mmap_prepare()` copies the result into the mapping state before the
  merge attempt.
- There is no hugetlbfs_file_mmap_prepare() here, and `shmem_mmap_prepare()`
  changes no flags.
- Atomic exception: `vma_set_atomic_flag()` with `VMA_MAYBE_GUARD_BIT` may run
  under the mmap read lock or a VMA read lock, as `madvise_guard_install()` in
  `mm/madvise.c` does.

## Per-VMA locks and lookups

**Per-VMA lock functions**

- `vma_start_read()`: `static inline` in `mm/mmap_lock.c`, called only by
  `lock_vma_under_rcu()` and `lock_next_vma()`. Other files read-lock through
  those two, or under the mmap read lock with `vma_start_read_locked()` or
  `vma_start_read_locked_nested()`.
- Without `CONFIG_PER_VMA_LOCK`: `vma_start_read_locked()`,
  `vma_start_read_locked_nested()` and `lock_next_vma()` have no stub, so
  callers sit under `#ifdef`, for example `stack_map_lock_vma()` in
  `kernel/bpf/stackmap.c`.
- Keeping new readers out has two stages. While the writer waits,
  `__vma_start_exclude_readers()` holds `VM_REFCNT_EXCLUDE_READERS_FLAG` in
  `vm_refcnt`. After the wait `__vma_start_write()` writes `vm_lock_seq`, then
  `__vma_end_exclude_readers()` removes the flag, and from then on it is
  `vm_lock_seq` that makes `vma_start_read()` fail.
- Names: there is no __vma_enter_locked() or __vma_exit_locked() here;
  `__vma_start_exclude_readers()` and `__vma_end_exclude_readers()`, static in
  `mm/mmap_lock.c`, do that job.
- Names: the reader limit is `VM_REFCNT_LIMIT`; there is no VMA_REF_LIMIT.
  `VMA_LOCK_OFFSET` exists only in `tools/testing/vma/include/dup.h`; kernel
  code uses `VM_REFCNT_EXCLUDE_READERS_FLAG`.
- `vma_start_write_killable()` on a detached VMA (`vm_refcnt` 0): returns 0
  without waiting and still writes `vm_lock_seq`.
- `vma_start_write_killable()` returning `-EINTR`: the mmap write lock is still
  held, and VMAs write-locked earlier stay write-locked until
  `mmap_write_unlock()`.
- `dup_mmap()` in `mm/mmap.c` is the only caller of
  `vma_start_write_killable()` outside `tools/`: it jumps to `loop_out`, tears
  down the partly built child mm, and unlocks both mms at `out`.

**Locking assertions:** With `CONFIG_PER_VMA_LOCK`:

| Helper | mmap read only | mmap write only | VMA read | VMA write | Can fire when |
|---|---|---|---|---|---|
| `mmap_assert_locked()` | yes | yes | no | yes | always |
| `mmap_assert_write_locked()` | no | yes | no | yes | always |
| `vma_assert_write_locked()` | no | no | no | yes | `CONFIG_DEBUG_VM` |
| `vma_assert_locked()` | no | no | yes | yes | `CONFIG_DEBUG_VM` |
| `vma_assert_stabilised()` | yes | yes | yes | yes | `CONFIG_DEBUG_VM` |

- Path reachable under either lock: `vma_assert_stabilised()`. With a
  `struct vm_fault` in hand, `assert_fault_locked()` in `include/linux/mm.h`
  picks the assertion from `FAULT_FLAG_VMA_LOCK`.
- VMA write column: a VMA write lock implies the mmap write lock, so both mmap
  assertions pass under it.
- `mmap_assert_locked()` and `mmap_assert_write_locked()`: compiled in without
  any debug option. `rwsem_assert_held()` and `rwsem_assert_held_write()` use
  lockdep under `CONFIG_LOCKDEP`, otherwise a `WARN_ON()` on the rwsem state
  that any task's hold satisfies.
- `vma_assert_write_locked()`: `VM_WARN_ON_ONCE_VMA()`, a one-time warning, not
  `VM_BUG_ON_VMA()`. Without `CONFIG_DEBUG_VM` the condition is not evaluated,
  so the `mmap_assert_write_locked()` nested in `__vma_raw_mm_seqnum()` does
  not run either.
- `vma_assert_locked()` under `CONFIG_LOCKDEP`: lockdep only decides a pass
  (this task holds the read lock). The failing check is still
  `vma_assert_write_locked()`, so nothing fires without `CONFIG_DEBUG_VM`.
- `vma_assert_locked()` without `CONFIG_LOCKDEP`: passes whenever `vm_refcnt`
  is above 1, which any task's read lock causes.
- `vma_assert_stabilised()` without `CONFIG_LOCKDEP`: passes whenever any task
  holds the mmap lock, tested with `rwsem_is_locked()`.
- `vma_assert_attached()` and `vma_assert_detached()`: plain `WARN_ON_ONCE()`
  on `vma_is_attached()`, compiled in without debug options; empty stubs
  without `CONFIG_PER_VMA_LOCK`.
- `vma_assert_can_modify()`: passes on a detached VMA with no lock; on an
  attached VMA it is `vma_assert_write_locked()`.

**Detaching a VMA**

- `vma_mark_detached()`: inline in `include/linux/mmap_lock.h`. It drops the
  attach reference with `__vma_refcount_put_return()` and returns if the count
  is 0. Otherwise it calls `__vma_exclude_readers_for_detach()` in
  `mm/mmap_lock.c`.
- Slow path of `vma_mark_detached()`: `__vma_exclude_readers_for_detach()`
  uses `__vma_start_exclude_readers()` and `__vma_end_exclude_readers()`.
- Dropping the attach reference does not by itself stop new readers: while
  `vm_refcnt` is non-zero and `VM_REFCNT_EXCLUDE_READERS_FLAG` is not yet set,
  `vma_start_read()` can still increment. Those readers fail the `vm_lock_seq`
  check and drop the reference; the wait covers them too.
- `tear_down_vmas()` in `mm/mmap.c`: calls `vma_mark_detached()` with no
  `vma_start_write()` of its own. In `exit_mmap()` the write locks come from
  `free_pgtables()` in `mm/memory.c`, which calls `vma_start_write()` only when
  `mm_wr_locked` in `struct unmap_desc` is set.
- `vms_gather_munmap_vmas()` in `mm/vma.c`: calls `vma_start_write()` and then
  `vma_mark_detached()` on each VMA.

**Freeing a detached VMA**

- `vm_area_free()` in `mm/vma_init.c`: calls `kmem_cache_free()` at once. No
  `call_rcu()` is used for a VMA; only `SLAB_TYPESAFE_BY_RCU` on
  `vm_area_cachep` delays reuse of the memory by other types.
- `vma_mark_detached()`: waits for reader references, not for an RCU grace
  period; a reader may still hold the pointer after the free.
- `vm_area_cachep` has no constructor. `vm_refcnt` is written to 0 on every
  allocation: `vm_area_alloc()` through the `memset()` in `vma_init()`,
  `vm_area_dup()` through `vma_lock_init(new, true)`.
- That write loses no reader's increment: `vm_area_free()` asserts with
  `vma_assert_detached()` that the count is already 0, and
  `__refcount_inc_not_zero_limited_acquire()` does not raise a count of 0.
- `vm_freeptr`: the allocator's free pointer shares a union with `vm_start` and
  `vm_end` (`freeptr_offset` in `vma_state_init()`), so a free can overwrite
  only that union and not `vm_refcnt`, `vm_mm` or `vm_lock_seq`.
- **Potentially unsafe usage**: reading fields of a VMA found under RCU without
  a VMA read lock.
  - Unsafe: when the values are acted on with no later check that the mm was
    not write-locked meanwhile; the object may be freed or belong to another
    mapping.
  - Safe: take the lock first and recheck, as `lock_vma_under_rcu()` does.
  - Safe: bracket the reads with `mmap_lock_speculate_try_begin()` and
    `mmap_lock_speculate_retry()` and discard the result on retry, as
    `find_active_uprobe_speculative()` in `kernel/events/uprobes.c` does;
    `mmap_write_lock()` changes `mm_lock_seq` through
    `mm_lock_seqcount_begin()`.

**Lockless lookup guarantees**

- Guarantees, rechecks and the `NULL` return: models have this right; see
  `lock_vma_under_rcu()` and `vma_start_read()` in `mm/mmap_lock.c`.
- `vmf_anon_prepare()` with `anon_vma` unset under `FAULT_FLAG_VMA_LOCK`:
  `__vmf_anon_prepare()` in `mm/memory.c` returns `VM_FAULT_RETRY` only when
  `mmap_read_trylock()` fails. Otherwise it allocates under the mmap read lock
  and the fault goes on under the VMA lock.
- `vmf_anon_prepare()` returning `VM_FAULT_RETRY`: the wrapper in
  `mm/internal.h` has already called `vma_end_read()`.
- Fallback where the caller cannot block: `mmap_read_trylock()` and give up on
  failure, as `stack_map_lock_vma()` in `kernel/bpf/stackmap.c` does.

**VMA iterator after RCU unlock**

- `vma_start_read()`: returns with RCU held only on success. Every failure
  return has already called `rcu_read_unlock()`: `NULL`, `ERR_PTR(-EAGAIN)` and
  the `vm_mm` mismatch path. The caller must not unlock again.
- `lock_next_vma()`: entered with RCU held and returns with RCU held on every
  path. Inside, it drops and retakes RCU on the `-EAGAIN` retry, when the lock
  attempt fails, and when either check after locking fails.
- `lock_next_vma()` can sleep: the fallback
  `lock_next_vma_under_mmap_lock()` calls `mmap_read_lock_killable()` after one
  `rcu_read_unlock()`. Other RCU-protected pointers the caller loaded before
  the call are not protected across it.
- `lock_next_vma()` return values: a read-locked VMA, `NULL` at the end,
  `ERR_PTR(-EINTR)`, or `ERR_PTR(-EAGAIN)` when `vma_start_read_locked()` fails
  under the mmap lock. The comment in `include/linux/mmap_lock.h` lists only
  `-EINTR`; `proc_get_vma()` in `fs/proc/task_mmu.c` handles both.
- Iterator on return from `lock_next_vma()`: on every path that dropped RCU it
  has already called `vma_iter_set()`, to `vma->vm_end` after a successful
  fallback and to `from_addr` otherwise. A caller that stayed in the RCU
  section may call `lock_next_vma()` again with no reset.
- **Potentially unsafe usage**: stepping a `struct vma_iterator` that was
  walked in an RCU section the caller has since left.
  - Unsafe: when the next `vma_next()` or `lock_next_vma()` runs with no
    `vma_iter_set()`, `vma_iter_init()` or `mas_set()` since the new
    `rcu_read_lock()`; maple nodes are freed through `ma_free_rcu()` in
    `lib/maple_tree.c`, so the cached node may be gone.
  - Safe: reset right after retaking RCU, as `reacquire_rcu()` in
    `fs/proc/task_mmu.c` does with `locked_vma->vm_end`.
  - Safe: reset after switching to the mmap lock, as `fallback_to_mmap_lock()`
    in `fs/proc/task_mmu.c` does.
  - Safe: an iterator that is not used again, as in
    `query_vma_find_by_addr()` in `fs/proc/task_mmu.c`.

## Locks and page tables

**Per-VMA-lock-only paths**

- `MADV_DONTNEED` and `MADV_DONTNEED_LOCKED`: the one per-VMA-lock path that
  frees an installed table, an empty PTE table, under `CONFIG_PT_RECLAIM`.
- Call chain: `madvise_dontneed_single_vma()` sets `reclaim_pt` and calls
  `zap_vma_range_batched()`; `zap_pte_range()` in `mm/memory.c` clears the PMD
  in `zap_empty_pte_table()` or `zap_pte_table_if_empty()`, then calls
  `pte_free_tlb()`.
- There is no mm/pt_reclaim.c, try_get_and_clear_pmd() or try_to_free_pte()
  here, and no zap_page_range_single() or zap_page_range_single_batched();
  `zap_vma_range()` and `zap_vma_range_batched()` replace the last two.
- `reclaim_pt`: set only in `madvise_dontneed_single_vma()`; zaps from other
  per-VMA-lock callers use `zap_vma_range()`, which passes `NULL` details and
  frees no installed table, for example
  `tcp_zerocopy_vm_insert_batch_error()`, `binder_alloc_free_page()` and
  `madvise_guard_install()`.
- `CONFIG_PT_RECLAIM`: `def_bool y` in `mm/Kconfig`, on wherever
  `MMU_GATHER_RCU_TABLE_FREE` is set and `HAVE_ARCH_TLB_REMOVE_TABLE` is not.
- hugetlb VMA under `MADV_DONTNEED`: `__unmap_hugepage_range()` can clear a
  PUD entry through `huge_pmd_unshare()`
  (`CONFIG_HUGETLB_PMD_PAGE_TABLE_SHARING`); `__hugetlb_zap_begin()` takes
  `hugetlb_vma_lock_write()` and `i_mmap_lock_write()` for it.
- `get_lock_mode()` in `mm/madvise.c`: returns `MADVISE_VMA_READ_LOCK` for
  `MADV_GUARD_INSTALL`, `MADV_GUARD_REMOVE`, `MADV_DONTNEED`,
  `MADV_DONTNEED_LOCKED` and `MADV_FREE`.
- `MADV_COLD` and `MADV_PAGEOUT`: `MADVISE_MMAP_READ_LOCK`, never the per-VMA
  lock.
- `MADV_GUARD_INSTALL` under the VMA read lock: sets marker PTEs through
  `walk_page_range_vma_unsafe()`, and `walk_pmd_range()` allocates a missing
  PTE table with `__pte_alloc()`.
- `is_vma_lock_sufficient()`: also rejects an anonymous VMA with no
  `anon_vma` for `MADV_GUARD_INSTALL`; `try_vma_read_lock()` then takes the
  mmap read lock.
- `lock_next_vma()` users in `fs/proc/task_mmu.c`: maps, smaps and numa_maps
  share `m_start()`; maps and `query_vma_find_by_addr()` read VMA fields only.
- smaps and numa_maps under the VMA read lock: walk page tables read-only via
  `walk_page_vma()` with `PGWALK_VMA_RDLOCK_VERIFY` ops, picked by
  `get_smaps_walk_ops()`, `get_smaps_shmem_walk_ops()` and
  `get_show_numa_ops()`.
- `damon_va_walk_page_range()` in `mm/damon/vaddr.c`: walks under the VMA read
  lock with `PGWALK_VMA_RDLOCK_VERIFY` when the range fits one VMA that is
  not `VM_PFNMAP`.
- `bpf_iter_task_vma_find_next()` and `stack_map_lock_vma()` in `kernel/bpf/`:
  read VMA fields, no page-table access.

**mmap write lock and tables**

- `mmap_write_downgrade()`: calls `vma_end_write_all()` just as
  `mmap_write_unlock()` does, so every VMA write lock ends at a downgrade.
- `hugepage_vma_revalidate()`: tests `thp_vma_suitable_order()` with
  `PMD_ORDER` whatever order is collapsed, so the one VMA that
  `collapse_huge_page()` write-locks covers the whole PTE table.
- `collapse_huge_page()`: frees no page table; it deposits the PTE table with
  `pgtable_trans_huge_deposit()` at PMD order, and re-installs it with
  `pmd_populate()` at a smaller order or on failure.
- `collapse_huge_page()` takes an `order`; below PMD order it keeps
  `anon_vma_lock_write()` until the PMD is re-installed, at PMD order it drops
  it after `__collapse_huge_page_isolate()`.
- PTE lock in `collapse_huge_page()`: taken by `pte_offset_map_lock()` on the
  saved `_pmd`, after `tlb_remove_table_sync_one()`;
  `__collapse_huge_page_isolate()` runs with it held.
- There is no __replace_page() here; `__uprobe_write()` in
  `kernel/events/uprobes.c` changes the one PTE, under the PTE lock that
  `folio_walk_start()` took.
- `uprobe_write()`: can free a PTE table; when `__uprobe_write()` returns a
  positive value (unregister zapped the page and the file folio is
  PMD-mappable) it calls `collapse_pte_mapped_thp()`.
- Callers of `uprobe_write()` hold the mmap write lock: for example
  `register_for_each_vma()`, `unapply_uprobe()` and x86
  `arch_uprobe_optimize()` take it; none calls `vma_start_write()`.
- `ptdump_walk_pgd()`: write-locks `mm` and, when `mm` is not `init_mm`, also
  `init_mm`; `walk_page_range_debug()` asserts both.
- `ptdump_walk_pgd()` is read-only: the callbacks use `ptep_get()`,
  `pmdp_get()` and the like, and `walk_pte_range()` maps a user PTE table with
  `pte_offset_map()`, without the PTE lock.
- ptdump's mm: x86 walks `current->mm`, user range included
  (`ptdump_walk_pgd_level_debugfs()`, called from
  `arch/x86/mm/debug_pagetables.c`); write mode is needed for the reason
  under "Freeing page tables".
- **Potentially unsafe usage**: under the mmap write lock, clearing a PMD
  entry that points to a PTE table, with no `vma_start_write()` on the VMA.
  - Unsafe: when the table still holds entries or is put back later; a
    per-VMA-lock fault fills the empty PMD through `__pte_alloc()`, and
    `collapse_huge_page()` warns on `!pmd_none()` before `pmd_populate()`,
    under `CONFIG_DEBUG_VM`.
  - Unsafe: when the table is freed at once with `pte_free()`; a walker
    inside `pte_offset_map_lock()` still holds it.
  - Safe: after `vma_start_write()` and `anon_vma_lock_write()`, as
    `collapse_huge_page()` does.
  - Safe: without `vma_start_write()`, when the folio lock is held, every
    entry was cleared under the PTE lock, the PMD is cleared under the PMD and
    PTE locks, and the table goes to `pte_free_defer()`, as
    `try_collapse_pte_mapped_thp()` does; `pte_offset_map_lock()` in
    `mm/pgtable-generic.c` holds `rcu_read_lock()` and rechecks the PMD.

**Freeing page tables**

- `vms_complete_munmap_vmas()`: calls `mmap_write_downgrade()` first when
  `vms->unlock` is set, so `free_pgtables()` then runs under the mmap read
  lock; otherwise under the write lock.
- After the downgrade no VMA is write-locked; `vma_mark_detached()` left
  `vm_refcnt` at zero, so `vma_start_read()` fails, and
  `do_vmi_align_munmap()` cleared the range from the tree before that.
- Call path: `vms_clear_ptes()` fills a `struct unmap_desc` (`mm/vma.h`) and
  calls `unmap_region()`, which calls `unmap_vmas()` then `free_pgtables()`.
- `free_pgtables(tlb, unmap)`: floor is `pg_start`; ceiling is the next VMA's
  `vm_start`, or `pg_end` after the last VMA; `vms_clear_ptes()` sets
  `pg_start` and `pg_end` from `vms->unmap_start` and `vms->unmap_end`.
- There is no hugetlb_free_pgd_range() and no unlink_file_vma() here;
  `free_pgtables()` calls `free_pgd_range()` for hugetlb VMAs too, and
  `unlink_file_vma_batch_add()` with `unlink_file_vma_batch_final()`.
- `mm_wr_locked`: `free_pgtables()` calls `vma_start_write()` only when it is
  true; `UNMAP_STATE()` sets it true, `unmap_all_init()` false, and
  `exit_mmap()` sets it after `mmap_write_lock()`.
- Attached VMAs reach `free_pgtables()` only with the mmap write lock held and
  `mm_wr_locked` true: in `exit_mmap()` and in the failure path of
  `dup_mmap()` in `mm/mmap.c`.
- `__mmap_new_file_vma()` error path: also uses `UNMAP_STATE()` under the
  write lock, on a new VMA that is not yet in the tree.
- `free_pgd_range()`: takes no page-table lock; `free_pte_range()` does
  `pmd_clear()` and `pte_free_tlb()` bare.
- RCU delay of the freed table: only with `CONFIG_MMU_GATHER_RCU_TABLE_FREE`;
  without `CONFIG_MMU_GATHER_TABLE_FREE`, `tlb_remove_table()` queues the
  table as an ordinary page.
- **Unsafe usage**: under the mmap read lock, walking user page tables at an
  address without first finding an attached VMA that covers it.
  - Unsafe: `vms_complete_munmap_vmas()` frees the tables of an unmapped
    range under the mmap read lock, and `free_pte_range()` takes no
    page-table lock.
  - Safe: under the mmap write lock, as `ptdump_walk_pgd()` does;
    `walk_page_range_debug()` asserts it.
  - Safe: after a VMA lookup under the lock, as
    `try_collapse_pte_mapped_thp()` does with `vma_lookup()` before
    `find_pmd_or_thp_or_none()`; the unmapped range has no VMA in the tree.

## Mapping a region

**mmap phases**

- `struct vm_area_desc`: declared on the stack of `__mmap_region()` with
  `vm_ops = &vma_dummy_vm_ops` and `action.type = MMAP_NOTHING`;
  `set_desc_from_map()` fills the range, `pgoff`, `vm_file`, `vma_flags` and
  `page_prot` as the last step of `__mmap_setup()`.
- Successful `vma_merge_new_range()`: skips only `__mmap_new_vma()` (so no
  `mmap` hook) and `mmap_action_complete()`.
- After the merge or `__mmap_new_vma()`, in order:
  `set_vma_user_defined_fields()` (file with `mmap_prepare` only), then
  `__mmap_complete()`, then `mmap_action_complete()` (file with
  `mmap_prepare` and a newly allocated VMA only).
- `have_mmap_prepare`: computed once from the file passed to
  `__mmap_region()`, before any hook can replace the file.
- `mmap` hook test in `__mmap_new_file_vma()`: `!map->file->f_op->mmap`, on
  the file as it stands after `mmap_prepare`; the call goes `mmap_file()` →
  `vfs_mmap()`.
- `vfs_mmap()` in `include/linux/fs.h`: calls `compat_vma_mmap()` instead of
  `f_op->mmap` when the file it is given has `mmap_prepare`; a stacked `mmap`
  hook reaches this, for example `backing_file_mmap()`.
- `compat_vma_mmap()` in `mm/util.c`: runs `mmap_prepare` while the VMA
  already exists, on a desc built by `compat_set_desc_from_vma()`, then
  applies it with `compat_set_vma_from_desc()` and completes the action at
  once with `is_compat` true.

**mmap hook fields**

- `desc->file`: input only; the replaceable file is `desc->vm_file`.
- `enum mmap_action_type` in `include/linux/mm_types.h`: five values;
  besides nothing, PFN remap and I/O remap there are `MMAP_SIMPLE_IO_REMAP`
  (`mmap_action_simple_ioremap()`) and `MMAP_MAP_KERNEL_PAGES`
  (`mmap_action_map_kernel_pages()`).
- `mmap_action_prepare()`: runs inside `call_mmap_prepare()` before the
  copy-back and edits the desc itself: `remap_pfn_range_prepare()` sets
  `VMA_REMAP_FLAGS` and may write `desc->pgoff`;
  `map_kernel_pages_prepare()` sets `VMA_MIXEDMAP_BIT`.
- I/O remap types: `mmap_action_prepare()` rewrites `MMAP_IO_REMAP_PFN` and
  `MMAP_SIMPLE_IO_REMAP` to `MMAP_REMAP_PFN`; `mmap_action_complete()` warns
  and fails with `-EINVAL` if it still sees either.
- `struct mmap_action`: has no success hook and no error hook.
- `error_override` in `struct mmap_action`: replaces the error returned from
  a failed action or a failed `mapped` when not called from the compat path;
  `check_mmap_action()` rejects a value that is not an error code.
- `mapped` in `struct vm_operations_struct`: the per-VMA callback;
  `call_vma_mapped()` in `mm/util.c` calls it from `mmap_action_finish()`
  after the action succeeds, also for `MMAP_NOTHING`.
- `hide_from_rmap_until_complete`: `__mmap_new_vma()` passes it to
  `vma_link_file()` as `hold_rmap_lock`, and `vma_link_file()` then returns
  with the file's `i_mmap_rwsem` still held for write;
  `maybe_rmap_unlock_action()` in `mm/internal.h`, called from
  `mmap_action_finish()`, releases it; `compat_vma_mmap()` forces it to
  false.

**Replacing the file in hooks**

- Old file in `mmap_prepare` called from `call_mmap_prepare()`: mm core holds
  no VMA reference on it when the hook runs, so nothing is dropped; the
  caller's reference stays.
- Handover in `call_mmap_prepare()`: `file_doesnt_need_get` is set only after
  both the hook and `mmap_action_prepare()` returned 0; if either fails, core
  drops no reference on the new file.
- `compat_set_vma_from_desc()` in `mm/vma.h`: installs a changed
  `desc->vm_file` with `vma_set_file()`, which takes its own reference; the
  hook's reference is not consumed on this path.
- After a successful `mmap` hook: `map->file = vma->vm_file`, so the rest of
  `__mmap_region()` uses the new file.
- `vma_set_file()` in `mm/util.c`: calls `fput()` on the old `vma->vm_file`
  without a NULL test, so the VMA must already have a file.
- **Unsafe usage**: `mmap_prepare` stores in `desc->vm_file` a file that an
  adjacent VMA may already map.
  - Unsafe: `is_mergeable_vma()` then allows the merge, and no code on the
    merge path drops the handed-over reference.
  - Safe: a newly created file, as `shmem_zero_setup_desc()` in `mm/shmem.c`
    stores; no existing VMA has it as `vm_file`.
- **Unsafe usage**: `mmap_prepare` stores in `desc->vm_file` a file whose
  `f_op->mmap` is set and can fail.
  - Unsafe: on that failure `__mmap_new_file_vma()` does
    `fput(vma->vm_file)` and `abort_munmap` does `fput(map.file)` on the same
    file.
  - Safe: a shmem file, as `shmem_zero_setup_desc()` stores;
    `shmem_file_operations` sets only `mmap_prepare`, so
    `__mmap_new_file_vma()` returns before any hook.
- **Potentially unsafe usage**: assigning `vma->vm_file` directly in an
  `mmap` hook.
  - Unsafe: when the hook returns with `vma->vm_file` not holding exactly one
    reference for the VMA, or with the core's reference on the old file
    neither dropped nor kept for a later `fput()`; `__mmap_new_file_vma()`
    puts the installed file on failure and `remove_vma()` puts it on unmap.
  - Safe: `vma_set_file()`, as `dma_buf_mmap()` does.
  - Safe: `fput()` the old file and install a new file's creation reference,
    as `shmem_zero_setup()` does.
  - Safe: `get_file()` the new file and keep the old file's reference until
    `close`, dropping it at once if the hook fails, as `coda_file_mmap()`
    does with `coda_vm_close()`.

**Anonymous VMAs with a file**

- `/dev/zero` in `drivers/char/mem.c`: there is no mmap_zero() function and
  no success hook; `mmap_zero_prepare()` calls `vma_desc_set_anonymous()` for
  a private mapping, and `set_vma_user_defined_fields()` then calls
  `vma_set_anonymous()`.
- Default `vm_ops`: `vma_init()` and the desc in `__mmap_region()` both start
  with `&vma_dummy_vm_ops`; a hook gets an anonymous VMA only by storing
  NULL.
- Inside `__mmap_new_vma()`: a VMA for a file with `mmap_prepare` still has
  `vma_dummy_vm_ops`, so `vma_is_anonymous()` is false there even for
  private `/dev/zero`; it becomes true in `set_vma_user_defined_fields()`.
- `vma_link_file()`: tests only `vma->vm_file`, so a private `/dev/zero` VMA
  is in the file's `i_mmap` tree; `__mmap_complete()` calls `uprobe_mmap()`
  on it for the same reason.
- `vm_pgoff` of a private `/dev/zero` VMA as `__mmap_region()` creates it:
  the file offset passed to `mmap()`, not `vm_start >> PAGE_SHIFT`; the
  virtual offset is kept separately and read with `vma_start_anon_pgoff()`.
- **Potentially unsafe usage**: treating `vma_is_anonymous()` as "no file and
  `vm_pgoff` is the virtual page offset".
  - Unsafe: for a private `/dev/zero` VMA, where `vm_file` is set and
    `vma_start_pgoff()` returns a file offset.
  - Safe: test `vma_is_anonymous(vma) && !vma->vm_file`, as
    `assert_sane_pgoff()` in `mm/vma.h`, `linear_anon_page_index()` in
    `include/linux/pagemap.h` and `dontunmap_complete()` in `mm/mremap.c` do.
  - Safe: use `vma_start_anon_pgoff()` or `linear_anon_page_index()` for the
    anonymous offset.
- **Potentially unsafe usage**: dereferencing `vma->vm_file` after testing
  only `vma_is_anonymous()`.
  - Unsafe: when no earlier test rejected a VMA with a NULL `vm_file`; a
    non-anonymous VMA may have one, since `vma_is_anonymous()` reads only
    `vm_ops`; for example a VMA from `__install_special_mapping()`.
  - Safe: test `vma->vm_file` itself before the dereference, as
    `page_address_in_vma()` in `mm/rmap.c` does.
  - Safe: when the callers already rejected a non-anonymous VMA with no
    file, as `collapse_single_pmd()` in `mm/khugepaged.c`; its callers pass
    only a VMA that `__thp_vma_allowable_orders()` accepted, which for a
    non-anonymous VMA with `TVA_KHUGEPAGED` or `TVA_FORCED_COLLAPSE` requires
    `shmem_file()` or `file_thp_enabled()`, and both test `vm_file`.

**Mapping over existing mappings**

- Point of no return: `vms_clean_up_area()`, which `__mmap_setup()` calls
  after its last failure return; not `vms_complete_munmap_vmas()` in
  `__mmap_complete()`.
- Failure after `__mmap_setup()` returned 0 (`mmap_prepare`,
  `mmap_action_prepare()`, `vm_area_alloc()`, `vma_iter_prealloc()`, the
  `mmap` hook, `shmem_zero_setup()`): the old mappings are gone and a gap is
  left.
- The gap: `vms_abort_munmap_vmas()` stores NULL over `vms->start` to
  `vms->end - 1`, which is the whole requested range.
- `reattach_vmas()`: only calls `vma_mark_attached()` on each VMA and
  destroys the side tree; it changes no flags and no `locked_vm`, because
  gathering only summed the counters into `struct vma_munmap_struct`.
- `vms_gather_munmap_vmas()` failure: it reattaches on its own error labels;
  `__mmap_setup()` then sets `vms->nr_pages = 0`, so
  `vms_abort_munmap_vmas()` returns at its first test.
- Splits at the range edges: `__split_vma()` in `vms_gather_munmap_vmas()` is
  not undone by any failure path, including the ones that reattach.
- Failure in `mmap_action_complete()`, including an error from the `mapped`
  callback: `mmap_action_finish()` unmaps the new VMA with `do_munmap()`; the
  old VMAs were already freed in `__mmap_complete()`, so a gap results.

**Undoing a failed mmap**

- `__mmap_setup()` failure: the only jump straight to `abort_munmap`.
- `call_mmap_prepare()` failure: goes to `unacct_error`, like a
  `__mmap_new_vma()` failure, so the charge from `__mmap_setup()` is
  released.
- `abort_munmap`: before `vms_abort_munmap_vmas()` it does `fput(map.file)`
  when `map.file_doesnt_need_get` is set.
- Where a step's undo lives: state that outlives the helper is recorded in
  `struct mmap_state` and released at a label (`charged`,
  `file_doesnt_need_get`); anything else is released by the helper before it
  returns, as the `free_iter_vma` and `free_vma` labels of `__mmap_new_vma()`
  do.
- Last jump to the labels: the `__mmap_new_vma()` failure; nothing after the
  VMA is inserted reaches them.
- A `mmap` hook that fails: must release what it took itself; core calls no
  callback, it drops the file reference, clears the page tables
  (`unmap_region()` in `__mmap_new_file_vma()`) and frees the VMA.

## vm_ops callbacks

**Callback timing**

- `struct vm_operations_struct`: defined in `include/linux/mm.h`.
- `mapped`, `may_split`, `mremap` and `mprotect` return `int`; `open` and
  `close` return `void`.

| Callback | Called from | When | Locks | Failure |
|---|---|---|---|---|
| `mapped` | `call_vma_mapped()` in `mm/util.c`, via `mmap_action_complete()` | file has `mmap_prepare` and `__mmap_region()` allocated a new VMA (not on merge); after the VMA is in the tree, after `__mmap_complete()` and after the mmap action succeeded | mmap write lock, VMA write-locked | `mmap_action_finish()` calls `do_munmap()` on the new VMA, so `close` runs; mmap returns the error or `action->error_override` |
| `may_split` | `__split_vma()`; also `prep_move_vma()` in `mm/mremap.c` | before anything is allocated or copied | mmap write lock; VMA not necessarily write-locked | the split, or the whole mremap move |
| `mremap` | `copy_vma_and_data()` in `mm/mremap.c` | after `move_page_tables()` moved the full length | mmap write lock | page tables moved back, new range unmapped, mremap fails |
| `mprotect` | `do_mprotect_pkey()` | per VMA, before `mprotect_fixup()` | mmap write lock | loop stops; VMAs already changed stay changed |

- `mapped` from `__compat_vma_mmap()` (`is_compat`): on failure nothing is
  unmapped; the error returns to the legacy `mmap` hook that called it.
- `mapped` receives no VMA: it gets the range, `pgoff`, file and a pointer
  through which it may replace `vm_private_data`.
- `prep_move_vma()`: calls `may_split` once for each end of the moved range
  that lies inside the VMA.
- `may_split` in `__split_vma()`: `vma_start_write()` on both VMAs comes after
  `open`; `mprotect_fixup()` and `vms_gather_munmap_vmas()` write-lock the VMA
  only after the split.
- `mremap`: the test is on `vm_ops` of the old VMA, the argument is the new
  VMA, which is an existing neighbour when `copy_vma()` merged.
- There is no vma_dup() here; `vm_area_dup()` in `mm/vma_init.c` makes the copy
  that `open` is called on.
- `open` in `dup_mmap()` (`mm/mmap.c`): after `vma_iter_bulk_store()`, before
  the file rmap insert and before `copy_page_range()`.
- `close` from `vms_clean_up_area()`: when a new mapping overwrites old VMAs,
  `__mmap_setup()` closes the old VMAs before the new file's `mmap_prepare` or
  `mmap` hook runs.
- `close` from `vms_complete_munmap_vmas()`: with `vms->unlock` (for example
  the munmap syscall) the mmap lock is already downgraded to read.

**open and close pairing**

- `mmap_prepare` files: the hook has no VMA; per-VMA setup belongs in
  `mapped`, which the core calls once for a newly allocated VMA.
- `mapped` in `vm_ops` that a legacy `mmap` hook assigns to `vma->vm_ops`
  itself: never called, and no error is raised; `call_vma_mapped()` is reached
  only from `mmap_action_complete()`, which a legacy hook reaches only through
  `compat_vma_mmap()` or `__compat_vma_mmap()`, as `uio_mmap()` does.
- Legacy `mmap` hook returns 0, when the file passed to `__mmap_region()` has
  no `mmap_prepare`: nothing later in `__mmap_region()` can fail, so the first
  `close` for that VMA comes from an unmap, not from an mmap error path.
- Legacy `mmap` hook returns an error: `mmap_file()` in `mm/internal.h`
  installs `vma_dummy_vm_ops`, so `close` is not called.
- **Unsafe usage**: taking a reference or allocating per-mapping state that
  `close` is to release, in the `mmap_prepare` hook.
  - Unsafe: after the hook returns 0, `__mmap_region()` may merge the range
    into a neighbour or fail in `__mmap_new_vma()`; neither path calls `close`
    or any other callback.
  - Safe: take it in `mapped`, as `tcmu_vma_mapped()` and `afs_mapped()` do.
- **Potentially unsafe usage**: a `close` that assumes `mapped` succeeded.
  - Unsafe: when `mapped` can return an error or `mmap_prepare` sets an mmap
    action; on either failure under `__mmap_region()`, `mmap_action_finish()`
    calls `do_munmap()` and `remove_vma()` reaches `close` with the `vm_ops`
    still installed.
  - Safe: when `mapped` always returns 0 and no action is set, as
    `afs_mapped()` with `afs_file_mmap_prepare()`.
- **Potentially unsafe usage**: `mapped` storing a per-VMA object through its
  `vm_private_data` argument.
  - Unsafe: when the mapping can merge at mmap time;
    `set_vma_user_defined_fields()` then overwrites `vm_ops` and
    `vm_private_data` of the VMA merged into, and `mapped` is not called.
  - Safe: when `mmap_prepare` sets a flag in `VMA_SPECIAL_FLAGS`, which
    `vma_merge_new_range()` refuses to merge; `remap_pfn_range_prepare()` sets
    `VMA_REMAP_FLAGS` for the remap actions.

**close and merging**

- `vma_complete()` on a removed VMA: `__remove_shared_vm_struct()` if
  file-backed, then `vma_mark_detached()`, `uprobe_munmap()` and `fput()` if
  file-backed, `unlink_anon_vmas()`, `mpol_put()`, `vm_area_free()`.
- `vma_complete()` and `commit_merge()`: no check for `close` on the VMA they
  remove.
- `vma_expand()`: its only check is
  `VM_WARN_ON_VMG(remove_next && !can_merge_remove_vma(next), vmg)`, which is
  compiled out without `CONFIG_DEBUG_VM` and does not stop the removal.
- **Unsafe usage**: calling `vma_expand()` with `vmg->next` set,
  `vmg->target != vmg->next` and `vmg->end == vmg->next->vm_end` without
  testing `next` first.
  - Safe: test `can_merge_remove_vma()` and shrink `vmg->end` when it fails,
    as `vma_merge_new_range()` does.
  - Safe: leave `vmg->next` unset, as `relocate_vma_down()` in
    `mm/vma_exec.c` does.
  - Safe: `vmg->target` is `vmg->next`, as in `vma_merge_new_range()` when
    only the right side merges; `vma_expand()` then removes nothing.
- Comment above `anon_vma_compatible()` in `mm/vma.c` says a VMA with `close`
  is refused merging; the code refuses only its removal.

## Merge and modify

**Merge conditions**

- `is_mergeable_vma()` in `mm/vma.c`: does not read `vm_ops`; its first test
  is `mpol_equal()` on `vmg->policy`.
- `vm_ops->close`: tested by `can_merge_remove_vma()`, called from
  `vma_merge_new_range()` and `vma_merge_existing_range()`, and only for a
  VMA the merge would delete.
- Proposed flags: held in `vmg->vma_flags` (`vma_flags_t`), in a union with
  `vmg->vm_flags`; `struct vma_merge_struct` has no member named flags.
- Special mappings: both merge functions return early when
  `vmg->vma_flags` has any bit of `VMA_SPECIAL_FLAGS`.
- Anonymous page offset: a VMA carries a second offset, read with
  `vma_start_anon_pgoff()`, and the vmg carries `anon_pgoff`.
- `needs_adjacent_anon_pgoff()`: true when `vmg->file` is set and
  `vma_flags_is_cow_mapping()` holds for `vmg->vma_flags`.
- When it is true, `can_vma_merge_before()` and `can_vma_merge_after()`
  also require the anonymous offsets to be contiguous, after the
  `vm_pgoff` test.
- Three-way merge: there is no are_anon_vmas_compatible(); the test of
  `prev->anon_vma` against `next->anon_vma` is inline at the end of
  `can_vma_merge_right()`.
- New attribute, member: add it to `struct vma_merge_struct` in
  `mm/vma.h`.
- New attribute, initialisers: `VMG_VMA_STATE()` copies each attribute
  from the VMA and needs a line for the new one.
- `VMG_STATE()` and `VMG_MMAP_STATE()` (the latter in `mm/vma.c`): leave
  `policy`, `uffd_ctx`, `anon_name` and `anon_vma` zero, so a new range
  proposes the zero value.
- New attribute, compare: one test in `is_mergeable_vma()` covers both
  sides and both merge functions.
- New attribute as a flag bit: compared automatically unless added to
  `VMA_IGNORE_MERGE_FLAGS`.

**Flags in merge decisions**

- `is_mergeable_vma()`: builds the difference with `vma_flags_diff_pair()`
  on `vma->flags` and `vmg->vma_flags`, then removes
  `VMA_IGNORE_MERGE_FLAGS` with `vma_flags_clear_mask()`.
- Mask names: `VMA_IGNORE_MERGE_FLAGS` is defined as `VMA_STICKY_FLAGS` in
  `include/linux/mm.h`; VM_IGNORE_MERGE and VM_STICKY are not defined.
- `VMA_STICKY_FLAGS`: `VMA_SOFTDIRTY_BIT` and `VMA_MAYBE_GUARD_BIT` under
  `CONFIG_MEM_SOFT_DIRTY`, otherwise `VMA_MAYBE_GUARD_BIT` alone.
- Sticky bits on the merged VMA: `vma_merge_existing_range()` and
  `vma_expand()` collect them and set them on the target after
  `commit_merge()` succeeds.
- Sources collected: the proposed `vmg->vma_flags`, the target, and `prev`
  or `next` when that side takes part; `middle` contributes only through
  `vmg->vma_flags`.
- `vma_modify_flags_uffd()`: takes `const vma_flags_t *` and writes nothing
  back.
- New mappings: `VMA_SOFTDIRTY_BIT` is set on the VMA after the merge
  attempt, in `__mmap_complete()` and at the end of `do_brk_flags()`, both
  gated by `pgtable_supports_soft_dirty()`.
- **Unsafe usage**: overwriting the returned VMA's flags with a copy of
  the requested flags taken before `vma_modify_flags()`.
  - Unsafe: after a merge, a sticky bit contributed by a neighbour is
    cleared from the merged VMA.
  - Safe: overwrite with the value written back through the pointer, as
    `mprotect_fixup()` does with `vma_flags_reset_once()`.
  - Safe: only add bits to the returned VMA, as `__mseal_range()` does
    with `vma_set_flags()`.
  - Safe: derive the new value from the returned VMA's own flags, as
    `userfaultfd_set_ctx()` does.

**Fork test during merge**

- Test name: `vma_is_fork_child()` in `mm/vma.c`; there is no
  vma_had_uncowed_parents().
- `is_mergeable_anon_vma()`: `tgt` is `vmg->next` or `vmg->prev`, `src` is
  `vmg->middle`, and the source `anon_vma` is `vmg->anon_vma`.

| Case | VMA tested |
|---|---|
| only source has an `anon_vma` | `vmg->middle` and `vmg->copied_from`; either one forked refuses |
| only target has an `anon_vma` | `tgt` |
| both have one | none; the two pointers must be equal |

- `copy_vma()`: `vma_merge_copied_range()` moves the source VMA from
  `vmg->middle` to `vmg->copied_from`, so a forked mremap source blocks
  the first case.
- `vma_merge_existing_range()`: warns if `vmg->copied_from` is set, under
  `CONFIG_DEBUG_VM`.

**Merge and modify results**

- Modify functions in this tree: `vma_modify_flags()`,
  `vma_modify_name()`, `vma_modify_policy()`, `vma_modify_flags_uffd()`;
  there is no vma_modify_flags_name().
- `give_up_on_oom` (set by `vma_modify_flags_uffd()` on request): a merge
  OOM is not reported; `vma_modify()` returns the unmerged VMA.
- Split failure in `vma_modify()`: the error can come from
  `vm_ops->may_split`, not only `-ENOMEM`.
- Failed second split: the first split is not undone, so the passed-in
  VMA is valid but its `vm_start` has already moved.
- VMA write lock: the modify functions do not assert it, and when no
  neighbour can merge and no split is needed nothing write-locks the
  returned VMA.
- Callers lock the returned VMA before changing it: `mprotect_fixup()`,
  `madvise_update_vma()` and `__mseal_range()` call `vma_start_write()`.
- Returned VMA after a merge: can be larger than the requested range;
  `mprotect_fixup()` keeps using its own `start` and `end` for
  `change_protection()`.
- `vmg_nomem()` after `vma_merge_new_range()`: true only when
  `commit_merge()` failed and `give_up_on_oom` is clear.
- `vma_expand()`: returns on `dup_anon_vma()` failure before it sets
  `VMA_MERGE_ERROR_NOMEM`, so that OOM reads as a plain no-merge.
- `__mmap_region()` and `copy_vma()`: do not call `vmg_nomem()`; any NULL
  leads to allocating a new VMA.
- `do_brk_flags()`: the one caller of `vma_merge_new_range()` that fails
  on `vmg_nomem()`.
- `vma_merge_extend()`: NULL covers both no-merge and OOM;
  `expand_vma_in_place()` in `mm/mremap.c` returns `-ENOMEM` for either.
- `copy_vma()`: also returns NULL when the destination range is occupied.
- `copy_vma()` and `*vmap`: changes only when the merge deleted the
  source VMA; otherwise left as passed.
- **Unsafe usage**: dereferencing the source VMA pointer held before
  `copy_vma()` after it returns.
  - Unsafe: when the new range merged with `prev` and deleted the source,
    the old pointer is freed.
  - Safe: pass the address of a local and use the local afterwards, as
    `copy_vma_and_data()` in `mm/mremap.c` does; it also sets
    `vrm->vmi_needs_invalidate` when the pointer changed.
- **Potentially unsafe usage**: using the VMA passed to a modify function
  after a successful return.
  - Unsafe: when the old pointer is used with no test that the returned
    VMA is the same one; if the range covered the whole VMA and a merge
    happened, the passed VMA is freed.
  - Safe: replace the local with the return value, as `mbind_range()` in
    `mm/mempolicy.c` does before `vma_replace_policy()`.
  - Safe: after testing that the returned VMA is the one passed, as
    `setup_arg_pages()` in `fs/exec.c` does with `BUG_ON(prev != vma)`
    after `mprotect_fixup()`; `vma_modify()` returns either the merge
    target or the VMA passed.
  - Safe: after an `IS_ERR()` return the passed VMA is still valid;
    `apply_mlockall_flags()` in `mm/mlock.c` sets `prev` from it.

**Merge state after failure**

- Restoring: neither `vma_merge_new_range()` nor
  `vma_merge_existing_range()` restores any member on failure, with or
  without `just_expand`.

| Function | Members a failed call can leave changed |
|---|---|
| `vma_merge_existing_range()` | `state`, `next`, `target`, `start`, `end`, `pgoff`, `anon_pgoff`, `__remove_middle`, `__remove_next`, `__adjust_middle_start`, `__adjust_next_start` |
| `vma_merge_new_range()` | `state`, `target`, `start`, `end`, `pgoff`, `anon_pgoff` |
| `vma_expand()` | `__remove_next`, `state` |
| `vma_merge_copied_range()` | `middle` (set NULL), `copied_from` |

- Never written by the functions in the table or by `commit_merge()`:
  `prev`, `anon_vma`, `file`, `policy`, `uffd_ctx`, `anon_name`,
  `vma_flags`.
- `__adjust_middle_start` and `__adjust_next_start`: only ever set to
  true, never cleared at entry.
- Iterator: only the `abort:` label of `vma_merge_existing_range()` sets
  it back to the original start; `commit_merge()` reconfigures it with
  `vma_iter_config()` before the allocation that can fail.
- Reset helper: none in `mm/`; `vmg_set_range()` in
  `tools/testing/vma/tests/merge.c` is test code; it resets the iterator
  and every member in the table except `state` and `copied_from`.
- **Potentially unsafe usage**: passing a vmg to a second merge call, or
  reading its range, after a failed attempt.
  - Unsafe: with no reset in between, `vma_merge_new_range()` warns on a
    set `vmg->target` and `vma_merge_existing_range()` on a set
    `vmg->next`, under `CONFIG_DEBUG_VM`.
  - Unsafe: with no reset in between, a stale `__adjust_next_start` or
    `__adjust_middle_start` is acted on by `commit_merge()` and
    `vmg_adjust_set_range()`.
  - Safe: reset the changed members and the iterator before the next
    call, as `try_merge_new_vma()` in `tools/testing/vma/tests/merge.c`
    does with `vmg_set_range()`.
  - Safe: copy `start`, `end` and `middle` to locals before the attempt,
    as `vma_modify()` does before `split_vma()`.
  - Safe: build a new vmg for each attempt; every caller in `mm/` does,
    with `VMG_STATE()`, `VMG_VMA_STATE()` or `VMG_MMAP_STATE()`.
  - Safe: set the iterator range again before storing, as
    `__mmap_new_vma()` does with `vma_iter_config()`.

## Range changes and the maple tree

**Page offsets**

- `struct vm_area_struct` stores two page offsets: `vm_pgoff`, and an
  anonymous offset split across `__vm_anon_pgoff_lo` and, under
  `CONFIG_64BIT`, `__vm_anon_pgoff_hi`.
- Accessors in `include/linux/mm.h`: `vma_start_pgoff()` and
  `vma_start_anon_pgoff()`, each with an end and a last variant.

| Offset | Used by |
|---|---|
| `vm_pgoff` | file rmap tree key, `vma_filebacked_address()`, `linear_page_index()`, merge check for every VMA |
| anonymous offset | anon rmap tree key, `vma_anon_address()`, `linear_anon_page_index()`, anon `folio->index` in `__folio_set_anon()` |

- There is no vma_address(), vma_pgoff_address() or vma_pgoff_offset() here;
  `vma_filebacked_address()` and `vma_anon_address()` in `mm/internal.h` and
  `linear_page_delta()` in `include/linux/pagemap.h` do those jobs.
- `MAP_PRIVATE` file VMA: anon folios are indexed by the anonymous offset,
  not the file offset; `struct page_vma_mapped_walk` carries `pgoff_is_anon`
  to select which offset `vma_address_end()` uses.
- `vma_is_anonymous()` VMA with no `vm_file`, under `CONFIG_MMU`: the two
  offsets are equal; `linear_anon_page_index()` warns under
  `CONFIG_DEBUG_VM` if they differ.
- Initial anonymous offset: `addr >> PAGE_SHIFT`, set in `__mmap_region()`
  and `insert_vm_struct()` for file-backed VMAs too.
- `anon_vma_compatible()` needs both offsets contiguous in every case.
- Setters: `vma_set_pgoff()`, `vma_set_anon_pgoff()`, `vma_add_pgoff()`,
  `vma_sub_pgoff()` in `mm/vma.h`, `vma_set_range()` in `mm/vma.c`; each
  calls `vma_assert_can_modify()`, so an attached VMA must be write-locked.
- `vma_add_pgoff()` and `vma_sub_pgoff()` move both offsets;
  `vma_set_range()` takes both as arguments.
- `assert_sane_pgoff()`: under `CONFIG_DEBUG_VM` and `CONFIG_MMU`,
  `vma_set_pgoff()` warns when a `vma_is_anonymous()` VMA with no `vm_file`
  and no `anon_vma` gets an offset other than `vm_start >> PAGE_SHIFT`, so
  write `vm_start` first, as `__split_vma()` and `expand_downwards()` do.
- Move, faulted VMA: `copy_vma_and_data()` passes both offsets of the old
  address to `copy_vma()`, which keeps them.
- Move, `!vma->anon_vma`: `copy_vma()` resets the anonymous offset to
  `addr >> PAGE_SHIFT` for any VMA, and `vm_pgoff` too only when
  `vma_is_anonymous()`.
- `MREMAP_DONTUNMAP` of a whole VMA: `dontunmap_complete()` unlinks the old
  VMA's anon_vmas and resets its anonymous offset to
  `vm_start >> PAGE_SHIFT`, and `vm_pgoff` too only when `vma_is_anonymous()`
  and `vm_file` is NULL.
- **Unsafe usage**: moving `vm_start` of a VMA that is in an rmap tree and
  adjusting only one of the two offsets.
  - Unsafe: `avc_start_pgoff()` and `vma_anon_address()` use the anonymous
    offset, the file tree uses `vm_pgoff`; the stale one maps folios to
    wrong addresses.
  - Safe: `vma_add_pgoff()` or `vma_sub_pgoff()`, as `__split_vma()`,
    `vmg_adjust_set_range()` and `expand_downwards()` do.
  - Safe: `vma_set_range()` with both offsets, as `commit_merge()` does.

**Reverse-map trees**

- There are no vma_interval_tree_insert() or anon_vma_interval_tree_insert()
  families here; a search for either prefix finds nothing.
- File helpers: `mapping_rmap_tree_insert()`,
  `mapping_rmap_tree_insert_after()`, `mapping_rmap_tree_remove()`,
  `mapping_rmap_tree_iter_first()`, `mapping_rmap_tree_iter_next()` and
  `mapping_rmap_tree_foreach()`.
- Anon helpers: `anon_rmap_tree_insert()`, `anon_rmap_tree_remove()`,
  `anon_rmap_tree_iter_first()`, `anon_rmap_tree_iter_next()`,
  `anon_rmap_tree_foreach()` and `anon_rmap_tree_verify()`.
- Both families are defined in `mm/interval_tree.c`, apart from the foreach
  macros in `include/linux/mm.h`; insert, remove, iter_first and iter_next
  wrap static functions generated by `INTERVAL_TREE_DEFINE()` with the
  prefixes `__mapping_rmap_tree` and `__anon_rmap_tree`.
- Insert, remove, iter_first and foreach: the file helpers take a
  `struct address_space *`, the anon helpers a `struct anon_vma *`; neither
  takes the rb root. iter_next takes the previous entry in its place.
- File tree (`mapping->i_mmap`) key: [`vma_start_pgoff()`,
  `vma_last_pgoff()`].
- Anon tree (`anon_vma->rb_root`) key: [`vma_start_anon_pgoff()`,
  `vma_last_anon_pgoff()`] of `avc->vma`, through `avc_start_pgoff()` and
  `avc_last_pgoff()`, both static in `mm/interval_tree.c`; this is not the
  `vm_pgoff` interval for a `MAP_PRIVATE` file VMA.
- `anon_rmap_tree_pre_update_vma()` and `anon_rmap_tree_post_update_vma()`:
  static in `mm/vma.c`; they remove and reinsert every
  `struct anon_vma_chain` of the VMA.
- `anon_rmap_tree_verify()`: built only under `CONFIG_DEBUG_VM_RB`.
- `__vma_link_file()`: calls `mapping_allow_writable()` only when
  `vma_is_shared_maywrite()`, which needs both shared and may-write.

**Range change sequence**

- `vma_prepare()`: takes no VMA lock; the caller calls `vma_start_write()`
  on every VMA that changes, is inserted or is removed before it.
- Preallocation and `vma_start_write()`: order is not fixed; `__split_vma()`
  and `vma_shrink()` preallocate first, merges write-lock first and
  preallocate in `commit_merge()`; both precede `vma_prepare()`.
- Fallible work after `vma_start_write()`: allowed up to `vma_prepare()`;
  `dup_anon_vma()` runs there in a merge.
- From `vma_prepare()` to `vma_complete()`: no call that can fail, in
  `__split_vma()`, `commit_merge()` and `vma_shrink()`.
- `vma_adjust_trans_huge()`: runs after `vma_prepare()` and before the range
  is written, in all three.
- `hugetlb_split()`: called at the same point by `__split_vma()` for a
  hugetlb VMA; it asserts the VMA write lock and `i_mmap_rwsem` held for
  write.
- `vma_complete()` stores `vp->insert` after the file-tree reinsertion and
  before `anon_rmap_tree_post_update_vma()`, with the rmap locks that
  `vma_prepare()` took still held.
- Removed VMA in `vma_complete()`: `unlink_anon_vmas()` drops its anon
  links; there is no anon_vma_merge() here.
- Tree helper names inside `vma_prepare()` and `vma_complete()`: as in
  "Reverse-map trees".

**Stack growth**

- `mm->page_table_lock`: not taken by `expand_downwards()` or
  `expand_upwards()` themselves; `__anon_vma_prepare()`, reached through
  `anon_vma_prepare()`, takes it while it sets `vma->anon_vma`.
- Growers exclude each other through the mmap write lock, which both
  functions check with `mmap_assert_write_locked()`.
- `expand_stack_locked()`: takes no lock and upgrades nothing; it calls the
  grow function, so its caller must hold the mmap write lock.
- File-backed growable VMA: excluded at creation; `do_mmap()` returns
  `-EINVAL` when `vma_flags_can_grow()` for any file mapping, for anonymous
  `MAP_SHARED` and for `MAP_DROPPABLE`.
- `expand_downwards()` and `expand_upwards()` have no file test of their
  own and do not take `i_mmap_rwsem`; they rely on that `do_mmap()` test.
- Anon tree update: done with `anon_rmap_tree_pre_update_vma()` and
  `anon_rmap_tree_post_update_vma()` under `anon_vma_lock_write()`, which
  locks the root anon_vma's `rwsem`.

**Writing to the maple tree**

- `vma_iter_store_new()`: for a detached VMA; it calls
  `vma_mark_attached()`, which asserts write-locked and detached, so
  `vma_start_write()` comes first.
- `vma_iter_store_overwrite()`: for a VMA already in the tree whose range
  changed; it calls `vma_assert_attached()`.
- There is no vma_iter_store() here.
- `vma_iter_store_gfp()`: only `do_brk_flags()` calls it; `vma_link()`
  preallocates and calls `vma_iter_store_new()`.
- There is no vma_iter_bulk_alloc() here; `dup_mmap()` copies the tree with
  `__mt_dup()` and replaces entries with `vma_iter_bulk_store()`.
- `vma_iter_clear_gfp()`, `vma_iter_bulk_store()` and `vma_iter_free()` are
  defined in `include/linux/mm.h`, the rest in `mm/vma.h`.
- Stored range: the store helpers take it from `vma->vm_start` and
  `vma->vm_end`, so both must be final before the store, as in
  `commit_merge()`.
- `vma_iter_clear()`: takes the range from `vma_iter_config()`;
  `vma_shrink()` clears before it writes `vm_end`.
- One preallocation serves one store: `mas_store_prealloc()` ends with
  `mas_destroy()`.
- `vma_iter_store_new()`, `vma_iter_store_overwrite()` and
  `vma_iter_clear()` return void; `mas_store_prealloc()` checks the result
  with `MAS_WR_BUG_ON()`.
- **Unsafe usage**: a tree write that can return an error after changes
  that cannot be undone.
  - Safe: `vma_iter_config()` and `vma_iter_prealloc()` for the stored
    range before `vma_prepare()`, then a preallocated store, as
    `commit_merge()` and `__split_vma()` do.
  - Safe: `vma_iter_clear_gfp()` before the point of no return, with
    `reattach_vmas()` on failure, as `do_vmi_align_munmap()` does.
  - Safe: `mas_store_gfp()` with `__GFP_NOFAIL`, as
    `vms_abort_munmap_vmas()` does once PTEs are already cleared.

**VMA count limit**

- `sysctl_max_map_count`: defined in `mm/util.c`; every check reads it
  through `get_sysctl_max_map_count()` in `mm/internal.h`.
- Checks in MMU builds, complete: `do_mmap()`, `do_brk_flags()`,
  `split_vma()`, `vms_gather_munmap_vmas()` and
  `__check_map_count_against_split()` in `mm/mremap.c`.
- `insert_vm_struct()` and `vma_link()`: no check.
- `mmap_region()`: no check for the VMA it adds; the only check below it is
  the one in `vms_gather_munmap_vmas()`, made when the range lies strictly
  inside one existing VMA.
- `__check_map_count_against_split()` from `prep_move_vma()`: passes when
  `map_count + 2` is at most the limit.
- `__check_map_count_against_split()` from `do_mremap()`: runs on every
  mremap right after the mmap write lock is taken, and passes when
  `map_count + 4` is at most the limit.
- `split_vma()` and `__split_vma()`: both static in `mm/vma.c`;
  `vma_modify()` is the only caller of `split_vma()`, and
  `vms_gather_munmap_vmas()` is the only caller of `__split_vma()` besides
  `split_vma()`.
- `mm/nommu.c` has its own `split_vma()`, which checks with `>=`.

## Fork and foreign address spaces

**Copying VMAs at fork**

- Failed fork: `dup_mmap()` in `mm/mmap.c` tears the child down itself, under
  both write locks. It does not store `XA_ZERO_ENTRY`; nothing under `mm/`
  tests `xa_is_zero()`.
- Failure sequence: set `MMF_OOM_SKIP`; `unmap_region()`; `tear_down_vmas()`;
  `vm_unacct_memory()`; `__mt_destroy()`; set `MMF_UNSTABLE`; unlock.
- Child tree after failure: empty. `exit_mmap()`, reached from `mmput()`,
  finds no VMA and jumps to its `destroy` label.
- Teardown bound `end`, also written to `unmap.tree_end`:

| Failure | `end` |
|---|---|
| no VMA stored yet (`map_count` is 0) | 0; unmap and teardown skipped |
| before the copy of `mpnt` is stored | `mpnt->vm_start` |
| `copy_page_range()` on a stored VMA | start of the next VMA, or `ULONG_MAX` |
| `arch_dup_mmap()` | `ULONG_MAX` |

- Entries at or above `end`: still the parent's VMAs from `__mt_dup()`.
  `__mt_destroy()` frees only tree nodes, so teardown that passes `end` would
  free parent VMAs.
- `tear_down_vmas()`: calls `remove_vma()` on each stored VMA, so every
  `vm_ops->open()` is paired with a close; it does not decrement `map_count`.
- Left stale on the child mm: `map_count`, and `total_vm`, `data_vm`,
  `exec_vm`, `stack_vm` copied from the parent.
- `__mt_dup()` failure: jumps to `out`, past the failure block; neither
  `MMF_OOM_SKIP` nor `MMF_UNSTABLE` is set.
- `mmap_write_lock_killable(oldmm)` failure: returns `-EINTR` with the child
  untouched.
- `vma_start_write_killable()` is what locks each parent VMA; it can fail,
  making that VMA the failure point.
- `dup_mm()` in `kernel/fork.c`, not `copy_mm()`, calls `mmput()` on failure,
  then `uprobe_end_dup_mmap()`. `uprobe_start_dup_mmap()` is called there too;
  `dup_mmap()` itself calls `uprobe_dup_mmap()`.
- Flag tests in `dup_mmap()` use `vma_test()` with `VMA_DONTCOPY_BIT`,
  `VMA_WIPEONFORK_BIT`, `VMA_ACCOUNT_BIT`; a search for `VM_DONTCOPY` in
  `mm/mmap.c` finds nothing.
- mlock bits: cleared by `vma_clear_flags_mask(tmp, VMA_LOCKED_MASK)`, not
  `vm_flags_clear()`.
- There is no vma_lock_alloc() here; `vm_area_dup()` in `mm/vma_init.c` calls
  `vma_lock_init(new, true)`.
- `vm_area_dup()`: copies field by field in `vm_area_init_from()`, not the
  whole struct. A field missing from that function is left out of the child.
- `pfnmap_track_ctx`, under `__HAVE_PFNMAP_TRACKING`: shared with the parent
  by `kref_get()`, not reset; `vm_area_dup()` returns NULL if the count is
  saturated.
- `vma_needs_copy()` in `mm/memory.c`: true if the child VMA has any
  `VM_COPY_ON_FORK` bit, or the parent VMA has an `anon_vma`. It has no
  hugetlb test, so a hugetlb VMA with neither is not copied.
- `VM_COPY_ON_FORK` is tested on the child VMA, after `dup_userfaultfd()` may
  have cleared the uffd bits there.

**Unstable address spaces**

- `check_stable_address_space()` in `include/linux/oom.h`: tests
  `MMF_UNSTABLE`, the mark; returns `VM_FAULT_SIGBUS`, type `vm_fault_t`, not
  an errno. Non-fault callers pick their own result;
  `hmm_range_fault_unlocked_timeout()` returns `-EFAULT`, `unuse_mm()` skips
  the mm and returns 0.
- `mm->flags` is a private `mm_flags_t`; access is through `mm_flags_test()`
  and `mm_flags_set()`, not `test_bit()` on `mm->flags`.
- `__oom_reap_task_mm()`: sets the mark and zaps under the mmap read lock,
  from both `oom_reap_task_mm()` and `process_mrelease` in `mm/oom_kill.c`.
- Mmap read lock held by a walker: does not stop the mark appearing mid-walk.
  Only the mmap write lock excludes the reaper.
- `finish_fault()`: tests the mark only when the VMA is not `VM_SHARED`.
  `do_anonymous_page()` tests under the PTE lock.
- Failed-fork mm: `dup_mmap()` holds the child's write lock from before
  `__mt_dup()` until after `__mt_destroy()`. A walker that gets the lock sees
  an empty tree, never a half-built one or the parent's VMAs.
- `__mt_dup()` failure in `dup_mmap()`: the mark is not set; the tree is empty.
- In-tree lock-then-test walkers: `register_for_each_vma()` (write lock),
  `unuse_mm()` in `mm/swapfile.c`, `hmm_range_fault_unlocked_timeout()` in
  `mm/hmm.c` (read lock). No function in `mm/userfaultfd.c` tests the mark.
- Reaper as walker: `oom_reap_task_mm()` and `process_mrelease` hold only
  `mmgrab()`. They take the mmap read lock, then test `MMF_OOM_SKIP` under it.
- `exit_mmap()`: sets `MMF_OOM_SKIP` before taking the write lock under which
  it frees page tables and VMAs.
- `folio_referenced_one()` in `mm/rmap.c`: tests the mark with no mmap lock,
  next to `mm_users == 0`, only as a hint to skip a folio.
- There is no hpage_collapse_test_exit() here; `collapse_test_exit()` in
  `mm/khugepaged.c` tests `mm_users == 0`, as `ksm_test_exit()` does.
- **Potentially unsafe usage**: installing a new page in a private mapping of
  a foreign mm after testing the mark only under the mmap read lock.
  - Unsafe: when the page fills an empty entry; `__oom_reap_task_mm()` can set
    the mark and zap the range after the test, and the new page then stands
    where the task's data was.
  - Safe: test under the page table lock just before the install, as
    `migrate_vma_insert_page()` and `do_anonymous_page()` do.
  - Safe: test under the mmap write lock, as `register_for_each_vma()` does;
    `__oom_reap_task_mm()` runs only under the mmap read lock.
  - Safe: replace an entry that is compared again under the PTE lock, as
    `unuse_pte()` under `unuse_mm()` does with `pte_same_as_swp()`; a zapped
    entry no longer matches.

## Overcommit accounting

**Overcommit charging**

- Flag name: code in `mm/` tests and sets `VMA_ACCOUNT_BIT`, for example
  through `vma_test()`, `vma_flags_test()` and `vma_flags_set()`; `VM_ACCOUNT`
  is still defined in `include/linux/mm.h`, but in `mm/` it is only in comments.
- LSM hook name: `vm_enough_memory`; there is no function named
  security_vm_enough_memory.
- `__mmap_region()` in `mm/vma.c`: the charge is made in `__mmap_setup()` and
  kept in `map.charged`; the `unacct_error:` label gives it back. There is no
  local `charged` in `mmap_region()`.
- `__mmap_region()` when `mmap_action_complete()` fails: returns with no
  `vm_unacct_memory()`; the VMA is already linked, and `mmap_action_finish()`
  unmaps it with `do_munmap()`, which uncharges by flag.
- Uncharge by flag: done in `vms_complete_munmap_vmas()` and by the callers of
  `tear_down_vmas()` in `mm/mmap.c`; `remove_vma()` has no
  `vm_unacct_memory()` call.
- `dup_mmap()` in `mm/mmap.c`: `charge` is reset for each VMA; `fail_nomem:`
  gives back only the charge of the VMA not yet stored in the new tree.
- `dup_mmap()` VMAs already stored in the new tree: uncharged by flag, from
  the count `tear_down_vmas()` returns.
- `acct_stack_growth()` in `mm/vma.c`: gives nothing back; the overcommit
  check is its last test, and `expand_upwards()` and `expand_downwards()`
  cannot fail once it returns 0. A failure point added after it would have to
  uncharge `grow`.

**Accounting flag on live VMAs**

- `mprotect_fixup()` clearing `VMA_ACCOUNT_BIT`: only when the new flags lack
  `VMA_WRITE_BIT`, the old flags have `VMA_ACCOUNT_BIT`, `vma_is_anonymous()`
  is true and `vma->anon_vma` is NULL.
- `mprotect_fixup()` uncharge on clear: `vm_unacct_memory(nrpages)` runs after
  `vma_flags_reset_once()` and `change_protection()`, so no failure can follow
  it.
- **Potentially unsafe usage**: clearing `VMA_ACCOUNT_BIT` and uncharging when
  a private mapping loses write permission.
  - Unsafe: when `vma_is_anonymous()` is false or `vma->anon_vma` is set; a
    VMA with an `anon_vma` may hold private pages that stay allocated after
    the charge is returned.
  - Safe: when `vma_is_anonymous()` is true and `vma->anon_vma` is NULL, as
    `mprotect_fixup()` tests; otherwise it leaves the flag and the charge.
- `unmap_source_vma()` in `mm/mremap.c`, for an accounted VMA moved without
  `MREMAP_DONTUNMAP`: clears `VMA_ACCOUNT_BIT` on the whole source VMA, not
  only the moved range, then sets it again on each remnant.
- `unmap_source_vma()` when `do_vmi_munmap()` fails: returns without setting
  `VMA_ACCOUNT_BIT` again; not a pattern to copy.
- Helpers used: `unmap_source_vma()` calls `vma_clear_flags()` and
  `vma_set_flags()`, and `mprotect_fixup()` calls `vma_flags_reset_once()`;
  none of the three takes or asserts the VMA write lock.
- `vm_flags_set()` and `vm_flags_clear()`: do call `vma_start_write()`, but no
  in-tree change of `VMA_ACCOUNT_BIT` uses them.
- **Unsafe usage**: changing `VMA_ACCOUNT_BIT` on an attached VMA with
  `vma_set_flags()`, `vma_clear_flags()` or `vma_flags_reset_once()` while the
  VMA is not write-locked.
  - Unsafe: these helpers update `vma->flags` non-atomically;
    `vma_set_atomic_flag()` sets `VMA_MAYBE_GUARD_BIT` in the same bitmap
    under a VMA read lock only, and that bit can be lost.
  - Safe: after `vma_start_write()` on that VMA; `move_vma()` calls it on the
    source before `unmap_source_vma()` clears the bit.
  - Safe: `unmap_source_vma()` calls `vma_start_write()` on each remnant
    before `vma_set_flags()`.
  - Safe: `mprotect_fixup()` calls `vma_start_write()` on the VMA that
    `vma_modify_flags()` returned, then `vma_flags_reset_once()`.

## Model gaps

### Other mistakes models make

- Models take the mm-core entry points to pass `vm_flags_t`. `do_mmap()`,
  `mmap_region()` and `do_brk_flags()` take a `vma_flags_t` by value, and
  `may_expand_vm()` a `const vma_flags_t *`; convert with
  `legacy_to_vma_flags()`.
- Models take `anon_vma_clone()` to have two arguments. It takes a third, an
  `enum vma_operation` (`mm/internal.h`), and `mm/rmap.c` warns, under
  `CONFIG_DEBUG_VM`, when the operation does not match the state of the two
  VMAs.
- Models look for `insert_vm_struct()` and `__vm_munmap()` in `mm/mmap.c`.
  Both are in `mm/vma.c`.
