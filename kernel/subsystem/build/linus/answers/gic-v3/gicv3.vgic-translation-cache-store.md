- `vgic_its_cache_translation()` makes one test of its own: `irq->hw`, which
  returns before the reference is taken.
- Its caller is `vgic_its_resolve_lpi()`, which returns before the call when
  the ITS is disabled, the ITE or a mapped collection is missing, the vCPU does
  not exist, or `vgic_lpis_enabled()` is false.
- The cache has no size limit and no eviction; `xa_store()` displaces an entry
  only when the same key is already present.
