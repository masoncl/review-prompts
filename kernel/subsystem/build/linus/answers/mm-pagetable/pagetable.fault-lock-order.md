- `vmf_can_call_fault()`: the test is `vma->vm_ops->map_pages` non-NULL; only
  then may `fault`, `page_mkwrite` or `pfn_mkwrite` run with
  `FAULT_FLAG_VMA_LOCK` set.
- When the test fails: it calls `vma_end_read()` and returns
  `VM_FAULT_RETRY`.
- Handlers gated by it: `fault`, `page_mkwrite` and `pfn_mkwrite`; see
  `wp_page_shared()` and `wp_pfn_shared()` in `mm/memory.c`.
- `huge_fault`: not gated; `create_huge_pmd()` calls it with no
  `vmf_can_call_fault()` test.
- `do_shared_fault()`: tests once, before `fault`; `page_mkwrite` then runs
  under the same lock.
- A `vm_ops` that adds `map_pages` therefore declares that its `fault`,
  `page_mkwrite` and `pfn_mkwrite` need no mmap lock.
