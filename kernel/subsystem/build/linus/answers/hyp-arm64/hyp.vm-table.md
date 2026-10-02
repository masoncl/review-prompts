- `get_vm_by_handle()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`: returns NULL for
  a slot holding `RESERVED_ENTRY`, as well as for an out-of-range index.
- Dying VM: `get_vm_by_handle()` returns it; callers that care test
  `hyp_vm->kvm.arch.pkvm.is_dying` themselves.
- NULL result, by caller: `__pkvm_init_vcpu()` returns `-ENOENT`; teardown,
  reclaim and the handle-based handlers that return a value, for example
  `handle___pkvm_host_unshare_guest()`, return `-EINVAL`;
  `host_stage2_decode_gfn_meta()` returns `-EAGAIN`; `pkvm_load_hyp_vcpu()`
  returns NULL.
- Handle: chosen by `allocate_vm_table_entry()` (first NULL slot) in
  `__pkvm_reserve_vm()`, which stores `RESERVED_ENTRY` there.
- VMID: `idx + 1`, set with `atomic64_set()` in `init_pkvm_hyp_vm()`, not in
  `insert_vm_table_entry()`; there is no VMID allocator at EL2.
- `__insert_vm_table_entry()`: returns `-EINVAL` unless the slot holds
  `RESERVED_ENTRY`.
