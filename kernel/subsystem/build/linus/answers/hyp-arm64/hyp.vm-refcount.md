- Count: `refcount` of the `struct hyp_page` for `hyp_virt_to_page(hyp_vm)`;
  `struct pkvm_hyp_vm` has no count field.
- Refusal: `get_pkvm_unref_hyp_vm_locked()` returns NULL while
  `hyp_page_count(hyp_vm)` is not zero, and `__pkvm_start_teardown_vm()` and
  `__pkvm_finalize_teardown_vm()` then return `-EINVAL`, not `-EBUSY`.
- `WARN_ON()`: none at EL2 for this; the host wraps both hypercalls in
  `WARN_ON()` in `arch/arm64/kvm/pkvm.c`.

| Takes a reference | Used by |
|---|---|
| `pkvm_load_hyp_vcpu()` | load; dropped by `pkvm_put_hyp_vcpu()` |
| `get_pkvm_hyp_vm()` | `__pkvm_reclaim_dying_guest_page()` |
| `get_np_pkvm_hyp_vm()` | unshare, wrprotect, test-clear-young, `handle___pkvm_tlb_flush_vmid()` |

- No reference by handle: the donate, share, relax-perms and mkyoung
  handlers use the loaded vCPU, whose load holds the reference.
- `__pkvm_init_vcpu()` and `__pkvm_host_force_reclaim_page_guest()`: take no
  reference; they hold `vm_table_lock` for the whole use.
- **Unsafe usage**: returning between `get_pkvm_hyp_vm()` or
  `get_np_pkvm_hyp_vm()` and `put_pkvm_hyp_vm()`.
  - Safe: put on every path after a non-NULL get, as
    `handle___pkvm_host_unshare_guest()` does; otherwise
    `get_pkvm_unref_hyp_vm_locked()` fails teardown with `-EINVAL` for good.
