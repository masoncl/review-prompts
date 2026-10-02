| Call | What `include/asm-generic/io.h` supplies when the arch has none |
|---|---|
| `ioremap()` | without `CONFIG_MMU`: a cast of the physical address, with an empty `iounmap()`; with `CONFIG_MMU` and `CONFIG_GENERIC_IOREMAP`: `ioremap_prot()` with `__pgprot(_PAGE_IOREMAP)`; otherwise nothing |
| `ioremap_wc()` | a macro for `ioremap` |
| `ioremap_wt()` | a macro for `ioremap` |
| `ioremap_uc()` | an inline that returns `NULL` |
| `ioremap_np()` | an inline that returns `NULL` |
| `ioremap_cache()` | nothing; the generic header does not define it |

- `_PAGE_IOREMAP`: an architecture that uses the `CONFIG_GENERIC_IOREMAP`
  inline `ioremap()` must define it; that `ioremap()` does not use
  `pgprot_noncached()`.
- `ioremap_cache()` caller: builds only on an architecture that defines
  `ioremap_cache()` itself.
- `memremap()` with `MEMREMAP_WB`: the place where a missing `ioremap_cache()`
  becomes `ioremap()`; see `arch_memremap_wb()` in `kernel/iomem.c`, which tests
  `#ifdef ioremap_cache`. That body is under `#ifndef arch_memremap_wb`; an
  architecture that defines its own (for example riscv) does not run it.
