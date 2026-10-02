- `__vm_id_reg()` in `arch/arm64/include/asm/kvm_host.h`: maps an encoding
  to its slot; there is no IDREG() macro.
- Outside `id_regs[]`: `ctr_el0`, `midr_el1`, `revidr_el1`, `aidr_el1` are
  separate fields of `struct kvm_arch`, reached through the same helper.
- Unknown encoding: `__vm_id_reg()` warns and returns NULL, which
  `kvm_read_vm_id_reg()` dereferences.
- Initialisation: `reset_vm_ftr_id_reg()`, called by `kvm_reset_sys_regs()`
  from `kvm_reset_vcpu()`; there is no kvm_reset_id_regs() or
  kvm_init_sysreg().
- First reset: reached from `__kvm_vcpu_set_target()`, which holds
  `config_lock` around `kvm_reset_vcpu()`.
- Later resets: the other callers of `kvm_reset_vcpu()` run without
  `config_lock`; `reset_vm_ftr_id_reg()` returns on
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED` before it reaches
  `kvm_set_vm_id_reg()`.
- `kvm_set_vm_id_reg()`: asserts `kvm->arch.config_lock`, does not take it.
- Writers: every call site of `kvm_set_vm_id_reg()` holds `config_lock`; the
  one outside `arch/arm64/kvm/sys_regs.c` is `kvm_vgic_finalize_idregs()`,
  so creating a vGIC rewrites three ID registers.
- `get_id_reg()`: takes `config_lock` until `kvm_vm_has_ran_once()`, then
  reads without it.
- pKVM non-protected VM: `vm_copy_id_regs()` copies `id_regs[]` from the
  host, and fails with `-EINVAL` if the host has not initialised them.
- pKVM, outside `id_regs[]`: `pkvm_init_features_from_host()` copies
  `ctr_el0` always and `midr_el1` only for a non-protected VM with
  `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS`.
- pKVM protected VM: `kvm_init_pvm_id_regs()` fills CRm 4 to 7 only.
