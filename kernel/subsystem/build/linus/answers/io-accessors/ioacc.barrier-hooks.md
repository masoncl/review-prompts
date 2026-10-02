| Hook | Default in `include/asm-generic/io.h` |
|---|---|
| `__io_br()` | `barrier()` |
| `__io_ar(v)` | `rmb()` if `rmb` is a macro when the header is read, else `barrier()` |
| `__io_bw()` | `wmb()` if `wmb` is a macro when the header is read, else `barrier()` |
| `__io_aw()` | `mmiowb_set_pending()` |
| `__io_pbr()` | `__io_br()` |
| `__io_par(v)` | `__io_ar(v)` |
| `__io_pbw()` | `__io_bw()` |
| `__io_paw()` | `__io_aw()` |

- `__io_aw()`, and `__io_paw()` through it: the one default that is empty,
  when `CONFIG_MMIOWB` is off; `mmiowb_set_pending()` is then
  `do { } while (0)` in `include/asm-generic/mmiowb.h`.
- `__io_br()` default: never empty, a compiler barrier.
- `CONFIG_MMIOWB`: `def_bool y if ARCH_HAS_MMIOWB` and `depends on SMP` in
  `kernel/Kconfig.locks`; a UP build of an architecture that selects
  `ARCH_HAS_MMIOWB` gets the empty `__io_aw()`.
- Port hooks: `arch/riscv/include/asm/io.h` is the only header that defines
  its own; everywhere else port I/O through `_inl()` gets the MMIO hooks.
- Architecture definitions of the MMIO hooks: search `define __io_` under
  `arch/`; only arm64, riscv and loongarch (`__io_aw()` only) have any.
