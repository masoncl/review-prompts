- `KVM_BUG_ON()` examples: the `nested_run_pending` test in
  `__vmx_handle_exit()` and `handle_nmi_window()` in `arch/x86/kvm/vmx/vmx.c`;
  both return `-EIO` on a hit.
- `KVM_BUG_ON_DATA_CORRUPTION()`: used only by the rmap helpers in
  `arch/x86/kvm/mmu/mmu.c`, for example `pte_list_remove()`.
- `KVM_EMULATOR_BUG_ON()` in `arch/x86/kvm/kvm_emulate.h`: the form for x86
  emulator code, which has no `struct kvm`; it goes through
  `emulator_vm_bugged()`.
- `TDX_BUG_ON()` and its numbered variants in `arch/x86/kvm/vmx/tdx.c`: with a
  non-NULL `struct kvm`, same effect as `KVM_BUG_ON()` plus a ratelimited
  print of the SEAMCALL error; with a NULL one, only the WARN and the print.
- A fatal state that a guest can cause: `kvm_vm_dead()` with no WARN, then
  `-EIO`; see `tdx_handle_ept_violation()`.
