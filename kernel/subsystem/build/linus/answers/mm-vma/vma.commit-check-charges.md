- Flag name: code in `mm/` tests and sets `VMA_ACCOUNT_BIT`, for example
  through `vma_test()`, `vma_flags_test()` and `vma_flags_set()`; `VM_ACCOUNT`
  is still defined in `include/linux/mm.h`, but in `mm/` it is only in comments.
- LSM hook name: `vm_enough_memory`; there is no function named
  security_vm_enough_memory.
- `__mmap_region()` in `mm/vma.c`: the charge is made in `__mmap_setup()` and
  kept in `map.charged`; the `unacct_error:` label gives it back. There is no
  local `charged` in `mmap_region()`.
- `__mmap_region()` when `mmap_action_complete()` fails: returns with no
  `vm_unacct_memory()`; the VMA is already linked, and `mmap_action_finish()`
  unmaps it with `do_munmap()`, which uncharges by flag.
- Uncharge by flag: done in `vms_complete_munmap_vmas()` and by the callers of
  `tear_down_vmas()` in `mm/mmap.c`; `remove_vma()` has no
  `vm_unacct_memory()` call.
- `dup_mmap()` in `mm/mmap.c`: `charge` is reset for each VMA; `fail_nomem:`
  gives back only the charge of the VMA not yet stored in the new tree.
- `dup_mmap()` VMAs already stored in the new tree: uncharged by flag, from
  the count `tear_down_vmas()` returns.
- `acct_stack_growth()` in `mm/vma.c`: gives nothing back; the overcommit
  check is its last test, and `expand_upwards()` and `expand_downwards()`
  cannot fail once it returns 0. A failure point added after it would have to
  uncharge `grow`.
