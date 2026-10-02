- `struct pkvm_hyp_vm`: the vCPU array is `vcpus[]`, sized by
  `kvm.created_vcpus`; there is no separate count or refcount field.
- Hyp VM reference count: the `refcount` of the `struct hyp_page` backing the
  hyp VM, changed under `vm_table_lock` by `pkvm_load_hyp_vcpu()`,
  `pkvm_put_hyp_vcpu()`, `get_pkvm_hyp_vm()` and `put_pkvm_hyp_vm()`.
- `loaded_hyp_vcpu` in `struct pkvm_hyp_vcpu`: points at the per-CPU variable
  of the same name in `arch/arm64/kvm/hyp/nvhe/pkvm.c`; NULL when not loaded.
- How a hypercall names its object, for example:

| Hypercall | VM named by | vCPU named by |
|---|---|---|
| `__pkvm_init_vm` | host `struct kvm *`; EL2 reads `arch.pkvm.handle` from it | - |
| `__pkvm_init_vcpu` | handle | host `struct kvm_vcpu *` |
| `__pkvm_vcpu_load` | handle | `vcpu_idx` |
| `__kvm_vcpu_run` | - | host `struct kvm_vcpu *`, checked against the loaded hyp vCPU |
| `__pkvm_host_share_guest`, `__pkvm_host_donate_guest`, `__pkvm_host_relax_perms_guest`, `__pkvm_host_mkyoung_guest` | - | none; the hyp vCPU loaded on this CPU |
| `__pkvm_host_unshare_guest`, `__pkvm_host_wrprotect_guest`, `__pkvm_host_test_clear_young_guest`, `__pkvm_tlb_flush_vmid` | handle | - |

- `get_vm_by_handle()`: returns NULL for a handle that is reserved but whose
  hyp VM is not created (`RESERVED_ENTRY`), and asserts `vm_table_lock`.
- Handle 0 on the host means "no handle":
  `pkvm_pgtable_stage2_destroy_range()` and `__pkvm_destroy_hyp_vm()` test it.
- `get_np_pkvm_hyp_vm()`: returns NULL for a protected VM, so
  `__pkvm_host_unshare_guest`, `__pkvm_host_wrprotect_guest` and
  `__pkvm_host_test_clear_young_guest` fail with `-EINVAL` on one.
- `kvm_vm_is_protected()`: a macro in `arch/arm64/include/asm/kvm_host.h`,
  `is_protected_kvm_enabled() && (kvm)->arch.pkvm.is_protected`.
- At EL2 the hyp vCPU's `vcpu.kvm` points at the hyp VM's embedded
  `struct kvm`, so `vcpu_is_protected()` there reads the hypervisor's copy.
