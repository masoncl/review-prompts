- Handle: reserved earlier by `__pkvm_reserve_vm()`, called from
  `pkvm_init_host_vm()`; `__pkvm_init_vm()` reads it from
  `host_kvm->arch.pkvm.handle`, not from a register.
- Failed `__pkvm_init_vm()`: leaves the reservation; the host releases it
  with `__pkvm_unreserve_vm()` in `__pkvm_destroy_hyp_vm()`.
- PGD size and `mmu->vtcr`: from EL2's `host_mmu.arch.mmu.vtcr`, not from
  `host_kvm->arch.mmu.vtcr`.

| Step, in order | Failure | Undone |
|---|---|---|
| `hyp_pin_shared_mem()` of `host_kvm` | its error | nothing |
| `READ_ONCE()` of `created_vcpus`, below 1 | `-EINVAL` | unpin |
| `READ_ONCE()` of `arch.pkvm.handle`, below `HANDLE_OFFSET` | `-EINVAL` | unpin |
| `map_donated_memory()` of the VM | `-ENOMEM` | unpin |
| `map_donated_memory_noclear()` of the PGD | `-ENOMEM` | VM memory, unpin |
| `init_pkvm_hyp_vm()` | cannot fail | - |
| `kvm_guest_prepare_stage2()` | its error | both donations, unpin |
| `insert_vm_table_entry()` | `-EINVAL` | `kvm_guest_destroy_stage2()`, both donations, unpin |

- `init_pkvm_hyp_vm()`: reads `arch.pkvm.is_protected` with `READ_ONCE()`.
- `pkvm_init_features_from_host()`: reads `arch.flags` with `READ_ONCE()`;
  `arch.ctr_el0`, `arch.vgic.vgic_model`, `arch.vcpu_features` and
  `arch.midr_el1` with plain loads.
- Table entry: never removed by `__pkvm_init_vm()`; insertion is the last
  step, so no failure follows it.
