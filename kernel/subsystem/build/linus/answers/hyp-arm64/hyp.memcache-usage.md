- Snapshot: `refill_memcache()` in `arch/arm64/kvm/hyp/nvhe/mm.c` copies
  `*host_mc` into the local `tmp`, works on `&tmp`, and writes `tmp` back.
  `flush_hyp_vcpu()` does not touch `pkvm_memcache`.
- `READ_ONCE()` is not used: `admit_host_page()` reads `nr_pages` and `head`,
  and `pop_hyp_memcache()` reads both again.
- **Potentially unsafe usage**: donating `mc->head` and then calling
  `pop_hyp_memcache()` on the same header.
  - Unsafe: when the header is in host memory; the host can change `head`
    between the two reads, and the pop dereferences a page that was not donated.
  - Safe: when the header is a hyp-private copy, as `refill_memcache()` passes
    `&tmp` to `admit_host_page()`.
  - Safe: `pop_hyp_memcache()` on the hyp vCPU's `pkvm_memcache`, as in
    `guest_s2_zalloc_page()`; its pages were donated by `admit_host_page()`.
  - Safe: `push_hyp_memcache()` on a header in host memory, as
    `teardown_donated_memory()` does; push stores `head` and never
    dereferences it.
- `min_pages`: `pkvm_refill_memcache()` passes the host's
  `host_vcpu->arch.pkvm_memcache.nr_pages`, read apart from the snapshot. It is
  only the loop bound; the hyp memcache has no capacity limit.
- Alignment of `head`: not checked. `hyp_phys_to_pfn()` and the `PAGE_MASK` in
  `pop_hyp_memcache()` both drop the low bits, so both name the same page.
- Failed donation: `refill_memcache()` returns `-ENOMEM` whatever the donation
  error was. Pages already admitted stay in the hyp memcache.
- Host memcache address: taken from `hyp_vcpu->host_vcpu`, which
  `init_pkvm_hyp_vcpu()` pinned with `hyp_pin_shared_mem()`; it is not a
  hypercall argument.
- Hyp vCPU memcache: no lock protects it. `pkvm_refill_memcache()` callers take
  the vCPU from `pkvm_get_loaded_hyp_vcpu()`; teardown pops it only after
  `get_pkvm_unref_hyp_vm_locked()` saw a zero page count.
- `guest_s2_zalloc_page()`: sets only `refcount` in `struct hyp_page`, not
  `order`. `__hyp_attach_page()` forces order 0 for a page outside the pool
  range.
