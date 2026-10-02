- Generic accessor stubs in `include/linux/pgtable.h`: keyed on
  `CONFIG_HAVE_ARCH_SOFT_DIRTY`, not on `CONFIG_MEM_SOFT_DIRTY`. With the
  first set and the second off, the architecture's own accessors are used.
- `VM_SOFTDIRTY`: non-zero whenever `CONFIG_MEM_SOFT_DIRTY` is set, whatever
  the runtime test says.
- `VM_SOFTDIRTY` on a new VMA: set only under
  `pgtable_supports_soft_dirty()`; see `mm/vma.c` and `mm/vma_exec.c`.
- `vm_flags_init()`, `vm_flags_reset()`, `vm_flags_clear()`:
  `VM_WARN_ON_ONCE()` when passed `VM_SOFTDIRTY` on a system without
  support.
- `vma_soft_dirty_enabled()` in `mm/internal.h`: tests
  `pgtable_supports_soft_dirty()` first, because tracking is on when
  `VM_SOFTDIRTY` is clear.
- **Potentially unsafe usage**: taking `!pte_soft_dirty(pte)` or a clear
  `VM_SOFTDIRTY` to mean that the entry needs write-protection.
  - Unsafe: with no support test before it; without the bit every entry
    reads as "not yet soft-dirty", so every entry is kept write-protected.
  - Safe: behind `vma_soft_dirty_enabled()`, as `pte_needs_soft_dirty_wp()`
    and `pmd_needs_soft_dirty_wp()` do.
  - Safe: copying the bit from one entry to another with no test, as
    `do_swap_page()` does with `pte_swp_soft_dirty()` and
    `pte_mksoft_dirty()`; both are stubs without
    `CONFIG_HAVE_ARCH_SOFT_DIRTY`.
- `pte_to_pagemap_entry()` and `pagemap_page_category()` in
  `fs/proc/task_mmu.c`: report from `pte_soft_dirty()` with no support test.
