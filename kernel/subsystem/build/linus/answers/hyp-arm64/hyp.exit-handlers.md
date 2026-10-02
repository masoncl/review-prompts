- `fixup_guest_exit()`: in `arch/arm64/kvm/hyp/nvhe/switch.c`; true re-enters
  the guest, false returns to the host.
- `__fixup_guest_exit()`: in `arch/arm64/kvm/hyp/include/hyp/switch.h`; does
  not save ELR_EL2 into the vCPU PC.
- Guest PC: saved by `__sysreg_save_state_nvhe(guest_ctxt)` after the loop;
  `regs.pstate` is saved on every exit by `synchronize_vcpu_pstate()`.
- There is no early_exit_filter() here; the AArch32 test is inline in
  `fixup_guest_exit()`, before `__fixup_guest_exit()`, on every exit.
- `hyp_exit_handlers`: has no entry for `ESR_ELx_EC_PAC` or
  `ESR_ELx_EC_HVC64`.
- `pvm_exit_handlers` versus `hyp_exit_handlers`:
  - adds `ESR_ELx_EC_HVC64`, `kvm_handle_pvm_hvc64()`;
  - `ESR_ELx_EC_SYS64` is `kvm_handle_pvm_sys64()`;
  - `ESR_ELx_EC_SVE` is `kvm_handle_pvm_restricted()`;
  - has no `ESR_ELx_EC_CP15_32` entry;
  - the remaining entries are the same.
- There is no kvm_handle_pvm_fpsimd here; `ESR_ELx_EC_FP_ASIMD` uses
  `kvm_hyp_handle_fpsimd()` in both tables.
- `kvm_handle_pvm_sys64()`: calls `kvm_hyp_handle_sysreg()` first, then
  `kvm_handle_pvm_sysreg()`.
- `kvm_handle_pvm_sysreg()` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`: register
  not in `pvm_sys_reg_descs` gets UNDEF and re-entry; a descriptor with NULL
  `access` returns to the host; otherwise it is emulated at EL2.
- `kvm_handle_pvm_hvc64()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`: handles four
  KVM vendor calls at EL2 and returns any other function to the host; a
  memory-share call on an unmapped page goes to the host as a faked data
  abort.
- `VCPU_INITIALIZED` on AArch32: cleared in the hyp vCPU's `cflags`;
  `sync_hyp_vcpu()` does not copy `cflags`, and no code under
  `arch/arm64/kvm/hyp/` tests the flag.
- Host on `ARM_EXCEPTION_IL`: `handle_exit()` returns `-EINVAL` with
  `KVM_EXIT_FAIL_ENTRY`.
