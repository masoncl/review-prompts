| Stage | Hypercall | Host call site |
|---|---|---|
| 1 | `__pkvm_start_teardown_vm` | `pkvm_pgtable_stage2_destroy_range()` |
| 2, protected | `__pkvm_reclaim_dying_guest_page` | `__pkvm_pgtable_stage2_reclaim()` |
| 2, non-protected | `__pkvm_host_unshare_guest` | `__pkvm_pgtable_stage2_unshare()` |
| 3 | `__pkvm_finalize_teardown_vm` | `__pkvm_destroy_hyp_vm()` |

- Stages 1 and 2: reached from `kvm_arch_flush_shadow_all()` through
  `kvm_free_stage2_pgd()`; stage 3 from `kvm_arch_destroy_vm()`.
- `__pkvm_start_teardown_vm()`: `-EINVAL` for an unknown handle, a non-zero
  count, or a VM already dying.
- `__pkvm_reclaim_dying_guest_page()`: `-EINVAL` for an unknown handle or a
  VM not dying.
- `__pkvm_finalize_teardown_vm()`: `-EINVAL` for an unknown handle, a
  non-zero count, or a VM not dying.
- `-EBUSY`: returned by none of the three. `-ENOENT`: never for the handle
  or the count; `__pkvm_reclaim_dying_guest_page()` can pass it on from
  `get_valid_guest_pte()` for a gfn with no valid entry.
- `is_dying`: a field of `struct kvm_protected_vm`; EL2 uses the copy in
  `hyp_vm->kvm.arch.pkvm`, the host keeps its own in `kvm->arch.pkvm`.
- `is_dying` is tested at EL2 in four places only: `pkvm_load_hyp_vcpu()` and
  `__pkvm_start_teardown_vm()` refuse; reclaim and finalize require it.
- Not tested by: `__pkvm_init_vcpu()`, `get_pkvm_hyp_vm()`,
  `get_np_pkvm_hyp_vm()`, so handle-based unshare still works on a dying VM.
- Share, donate, relax-perms, mkyoung: no `is_dying` test; they need a
  loaded vCPU, and none can be loaded once the VM is dying.
- VM reserved but never created: `__pkvm_destroy_hyp_vm()` calls
  `__pkvm_unreserve_vm` instead of finalize.
