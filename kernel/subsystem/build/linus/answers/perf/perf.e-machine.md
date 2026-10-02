- `HEADER_E_MACHINE`: exists, in `tools/perf/util/header.h`; payload is two
  `u32`, the ELF machine and the ELF flags.
- `write_e_machine()`: stores what `perf_session__e_machine()` returns.
- `process_e_machine()`: fills `env->e_machine` and `env->e_flags` in
  `struct perf_env`.

| Accessor | Order of sources |
|---|---|
| `perf_env__e_machine()` | `env->e_machine` if not `EM_NONE`; else `perf_env__e_machine_nocache()` |
| `perf_env__e_machine_nocache()` | `env->arch` string; else host `uname()` machine; both mapped by `perf_arch_to_e_machine()` |
| `perf_session__e_machine()` | NULL session: `EM_HOST`; `env->e_machine`; first thread via `thread__e_machine()`; `perf_env__e_machine_nocache()` |
| `evsel__e_machine()` | `perf_session__e_machine()` of the evsel's session |
| `thread__e_machine()` | cached field; process leader; maps; `/proc/<pid>/exe` or env; `EM_HOST` |
| `dso__e_machine()` | ELF header of the DSO file; `EM_NONE` if not found or unreadable |

- `perf_arch_to_e_machine()`: returns `EM_NONE` for an unrecognised arch
  string, and `EM_HOST` only when it is passed NULL.
- `perf_env__e_machine()` with no arch string: the result comes from the
  host's `uname()`, which can differ from `EM_HOST` (32-bit perf on a 64-bit
  kernel).
- `perf_env__e_machine()` caching: writes `env->e_machine` only when
  `env->arch` is set; `env->arch` is set only by `process_arch()`.
- `thread__e_machine()` maps step: uses the first map whose DSO gives a value
  other than `EM_NONE`, not the main executable.
- `thread__e_machine()` does not read `env->e_machine` before the maps; the
  header value does not override per-thread detection.
- `thread__e_machine()` after the maps: `/proc/<pid>/exe` when `is_live` is
  set, else `perf_env__e_machine(machine->env)`; see
  `thread__e_machine_endian()` in `tools/perf/util/thread.c`.
- `is_live`: set whenever `machine->machines` is NULL, which holds for every
  host machine; only `machines__add()` sets `machine->machines`. Do not rely
  on it to keep `/proc` reads away from file data.
- `thread__e_machine()` with a NULL thread: returns
  `perf_env__e_machine()` of `machine->env`, or of NULL.
- `thread__e_machine()` with a thread: returns `EM_HOST` in place of
  `EM_NONE`; the process leader does not cache that fallback.
- `perf_session__e_machine()`: caches the first thread's value in
  `env->e_machine`; it does not cache the `perf_env__e_machine_nocache()`
  result.
- `dso__e_machine()` on kernel, kcore, BPF, OOL and JIT DSO types: returns
  `perf_env__e_machine(machine->env)` without opening a file.
- `perf_env__arch()`: does not normalise `env->arch`; it converts
  `perf_env__e_machine()` back to a name with `e_machine_to_perf_arch()`.
- `write_arch()`: writes that derived name (for example "x86", "arm64") as
  `HEADER_ARCH`; `perf_arch_to_e_machine()` accepts both such names and
  `uname()` names.
