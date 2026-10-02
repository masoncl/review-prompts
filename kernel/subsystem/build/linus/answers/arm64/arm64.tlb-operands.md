- `__TLBI_VADDR()` and `__tlbi_user()`: `#undef`ed at the end of
  `arch/arm64/include/asm/tlbflush.h`, so unusable outside it.
- No __TLBI_VADDR_RANGE() or __tlbi_user_level() here; `__tlbi_range()`
  builds the range operand with `FIELD_PREP()` and the `TLBIR_ASID_MASK`
  family of masks.
- Ops are `tlbi_op` functions, not macro arguments;
  `__flush_s1_tlb_range_op()` and `__flush_s2_tlb_range_op()` paste `r##op`,
  so an op needs an r-prefixed twin, for example `vale1is()` and
  `rvale1is()`.
- KPTI second op: done inside the user op functions such as `vae1is()`;
  `vaale1is()`, the hyp ops and the stage-2 ops issue one TLBI only.
- `__tlbi_level_asid()` hint: written for any `level <= 3`, level 0
  included, when the CPU has `ARM64_HAS_ARMv8_4_TTL`.
- Unknown level: `TLBI_TTL_UNKNOWN`, which is `INT_MAX`; 0 does not mean
  unknown.
- `__tlbi_range()` hint: does not test `ARM64_HAS_ARMv8_4_TTL`; the two-bit
  field holds levels 1 to 3, and level 0 or above 3 is written as 0.
- `__flush_tlb_range_op()` order: single ops until 64K aligned (LPA2 only),
  range ops from scale 3 downwards, one single op last for an odd page.
- Limit: `__flush_tlb_range_limit_excess()`, used by both
  `__do_flush_tlb_range()` and `flush_tlb_kernel_range()`.
- Limit with range ops: `pages > MAX_TLBI_RANGE_PAGES`.
- Limit without range ops: `pages >= (MAX_DVM_OPS * stride) >> PAGE_SHIFT`;
  the constant is `MAX_DVM_OPS`, there is no MAX_TLBI_OPS definition.
- **Unsafe usage**: `pages * PAGE_SIZE` not a multiple of `stride` in
  `__flush_tlb_range_op()`.
  - Unsafe: the single-op path adds `stride` and the loop runs while
    `addr != end`, so it steps past `end`.
  - Safe: go through `__flush_tlb_range()`, which rounds both ends to
    `stride`; `__do_flush_tlb_range()` and `__flush_tlb_range_op()` do not
    round.
  - Safe: `flush_tlb_kernel_range()` rounds to `PAGE_SIZE` itself.
- **Unsafe usage**: calling `__flush_tlb_range_op()` with more than
  `MAX_TLBI_RANGE_PAGES` pages on a CPU with range ops.
  - Unsafe: `__TLBI_RANGE_NUM()` does not clamp to 31 and `FIELD_PREP()`
    masks the excess silently, while `addr` advances by the full count.
  - Safe: test `__flush_tlb_range_limit_excess()` first, as
    `flush_tlb_kernel_range()` does.
  - Safe: split the range, as `kvm_tlb_flush_vmid_range()` in
    `arch/arm64/kvm/hyp/pgtable.c` does with `min(pages,
    MAX_TLBI_RANGE_PAGES)`.
- **Unsafe usage**: a fixed level hint for a range that may hold entries of
  another level or table entries.
  - Unsafe: the hinted invalidation may skip those entries.
  - Safe: `TLBI_TTL_UNKNOWN`, as `flush_tlb_range()` passes.
  - Safe: a level derived from the mapping size, as
    `__flush_hugetlb_tlb_range()` in `arch/arm64/include/asm/hugetlb.h`
    does from `stride`.
  - Safe: the `TLBI_TTL_UNKNOWN` that `tlb_get_level()` returns when
    `tlb->freed_tables` is set or other than exactly one cleared level is
    recorded.
