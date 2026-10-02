- Tier: `lru_tier_from_refs()` in `include/linux/mm_inline.h` returns
  `MAX_NR_TIERS - 1` when its `workingset` argument is true, else
  `order_base_2(refs)`.
- `folio_lru_refs()`: 0 when `PG_referenced` is clear, else the
  `LRU_REFS_MASK` value plus one.
- `LRU_REFS_FLAGS`: `LRU_REFS_MASK | BIT(PG_referenced)`; `PG_workingset` is
  not part of it.
- Bit position: `LRU_REFS_PGOFF` is `LRU_GEN_PGOFF - LRU_REFS_WIDTH`, so the
  counter sits just below the generation field.
- Flags word: `folio->flags` is a struct; the generation and the counter are
  read and written through `folio->flags.f`.
