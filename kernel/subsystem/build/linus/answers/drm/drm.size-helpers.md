- Arguments of `size_mul()`, `size_add()` and `size_sub()`: are `size_t`
  parameters, so a `u64` count is truncated on 32-bit before the overflow
  test runs.
- `kmalloc_objs()`, `kzalloc_objs()`, `kvmalloc_objs()`, `kzalloc_flex()` and
  relatives in `include/linux/slab.h`: used for arrays in DRM core, beside
  `kmalloc_array()`; they call `size_mul()` or `struct_size_t()` and hand the
  result, saturated or not, to the allocator.
- `kmalloc_array()` and `kvmalloc_array()`: return NULL from
  `check_mul_overflow()` without calling the allocator.
- **Potentially unsafe usage**: relying on the allocator to reject a size
  built from a count that userspace controls.
  - Unsafe: without `__GFP_NOWARN`, when nothing bounds the count first;
    `__kvmalloc_node_noprof()` in `mm/slub.c` hits `WARN_ON_ONCE()` for a
    size above `INT_MAX`, and `alloc_order_allowed()` in `mm/page_alloc.c`
    hits `WARN_ON_ONCE_GFP()` for an order above `MAX_PAGE_ORDER`.
  - Safe: with `__GFP_NOWARN`, which both tests honour, as `submit_create()`
    in `drivers/gpu/drm/msm/msm_gem_submit.c` does.
- **Potentially unsafe usage**: passing the result to code that rounds it up
  before any size test.
  - Unsafe: through `PAGE_ALIGN()`, `ALIGN()` or `round_up()` when nothing
    bounds the count first; they turn `SIZE_MAX` into 0.
    `drm_gem_shmem_create()`, in `__drm_gem_shmem_create()`, and
    `drm_gem_dma_create()` round their `size` argument this way first.
  - Safe: through `kmalloc_size_roundup()`, which returns a size above
    `KMALLOC_MAX_SIZE` unchanged, as `dma_resv_list_alloc()` in
    `drivers/dma-buf/dma-resv.c` does.
  - Safe: when the count is already bounded, as in `swiotlb_init_remap()` in
    `kernel/dma/swiotlb.c`, which has allocated `nslabs << IO_TLB_SHIFT`
    bytes before it calls `PAGE_ALIGN()` on `array_size()` of `nslabs` slots.
- **Potentially unsafe usage**: passing the result to a sink that is not an
  allocator and then adds to it.
  - Unsafe: when the sink does plain `+` on the length with no bound before
    it; `SIZE_MAX` wraps to a small value.
  - Safe: when the sink bounds the length first, as
    `drm_property_create_blob()` does with `length > INT_MAX -
    sizeof(struct drm_property_blob)`; `drm_plane_add_size_hints_property()`
    passes it `array_size()`.
