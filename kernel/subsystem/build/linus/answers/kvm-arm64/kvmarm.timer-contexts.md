- `get_timer_map()`:

  | Case | direct | emulated |
  |---|---|---|
  | NV, `is_hyp_ctxt()` | hvtimer, hptimer | vtimer, ptimer |
  | NV, not `is_hyp_ctxt()` | vtimer, ptimer | hvtimer, hptimer |
  | VHE, no NV | vtimer, ptimer | none |
  | nVHE | vtimer | ptimer |

- `direct_ptimer`: NULL on nVHE; users that can run there test it, or pass it
  to a helper that accepts NULL, for example `kvm_timer_pending()` and
  `timer_get_offset()`.
- `vm_offset` in `timer_context_init()`: `voffset` for `TIMER_VTIMER`,
  `poffset` for the other three.
- `vm_offset` of a protected VM: NULL, which reads as offset 0.
- NV vtimer: `kvm_timer_vcpu_reset()` points `vm_offset` at `poffset` and
  `vcpu_offset` at the `CNTVOFF_EL2` slot.
- `kvm_vm_ioctl_set_counter_offset()`: holds `kvm->lock` and every vCPU mutex;
  it does not take `config_lock`.
- `-EBUSY` from it: only when `kvm_trylock_all_vcpus()` fails; there is no
  test that a vCPU has run.
- `-EINVAL` from it: protected VM, or `reserved` non-zero.
- Legacy counter write: `arch_timer_set_user()` in `arch/arm64/kvm/sys_regs.c`
  writes the VM-wide offset with `timer_set_offset()`, unless
  `KVM_ARCH_FLAG_VM_COUNTER_OFFSET` is set.
- `arch_timer_set_user()` and `kvm_timer_vcpu_init()`: take no VM-wide lock
  for the write.
