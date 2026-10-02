- `inject_abt64()` and `inject_undef64()` in `arch/arm64/kvm/inject_fault.c`:
  OR in `ESR_ELx_IL` unconditionally; neither calls
  `kvm_vcpu_trap_il_is32bit()`, including when `inject_abt64()` reports a
  fault taken from AArch32 EL0.
- `kvm_vcpu_trap_il_is32bit()`: no injection path calls it.
- `inject_abt32()`, `inject_undef32()`: build no ESR-format value, so there is
  no IL to set.
- `kvm_inject_nested_sea()`, `kvm_inject_nested_serror()`, and the emulated
  path of `kvm_inject_serror_esr()`: set `ESR_ELx_IL` unconditionally.
- Fake trapped syndromes written to `vcpu->arch.fault.esr_el2`
  (`__pkvm_memshare_page_req()`, `kvm_hyp_handle_impdef()`): also set
  `ESR_ELx_IL`.
- **Unsafe usage**: building a syndrome to inject into a guest from an EC
  constant such as `ESR_ELx_EC_UNKNOWN` without `ESR_ELx_IL`.
  - Safe: OR in `ESR_ELx_IL` unconditionally, as `inject_undef64()`,
    `kvm_inject_nested_sve_trap()` and `kvm_inject_nested_excl_atomic()` do.
- **Unsafe usage**: rewriting a syndrome that is injected or reported whole,
  EC included, with a mask that drops `ESR_ELx_IL`.
  - Safe: clear and replace only the field that changes, as
    `kvm_inject_size_fault()` and `handle_vncr_perm()` do for `ESR_ELx_FSC`,
    and `host_inject_mem_abort()` does for the EC.
  - Safe: an allow-list that names `ESR_ELx_IL`, as `set_thread_esr()`,
    `kvm_emulate_nested_eret()` and `kvm_handle_guest_sea()` use.
- `set_thread_esr()`: is in `arch/arm64/mm/fault.c`; it never sets
  `ESR_ELx_IL`. The IL user space sees is the hardware value: stored
  unmodified for a TTBR0 address, kept by the mask otherwise.
