- `ESR_ELx_ERET_ISS_ERET` is 0x2 and `ESR_ELx_ERET_ISS_ERETA` is 0x1; test
  them with `esr_iss_is_eretax()` and `esr_iss_is_eretab()`.
- FPAC syndrome: the trapped value is masked with
  `ESR_ELx_ERET_ISS_ERETA | ESR_ELx_IL`, then `ESR_ELx_EC_FPAC` is inserted.
  IL is kept from the trapped syndrome; ISS bit 1 and ISS2 are dropped.
- Injection needs both `kvm_has_pauth(vcpu->kvm, FPACCOMBINE)` and
  `PSR_IL_BIT` clear in the SPSR returned by
  `kvm_check_illegal_exception_return()`.
- `kvm_auth_eretax()` in `arch/arm64/kvm/pauth.c`: returns true without
  authenticating when the key's enable bit (`SCTLR_EL1_EnIA` or
  `SCTLR_EL1_EnIB`) is clear in the guest's SCTLR_EL2; the ELR is then used
  as it is and no FPAC is possible.
- Mangled ELR on failure: `corrupt_addr()` writes the error code only when the
  guest lacks PAuth2; with PAuth2 the value is `ptr ^ (pac & mask)`.
- When FPAC is injected, `kvm_emulate_nested_eret()` returns before the
  PC/PSTATE switch; the exception return is not performed.
- `kvm_handle_eret()` in `arch/arm64/kvm/handle_exit.c` gates the emulation:
  - ERETAx without `vcpu_has_ptrauth()`: goes to `kvm_handle_ptrauth()`, which
    injects UNDEF.
  - not `is_hyp_ctxt()`: the trap is forwarded with the unmodified syndrome.
- `kvm_hyp_handle_eret()` in `arch/arm64/kvm/hyp/vhe/switch.c`: returns false
  when `kvm_auth_eretax()` fails, so `kvm_emulate_nested_eret()` runs the
  authentication a second time.
