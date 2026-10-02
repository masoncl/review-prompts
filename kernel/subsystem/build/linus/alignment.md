# Alignment Helpers

## Main structures

### Objects and how they relate

- `round_up()`, `round_down()`, `roundup()`, `rounddown()`, `DIV_ROUND_UP()`
  and `DIV_ROUND_UP_ULL()`: `include/linux/math.h`.
- `PAGE_ALIGN_DOWN()`: exists, in `include/linux/mm.h`, as
  `ALIGN_DOWN(addr, PAGE_SIZE)`.
- `roundup_u64()`: exists, in `include/linux/math64.h`. It is a `static
  inline` function, not a macro, and takes a `u32` multiple. There is no
  rounddown_u64() here.
- `DIV_ROUND_UP_POW2()` in `include/linux/math.h`: divide-and-round-up for a
  power-of-two divisor. It does not add to `n` before dividing, so it cannot
  wrap the way `DIV_ROUND_UP()` can.
- `ALIGN` in assembly sources: the macro from `include/linux/linkage.h`, not
  the C one. Its `__ALIGN` is `.balign CONFIG_FUNCTION_ALIGNMENT` unless the
  architecture's `asm/linkage.h` defines `__ALIGN`; for example
  `arch/arm/include/asm/linkage.h` uses `.align 0`. A search for `ALIGN` hits
  both macros.
- `ALIGN()`, `IS_ALIGNED()`, `round_up()`, `round_down()`: `a`, or `y - 1`,
  is cast to `typeof(x)`, so an `a` or `y` wider than `x` is truncated.
- `ALIGN()`, `round_up()`, `round_down()`: the result has the
  integer-promoted type of `x`.
- How many times each macro evaluates its arguments (`typeof` operands are
  not counted):

| Macro | `x` or `p` | `a` or `y` |
|---|---|---|
| `ALIGN()`, `PTR_ALIGN()` | once | twice |
| `ALIGN_DOWN()`, `PTR_ALIGN_DOWN()` | once | three times |
| `IS_ALIGNED()`, `round_up()`, `round_down()` | once | once |
| `roundup()`, `rounddown()` | once | once |

- `roundup()` copies `y` into a local `__y`; `rounddown()` copies `x` into a
  local `__x` and uses `y` directly.

## Where to look

**Core files**

| Job | Header | Easy to miss |
|---|---|---|
| Generic round-up, round-down, test and pointer macros | `include/vdso/align.h` | `include/linux/align.h` defines nothing; it only includes `include/vdso/align.h`. |
| Pointer test macro | none | No generic `PTR_IS_ALIGNED()`; the tree's only definition is private to `drivers/net/ethernet/freescale/dpaa/dpaa_eth.c`. |
| Mask forms | `include/vdso/align.h` | `__ALIGN_MASK()` is the only mask form in that header; there is no ALIGN_UP_MASK in the tree. |
| `ALIGN` in assembly files | `include/linux/linkage.h` | A different macro with no arguments: expands to `__ALIGN`, under `__ASSEMBLY__` and not `LINKER_SCRIPT`. |
| Page size and page mask | `include/vdso/page.h` | Every directory under `arch/` includes it from a page header; for example x86 from `arch/x86/include/asm/page_types.h`, arm64 from `arch/arm64/include/asm/page-def.h`. |
| Page size, own definitions | `arch/powerpc/boot/page.h`, `arch/arc/include/uapi/asm/page.h` | The only other `PAGE_SHIFT` definitions outside `tools/`: the powerpc boot wrapper, and the arc branch for non-`__KERNEL__` builds. |
| Page size, generic fallback | none | There is no include/asm-generic/page.h in this tree. |
| Pageblock forms | `include/linux/pageblock-flags.h` | `PAGE_BLOCK_MAX_ORDER`, which the constant forms of `pageblock_order` use, is in `include/linux/mmzone.h`; `include/linux/pageblock-flags.h` includes only `linux/types.h`. |
| Byte address to page frame number, second spelling | `include/asm-generic/memory_model.h` | `__phys_to_pfn()` and `__pfn_to_phys()` expand to `PHYS_PFN()` and `PFN_PHYS()` from `include/linux/pfn.h`. |
| Primitives, page-sized forms, PFN conversions, power-of-two rounding, rounding to a multiple | `include/uapi/linux/const.h`, `include/linux/mm.h`, `include/linux/pfn.h`, `include/linux/log2.h`, `include/linux/math.h` | Headers are listed in the order of the jobs. |

## Generic helpers

**Power-of-two alignment argument**

- The "@a is a power of 2 value" comment: in `include/vdso/align.h`, above
  `ALIGN()`.
- `roundup()` and `rounddown()` in `include/linux/math.h`: use the C `/` and
  `%` operators on the operand types, not `do_div()`.
- 64-bit value in a 32-bit build: `roundup_u64()` in
  `include/linux/math64.h` takes a `u32` multiple; `DIV_U64_ROUND_UP()` and
  `DIV64_U64_ROUND_UP()` are in the same file, `DIV_ROUND_UP_ULL()` in
  `include/linux/math.h`.

**Rounding results**

- Non-power-of-two `a`, direction: without wrap `ALIGN(x, a)` is never below
  `x` and `ALIGN_DOWN(x, a)` is never above `x`; each differs from `x` by at
  most `a - 1`.
- Non-power-of-two `a`, value: the result has the bits of `a - 1` clear; it
  may or may not be a multiple of `a`.
- Multiple of a non-power-of-two `a`: need not be returned unchanged;
  `ALIGN(6, 6)` is `11 & ~5`, which is 10, and `ALIGN_DOWN(6, 6)` is
  `6 & ~5`, which is 2.

**Operand types**

- Pointer test: `IS_ALIGNED((unsigned long)p, a)`, as `kernel/rseq.c` does;
  `include/vdso/align.h` has only `PTR_ALIGN()` and `PTR_ALIGN_DOWN()` for
  pointers.
- `ALIGN_DOWN(x, a)`: `a` is cast to the type of `(x) - ((a) - 1)`, the
  common type of `x` and `a`, so the result can be wider than `x` and a wide
  `a` is not truncated as it is in `ALIGN()`.

**Rounding up past the maximum**

- Unsigned operand at least as wide as `int`, power-of-two `a`: the result is
  exactly 0, not another small value.
- Signed operand at least as wide as `int`: the result is the minimum of the
  type, for example `INT_MIN`.
- Operand narrower than `int`: the sum is computed in `int` and does not
  wrap; the result is out of range for the operand type until it is stored.
- `CONFIG_UBSAN_INTEGER_WRAP` in `lib/Kconfig.ubsan`: the wrap sanitizer; it
  depends on `BROKEN`, and `scripts/integer-wrap-ignore.scl` limits it to
  `size_t`.
- `mm/mremap.c`: `do_mremap()` aligns both lengths; `check_mremap_params()`
  returns `-EINVAL` for a zero `new_len` and for `new_len > TASK_SIZE`; a
  zero `old_len` passes `check_mremap_params()`.
- `mm/madvise.c`: the wrap test is in `check_input_range()`.
- `vm_mmap()` in `mm/util.c`: its test covers the sum
  `offset + PAGE_ALIGN(len)`; it passes when `PAGE_ALIGN(len)` itself wrapped
  to 0, and `do_mmap()` rejects that case later.
- `do_mprotect_pkey()` in `mm/mprotect.c`: returns 0 for `!len` before it
  aligns, then returns `-ENOMEM` when `start + PAGE_ALIGN(len) <= start`.
- `validate_mmap_request()` in `mm/nommu.c`: rejects an aligned length of 0
  or above `TASK_SIZE` with `-ENOMEM`.
- **Potentially unsafe usage**: `ALIGN()` or `PAGE_ALIGN()` on a length or
  address from outside the kernel.
  - Unsafe: when nothing bounds the value to the type's maximum minus
    `a - 1` before the call and nothing tests the result for a wrap after
    it; `__ALIGN_KERNEL_MASK()` wraps and the result 0 is used as a size or
    an end.
  - Unsafe: when the only test is "result is 0" and a zero input is legal;
    the test cannot tell a wrap from a zero input.
  - Safe: reject a zero input, align, then reject a zero result, as
    `do_mmap()` in `mm/mmap.c` does (`-EINVAL`, then `-ENOMEM`).
  - Safe: test `len_in && !len` after aligning, as `check_input_range()`
    does.
  - Safe: test `len < request` after aligning, as `vm_brk_flags()` in
    `mm/mmap.c` does.

**Tools, scripts and Rust copies**

- `tools/include/uapi/linux/const.h`: the only copy a script compares; it is
  in the `FILES` list of `tools/perf/check-headers.sh`, which prints a
  warning and does not fail the build.
- `tools/include/linux/align.h`: exists, defines only `ALIGN()`,
  `ALIGN_DOWN()` and `IS_ALIGNED()`, and is in no list of the script.
- `include/vdso/align.h`: has no copy under `tools/include/vdso/`.
- `tools/include/linux/kernel.h`: has `PERF_ALIGN()` and
  `__PERF_ALIGN_MASK()`, not `ALIGN()`.
- Pageblock copies: `tools/testing/memblock/linux/mmzone.h` and
  `tools/testing/vma/linux/mmzone.h`; no script compares them.
- Pageblock copies, contents: `pageblock_order` is fixed to `MAX_PAGE_ORDER`
  (10); they define `pageblock_align()` and `pageblock_start_pfn()` but not
  `pageblock_aligned()` or `pageblock_end_pfn()`.
- `scripts/gdb`: holds no copy of `ALIGN()` or of the pageblock macros;
  `scripts/gdb/linux/mm.py` has `PAGE_SIZE` and `PAGE_MASK`.
- Other private copies: search for `#define ALIGN(` under `tools/` and
  `scripts/`; for example `tools/firmware/ihex2fw.c` and
  `tools/testing/scatterlist/linux/mm.h` copy `__ALIGN_KERNEL()`.
- `tools/hv/vmbus_bufring.c`: its `ALIGN()` rounds down.
- `tools/virtio/ringtest/ptr_ring.c`: its `ALIGN()` divides, so it accepts
  any multiple.
- Rust `page_align()` in `rust/kernel/page.rs`: returns `Option<usize>`; it
  uses `checked_add` and returns `None` where C `PAGE_ALIGN()` returns 0; it
  does not panic under `CONFIG_RUST_OVERFLOW_CHECKS`.
- Rust `Alignable` in `rust/kernel/ptr.rs`: `align_up()` returns
  `Option<Self>` and `None` on overflow; `const_align_up()` does the same
  for `usize`; `align_down()` returns a plain value.
- Rust `align_up()` with an alignment that does not fit the value's type:
  returns `None` unless the value is 0; C `ALIGN()` truncates `a` and
  returns 0.
- Rust `Alignment` in `rust/kernel/ptr.rs`: `Alignment::new()` rejects a
  non-power-of-two at build time and `Alignment::new_checked()` returns
  `None` at run time; the C macros check nothing.

**UAPI alignment primitives**

- `CONFIG_UAPI_HEADER_TEST`: `usr/include/Makefile` compiles the exported
  headers with `-std=c90`, and with `-std=c++98` for C++, but headers under
  `include/uapi` expand `__ALIGN_KERNEL()` and `__ALIGN_KERNEL_MASK()` only
  inside other macro definitions, for example `XT_ALIGN()` and
  `NL_MMAP_MSG_ALIGN()`, so the test parses no expansion of them.
- Direct UAPI users of `__ALIGN_KERNEL()`: `XT_ALIGN()` in
  `include/uapi/linux/netfilter/x_tables.h` and `NL_MMAP_MSG_ALIGN()` in
  `include/uapi/linux/netlink.h`; `XT_TARGET_INIT()` puts `XT_ALIGN()` in a
  struct initializer.
- `__ALIGN_KERNEL_MASK()` in assembly: `LOAD_PHYSICAL_ADDR` in
  `arch/x86/include/asm/page_types.h` expands it and
  `arch/x86/boot/header.S` uses that value, so the mask form must stay plain
  arithmetic with no cast and no `__typeof__`.
- vDSO: the kernel wrappers are in `include/vdso/align.h`, which
  `include/vdso/datapage.h` includes, so an expansion must also compile in
  vDSO code.

## Page helpers

**Page alignment macros**

- `PAGE_ALIGN()` result type: the integer-promoted type of `addr`, because
  `__ALIGN_KERNEL()` in `include/uapi/linux/const.h` casts `a` to
  `__typeof__(x)`; a `u64` stays 64 bits wide on a 32-bit kernel.
- `PAGE_ALIGN_DOWN()` result type: the type of `addr - (PAGE_SIZE - 1)`, not
  the type of `addr`, because `ALIGN_DOWN()` in `include/vdso/align.h` does the
  subtraction before `__ALIGN_KERNEL()` takes the typeof.
  - Argument narrower than unsigned long, for example `u32` on a 64-bit kernel:
    result is unsigned long.
  - Signed argument of the same width as unsigned long, for example `loff_t` on
    a 64-bit kernel: result is unsigned.
  - Argument wider than unsigned long, for example `u64` or `loff_t` on a
    32-bit kernel: keeps its type and its high bits.
- Pointer argument to `PAGE_ALIGN()` or `PAGE_ALIGN_DOWN()`: does not compile,
  although the comments above them in `include/linux/mm.h` say "align the
  pointer"; the expansion adds the pointer to a mask of pointer type.
- `PAGE_ALIGNED()` on a value wider than unsigned long on a 32-bit kernel: the
  cast drops the high bits, and the result is still correct, since only bits
  below `PAGE_SHIFT` are tested.

**Addresses and page frame numbers**

- `PFN_UP()` result type: the type of `x + PAGE_SIZE`, so unsigned long for an
  argument narrower than unsigned long, and `u64` for a `u64` argument on a
  32-bit kernel.
- `PFN_DOWN()` result type: the integer-promoted type of `x`.
- There is no pfn_t type in this tree; `include/linux/pfn.h` defines only
  five function-like macros.

**Masking with the page mask**

- `PAGE_MASK` has two definitions in `include/vdso/page.h`, selected by
  `#if !defined(CONFIG_64BIT)`:

| Kernel | Definition | Type |
|---|---|---|
| `CONFIG_64BIT` not set | `(~((1 << CONFIG_PAGE_SHIFT) - 1))` | int, negative |
| `CONFIG_64BIT` set | `(~(PAGE_SIZE - 1))` | unsigned long |

- `CONFIG_PHYS_ADDR_T_64BIT` is not tested in `include/vdso/page.h`; every
  32-bit kernel gets the int form, with or without wide physical addresses.
- `value & PAGE_MASK` on a 32-bit kernel: keeps bits 32 to 63 of a `u64`,
  `phys_addr_t`, `dma_addr_t` or `loff_t`, because the int is sign-extended to
  the wider type.
- `(u64)PAGE_MASK` on a 32-bit kernel: also sign-extends, the high 32 bits are
  ones.
- There is no PHYS_PAGE_MASK in this tree; x86 has `PHYSICAL_PAGE_MASK` in
  `arch/x86/include/asm/page_types.h`, which casts `PAGE_MASK` to
  `signed long` and ANDs it with `__PHYSICAL_MASK`.
- **Potentially unsafe usage**: masking with a hand-written
  `~(PAGE_SIZE - 1)`.
  - Unsafe: when the value is wider than unsigned long, such as a `u64`, a
    `loff_t`, or a `phys_addr_t` under `CONFIG_PHYS_ADDR_T_64BIT`, on a kernel
    without `CONFIG_64BIT`; `PAGE_SIZE` is `_AC(1,UL) << CONFIG_PAGE_SHIFT`,
    so the mask is a 32-bit unsigned long, is zero-extended, and clears bits
    32 to 63.
  - Safe: when the value is unsigned long or narrower, as
    `pt_topa_prev_entry()` in `arch/x86/events/intel/pt.c` does after casting
    a pointer to unsigned long.
  - Safe: in code built only with `CONFIG_64BIT`, where unsigned long is 64
    bits, as `handle_pfmf()` in `arch/s390/kvm/s390/priv.c`.
  - Safe: `PAGE_MASK` itself applied to the wide value, as `__early_ioremap()`
    in `mm/early_ioremap.c` does with `phys_addr &= PAGE_MASK` on a
    `resource_size_t`.
- **Potentially unsafe usage**: converting `PAGE_MASK` to unsigned long, or
  another unsigned 32-bit type, before it meets the value: stored in an
  unsigned long variable, passed as an unsigned long parameter, or combined
  first with an unsigned long operand.
  - Unsafe: when the result then masks a value wider than unsigned long on a
    kernel without `CONFIG_64BIT`; the sign extension is lost and bits 32 to
    63 are cleared.
  - Safe: when the value masked is unsigned long or narrower, as in
    `PFN_ALIGN()` in `include/linux/pfn.h`, whose argument is cast to
    unsigned long first.
  - Safe: a cast straight to the wide type or to a signed type, as
    `(loff_t)PAGE_MASK` in `bl_write_pagelist()` in
    `fs/nfs/blocklayout/blocklayout.c`, or `(signed long)PAGE_MASK` in
    `PHYSICAL_PAGE_MASK`.

## Pageblocks

**Pageblock size**

- Constant forms in `include/linux/pageblock-flags.h`: every one is capped by
  `PAGE_BLOCK_MAX_ORDER`, not `MAX_PAGE_ORDER`.
  - `CONFIG_HUGETLB_PAGE` without `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`:
    `MIN_T(unsigned int, HUGETLB_PAGE_ORDER, PAGE_BLOCK_MAX_ORDER)`.
  - `CONFIG_TRANSPARENT_HUGEPAGE` without hugetlb:
    `MIN_T(unsigned int, HPAGE_PMD_ORDER, PAGE_BLOCK_MAX_ORDER)`.
  - neither: `PAGE_BLOCK_MAX_ORDER`.
- Variable form: `unsigned int pageblock_order __read_mostly` is defined in
  `mm/page_alloc.c`, under `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`.
- `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`: the only `select` is in
  `arch/powerpc/Kconfig`, for `PPC_BOOK3S_64 && HUGETLB_PAGE`; there is no
  ia64 in this tree.
- `set_pageblock_order()`: one call site, in `free_area_init()` in
  `mm/mm_init.c`; `sparse_init()` does not call it.
- `mm_core_init_early()` calls `free_area_init()` before `sparse_init()`.
- `set_pageblock_order()` body: starts from `PAGE_BLOCK_MAX_ORDER` and lowers
  to `HUGETLB_PAGE_ORDER` when that is smaller and `HPAGE_SHIFT > PAGE_SHIFT`.
- `set_pageblock_order()` has no assertion and does not mention
  `MAX_PAGE_ORDER`.
- Before `set_pageblock_order()` runs the variable is 0, so
  `pageblock_nr_pages` is 1 and `CMA_MIN_ALIGNMENT_BYTES` is `PAGE_SIZE`.
- `cma_init_reserved_mem()` in `mm/cma.c`: returns `-EINVAL` with a
  `pr_err()` while `pageblock_order` is 0.
- `arch_mm_preinit()` in `arch/powerpc/mm/mem.c`: does its CMA reservations
  there because they need `pageblock_order` set.
- `PAGE_BLOCK_MAX_ORDER` and the `#error` for
  `PAGE_BLOCK_MAX_ORDER > MAX_PAGE_ORDER`: both in `include/linux/mmzone.h`;
  the bound is a preprocessor test, not a runtime check.
- `pageblock_order < MAX_PAGE_ORDER`: one free buddy page can cover several
  pageblocks.
- `__move_freepages_block_isolate()` in `mm/page_alloc.c`: skips
  `find_large_buddy()` and the split when
  `pageblock_order == MAX_PAGE_ORDER`.

**Interfaces needing pageblock alignment**

- `start_isolate_page_range()` and `undo_isolate_page_range()`: round out
  themselves, to `pageblock_start_pfn(start_pfn)` and
  `pageblock_align(end_pfn)`; an unaligned range is accepted.
- `VM_BUG_ON(!pageblock_aligned(boundary_pfn))` in
  `isolate_single_pageblock()`: tests the rounded value, not the caller's.
- First and last pageblock of `start_isolate_page_range()`: scanned whole for
  unmovable pages, including the part outside the caller's range, so an
  unmovable page there fails the call with `-EBUSY`.
- A `MIGRATE_CMA` block under `PB_ISOLATE_MODE_CMA_ALLOC` is not scanned;
  see `has_unmovable_pages()`.
- `test_pages_isolated()`: no rounding; it walks from the given `start_pfn`
  in steps of `pageblock_nr_pages`.
- `test_pages_isolated()` need not get the range that was isolated:
  `alloc_contig_frozen_range_noprof()` passes `outer_start`.
- `alloc_contig_range_noprof()`: a wrapper around
  `alloc_contig_frozen_range_noprof()` in `mm/page_alloc.c`.
- `alloc_contig_range_noprof()` with `__GFP_COMP`: `WARN_ON()` and `-EINVAL`
  before anything is isolated.
- `alloc_contig_frozen_range_noprof()`: passes the raw `start` and `end` to
  `start_isolate_page_range()` and `undo_isolate_page_range()`; it calls
  neither `pageblock_start_pfn()` nor `pageblock_align()`.
- `alloc_contig_frozen_range_noprof()` with `__GFP_COMP`: `-EINVAL` and
  `WARN()` unless the free pages it took are exactly `[start, end)` and the
  size is a power of two.
- Rounded-out part of the boundary pageblocks in
  `alloc_contig_frozen_range_noprof()`: only isolated for the call, then
  released by `undo_isolate_page_range()` at `done`.
- Pages outside `[start, end)` that are taken and given back, without
  `__GFP_COMP`: only those of a free page straddling `start` (see
  `find_large_buddy()`) or `end`, returned with
  `__free_contig_frozen_range()`.
- `CMA_MIN_ALIGNMENT_PAGES` in `include/linux/cma.h`: exactly
  `pageblock_nr_pages`, with no link to `MAX_PAGE_ORDER`.
- `cma_declare_contiguous_nid()`: the work is in
  `__cma_declare_contiguous_nid()` in `mm/cma.c`.

| Argument of `__cma_declare_contiguous_nid()` | Not aligned |
|---|---|
| fixed base | `pr_err()` and `-EINVAL` |
| base, not fixed | rounded up |
| size | rounded up, no error |
| `limit` | rounded down |

- Fixed base: tested against `alignment` after it is raised to at least
  `CMA_MIN_ALIGNMENT_BYTES`, so a larger caller alignment binds the base too.
- Fixed base of 0: passes the test and is then treated as not fixed.
- `online_pages()` and `offline_pages()`: make the pageblock and section
  test themselves.
- `check_hotplug_memory_range()`: tests `memory_block_size_bytes()` alignment
  on add and remove, in `__add_memory_resource()` and `try_remove_memory()`.
- `try_remove_memory()`: wraps that test in `BUG_ON()`.
- Memmap-on-memory: `mhp_supports_memmap_on_memory()` refuses a memmap that
  is not whole pageblocks.
- Under `MEMMAP_ON_MEMORY_FORCE`,
  `memory_block_memmap_on_memory_pages()` rounds it up with
  `pageblock_align()` instead.

**Range ends and pageblocks**

- `@end_pfn` of `start_isolate_page_range()` and
  `undo_isolate_page_range()`: one past the last pfn, although the kerneldoc
  says "The last PFN".
- `offline_pages()` passes `start_pfn + nr_pages` as that end, and
  `alloc_contig_frozen_range_noprof()` passes `end`.
- Last block in `start_isolate_page_range()`: starts at
  `isolate_end - pageblock_nr_pages`; the function does not use
  `pageblock_start_pfn(end_pfn - 1)`.
- `pageblock_start_pfn(end_pfn - 1)` for the last block of an exclusive end:
  see `compact_zone()` and `reset_cached_positions()` in `mm/compaction.c`,
  and the `VM_BUG_ON()` in `has_unmovable_pages()`.
- `pageblock_end_pfn(pfn)`: `pfn` is a page frame inside the block; for an
  aligned exclusive end it returns the end of the next block. The last pfn of
  a block is `pageblock_end_pfn(pfn) - 1`, as in `__reset_isolation_pfn()` in
  `mm/compaction.c`.
- **Potentially unsafe usage**: acting on the first and the last pageblock of
  a range one after the other.
  - Unsafe: when the range lies in one pageblock, both are the same block; a
    second `set_migratetype_isolate()` on it returns `-EBUSY`.
  - Safe: test `isolate_start == isolate_end - pageblock_nr_pages` first, as
    `start_isolate_page_range()` does to set `skip_isolation`.
- **Potentially unsafe usage**: `start_isolate_page_range()` on an empty
  range.
  - Unsafe: with `start_pfn == end_pfn` and both aligned, it isolates the
    block at `start_pfn` and the block before it; the function has no test.
  - Safe: reject a zero length before the call, as `offline_pages()` does
    with `!nr_pages`.
- **Potentially unsafe usage**: using a rounded-out block without checking
  the zone.
  - Unsafe: when the zone starts or ends inside the block, part of the
    rounded block belongs to another zone or to none.
  - Safe: clamp to `zone->zone_start_pfn` and `zone_end_pfn()`, as
    `fast_isolate_around()` and `__reset_isolation_pfn()` in
    `mm/compaction.c` do.
  - Safe: refuse the block, as `prep_move_freepages_block()` does with
    `zone_spans_pfn()` on both ends; isolation then returns `-EBUSY`.
- Memmap of the boundary blocks: `isolate_single_pageblock()` calls
  `pfn_to_page()` on the rounded block start with no online test.
- Middle blocks of `start_isolate_page_range()`: the page passed to
  `set_migratetype_isolate()` comes from `__first_valid_page()`; for the
  boundary blocks it does not.

## Allocator alignment

**kmalloc alignment guarantee**

- Sizes that are not a power of two: the documented guarantee is the largest
  power-of-two divisor of the requested size.
- `create_boot_cache()` in `mm/slab_common.c`: computes
  `1U << (ffs(size) - 1)` from the cache size, so the alignment an object
  gets is that of its cache, never less than the documented value.
- `create_kmalloc_cache()`: adds `SLAB_KMALLOC` to the flags and computes no
  alignment; the raise is in `create_boot_cache()`, under that flag.
- `calculate_alignment()`: also raises every cache to `arch_slab_minalign()`
  and rounds up to `sizeof(void *)`.
- Documentation: the kernel-doc of `kmalloc()` in `include/linux/slab.h`
  states the same three guarantees as
  `Documentation/core-api/memory-allocation.rst`.
- `kmem_buckets_create()` with `CONFIG_SLAB_BUCKETS`: creates its caches with
  `kmem_cache_create_usercopy()`, align 0 and no `SLAB_KMALLOC`, so the
  size-based raise is not applied to them; their floor is what
  `calculate_alignment()` gives.

**Minimum alignment constants**

| Constant | Default when the arch does not define it | Where |
|---|---|---|
| `ARCH_DMA_MINALIGN` | `__alignof__(unsigned long long)` | `include/linux/cache.h` |
| `ARCH_KMALLOC_MINALIGN` | `ARCH_DMA_MINALIGN` if `ARCH_HAS_DMA_MINALIGN` and the value is above 8, else `__alignof__(unsigned long long)` | `include/linux/slab.h` |
| `ARCH_SLAB_MINALIGN` | `__alignof__(unsigned long long)` | `include/linux/slab.h` |

- `ARCH_HAS_DMA_MINALIGN`: defined by `include/linux/cache.h` only when the
  arch supplied `ARCH_DMA_MINALIGN`.
- `dma_get_cache_alignment()` default: `ARCH_DMA_MINALIGN` with
  `ARCH_HAS_DMA_MINALIGN`, otherwise 1.
- Configurations where `ARCH_KMALLOC_MINALIGN` is smaller: arm64 (8 vs 128),
  riscv with `CONFIG_RISCV_DMA_NONCOHERENT` (8 vs `L1_CACHE_BYTES`), parisc
  (16 vs 32 or 128).
- `CONFIG_DMA_BOUNCE_UNALIGNED_KMALLOC`: selected by arm64; by riscv only
  `if SWIOTLB`; not by parisc.
- `__kmalloc_minalign()` in `mm/slab_common.c`: decides the cache minimum;
  there is no kmalloc_minalign() without the underscores.
- `__kmalloc_minalign()`: returns `max(minalign, arch_slab_minalign())` on
  both paths; `ARCH_KMALLOC_MINALIGN` is not a second floor there.
- Without the bounce option, or when `is_swiotlb_allocated()` is false: every
  kmalloc cache is at least `dma_get_cache_alignment()` aligned, and no
  `kmalloc()` buffer is bounced for alignment.
- `new_kmalloc_cache()`: when the minimum exceeds `ARCH_KMALLOC_MINALIGN`,
  aliases a small size class to the cache of the rounded-up size, for every
  cache type.
- `dma_kmalloc_needs_bounce()`: receives the device, the mapped length and
  the direction; it sees neither the address nor the enclosing object.
- `dma_kmalloc_size_aligned()`: passes any length of
  `2 * ARCH_DMA_MINALIGN` or more without a look at `kmalloc_size_roundup()`.
- `kernel/dma/direct.c`: when a bounce is needed and `is_swiotlb_active()` is
  false or `DMA_ATTR_REQUIRE_COHERENT` is set, the map returns
  `DMA_MAPPING_ERROR`.
- `ARCH_KMALLOC_MINALIGN`: not a DMA-safe alignment on these configurations;
  `ARCH_DMA_MINALIGN` is the build-time value, `dma_get_cache_alignment()`
  the run-time one.
- `____cacheline_aligned`: is `SMP_CACHE_BYTES` (`include/vdso/cache.h`);
  arm64 has `L1_CACHE_BYTES` 64 and `ARCH_DMA_MINALIGN` 128, so it does not
  isolate a DMA member there.
- `__dma_from_device_group_begin()` and `__dma_from_device_group_end()`:
  defined in `include/linux/dma-mapping.h`; they add
  `__aligned(ARCH_DMA_MINALIGN)` only under `ARCH_HAS_DMA_MINALIGN`.
- **Potentially unsafe usage**: mapping a member of a `kmalloc()`ed struct
  for `DMA_FROM_DEVICE` or `DMA_BIDIRECTIONAL`.
  - Unsafe: on a non-coherent device when the member shares
    `ARCH_DMA_MINALIGN` bytes with a field the CPU writes; the length test in
    `dma_kmalloc_needs_bounce()` cannot detect it.
  - Unsafe: when the member is aligned but the allocation size is not a
    multiple of `ARCH_DMA_MINALIGN` (for example a trailing flexible array);
    on arm64 when `__kmalloc_minalign()` took the bounce path, 136 bytes
    lands in the 192-byte cache, which `create_boot_cache()` aligns to 64.
  - Safe: member between `__dma_from_device_group_begin()` and
    `__dma_from_device_group_end()` in a struct allocated at exactly its
    `sizeof`, as `probe_common()` does for `struct virtrng_info` in
    `drivers/char/hw_random/virtio-rng.c`; the size rule in
    `create_boot_cache()` then aligns the base.
  - Safe: `DMA_TO_DEVICE`, or a coherent device; `dma_kmalloc_safe()` defines
    both.

**Origin of page-aligned memory**

- Large-kmalloc test: `PageLargeKmalloc()` and `folio_test_large_kmalloc()`,
  generated by `PAGE_TYPE_OPS(LargeKmalloc, large_kmalloc, large_kmalloc)` in
  `include/linux/page-flags.h`; `___kmalloc_large_node()` in `mm/slub.c` sets
  it.
- `PageSlab()` and `PageLargeKmalloc()`: test the page type of the page
  passed; `alloc_slab_page()` and `___kmalloc_large_node()` set it on the
  head page only.
- Pointer into a tail page of a multi-page slab: `PageSlab(virt_to_page(p))`
  is false; use `folio_test_slab(virt_to_folio(p))` or
  `PageSlab(virt_to_head_page(p))`, as `free_resource()` in
  `kernel/resource.c` does.
- `kfree()` and `__ksize()` in `mm/slub.c`: use `virt_to_page()`, then
  `page_slab()` and `PageLargeKmalloc()`, not a folio test.
- `kfree()` on a pointer that is neither slab nor large kmalloc:
  `free_large_kmalloc()` warns, dumps the page and returns without freeing.
- `put_page()` on a slab or large-kmalloc page: returns without action.
- `get_page()` on a slab or large-kmalloc page: `WARN_ON_ONCE()` and no
  reference taken.
- Slab and large-kmalloc pages: allocated frozen (`alloc_frozen_pages()`), so
  the `page_count()` test in `sendpage_ok()` rejects them too.
- `mem_dump_obj()` in `mm/util.c`: only prints where a pointer came from,
  returns nothing, and is an empty stub without `CONFIG_PRINTK`.
- `kmem_dump_obj()` in `mm/slab_common.c`: shows the safe order, a
  `virt_addr_valid()` test before `virt_to_slab()`.
- `is_vmalloc_addr()` without `CONFIG_MMU`: constant `false`
  (`include/linux/mm.h`).
- `kvfree()`: defined in `mm/slub.c`.

## Model gaps

### Other mistakes models make

- Models take a large `kmalloc()` to be an ordinary refcounted compound
  page. `free_large_kmalloc()` in `mm/slub.c` frees it with
  `free_frozen_pages()`.
- Models know the `CMA_MIN_ALIGNMENT_BYTES` rule only for
  `cma_init_reserved_mem()` and `cma_declare_contiguous_nid()`.
  `cma_declare_contiguous_multi()` aligns the start and end of each
  candidate range to at least it, and `cma_reserve_early()` returns `NULL`
  for a size that is not aligned to it.
- Models take the tools `PAGE_MASK` to match the kernel one.
  `tools/include/linux/mm.h` fixes `PAGE_SHIFT` at 12 and defines
  `PAGE_MASK` as `unsigned long` in every build.
