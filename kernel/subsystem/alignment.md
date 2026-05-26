# Alignment Helpers

## Generic ALIGN Semantics

`ALIGN(x, a)` rounds `x` **up** to an `a` boundary. If `x` is already aligned,
the result is `x`, not the next boundary. `ALIGN_DOWN(x, a)` rounds `x` **down**
to an `a` boundary. `IS_ALIGNED(x, a)` tests whether `x` is already aligned.

The alignment argument `a` is expected to be a power-of-two value.

For a half-open range `[start, end)`, use `ALIGN_DOWN(start, a)` and
`ALIGN(end, a)` to cover the whole range. Use `ALIGN(start, a)` and
`ALIGN_DOWN(end, a)` only when selecting fully-contained aligned chunks.

## Page Alignment Helpers

`PAGE_ALIGN(addr)` is `ALIGN(addr, PAGE_SIZE)`. `PAGE_ALIGN_DOWN(addr)` is
`ALIGN_DOWN(addr, PAGE_SIZE)`. `PAGE_ALIGNED(addr)` tests `PAGE_SIZE`
alignment. These helpers operate on addresses, not PFNs.

## Pageblock Alignment Helpers

`pageblock_nr_pages` is `1UL << pageblock_order`. Pageblock helpers operate on
PFNs, not byte addresses:

```c
#define pageblock_align(pfn)       ALIGN((pfn), pageblock_nr_pages)
#define pageblock_aligned(pfn)     IS_ALIGNED((pfn), pageblock_nr_pages)
#define pageblock_start_pfn(pfn)   ALIGN_DOWN((pfn), pageblock_nr_pages)
#define pageblock_end_pfn(pfn)     ALIGN((pfn) + 1, pageblock_nr_pages)
```

`pageblock_start_pfn(pfn)` returns the inclusive start PFN of the pageblock
containing `pfn`. `pageblock_end_pfn(pfn)` returns the exclusive end PFN of the
pageblock containing `pfn`; when `pfn` is itself pageblock-aligned, this is the
next pageblock boundary, not `pfn`.

`pageblock_align(pfn)` rounds **up** to the first pageblock boundary at or after
`pfn`. It is not equivalent to `pageblock_start_pfn(pfn)` for an unaligned PFN.

Example with `pageblock_nr_pages == 1024`:

| PFN | `pageblock_start_pfn()` | `pageblock_align()` | `pageblock_end_pfn()` |
|-----|-------------------------|---------------------|-----------------------|
| 2048 | 2048 | 2048 | 3072 |
| 2049 | 2048 | 3072 | 3072 |

For a half-open PFN range `[start_pfn, end_pfn)`, align the covering range with
`pageblock_start_pfn(start_pfn)` and `pageblock_end_pfn(end_pfn - 1)` when the
range is non-empty.

## Common Review Mistakes

- Treating `ALIGN(x, a)` as strictly greater than `x`; it returns `x` when
  already aligned.
- Treating `ALIGN_DOWN(x, a)` as a no-op for unaligned values; it moves to the
  previous boundary.
- Passing an order where a size/count is required. Use `1UL << order`,
  `PAGE_SIZE << order`, or `pageblock_nr_pages`, not raw `order`.
- Confusing byte-address helpers (`PAGE_ALIGN()`) with PFN helpers
  (`pageblock_*_pfn()`).
- Treating `pageblock_end_pfn(pfn)` as inclusive. It is an exclusive end PFN.
- Passing an exclusive range end directly to `pageblock_end_pfn()` when the
  intended input is the last PFN in the range; use `end_pfn - 1` for non-empty
  half-open ranges.
