- Pool argument: `hyp_get_page()` and `hyp_put_page()` use the pool passed
  in; nothing derives it from the address and `struct hyp_page` records no
  pool.
- `hyp_page_to_pool()` in `arch/arm64/kvm/hyp/include/nvhe/memory.h`:
  unused, and names a `pool` field that `struct hyp_page` does not have.
- Address argument: any hyp linear-map VA inside the page;
  `arch/arm64/kvm/hyp/pgtable.c` passes `ctx->ptep`.
- `NULL` test: `guest_s2_zalloc_page()` tests the result itself;
  `hyp_zalloc_hyp_page()` and `host_s2_zalloc_page()` do not, and the test
  is in their caller in `arch/arm64/kvm/hyp/pgtable.c`.
- Guest pool callbacks: valid only under `guest_lock_component()`, which
  sets `current_vm`; `kvm_guest_prepare_stage2()` takes it around
  `__kvm_pgtable_stage2_init()` for that reason.
- There is no host_get_page() or host_put_page() at EL2; the host stage-2
  callbacks are `host_s2_get_page()` and `host_s2_put_page()`.
- **Unsafe usage**: `hyp_get_page()` or `hyp_put_page()` on a tail page of
  an order > 0 block that was not split.
  - Unsafe: tails have `refcount` 0, so the put hits `BUG_ON(!p->refcount)`
    in `hyp_page_ref_dec()`.
  - Safe: call `hyp_split_page()` on the head right after allocation, as
    `guest_s2_zalloc_pages_exact()` does; `guest_s2_free_pages_exact()` then
    puts each page.
- **Potentially unsafe usage**: `hyp_put_page()` into a pool whose
  `range_start`..`range_end` does not contain the page.
  - Unsafe: for a block larger than one page; `__hyp_attach_page()` forces
    order 0, so only the first page is zeroed and enters the pool.
  - Safe: for a single hyp-owned page with `refcount` 1, as the memcache
    page from `guest_s2_zalloc_page()` later freed by `guest_s2_put_page()`;
    `__hyp_attach_page()` inserts it at order 0 without coalescing.
