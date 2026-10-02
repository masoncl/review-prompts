- Models take `guest_lock_component()` to be one of several places that take
  the `lock` of `struct pkvm_hyp_vm`. No other code takes that lock
  (`arch/arm64/kvm/hyp/nvhe/mem_protect.c`).
- Models know of no hypercall that must serve both a trusted and an
  untrusted host. The tracing hypercalls, for example `__tracing_load`, sit
  between `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` and
  `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` in `arch/arm64/include/asm/kvm_asm.h`,
  so `handle_host_hcall()` accepts them with and without pKVM.
- Models take EL2 to donate every host buffer it uses. `__admit_host_mem()`
  in `arch/arm64/kvm/hyp/nvhe/trace.c` skips the donation when
  `!is_protected_kvm_enabled()`.
- Models take a guest share request on an unmapped IPA to return an error to
  the guest. `__pkvm_memshare_page_req()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` rewinds ELR_EL2 by 4 before the exit to
  the host, so the guest executes the HVC again on its next entry.
- Models take `hyp_fixblock_map()` to return the slot base. It returns the
  slot address plus `offset_in_page(phys)`
  (`arch/arm64/kvm/hyp/nvhe/mm.c`).
- Models take HCR_EL2 to be written with `write_sysreg()`. C code under
  `arch/arm64/` uses only `write_sysreg_hcr()` or `sysreg_clear_set_hcr()`
  and assembly uses `msr_hcr_el2`; these carry the barriers for
  `CONFIG_AMPERE_ERRATUM_AC04_CPU_23`.
- Models list no key switch on entry from the host. With
  `CONFIG_ARM64_PTR_AUTH_KERNEL`, `ARM64_HAS_ADDRESS_AUTH` and
  `ARM64_KVM_PROTECTED_MODE`, `__host_exit` saves the host's
  pointer-authentication keys and loads EL2's own from `kvm_hyp_ctxt`;
  `pkvm_hyp_init_ptrauth()` in `arch/arm64/kvm/arm.c` generates them.
- Models take a host stage-2 unmap to need only the page-table update. With
  `ARM64_WORKAROUND_4193714`, `host_stage2_set_owner_metadata_locked()`
  also makes a firmware call through `pkvm_sme_dvmsync_fw_call()`.
- Models take UBSAN to be always off in the nVHE object.
  `nvhe_hyp_panic_handler()` in `arch/arm64/kvm/handle_exit.c` decodes
  UBSAN BRKs under `CONFIG_UBSAN_KVM_EL2` and, under `CONFIG_CFI`, CFI BRKs,
  and both are fatal.
