- Per-architecture analysis code: `tools/perf/util/perf-regs-arch/`,
  `tools/perf/util/dwarf-regs-arch/`, `tools/perf/util/annotate-arch/`,
  `tools/perf/util/libunwind-arch/`, `tools/perf/util/kvm-stat-arch/`.
- `tools/perf/arch/x86/util/` and its siblings: hold no `perf_regs.c`,
  DWARF-register, unwind or kvm-stat file in this tree.
- Not unconditional: `tools/perf/util/dwarf-regs-arch/` needs `CONFIG_LIBDW`,
  `tools/perf/util/kvm-stat-arch/` needs `CONFIG_LIBTRACEEVENT`,
  `tools/perf/util/libunwind-arch/` needs `CONFIG_LIBUNWIND`.
- `tools/perf/util/libunwind-arch/`: with `CONFIG_LIBUNWIND` every file is
  built, but the libunwind calls in each are under a per-arch macro such as
  `HAVE_LIBUNWIND_X86_64_SUPPORT`; without it
  `__libunwind_arch__create_addr_space_x86_64()` returns NULL.
- Selector: there is no single function; each family dispatches on the ELF
  machine itself, most with a `switch` (search `tools/perf/util/` for
  `case EM_AARCH64:`), annotate with the `arch_new_fn[]` table in
  `arch__find()`.
- `arch__find()`: defined in `tools/perf/util/disasm.c`, takes
  `(e_machine, e_flags, cpuid)`, not an arch name string.
- `arch__find()` on a machine with no entry in `arch_new_fn[]`: returns NULL
  with `errno` set to `ENOTSUP`.
- `arch__find()` caller: only `map_symbol__get_arch()` in
  `tools/perf/util/annotate.c`; there is no thread__get_arch() here.
- `perf_reg_name()`: takes `(id, e_machine, e_flags)`; returns the string
  "unknown", not NULL, for an unknown machine or register.
- Register masks: `perf_user_reg_mask()` and `perf_intr_reg_mask()` in
  `tools/perf/util/perf_regs.c` take an ELF machine; they are not under
  `tools/perf/arch/`.
- `tools/perf/util/` also holds record-time code: `__perf_reg_mask_x86()`
  probes the running kernel with `sys_perf_event_open()` when `intr` is set,
  so its result is meaningful only for `EM_HOST`.
- Syscall tables compiled in: only the host family plus a generic `EM_NONE`
  table; each per-arch table is under a host-macro `#if` and
  `ALL_SYSCALLTBL` is defined nowhere.
- `find_table()` in `tools/perf/trace/beauty/syscalltbl.c`: a machine with no
  table silently gets the generic `EM_NONE` table.
- `tools/perf/arch/x86/include/` and siblings: not host only;
  `tools/perf/util/perf-regs-arch/perf_regs_x86.c` and
  `tools/perf/util/dwarf-regs.c` include these headers whatever the host is.
- `tools/perf/arch/common.c`: built into every binary and is analysis code;
  `perf_env__lookup_objdump()` picks a cross objdump from the recorded ELF
  machine.
