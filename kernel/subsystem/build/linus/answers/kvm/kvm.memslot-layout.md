- `hva_node[2]`: `struct interval_tree_node`, not `struct rb_node`;
  `hva_tree` is a `struct rb_root_cached` used as an interval tree.
- `node_idx`: written once in `kvm_create_vm()` as the set's index in
  `__memslots[as_id][]`; it names the set, not whether it is active.
- Active set: only `kvm->memslots[as_id]` says which one it is.
- `KVM_MEMSLOT_GEN_UPDATE_IN_PROGRESS`: bit 63 of `generation`, set while
  `kvm_swap_active_memslots()` runs; it does not identify a set.
- New slot object: `kvm_set_memory_region()` allocates one for every change
  except delete; the request's values are written to the new object, never
  to the old one.
- `kvm_copy_memslot()`: only caller is `kvm_invalidate_memslot()`; it leaves
  the node arrays alone.
