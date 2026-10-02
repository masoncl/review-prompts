- `tools/testing/vma/main.c`: includes `mm/vma_init.c`, `mm/vma_exec.c` and
  `mm/vma.c` textually, then `tests/merge.c`, `tests/mmap.c`, `tests/vma.c`.
- `#include "vma_internal.h"` in a core file: still resolves to
  `mm/vma_internal.h`; its body is skipped because
  `tools/testing/vma/vma_internal.h`, included first through `shared.h`,
  defines the same guard `__MM_VMA_INTERNAL_H`.
- New include in `mm/vma_internal.h`: the test build never reads it; every
  symbol the core then uses must be supplied on the test side.
- Where test-side definitions go, under `tools/testing/vma/include/`:

| File | Holds |
|---|---|
| `stubs.h` | no-op versions, for example the mmap lock calls and `uprobe_mmap()` |
| `dup.h` | copies of kernel types and helpers that must match the kernel, for example `struct vm_area_struct` and `struct vm_area_desc`; `struct mm_struct` is a cut-down version |
| `custom.h` | versions altered for testing, for example `vma_start_write()` increments `vm_lock_seq`, and `struct anon_vma` has test fields |

- New field the core touches: add it to the test's copy of the struct, in
  `dup.h` for example for `struct vm_area_struct`; `struct anon_vma` is in
  `custom.h`.
- `mm/vma.h`: included unmodified by `shared.h` and has no `#include`;
  every type and helper it uses must be defined by the shim before it.
- New core `.c` file: add an `#include` to `main.c` and add the file to the
  prerequisites of the `main.o` rule in `tools/testing/vma/Makefile`.
- Kernel globals the core reads: defined by the test, for example
  `sysctl_max_map_count` in `main.c` and `stack_guard_gap` in `shared.c`.
- `CONFIG_` symbols: the shim defines `CONFIG_MMU` and
  `CONFIG_PER_VMA_LOCK`; `tools/testing/shared/shared.mk` generates a header
  that defines `CONFIG_64BIT` on a 64-bit build; the `Makefile` sets
  `NUM_VMA_FLAG_BITS` and `NUM_MM_FLAG_BITS` to 64; core code under a symbol
  the test build does not define is not compiled by the test.
