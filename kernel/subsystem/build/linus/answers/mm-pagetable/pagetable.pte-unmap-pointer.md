- `CONFIG_HIGHPTE`: defined only in `arch/arm/Kconfig` here, with
  `depends on HIGHMEM && !PREEMPT_RT`; no other architecture has it.
- Everywhere else `pte_unmap()` is only `rcu_read_unlock()`, so a wrong
  pointer or wrong release order shows no symptom outside such arm builds.
- Release order, where it is written down: the comment at the `out:` label of
  `move_pages_ptes()` in `mm/userfaultfd.c`.
