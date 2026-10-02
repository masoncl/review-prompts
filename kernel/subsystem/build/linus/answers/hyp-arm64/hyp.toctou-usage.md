- Requirement 1, the page is readable at EL2: it is pinned with
  `hyp_pin_shared_mem()` or was donated first. See "Pinning shared host
  memory" for why a shared, unpinned page is not enough.
- Requirement 2, one fetch: copy the field into a local or into
  `hyp_vcpu->vcpu`, validate or clamp the copy, use only the copy.
- `flush_hyp_vcpu()`: only the `hcr_el2` read uses `READ_ONCE()`; the other
  fields are plain assignments into `hyp_vcpu->vcpu`.
- `vcpu_idx`: `init_pkvm_hyp_vcpu()` reads it once with `READ_ONCE()`; the
  range check is in `register_hyp_vcpu()`, on the hyp copy.
- Snapshot of a whole object: `refill_memcache()` in
  `arch/arm64/kvm/hyp/nvhe/mm.c` copies the host `struct kvm_hyp_memcache`
  into a local; `__do_ffa_mem_xfer()` copies the host TX buffer into
  `hyp_buffers.tx` and parses that.
- Donate instead of copy: `__tracing_load()` in
  `arch/arm64/kvm/hyp/nvhe/trace.c`, in protected mode, donates the
  descriptor with `__pkvm_host_donate_hyp()` (through `__admit_host_mem()`),
  validates it in place, then gives it back.
- **Unsafe usage**: in protected mode, applying `kern_hyp_va()` to a pointer
  taken from a hypercall argument or from host memory after de-privilege, and
  dereferencing it without a pin or a donation.
  - Unsafe: the access faults at EL2 when the page is not mapped there.
  - Safe: pin first and keep the pin for the whole use, as
    `init_pkvm_hyp_vcpu()` and `__pkvm_init_vm()` do; `hyp_unpin_shared_mem()`
    is what unmaps.
  - Safe: compare the argument with an already pinned pointer and use that,
    as `__get_host_hyp_vcpus()` does with `hyp_vcpu->host_vcpu`.
  - Safe: donate the page before the first read, as `admit_host_page()` does
    before `pop_hyp_memcache()` reads the link stored in the page.
  - Safe: when `is_protected_kvm_enabled()` is false; `kvm_share_hyp()` then
    maps through `create_hyp_mappings()` and `__pin_shared_page()` skips the
    pin.
- **Potentially unsafe usage**: reading the same field of host memory twice.
  - Unsafe: when the first read is checked and the second is used as an
    index, a length or a pointer at EL2.
  - Safe: one `READ_ONCE()` into a local that is clamped to a hyp-owned limit
    before use, as `pkvm_vcpu_init_sve()` does with `kvm_host_sve_max_vl`.
  - Safe: when neither read is trusted. `pkvm_refill_memcache()` reads
    `nr_pages` twice, and each page is still validated by
    `__pkvm_host_donate_hyp()` in `admit_host_page()`.
