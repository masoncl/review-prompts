- `check_stable_address_space()` in `include/linux/oom.h`: tests
  `MMF_UNSTABLE`, the mark; returns `VM_FAULT_SIGBUS`, type `vm_fault_t`, not
  an errno. Non-fault callers pick their own result;
  `hmm_range_fault_unlocked_timeout()` returns `-EFAULT`, `unuse_mm()` skips
  the mm and returns 0.
- `mm->flags` is a private `mm_flags_t`; access is through `mm_flags_test()`
  and `mm_flags_set()`, not `test_bit()` on `mm->flags`.
- `__oom_reap_task_mm()`: sets the mark and zaps under the mmap read lock,
  from both `oom_reap_task_mm()` and `process_mrelease` in `mm/oom_kill.c`.
- Mmap read lock held by a walker: does not stop the mark appearing mid-walk.
  Only the mmap write lock excludes the reaper.
- `finish_fault()`: tests the mark only when the VMA is not `VM_SHARED`.
  `do_anonymous_page()` tests under the PTE lock.
- Failed-fork mm: `dup_mmap()` holds the child's write lock from before
  `__mt_dup()` until after `__mt_destroy()`. A walker that gets the lock sees
  an empty tree, never a half-built one or the parent's VMAs.
- `__mt_dup()` failure in `dup_mmap()`: the mark is not set; the tree is empty.
- In-tree lock-then-test walkers: `register_for_each_vma()` (write lock),
  `unuse_mm()` in `mm/swapfile.c`, `hmm_range_fault_unlocked_timeout()` in
  `mm/hmm.c` (read lock). No function in `mm/userfaultfd.c` tests the mark.
- Reaper as walker: `oom_reap_task_mm()` and `process_mrelease` hold only
  `mmgrab()`. They take the mmap read lock, then test `MMF_OOM_SKIP` under it.
- `exit_mmap()`: sets `MMF_OOM_SKIP` before taking the write lock under which
  it frees page tables and VMAs.
- `folio_referenced_one()` in `mm/rmap.c`: tests the mark with no mmap lock,
  next to `mm_users == 0`, only as a hint to skip a folio.
- There is no hpage_collapse_test_exit() here; `collapse_test_exit()` in
  `mm/khugepaged.c` tests `mm_users == 0`, as `ksm_test_exit()` does.
- **Potentially unsafe usage**: installing a new page in a private mapping of
  a foreign mm after testing the mark only under the mmap read lock.
  - Unsafe: when the page fills an empty entry; `__oom_reap_task_mm()` can set
    the mark and zap the range after the test, and the new page then stands
    where the task's data was.
  - Safe: test under the page table lock just before the install, as
    `migrate_vma_insert_page()` and `do_anonymous_page()` do.
  - Safe: test under the mmap write lock, as `register_for_each_vma()` does;
    `__oom_reap_task_mm()` runs only under the mmap read lock.
  - Safe: replace an entry that is compared again under the PTE lock, as
    `unuse_pte()` under `unuse_mm()` does with `pte_same_as_swp()`; a zapped
    entry no longer matches.
