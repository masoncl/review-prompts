- Where the order is written: the one-line comment above
  `enum pkvm_component_id` in
  `arch/arm64/kvm/hyp/include/nvhe/mem_protect.h`; there is no comment beside
  the wrappers in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `enum pkvm_component_id`: exactly `PKVM_ID_HOST`, `PKVM_ID_HYP`,
  `PKVM_ID_GUEST`; there is no FF-A value.
- Order enforcement: none; `host_lock_component()`, `hyp_lock_component()`
  and `guest_lock_component()` call `hyp_spin_lock()` with no order check.
- `__pkvm_host_force_reclaim_page_guest()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`: takes `vm_table_lock`, then host,
  then guest, and releases in reverse.
- `vm_table_lock` in that function: held to the end because the VM comes
  from `get_vm_by_handle()` through `host_stage2_decode_gfn_meta()` and no
  reference is taken on it.
- `__pkvm_init_vcpu()`: holds `vm_table_lock` while `hyp_pin_shared_mem()`
  takes host then hyp.
- Nesting sites: those two functions are the only ones that take a component
  lock under `vm_table_lock`.
- `__pkvm_init_vm()`: does not hold `vm_table_lock` around
  `kvm_guest_prepare_stage2()`; `insert_vm_table_entry()` takes it
  afterwards.
- There is no __pkvm_teardown_vm() here; `__pkvm_start_teardown_vm()` and
  `__pkvm_finalize_teardown_vm()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c` do that.
- `__pkvm_finalize_teardown_vm()`: drops `vm_table_lock` before
  `reclaim_pgtable_pages()` takes the guest lock.
