- Selection is by ELF machine, not by arch string: `perf_env__arch()` is used
  only for endianness, error messages and `write_arch()`.
- `perf_session__e_machine()` gives one value per session; a session can mix
  32-bit and 64-bit threads, so per-sample code uses `thread__e_machine()`,
  as `dump_sample()` in `tools/perf/util/session.c` does.
- Unwinding: `libdw__get_entries()` and `libunwind__get_entries()` take the
  machine from `thread__e_machine()` and pass it to `perf_arch_reg_ip()`.
- `unwind__prepare_access()` with `HAVE_LIBUNWIND_SUPPORT`: takes
  `(maps, e_machine)` and dispatches through
  `libunwind_arch__create_addr_space()`; it does not look at the DSO type or
  at `perf_env__arch()`.
- Live mode does not make `EM_HOST` right for per-thread data:
  `tools/perf/builtin-trace.c` calls `thread__e_machine()` per thread to pick
  the syscall table.
- ELF flags: only `EM_CSKY` consumers read them, for example
  `__perf_reg_name_csky()` and `e_machine_and_eflags__cmp()`, the comparison
  behind `arch__find()`.
- There is no arch__user_reg_mask() here; `perf_user_reg_mask()` in
  `tools/perf/util/perf_regs.c` does that.
- **Potentially unsafe usage**: `EM_HOST`, a host compiler macro such as
  `__x86_64__`, or `uname()` used to choose the architecture.
  - Unsafe: when the value interprets a sample, thread or DSO that came from
    a perf.data file and no recorded source was tried first;
    `perf_reg_name()` then names registers from the host's table.
  - Safe: when it describes an event to open on the running kernel:
    `__parse_regs()` in `tools/perf/util/parse-regs-options.c` and
    `__evsel__config_callchain()` in `tools/perf/util/evsel.c` pass `EM_HOST`
    to `perf_user_reg_mask()`, and the result becomes the event's register
    mask (`attr->sample_regs_user` in `__evsel__config_callchain()`).
  - Safe: when it builds a probe for the running kernel, as
    `synthesize_sdt_probe_arg()` in `tools/perf/util/probe-file.c` does with
    `perf_sdt_arg_parse_op()`.
  - Safe: as the value compared against the recorded machine, as
    `perf_env__lookup_binutils_path()` in `tools/perf/arch/common.c` does to
    decide whether the native objdump can be used.
  - Safe: as the last fallback when no recorded source exists, as
    `perf_env__e_machine_nocache()` does: it reads `uname()` only when
    `env->arch` is NULL.
- **Potentially unsafe usage**: a `__weak` hook in `tools/perf/util/`
  overridden under `tools/perf/arch/x86/util/` or a sibling.
  - Unsafe: when the hook runs while recorded data is processed; the override
    is chosen by `$(SRCARCH)` in `tools/perf/arch/Build`, not by the data.
  - Safe: when the hook is reached only while recording:
    `auxtrace_record__init()` is called only from
    `tools/perf/builtin-record.c`.
- **Potentially unsafe usage**: passing an accessor's result to a helper
  without handling `EM_NONE`.
  - Unsafe: with a value from `dso__e_machine()` or `perf_env__e_machine()`:
    `perf_arch_reg_ip()` returns 0, which is also a valid register number, and
    `get_dwarf_regstr()` silently substitutes `EM_HOST`.
  - Safe: with a fallback and a NULL check, as `map_symbol__get_arch()` in
    `tools/perf/util/annotate.c` does; `arch__find()` returns NULL there.
  - Safe: with a value from `thread__e_machine()` on a non-NULL thread, which
    returns `EM_HOST` in place of `EM_NONE`.
