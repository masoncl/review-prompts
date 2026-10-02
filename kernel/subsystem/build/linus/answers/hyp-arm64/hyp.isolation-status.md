- Status per mechanism, as `Documentation/virt/kvm/arm/pkvm.rst` gives it:

| Mechanism | Status |
|---|---|
| CPU memory isolation | anonymous memory and metadata pages |
| CPU state isolation | Unimplemented |
| DMA isolation using an IOMMU | Unimplemented |
| Proxying of Trustzone services | FF-A and PSCI calls from the host |
| Protected VM firmware (pvmfw) | Unimplemented |

- Device assignment and attestation: not mentioned in
  `Documentation/virt/kvm/arm/pkvm.rst`.
- Guest-initiated share and unshare: implemented. `kvm_handle_pvm_hvc64()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` reaches `__pkvm_guest_share_host()` and
  `__pkvm_guest_unshare_host()`.
- Teardown reclaim: implemented, `__pkvm_host_reclaim_page_guest()`; from the
  host it is reached only through `__pkvm_reclaim_dying_guest_page()`, once
  `__pkvm_start_teardown_vm()` has set `is_dying`.
- Taint: `pkvm_init_host_vm()` in `arch/arm64/kvm/pkvm.c` itself calls
  `add_taint(TAINT_USER, LOCKDEP_STILL_OK)` when `type` has
  `KVM_VM_TYPE_ARM_PROTECTED`.
- Taint timing: at `KVM_CREATE_VM` (`kvm_arch_init_vm()`), right after the
  `__pkvm_reserve_vm` hypercall succeeds, before the hyp VM exists; the hyp VM
  is built later by `pkvm_create_hyp_vm()`.
- Non-protected VM under pKVM: also goes through `pkvm_init_host_vm()` and
  reserves a handle, without taint.
- `KVM_VM_TYPE_ARM_PROTECTED` without protected mode: `kvm_arch_init_vm()`
  returns `-EINVAL`, no taint.
