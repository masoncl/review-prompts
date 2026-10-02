# Perf Tools Subsystem

## Main structures

### Objects and how they relate

- `DECLARE_RC_STRUCT()`: search for it to list the types that are checked
  under `REFCNT_CHECKING`. The surprising member is `struct evlist`: reach
  its libperf part with `evlist__core()`, not `evlist->core`.
- `struct maps`: defined only in `tools/perf/util/maps.c`, so every other
  file goes through accessors. Its `maps_by_address` array is sorted only
  while `maps_by_address_sorted` is true.
- `struct threads`: the per-machine thread table is an array of
  `struct threads_table_entry`, each a hashmap keyed by tid with its own
  lock; see `tools/perf/util/threads.h`.
- `struct perf_sample`: carries its `struct evsel` in `sample->evsel`, as a
  counted reference taken in `__evsel__parse_sample()`. The `sample`
  callbacks of `struct perf_tool` take no `struct evsel *` argument.
- `struct addr_location` and `struct map_symbol`: hold `thread`, `map` and
  `sym`. Neither has a `struct maps` or `struct dso` member; reach those
  with `thread__maps()` and `map__dso()`.
- `addr_location__exit()` and `map_symbol__exit()`: put only `thread` and
  `map`. `struct symbol` has no reference count; the `struct dso` behind
  the map owns it.
- Per-evsel cpu and thread maps: `evlist__open()` opens each evsel on its
  own `evsel->core.cpus` and `evsel->core.threads`, not on the evlist's maps.
  `__perf_evlist__propagate_maps()` in `tools/lib/perf/evlist.c` sets the
  evsel's `cpus`, mostly from the evlist's `user_requested_cpus` and the
  evsel's `pmu_cpus`.
- **Potentially unsafe usage**: calling `evsel__hists()` on an evsel.
  - Unsafe: in a command that has not called `hists__init()`. The evsel is
    then allocated as a bare `struct evsel`, and `evsel__hists()` returns
    an address past the end of that allocation.
  - Safe: after `hists__init()` ran before any evsel was created, as in
    `tools/perf/builtin-report.c`. `hists__init()` sets the allocation size
    to `sizeof(struct hists_evsel)` through `evsel__object_config()`.
  - Safe: in shared code, a call made only when `symbol_conf.skip_empty` is
    set, as in `evsel__group_desc()`. Only `cmd_report()` and
    `cmd_annotate()` set it, and both call `hists__init()` first.

## Where to look

**Source layout**

| Directory | What differs from the usual picture |
|---|---|
| `tools/perf` (top level) | No command-list.txt in this tree; the common-command help table is `common_cmds[]` in `list_common_cmds_help()` in `tools/perf/builtin-help.c`. `tools/perf/Build` sorts objects by prefix: `perf-y` is linked directly as `perf-in.o`; `perf-util-y`, `perf-test-y`, `perf-ui-y` and `perf-bench-y` each become an archive, for example `libperf-util.a`; `gtk-y` becomes `libperf-gtk.so`. |
| `tools/perf/util` | Per-arch code that is built whatever `$(SRCARCH)` is lives here, not under `tools/perf/arch`: `tools/perf/util/annotate-arch/`, `tools/perf/util/perf-regs-arch/`, `tools/perf/util/dwarf-regs-arch/`, `tools/perf/util/libunwind-arch/`, `tools/perf/util/kvm-stat-arch/`. `annotate-data` is `tools/perf/util/annotate-data.c`, not a directory. |
| `tools/perf/arch` | `tools/perf/arch/Build` builds `common.o` and, of the architecture directories, only `$(SRCARCH)/`; `tools/perf/arch/arm64/util/Build` also compiles files from `tools/perf/arch/arm/util/`. No annotate directory, and no per-arch `perf_regs.c` or `dwarf-regs.c` under `tools/perf/arch/x86/util/` or its siblings; see the `tools/perf/util` row. `tests/` exists only for some architectures (for example `tools/perf/arch/x86`, `tools/perf/arch/arm64`); some directories, for example `tools/perf/arch/xtensa`, hold only a syscall table and `include/`. |
| `tools/perf/arch/x86/entry/syscalls` and siblings | Hold `.tbl` files only; `tools/perf/trace/beauty/syscalltbl.sh` generates the table from `tools/scripts/syscall.tbl` and the per-arch `.tbl` files it names one by one. The wildcard over every `syscall*.tbl` in `tools/perf/trace/beauty/Build` is only the dependency list; `tools/perf/arch/arm64/entry/syscalls/syscall_32.tbl` is not read by the script. `tools/perf/arch/riscv`, `tools/perf/arch/loongarch` and `tools/perf/arch/csky` have no `entry/`. |
| `tools/perf/tests` | No tests/attr/ directory; attr tests are `tools/perf/tests/shell/attr/`, run by `tools/perf/tests/shell/attr.sh` and `tools/perf/tests/shell/lib/attr.py`. Objects use `perf-test-y`. |
| `tools/perf/ui` | `tools/perf/ui/gtk/` is present; its objects use `gtk-y`. The other objects use `perf-ui-y`. |
| `tools/perf/pmu-events` | JSON path is `tools/perf/pmu-events/arch/x86/skylake/` style (arch, then model) for x86, powerpc and s390; a vendor level exists for arm64 and riscv, as in `tools/perf/pmu-events/arch/riscv/sifive/p550/`. `legacy-cache.json`, `extra-metrics.json` and `extra-metricgroups.json` are not checked in: `tools/perf/pmu-events/Build` generates them under `$(OUTPUT)pmu-events/arch/` with `make_legacy_cache.py`, `intel_metrics.py`, `amd_metrics.py` and `arm64_metrics.py`. `empty-pmu-events.c` is checked in, and `tools/perf/pmu-events/Build` diffs it against `jevents.py none none` output in a build without `NO_JEVENTS=1`. |
| `tools/perf/scripts` | `tools/perf/scripts/perl/` is present. Besides `python/` and `perl/` it holds only `Build` and `install-build-deps.sh`; `syscalltbl.sh` is under `tools/perf/trace/beauty/`. |
| `tools/perf/python` | Also holds `perf.pyi`, the type stub for the module; the module target in `tools/perf/Makefile.perf` lists it as a prerequisite. |
| `tools/perf/trace` | Two subdirectories: `tools/perf/trace/beauty/` and `tools/perf/trace/strace/groups/`. |
| `tools/perf/Documentation` | Man pages of the perf commands are only here; `tools/lib/perf/Documentation` holds the libperf ones. Kernel-side perf docs do exist under the kernel root: `Documentation/admin-guide/perf-security.rst` and `Documentation/admin-guide/perf/`. |
| `tools/lib` (loose files) | `tools/perf/util/Build` has one explicit rule per file it compiles from `../lib/`; `string.c` becomes `libstring.o`. `zalloc.c` reaches perf through `tools/lib/perf/Build` and `tools/perf/ui/gtk/Build`, `str_error_r.c` through `tools/lib/api/Build`. |
| `tools/lib/perf`, `tools/lib/api`, `tools/lib/subcmd`, `tools/lib/symbol`, `tools/lib/bpf`, `tools/build` | The `LIBAPI_DIR` block in `tools/perf/Makefile.perf` sets the five `tools/lib` directories; `tools/perf/MANIFEST` lists them and `tools/build`. |

## Recorded and host architecture

**Placing architecture code**

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

**Finding the recorded architecture**

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

**Host assumptions in analysis code**

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

## Object lifetime and reference counts

**Reference count checking**

- `REFCNT_CHECKING`: defined by `tools/lib/perf/include/internal/rc_check.h`
  itself when `__SANITIZE_ADDRESS__`, `LEAK_SANITIZER` or `ADDRESS_SANITIZER`
  is defined, or `__has_feature(address_sanitizer)` or
  `__has_feature(leak_sanitizer)` is true; a `-fsanitize=address` build is
  a checked build with no further flag.
- Forcing it without a sanitizer: pass `-DREFCNT_CHECKING=1` in
  `EXTRA_CFLAGS`, as `make_refcnt_check` in `tools/perf/tests/make` does;
  no makefile variable of that name is handled anywhere.
- Finding out whether a struct is checked: search `tools/` for
  `DECLARE_RC_STRUCT(name)`, not only the struct's header; `struct maps` is
  declared in `tools/perf/util/maps.c` and `struct comm_str` in
  `tools/perf/util/comm.c`.
- `struct evlist`: checked, declared in `tools/perf/util/evlist.h`.
- `struct evsel`: counted (`refcount_t refcnt`) but a plain struct, so not
  checked; a missed or double `evsel__put()` gets no wrapper report.

**Shared and owned objects**

- There is no dsos__findnew() here; `dsos__findnew_id()` in
  `tools/perf/util/dsos.c` does that, and `machine__findnew_dso()` wraps it.
- Functions in `tools/perf/util/dsos.c` that return `struct dso *` return a
  reference the caller must `dso__put()`, for example `dsos__find()` and
  `dsos__findnew_module_dso()`.
- `maps__find_symbol()` and `maps__find_symbol_by_name()`: return an
  uncounted `struct symbol *`; the counted map comes back through `mapp`,
  and the caller must `map__put()` it; with `mapp` NULL there is nothing to
  put.
- `maps__find_symbol()`: stores the map in `*mapp` whenever a map covers the
  address, even when it returns NULL for the symbol.
- `maps__find_symbol_by_name()`: writes `*mapp` only when it returns a
  symbol.
- `machine__find_kernel_symbol()` and
  `machine__find_kernel_symbol_by_name()` in `tools/perf/util/machine.h`:
  inline wrappers with the same `mapp` rule.
- `thread__find_map()`: the returned map is the reference stored in
  `al->map`; it is released by `addr_location__exit()`, not by a separate
  `map__put()`.
- `machines__exit()`: exits only `machines->host`; guest machines are
  erased and passed to `machine__delete()` in
  `machines__destroy_kernel_maps()`, which `perf_session__delete()` reaches
  before `machines__exit()`.

**evlist and evsel lifetime**

- `struct evlist`: reference counted and refcount-checked; `evlist__new()`
  returns it with a count of 1, released with `evlist__put()`.
- `struct evsel`: reference counted through `refcnt`, set to 1 by
  `evsel__new_idx()` and `evsel__newtp_idx()`; released with `evsel__put()`.
- There is no evlist__delete() or evsel__delete() in `tools/perf`;
  `evsel__exit()` and `evlist__exit()` are `static`.
- `evlist__add()`: takes over the caller's evsel reference (it does not
  call `evsel__get()`), and sets `entry->evlist` to an `evlist__get()`
  reference, so every evsel on a list holds a counted back-reference.
- `evlist__put()`: frees the list when the count reaches zero, or when
  every remaining reference is a back-reference from an evsel on the list
  whose own `refcnt` is 1.
- Evsel on a list with `refcnt` above 1: its back-reference counts as a real
  holder, so `evlist__put()` by the last outside holder does not free the
  list.
- `evlist__purge()`, run when the list is freed: unlinks each evsel, drops
  its back-reference, sets `evsel->evlist` to NULL, then calls
  `evsel__put()`; an evsel with another holder survives with a NULL
  `evlist`.
- `evlist__remove()`: unlinks, puts the back-reference and clears
  `evsel->evlist`; it does not call `evsel__put()`, so the list's reference
  passes to the caller.
- `perf_session__delete()`: puts `session->evlist` only when `session->data`
  is set and open for reading (the list made by `evlist__new()` in
  `tools/perf/util/header.c`); a tool that assigned its own list to
  `session->evlist` still owns it.
- **Unsafe usage**: dropping the last reference to an evsel that is still
  linked on an evlist, for example `evsel__put()` after `evlist__add()`
  when no `evsel__get()` was taken.
  - Unsafe: `evsel__exit()` asserts `list_empty(&evsel->core.node)` and
    `evsel->evlist == NULL`; the list still links the freed evsel.
  - Safe: keep an own reference by passing `evsel__get(evsel)` to
    `evlist__add()`, as `pyrf_evlist__add()` in `tools/perf/util/python.c`
    does.
  - Safe: unlink and clear `evsel->evlist` before the put, as
    `evlist__purge()` does.

**addr_location and perf_sample references**

- `struct addr_location`: has no maps field; the counted fields are
  `thread` and `map`, and maps are reached with `thread__maps(al->thread)`.
- `addr_location__exit()`: `map__zput()` and `thread__zput()`, nothing else.
- `addr_location__init()`: sets fields one by one and leaves `latency`
  unset.
- `struct map_symbol`: fields are `thread`, `map` and `sym`; `thread` and
  `map` are counted.
- `map_symbol__copy()`: `thread__get()` and `map__get()`, `sym` copied as a
  plain pointer; released by `map_symbol__exit()`, which puts both.
- `map_symbol__copy()` does not release what `dst` held;
  `addr_location__copy()` puts `dst->thread` and `dst->map` first.
- Reusing one `struct addr_location`: `thread__find_map()` puts the old
  `map` and `thread` before it fills them, so no exit is needed between
  fills; garbage in an uninitialised one is put there.
- `perf_sample__exit()`: calls `evsel__put(sample->evsel)`, frees
  `user_regs` and `intr_regs`, and frees `callchain` only when
  `merged_callchain` is set; it never frees `branch_stack`.
- `perf_sample__init()` with `all` false: clears `evsel`, `user_regs`,
  `intr_regs`, `merged_callchain` and `callchain`.
- `__evsel__parse_sample()`: calls `perf_sample__init()` with `all` true and
  then `evsel__get()` into `data->evsel` before any check, so the sample
  needs `perf_sample__exit()` after a failed parse too.
- `evlist__parse_sample()` with no matching evsel: initialises the sample
  and returns `-EFAULT`, so exit is still safe.
- **Unsafe usage**: `map_symbol__copy()` into a `dst` that already holds
  references.
  - Unsafe: the old `thread` and `map` references are overwritten and leak.
  - Safe: `map_symbol__exit()` on `dst` first, as
    `callchain_cursor_append()` does.
  - Safe: `dst` freshly zeroed or just struct-assigned from `src`, as
    `callchain_node__make_parent_list()` does.
- **Unsafe usage**: parsing into a `struct perf_sample` that still holds a
  previous parse.
  - Unsafe: the re-initialisation drops the `evsel` reference and the
    allocated registers without releasing them.
  - Safe: `perf_sample__exit()` between parses, as the loop in
    `session__flush_deferred_samples()` does.
- **Potentially unsafe usage**: assigning `sample->evsel` without
  `evsel__get()`.
  - Unsafe: when the sample reaches `perf_sample__exit()` with that value,
    which puts a reference nobody took.
  - Safe: save the old value and restore it before returning, as
    `deliver_sample_value()` in `tools/perf/util/session.c` does.
  - Safe: a local sample that never reaches `perf_sample__exit()`, as in
    `evsel__parse_sample_timestamp()`.
- **Potentially unsafe usage**: struct assignment of a
  `struct addr_location`, of a `struct map_symbol`, or of a struct that
  embeds a `struct map_symbol`.
  - Unsafe: when nothing then takes references for the copy and the copy is
    later released with `map_symbol__exit()` or `addr_location__exit()`;
    both copies put the same `thread` and `map`.
  - Safe: assignment followed at once by a get on each counted field, as
    `addr_location__copy()` and `callchain_node__make_parent_list()` do.
  - Safe: a borrowed copy that is never released and is dropped before its
    source, as `seen[]` in `c2c_function__process_cl()` in
    `tools/perf/util/c2c-function.c`, which is only compared and then
    passed to `free()`.

**Error returns from constructors**

- `perf_session__new()`: returns `ERR_PTR()` on every failure, never NULL;
  test with `IS_ERR()`; see `__perf_session__new()` in
  `tools/perf/util/session.c`.
- `evsel__new()` and `evsel__new_idx()`: return NULL, unlike
  `evsel__newtp()`; test with `!evsel`.
- Release functions test for NULL only: `perf_session__delete()` and
  `evsel__put()` dereference an `ERR_PTR()` value, so a failed constructor
  result must not reach them.
- Written preference for new code: none in this tree; the comment above
  `evsel__newtp_idx()` only says the pointer carries an encoded error, and
  `tools/perf/Documentation` says nothing on it.

**Pointers to refcount-checked structs**

- `RC_CHK_ACCESS()` outside the owning file: used in this tree for direct
  field access, for example on a `struct dso` in
  `tools/perf/util/symbol-minimal.c`, and for object identity.
- `struct maps` and `struct comm_str`: opaque outside
  `tools/perf/util/maps.c` and `tools/perf/util/comm.c`, so neither
  `RC_CHK_ACCESS()` nor `RC_CHK_EQUAL()` compiles on them elsewhere under
  checking; compare maps with `maps__equal()`.
- `struct addr_location` has no maps field; the kernel-maps test is
  `maps__equal(thread__maps(al->thread), machine__kernel_maps(machine))`,
  as in `tools/perf/util/callchain.c`.
- `struct evlist`: checked, so `evlist->field` does not compile under
  checking; use the accessors in `tools/perf/util/evlist.h`.
- `RC_CHK_EQUAL()`: accepts NULL on either side.
- Hash and ordering keys: built from `RC_CHK_ACCESS(ptr)`, as
  `remap_addresses__hash()` in `tools/perf/util/aslr.c` does.
- **Potentially unsafe usage**: `RC_CHK_ACCESS(ptr)` used only to obtain
  the object's address.
  - Unsafe: when `ptr` may be NULL; under checking the macro reads
    `ptr->orig`, with checking off it just yields NULL.
  - Safe: test `ptr` for NULL first, as `__hpp__sort_acc()` in
    `tools/perf/ui/hist.c` does, or use `RC_CHK_EQUAL()`.
- **Potentially unsafe usage**: `container_of()` from a member embedded in
  a checked struct.
  - Unsafe: when the result is used as a `struct name *` in code that is
    compiled under checking; there it points at the `RC_STRUCT(name)`
    object, not at a wrapper.
  - Safe: wrap the result with `ADD_RC_CHK()`, take a count, and put it
    when done, as `from_list_start()` and `from_list_end()` in
    `tools/perf/util/evlist.c` do.
  - Safe: keep a counted back-pointer in the member under
    `#ifdef REFCNT_CHECKING`, as `dso__list_add()` and `close_first_dso()`
    in `tools/perf/util/dso.c` do.
- **Potentially unsafe usage**: calling a get and ignoring its return
  value.
  - Unsafe: for a struct declared with `DECLARE_RC_STRUCT`; the new wrapper
    is lost and the later put frees the wrapper of another holder.
  - Safe: for `struct evsel`, which is not checked; `evsel__get()` returns
    its argument.

## Tool callbacks and records

**perf_tool initialisation**

- `perf_tool__init()` in `tools/perf/util/tool.c`: assigns every member of
  `struct perf_tool`, so the tool need not be zeroed first.
- `merge_deferred_callchains`: set to `true` by `perf_tool__init()`; it is the
  one flag whose default is not zero. `dont_split_sample_group` is set to
  `false`.
- `__perf_session__new()`: reads only `ordering_requires_timestamps` and
  `ordered_events` from the tool, for its switch-off test; a write to either
  after session creation is not seen by that test.
- Callbacks: read at dispatch time, so a handler may be installed after
  session creation and before `perf_session__process_events()`, as
  `__cmd_script()` does.
- `perf_session__new()` with a NULL tool: accepted;
  `perf_session__process_event()` dereferences `session->tool`, so such a
  session cannot process events.
- `delegate_tool__init()`: copies the flags from the delegate once and sets
  every callback to a forwarder; flags changed on the delegate afterwards are
  not seen. `aslr_tool__init()` then overrides on the wrapper.
- **Unsafe usage**: processing events through a tool that never went through
  `perf_tool__init()` or `delegate_tool__init()`.
  - Unsafe: any callback left NULL; `machines__deliver_event()` and
    `perf_session__process_user_event()` call through the member with no
    NULL test.
  - Safe: `perf_tool__init()` first, then assign handlers, as `cmd_report()`
    in `tools/perf/builtin-report.c` does.
  - Safe: a tool used only as the argument of a `perf_event__handler_t`
    during synthesis, with a session created with a NULL tool, as
    `__cmd_top()` in `tools/perf/builtin-top.c` does; nothing dispatches
    through its members.
- **Potentially unsafe usage**: writing `tool->ordered_events = true` after
  `perf_tool__init(tool, false)`.
  - Unsafe: when `finished_round` is left alone; it is still
    `process_finished_round_stub()`, so no round flush happens and the queue
    holds every record until the final flush.
  - Safe: when `finished_round` is also assigned a handler that calls
    `perf_event__process_finished_round()`, as `host__finished_round()` in
    `tools/perf/builtin-inject.c` does.
  - Safe: when the init call already passed `true`, as `trace__replay()` in
    `tools/perf/builtin-trace.c` does.

**Callbacks left unset**

- `mmap`, `mmap2`, `comm`, `fork`, `exit`, `namespaces`, `cgroup`: default to
  `process_event_stub()`. A command that leaves them unset gets no threads
  and no maps from these records.
- `attr`, `event_update`, `tracing_data`, `build_id`, `id_index`, `feature`:
  default to stubs. Nothing populates the evlist from pipe input unless the
  command installs `perf_event__process_attr()` or a wrapper that calls it.

| Default that is not a stub | Effect |
|---|---|
| `perf_event__process_switch()` for `context_switch` | changes `machine->parallelism` |
| `perf_event__process_ksymbol()`, `perf_event__process_bpf()`, `perf_event__process_text_poke()` | change kernel maps or their DSOs; `perf_event__process_bpf()` only with `HAVE_LIBBPF_SUPPORT` |
| `perf_event__process_finished_round()` (init boolean true) | flushes the queue |
| `perf_session__process_compressed_event()` (`HAVE_ZSTD_SUPPORT`) | adds a decompressed buffer to the session |
| `perf_event__process_lost()`, `perf_event__process_lost_samples()`, `perf_event__process_aux()`, `perf_event__process_itrace_start()`, `perf_event__process_aux_output_hw_id()` | print under dump only |

- Session work that does not depend on the callback, for example: the copy
  into `session->time_conv` for `PERF_RECORD_TIME_CONV`,
  `perf_session__auxtrace_error_inc()`, and after `tool->attr` returns 0
  `perf_session__set_id_hdr_size()` and `perf_session__set_comm_exec()`.
- Pointer comparisons: the session compares only `tool->lost`,
  `tool->lost_samples` and `tool->aux` with their defaults, and
  `tool->compressed` with its stub through `perf_tool__compressed_is_stub()`.
  It does not compare `sample`, `attr` or `finished_round`.
- `machines__deliver_event()`: adds to `total_lost`, `total_lost_samples`,
  `total_aux_lost`, `total_aux_partial` and `total_aux_collision` only while
  the default is installed.
- `PERF_RECORD_MISC_LOST_SAMPLES_BPF`: counted in `total_dropped_samples`
  whatever `tool->lost_samples` is.
- `perf_session__warn_about_errors()`: makes the same three comparisons, so
  replacing `lost`, `lost_samples` or `aux` also silences the matching
  end-of-run warnings.
- `delegate_tool__init()`: a wrapped tool fails all three comparisons and
  `perf_tool__compressed_is_stub()`, even when the delegate holds the
  defaults.

**Dispatch by record type**

- `perf_session__process_event()`: calls `perf_session__process_user_event()`
  directly for types at or above `PERF_RECORD_USER_TYPE_START`; only kernel
  records go through `perf_session__deliver_event()`.
- Order in `perf_session__process_event()`: size alignment, type range,
  `perf_event__too_small()`, swap, `events_stats__inc()`, dispatch. A record
  skipped by the range, size or swap check is not counted in `nr_events[]`.
- Type at or above `PERF_RECORD_HEADER_MAX`: reaches neither dispatcher;
  `perf_session__process_event()` prints a `ui__warning()` and returns 0.
- Unknown type in `machines__deliver_event()`: `nr_unknown_events++` and -1,
  which aborts the read.
- `perf_session__deliver_event()`: calls `evlist__event2evsel()` then
  `evsel__parse_sample()`; a NULL evsel is `-EFAULT` and aborts.
- Sample id that matches no evsel, in an evlist with more than one evsel:
  aborts with `-EFAULT`; it is not counted in `nr_unknown_id`.
- `nr_unknown_id` in `machines__deliver_event()`: reachable only when the
  caller passes a sample with no `evsel`, as through
  `perf_session__deliver_synth_event()`; `__evsel__parse_sample()` always
  sets `evsel`.
- Ordered mode: an error other than -1 from
  `evlist__parse_sample_timestamp()` aborts before the record is queued.
- Queued record: the checks and the handler in `perf_session__deliver_event()`
  run at flush time, so their error is returned by the `finished_round` call
  or the final flush.
- `perf_session__deliver_synth_event()`: applies the same split by type, with
  no alignment, range, size or swap step and no queue.
- Records inside `PERF_RECORD_COMPRESSED` and `PERF_RECORD_COMPRESSED2`:
  `__perf_session__process_decomp_events()` feeds each one to
  `perf_session__process_event()`, so they are checked and queued like any
  other.

**Ordered events**

- `PERF_RECORD_FINISHED_INIT`: does not flush; it calls `tool->finished_init`,
  whose default is `process_event_op2_stub()`.
- Switch-off in `__perf_session__new()`: needs `ordering_requires_timestamps`,
  `ordered_events`, input that is not a pipe, and `evlist__sample_id_all()`
  false. `PERF_SAMPLE_TIME` is not tested.
- Switch-off message: `dump_printf()` only; nothing is printed in a normal
  run.
- Switch-off effect: writes `false` into the caller's `tool->ordered_events`
  and leaves `tool->finished_round` as it was.
- Pipe input: never switched off; `__perf_session__process_pipe_events()`
  calls `ordered_events__set_copy_on_queue()` because its read buffer is
  reused.
- `OE_FLUSH__HALF`: `ordered_events__init()` sets `max_alloc_size` to
  `(u64)-1`, so it happens only after `ordered_events__set_alloc_size()`, as
  in `cmd_report()`, or when an allocation fails.
- First `OE_FLUSH__ROUND`: delivers nothing; `do_flush()` returns while
  `next_flush` is 0, and each round delivers up to the previous round's
  `max_timestamp`.

**MMAP and MMAP2 records**

- There is no buildid_mmap2 field here; `symbol_conf.no_buildid_mmap2` in
  `tools/perf/util/symbol_conf.h` does that job, with the opposite sense.
- `__perf_event__synthesize_kernel_mmap()` and
  `perf_event__synthesize_modules()`: emit `PERF_RECORD_MMAP2` unless
  `symbol_conf.no_buildid_mmap2` is set.
- `symbol_conf.no_buildid_mmap2`: set only by `cmd_record()`, when
  `rec->buildid_mmap` is false; `buildid_mmap` defaults to `true` and is
  cleared when `perf_can_record_build_id()` fails.
- `perf_event__synthesize_extra_kmaps()` in
  `tools/perf/arch/x86/util/event.c`: always emits `PERF_RECORD_MMAP`, so a
  file can hold both types.
- Only `mmap2` handled: loses the x86_64 extra kernel maps, and the kernel and
  module maps of files recorded with `no_buildid_mmap2`, as well as the maps
  the kernel reports for an event opened without `attr.mmap2`.
- Only `mmap` handled: loses the kernel and module maps too in a default
  recording.
- `PERF_RECORD_MISC_PROC_MAP_PARSE_TIMEOUT`: counted in `nr_proc_map_timeout`
  for `PERF_RECORD_MMAP2` only.
- `machine__process_mmap_event()` and `machine__process_mmap2_event()`:
  return 0 when the map cannot be built, with a message under dump only.

**Validating records**

- `perf_event__too_small()` in `tools/perf/util/session.c`: compares
  `header.size` with `perf_event__min_size[]`, indexed by type; an entry of 0
  means no minimum.
- `perf_event__min_size[]` values: can be below the size of the current
  struct, for example `offsetof(struct perf_record_time_conv, time_cycles)`,
  so a field added later still needs a size test, as `event_contains()` does
  for `time_cycles` in `perf_event__time_conv_swap()` and for
  `cap_user_time_short` in `perf_event__fprintf_time_conv()`.
- `PERF_RECORD_SAMPLE`, `PERF_RECORD_FINISHED_ROUND`,
  `PERF_RECORD_FINISHED_INIT` and `PERF_RECORD_COMPRESSED`: have no entry.
- Swap ops: return `int`; they bound or clamp embedded counts and locate
  strings with `strnlen()`. They run only for cross-endian input.

| Check | Where | On failure |
|---|---|---|
| `header.size` below the header size | `reader__read_event()` | abort |
| record too large to fit a remapped window | `prefetch_event()`, called from `fetch_mmaped_event()` | abort |
| `header.size` not a multiple of 8, except `PERF_RECORD_HEADER_TRACING_DATA`, `PERF_RECORD_COMPRESSED`, `PERF_RECORD_HEADER_FEATURE` | `perf_session__process_event()` | abort, `-EINVAL` |
| type at or above `PERF_RECORD_HEADER_MAX` | same | skip |
| `perf_event__too_small()` | same | skip |
| swap op returns non-zero | same | skip |
| no evsel for the record, or `evsel__parse_sample()` fails | `perf_session__deliver_event()` | abort |
| `sample.cpu` out of range, other than `(u32)-1` | same | set to 0, delivered |
| string has no NUL: `PERF_RECORD_MMAP`, `PERF_RECORD_MMAP2`, `PERF_RECORD_COMM`, `PERF_RECORD_CGROUP`, `PERF_RECORD_KSYMBOL` | `machines__deliver_event()` | skip |
| `nr_namespaces` or text poke lengths exceed the record | same | skip |
| `PERF_RECORD_THREAD_MAP` `nr` exceeds the record | `perf_session__process_user_event()` | abort, `-EINVAL` |
| counts of `PERF_RECORD_CPU_MAP`, `PERF_RECORD_STAT_CONFIG`, `PERF_RECORD_BPF_METADATA`; strings of `PERF_RECORD_HEADER_BUILD_ID` and `PERF_RECORD_BPF_METADATA` | same | skip |

- Skip means the function returns 0 without calling the callback; the reader
  advances by `header.size`.
- `PERF_RECORD_HEADER_ATTR`, `PERF_RECORD_EVENT_UPDATE`,
  `PERF_RECORD_ID_INDEX`: the bounds checks are in
  `perf_event__process_attr()`, `perf_event__process_event_update()` and
  `perf_event__process_id_index()`. A command whose handler does not call
  them gets none of them.
- Native-endian file input: `reader__mmap()` maps it `PROT_READ` unless
  `in_place_update` is set, so a handler cannot clamp or terminate a field in
  the record; the session skips where the swap op would clamp.
- `perf_session__peek_event()`: makes the alignment, range, size and swap
  checks itself; only `perf_session__peek_events()` skips on failure.
- **Potentially unsafe usage**: looping on a count or calling `strlen()` on a
  string taken from the record.
  - Unsafe: for a type with no check in the table above, when the handler
    does not compare against `header.size` first.
  - Safe: for the types the table lists, in a handler reached through
    `machines__deliver_event()` or `perf_session__process_user_event()`, as
    `process_stat_config_event()` in `tools/perf/builtin-stat.c` is for
    `nr`.
  - Safe: after the handler's own test, as `perf_event__process_id_index()`
    does for `nr`.

**Adding a record type**

| Place in `tools/perf/util/` | When the new type is missing |
|---|---|
| `perf_event__min_size[]` in `session.c` | entry is 0: no minimum, the swap op and handler see records as short as the header |
| alignment exemption in `perf_session__process_event()` and `perf_session__peek_event()` | a record whose size is not a multiple of 8 aborts with `-EINVAL` in `perf_session__process_event()`, and makes `perf_session__peek_event()` return -1 |
| `perf_event__swap_ops[]` in `session.c` | NULL: `event_swap()` returns 0 and cross-endian payload is delivered unswapped |
| `switch` in `perf_session__process_user_event()` | `-EINVAL`, abort |
| `perf_tool__init()` in `tool.c` | member keeps whatever the storage held; a call through NULL or a stale pointer on the first record |
| `delegate_tool__init()` and its `CREATE_DELEGATE_OP2()` line in `tool.c` | wrapper member not set; the delegate's handler is never reached |
| `perf_event__names[]` in `event.c` | `perf_event__name()` returns "INVALID" for a type past the array end, "UNKNOWN" for a hole |
| `pyrf_event__type[]` in `python.c` | `pyrf_event__new()` raises `TypeError` |

- `perf_event__swap_ops[]`: sized by its `[PERF_RECORD_HEADER_MAX] = NULL`
  entry, so indexing a new type is in bounds.
- Swap op signature: returns `int`; non-zero makes
  `perf_session__process_event()` skip the record. It runs after
  `perf_event__too_small()`, so it may rely on the minimum size and nothing
  more.
- Counts and strings: the session-level check goes in the new `case` of
  `perf_session__process_user_event()`, where native-endian input is caught;
  the swap op covers only cross-endian input.
- `perf_event__fprintf()` in `event.c`: a type with no case prints its name
  only.

## File and pipe formats

**Headers and format detection**

- `perf_session__read_header()` in `tools/perf/util/header.c`: calls
  `perf_header__read_pipe()` first for every input, whatever
  `perf_data__is_pipe()` says.
- `perf_header__read_pipe()`: succeeds only when the magic passes
  `check_magic_endian()` and `size` equals
  `sizeof(struct perf_pipe_file_header)`.
- On success, or when `perf_data__is_pipe()` was already true,
  `perf_session__read_header()` sets `data->is_pipe = true` and returns the
  result of the pipe read.
- A regular file on disk in pipe format: opened by path as a normal file, then
  switched to pipe mode by that assignment.
- `perf_data__is_pipe()` on input: final only after `perf_session__new()`
  returns. Before that only `check_pipe()` in `tools/perf/util/data.c` has set
  it.
- `check_pipe()`: path `-` is a pipe; the `S_ISFIFO()` test on stdin or stdout
  runs only when `data->path` is NULL.
- Input that `check_pipe()` marked as a pipe and whose pipe header fails:
  `perf_session__read_header()` returns the error; `perf_file_header__read()`
  is not tried.
- `session->evlist`: allocated by `perf_session__read_header()` itself, before
  either header is read.
- Pipe path: leaves `data_offset`, `data_size`, `feat_offset` and
  `adds_features` of `struct perf_header` at zero, and sets `last_feat` to 0.
- File path: `perf_file_header__read()` sets `last_feat` to
  `HEADER_LAST_FEATURE`.

**Limits of pipe input**

- Reader side, input in pipe format (a real pipe or a regular file):

| Place | On pipe input |
|---|---|
| `perf_session__open()` | returns before `evlist__valid_sample_type()`, `evlist__valid_sample_id_all()`, `evlist__valid_read_format()` |
| `__perf_session__new()` | skips `perf_session__set_id_hdr_size()`, `perf_session__set_comm_exec()` and the `evlist__sample_id_all()` fallback to unordered processing |
| `perf_session__process_events()` | tests pipe before directory; directory data is not read |
| `perf_session__peek_event()` | returns -1 from the branch taken when `session->one_mmap` is false or `needs_swap` is set |
| `auxtrace_queue_data()` | returns 0 and queues nothing |
| `auxtrace_queues__add_buffer()` | copies the data with `auxtrace_copy_data()` |
| `perf_header__fprintf_info()` | skips the "missing features" line |
| `report__setup_sample_type()` | skips the callchain, branch, `PERF_SAMPLE_DATA_SRC` and `HEADER_AUXTRACE` checks |
| `perf c2c report` in `tools/perf/builtin-c2c.c` | refuses, with only a `pr_debug()` |
| `perf inject --convert-callchain` | refuses pipe input and pipe output |

- `perf report --header` and `--header-only`: not refused. Features print as
  they arrive, because `cmd_report()` sets `show_feat_hdr`.
- `perf report --header-only` on pipe: calls `perf_session__process_events()`
  and stops when `process_feature_event()` sees the end marker.
- `perf inject` in-place update: refused only by name, when the input name is
  `-`.
- `tools/perf/builtin-inject.c`: has no pipe test tied to `--jit`.
- `perf record --switch-output` on pipe output: not refused;
  `switch_output_setup()` has no pipe test. Only `rec->timestamp_filename` is
  cleared, with a warning.
- Feature section table: always at `data.offset + data.size`. The reader
  computes that as `feat_offset`; the file header does not store it.
- Attrs before data is not guaranteed. `perf_session__do_write_header()` with
  `write_attrs_after_data` writes header, data, features, then ids and attrs.
- `write_attrs_after_data`: true in `perf inject` when input is pipe format
  and output is a file.
- `perf_file_header__read()`: accepts attrs before or after data; it rejects
  them only when they overlap.

**Attributes and features over a pipe**

- `perf_event__synthesize_for_pipe()` in
  `tools/perf/util/synthetic-events.c`: emits attrs, then features with the
  end marker, then, under `HAVE_LIBTRACEEVENT`, tracing data if the evlist has
  tracepoints.
- It emits no `PERF_RECORD_HEADER_BUILD_ID`, no
  `PERF_RECORD_HEADER_EVENT_TYPE` and no `PERF_RECORD_FINISHED_INIT`.
- `PERF_RECORD_FINISHED_INIT`: written by `write_finished_init()` in
  `tools/perf/builtin-record.c`.
- Event names, units and scales: arrive later as `PERF_RECORD_EVENT_UPDATE`
  from `perf_event__synthesize_extra_attr()`; the name only when `is_pipe`.
- Features are sent in the same call as the attrs. `record__synthesize()`
  makes that call before recording, or after it when `opts.tail_synthesize`
  is set.
- `perf_event__synthesize_for_pipe()` output: all attrs precede the first
  feature event. `process_header_feature()` in `tools/perf/builtin-evlist.c`
  relies on it to stop reading.
- `perf_tool__init()` defaults: `attr` is `process_event_synth_attr_stub()`,
  `feature` is `process_event_op2_stub()`. Both return 0, so the events are
  dropped without an error.
- `attr`: must be `perf_event__process_attr()` or a wrapper that calls it
  first, for any command that reads samples from a pipe.
- `feature`: not needed to read samples. For example
  `tools/perf/builtin-kwork.c` and `tools/perf/builtin-mem.c` set `attr` and
  leave `feature` at the stub.
- `perf_event__process_tracing_data()`: declared only under
  `HAVE_LIBTRACEEVENT`. `cmd_report()` wraps the assignment in that `#ifdef`.
- **Potentially unsafe usage**: dereferencing `evlist__first()` or
  `evlist__last()` of `session->evlist`, directly or through a helper, after
  `perf_session__new()`.
  - Unsafe: on pipe input before the first attr was processed, when the list
    is empty. `perf_evlist__first()` is a bare `list_entry()` on the list
    head, so `evlist__sample_id_all()` reads memory that is not an evsel.
  - Safe: on file input with at least one attr, guarded by `!data->is_pipe`,
    as `__perf_session__new()` does for `evlist__sample_id_all()`;
    `perf_session__read_header()` has added the file's attrs with
    `evlist__add()`.
  - Safe: inside an `attr` wrapper after `perf_event__process_attr()`
    returned 0, as `process_attr()` in `tools/perf/builtin-script.c` does with
    `evlist__last()`; `perf_event__process_attr()` has then called
    `evlist__add()`.
  - Safe: `evlist__combined_sample_type()`, which iterates and returns 0 on an
    empty list. `report__setup_sample_type()` guards its tests of that value
    with `!is_pipe`.

**Unknown and missing features**

- File, bit at or above `HEADER_LAST_FEATURE`: skipped with no message.
  `perf_header__process_sections()` loops only up to `header->last_feat`.
- The `pr_debug()` for an unknown feature in `perf_file_section__process()` is
  not reached through that loop.
- Pipe, `perf_event__process_feature()` in `tools/perf/util/header.c`:

| `feat_id` | Result |
|---|---|
| `HEADER_RESERVED`, negative, or `INT_MAX` | `pr_warning()`, returns -1 |
| at or above `HEADER_LAST_FEATURE`, with payload | `pr_warning()` "unknown feature", returns 0 |
| at or above `HEADER_LAST_FEATURE`, no payload | taken as the end marker, silent, returns 0 |
| known, `process` hook is NULL | no warning, returns 0 |
| known, `process` hook fails, with payload | returns -1 |
| known and at or above `last_feat`, `process` hook fails, no payload | failure ignored, returns 0 |
| known and below `last_feat`, `process` hook fails, no payload | returns -1 |

- A return of -1: makes `__perf_session__process_pipe_events()` stop with
  `-EINVAL`.
- File, known feature whose `process` hook fails:
  `perf_session__read_header()` fails, so the session does not open.
- `last_feat` in `struct perf_header`: on pipe it starts at 0 and grows as
  `perf_event__process_feature()` handles features, capped at
  `HEADER_LAST_FEATURE`.
- End marker: recognised by `header.size ==
  sizeof(struct perf_record_header_feature)` and `feat_id >= last_feat`. A
  writer built from another version sends another `HEADER_LAST_FEATURE`.
- `perf_event__process_feature()` handles the end marker itself. Wrappers call
  it first and test for the marker afterwards, as `process_feature_event()` in
  `tools/perf/builtin-report.c` does.
- `perf_header__has_feat()` on pipe input: false for every feature the input
  carries, before and after the feature events.
  `perf_event__process_feature()` does not call `perf_header__set_feat()`.
- `perf_header__has_feat()` on a file whose header has `data.size == 0`: false
  for every feature. `perf_session__read_header()` zeroes the bitmap and skips
  the sections.
- **Potentially unsafe usage**: choosing a mode or failing on the result of
  `perf_header__has_feat()`.
  - Unsafe: when the input can be pipe format and nothing else tests for it;
    the feature may have arrived and the test still says absent.
  - Safe: combined with `!is_pipe`, as `report__setup_sample_type()` does for
    `HEADER_AUXTRACE`.
  - Safe: testing the value the `process` hook stored in `struct perf_env`, as
    `perf_session__process_compressed_event()` in `tools/perf/util/tool.c`
    does with `comp_mmap_len`; on pipe input the value is there only when
    `feature` is `perf_event__process_feature()` or a wrapper.

**Adding a header feature**

- `FEAT_OPR` and `FEAT_OPN`: both set `.write`, `.print` and `.process`. The
  only difference is `.synthesize = true` in `FEAT_OPR`.
- `FEAT_OPN` feature: never reaches a pipe reader through
  `perf_event__synthesize_features()`.
- `FEAT_OPN` does not imply that the write hook needs the fd. `HEADER_CACHE`
  and `HEADER_HYBRID_TOPOLOGY` are `FEAT_OPN` and write through `do_write()`
  only.
- Both macros paste `write_`, `print_` and `process_` onto the name. A hook
  that does not exist is `#define`d to `NULL` above `feat_ops`, as
  `process_stat` is.
- `FEAT_OPR` write hook, pipe output: runs with `ff->buf` set and no usable
  `ff->fd`. `__do_write_buf()` returns `-E2BIG` once `ff->offset` plus the
  write passes `0xffff - sizeof(struct perf_event_header)`.
- `FEAT_OPR` process hook, pipe input: runs with `data` NULL and reads from
  `ff->buf`.
- Write hook fails, file output: `perf_header__adds_write()` clears the bit and
  carries on; the only message is `pr_debug()`.
- Write hook fails, pipe output: `perf_event__synthesize_features()` skips the
  feature, again with `pr_debug()` only.
- `record__init_features()` covers `perf record` only. `init_features()` in
  `tools/perf/builtin-stat.c` uses the same set-all loop.
- `perf_sched__schedstat_record()` in `tools/perf/builtin-sched.c`: sets an
  explicit list, so a new feature is not written there unless added.
- `perf inject`: keeps the input's bits. `keep_feat()` in
  `tools/perf/builtin-inject.c` decides per feature whether the section is
  copied from the input.
- A feature not listed in `keep_feat()`: takes `default: return false`, and is
  regenerated by its write hook on the machine that runs `perf inject`.
- `tools/perf/Documentation/perf.data-file-format.txt`: lists each feature with
  its number.

## The recorded environment

**Environment ownership**

- Global env: none. There is no perf_env__host(); each live user declares its
  own `struct perf_env host_env` (search `host_env` under `tools/perf`).
- `perf_session__env()`: returns `&session->header.env` for every kind of
  session, including live ones.
- `session->machines.host.env` is a second route and is not always the same
  object:

  | Session | `perf_session__env()` | `session->machines.host.env` |
  |---|---|---|
  | read, file or pipe | `header.env`, filled from the input | same object, set in `perf_session__read_header()` |
  | write (`perf record`) | `header.env` | NULL |
  | `data == NULL` (live) | `header.env`; `__perf_session__new()` only `perf_env__init()`s it | the caller's `host_env` |

- Guest machines: `machine->env` stays NULL from `machine__init()`.
- `__perf_session__new()` with `data == NULL`: `assert(host_env != NULL)`, then
  stores the pointer; nothing is copied.
- `perf_session__new()`: passes NULL for `host_env`, so it cannot be used
  without a `struct perf_data`.
- `host_env` lifetime: the caller owns it; `perf_session__delete()` calls
  `perf_env__exit()` on `session->header.env` only.
- `perf_env__set_cmdline()`: not called by `__perf_session__new()`; callers
  call it on their `host_env`, as `cmd_top()` does.
- `cmd_top()` in `tools/perf/builtin-top.c`: fills `host_env` eagerly with
  cmdline, `perf_env__read_cpuid()` and, with branch stacks,
  `perf_env__read_core_pmu_caps()`; with `HAVE_LIBBPF_SUPPORT`, BPF side-band
  data also goes to `host_env`.
- `cmd_top()` data in `host_env` is not visible through
  `perf_session__env(top->session)`.
- perf trace live: no session; `trace->host_env` is passed to
  `machine__new_host()`, so the env is reached as `machine->env`, not through
  a session.
- `struct evlist`: has no `env` member, only a `session` back-pointer set by
  `evlist__set_session()`.
- `evsel__env()`: returns `perf_session__env()` of the evlist's session, or
  NULL when the evsel has no evlist or the evlist has no session.
- Pipe fill: `PERF_RECORD_HEADER_FEATURE` reaches `tool->feature`;
  `perf_tool__init()` installs `process_event_op2_stub()`, so no header
  feature reaches the env unless the tool sets `feature` to
  `perf_event__process_feature()` or a wrapper.
- Regular file, `nr_cpus_avail` still 0 after the sections:
  `perf_session__read_header()` sets it to `MAX_NR_CPUS`; the pipe path returns
  before this.
- Header `write` callbacks: some use `ff->ph->env`, for example
  `write_cmdline()` and `write_cpu_topology()`; the latter fills `env->cpu`
  through `perf_env__read_cpu_topology_map()`.

**Reading perf_env fields**

- normalize_arch(), perf_env__raw_arch(), perf_env__read_arch(),
  perf_env__init_nodes(), perf_env__find_pmu_caps() and evsel__get_arch() do
  not exist here; the raw recorded string is the field `env->arch`.
- `perf_env__arch()`: maps `perf_env__e_machine()` to a static perf arch name
  such as "x86", "arm64" or "powerpc"; never NULL, never the `uname()` string,
  and it does not write `env->arch`.
- `perf_env__e_machine()` in `tools/perf/util/env.c`: the accessor used for
  arch decisions, compared with `EM_` constants; see
  `evlist__init_trace_event_sample_raw()` in `tools/perf/util/sample-raw.c`.
- `env->arch != NULL`: the in-tree test for "recorded, not live"; for example
  `perf_env__lookup_objdump()` in `tools/perf/arch/common.c` returns early
  when it is NULL.
- `perf_env__os_release()`: with `env->os_release` unset, returns NULL when
  `env->arch` is set and fills from `uname()` only when it is not; a NULL env
  gives `perf_version_string`.
- `env->lock`: taken only by `perf_env__os_release()`; the other lazy
  accessors fill their fields without it.
- NULL env is accepted by `perf_env__arch()`, `perf_env__e_machine()`,
  `perf_env__e_machine_nocache()`, `perf_env__nr_cpus_avail()` and
  `perf_env__os_release()`; the other accessors in `tools/perf/util/env.c` and
  `perf_env__get_cpu_topology()` have no NULL test of `env`.
- `perf_env__get_cpu_topology()`: static inline in `tools/perf/util/env.h`;
  returns `&env->cpu[cpu.cpu]`, or NULL when `env->cpu` is NULL or the cpu is
  outside `[0, env->nr_cpus_avail)`; it fills nothing.
- `perf_env__get_cpu_topology()` in use: for example
  `perf_env__get_socket_aggr_by_cpu()` in `tools/perf/builtin-stat.c`, which
  leaves the id empty on NULL.
- `perf_env__numa_node()`: its only caller is
  `perf_env__get_node_aggr_by_cpu()` in `tools/perf/builtin-stat.c`.
- `env->nr_cpus_avail == 0`: not a test for a missing `HEADER_NRCPUS` on a
  regular file, see "Environment ownership"; it is 0 in a record session until
  `write_cpu_topology()` runs.
- **Potentially unsafe usage**: indexing `env->cpu[]` directly.
  - Unsafe: with a cpu from a sample or cpu map when nothing has shown
    `env->cpu` non-NULL; `process_cpu_topology()` in
    `tools/perf/util/header.c` leaves it NULL for old-format data while
    `nr_cpus_avail` is set.
  - Safe: through `perf_env__get_cpu_topology()` with a NULL test, as
    `perf_env__get_core_aggr_by_cpu()` does.
  - Safe: after `perf_env__read_cpu_topology_map()` returned 0, with the index
    bounded by `env->nr_cpus_avail`, as `write_cpu_topology()` does.
- **Potentially unsafe usage**: passing a wider cpu number to
  `perf_env__get_cpu_topology()`.
  - Unsafe: when the value was not range-checked first; `struct perf_cpu`
    holds an `int16_t`, so a large value wraps to a valid index.
  - Safe: when the wide value is known to be below `env->nr_cpus_avail` and
    inside the `int16_t` range before the `struct perf_cpu` is built:
    `machine__resolve()` in `tools/perf/util/event.c` compares `al->cpu` with
    `env->nr_cpus_avail`, and for a sample that came through
    `perf_session__deliver_event()` that function has already clamped
    `sample.cpu` below `MAX_NR_CPUS`, other than `(u32)-1`, which the
    `al->cpu >= 0` test in `machine__resolve()` rejects.
- **Potentially unsafe usage**: dereferencing the result of `evsel__env()` or
  `machine->env`.
  - Unsafe: when the evlist has no session, or the machine is a guest or the
    host of a write-mode session; the pointer is NULL.
  - Safe: test first, as `thread__resolve_callchain_sample()` in
    `tools/perf/util/machine.c` and `format_field__get_cpumask()` in
    `tools/perf/util/evsel.c` do.
  - Safe: `perf_session__env()` on a valid session; it returns the address of
    an embedded member.

## Events and PMUs

**Kinds of PMU**

- Kinds created without a sysfs PMU directory:

| Kind | Created by | File | `type` |
|---|---|---|---|
| tool | `tool_pmu__new()` | `tools/perf/util/tool_pmu.c` | `PERF_PMU_TYPE_TOOL` |
| hwmon | `perf_pmus__read_hwmon_pmus()` | `tools/perf/util/hwmon_pmu.c` | `PERF_PMU_TYPE_HWMON_START` + N |
| DRM | `perf_pmus__read_drm_pmus()` | `tools/perf/util/drm_pmu.c` | from `PERF_PMU_TYPE_DRM_START` |
| fake | `perf_pmus__fake_pmu()` | `tools/perf/util/pmus.c` | `PERF_PMU_TYPE_FAKE` |
| placeholder core | `perf_pmu__create_placeholder_core_pmu()` | `tools/perf/util/pmu.c` | `PERF_TYPE_RAW` |

- There is no perf_pmus__tool_pmu() and no perf_pmu__fake symbol here.
- `perf_pmus__fake_pmu()`: returns a function-static struct and does not add it
  to `core_pmus` or `other_pmus`.
- Placeholder core PMU: made by `pmu_read_sysfs()` when `core_pmus` is empty
  after the sysfs read; it has `is_core` set and counts as
  `PERF_PMU_KIND_PE`, so no kind test separates it from a sysfs core PMU.
- `perf_pmu__kind()` in `tools/perf/util/pmu.h`: maps `pmu->type` to
  `enum pmu_kind`; compare with `PERF_PMU_KIND_PE` to cover DRM, hwmon, tool
  and fake in one test, as `store_evsel_ids()` does.
- `evsel__is_non_perf_event_open_pmu()` in `tools/perf/util/evsel.c`: the
  evsel form, `evsel->pmu->type > PERF_PMU_TYPE_PE_END`.
- NULL PMU: `perf_pmu__kind()` returns `PERF_PMU_KIND_PE`;
  `perf_pmu__is_tool()`, `perf_pmu__is_hwmon()` and `perf_pmu__is_drm()` return
  false; `perf_pmu__is_fake()` and `perf_pmu__is_tracepoint()` dereference it.
- `attr.type`: `parse_events_add_pmu()` stores `pmu->type` there for every
  kind, so a tool, hwmon or DRM evsel carries the synthetic type in its attr;
  what must be guarded is the syscall, not the assignment.
- Walkers: tool, hwmon and DRM PMUs are put on `other_pmus`, so
  `perf_pmus__scan()` returns them; `perf_pmus__scan_core()` walks `core_pmus`
  only.
- Event lookup in `tools/perf/util/pmu.c`: `perf_pmu__have_event()` and
  `perf_pmu__num_events()` hand off for tracepoint, hwmon and DRM only.
- Tool PMU events: ordinary aliases from the json table named "common" (set
  in `tool_pmu__new()`), filtered by `tool_pmu__skip_event()`.
- Tracepoint PMU: kind `PERF_PMU_KIND_PE`, yet its events come from
  `tools/perf/util/tp_pmu.c`, not from aliases.

**Opening on older kernels**

- `evsel__detect_missing_features()`: called only from `evsel__open_cpu()`, at
  `try_fallback`, and only when `err == -EINVAL`.
- Order at `try_fallback`: `evsel__ignore_missing_thread()`, then the
  `-EMFILE` rlimit retry, then the detection, then
  `evsel__precise_ip_fallback()`.
- A true return: `goto fallback_missing_features`, not `retry_open`; that
  label reruns `evsel__disable_missing_features()` and restarts the open loop
  at `start_cpu_map_idx`.
- Generic probes: use a scratch attr (software task-clock, disabled), never
  the evsel's attr; the evsel's attr is edited by
  `evsel__disable_missing_features()`, not by the probes.
- Run-once state: a separate static `detection_done` in each of
  `evsel__detect_missing_features()`,
  `evsel__detect_missing_brstack_features()` and
  `evsel__detect_missing_aux_action_feature()`; per PMU it is
  `pmu->missing_features.checked`.
- Every call, even after `detection_done`: the helper calls and the tests
  under `check:` run, so the return value is per evsel.
- `exclude_guest`: kept in `pmu->missing_features.exclude_guest`; the
  `exclude_guest` member of `struct perf_missing_features` is neither read nor
  written.
- `struct perf_missing_features` has no `build_id` member.
- Where a new probe goes, directly under the comment "Please add new feature
  detection here." of the matching list:

| Feature | Function | Probe event |
|---|---|---|
| kernel-wide attr bit or flag | `evsel__detect_missing_features()` | scratch software event |
| `branch_sample_type` bit | `evsel__detect_missing_brstack_features()` | the evsel's `type` and `config` |
| depends on the PMU | `evsel__detect_missing_pmu_features()` | the evsel's `type` and `config` |

- A feature perf can drop needs all four:
  - a `bool` in `struct perf_missing_features`
  - the probe, which on failure sets the flag and then resets its bits in the
    scratch attr, so the next probe tests one feature
  - the clear in `evsel__disable_missing_features()`
  - a test under `check:` that returns true when this evsel uses the feature
- Without the `check:` test the function returns false and the open fails
  with `-EINVAL` although the flag is set.
- A feature perf cannot drop gets the `bool` and the probe, no clear and no
  `check:` test, and a message under `EINVAL` in `evsel__open_strerror()`; for
  example `code_page_size` and `data_page_size`.
- `write_backward` and `aux_output`: also rejected with `-EINVAL` by
  `__evsel__prepare_open()` once the flag is set.

**Adding a sample field**

- `evsel__parse_sample()`: an inline wrapper in `tools/perf/util/evsel.h`; the
  parser to change is `__evsel__parse_sample()` in `tools/perf/util/evsel.c`.
- `aslr_tool__process_sample()` in `tools/perf/util/aslr.c`: another walker of
  the raw sample layout; it steps through the original `sample_type` bit by
  bit, so a new field has to be copied or skipped there, in the same order.
- `ASLR_SUPPORTED_SAMPLE_TYPE` in `tools/perf/util/aslr.h`: the bits the ASLR
  tool keeps; `aslr_tool__strip_evlist()` masks every other bit out of
  `sample_type`.
- `__evsel__sample_size()`: counts only bits in `PERF_SAMPLE_MASK`
  (`tools/perf/util/event.h`); change it only if the new bit joins that mask.
- Fields outside `PERF_SAMPLE_MASK`: `perf_event__check_size()` does not bound
  them.
- **Unsafe usage**: a read of a field outside `PERF_SAMPLE_MASK` in
  `__evsel__parse_sample()` with no `OVERFLOW_CHECK()` or
  `OVERFLOW_CHECK_u64()` before it; the read can go past `header.size`.
  - Safe: `OVERFLOW_CHECK_u64(array)` before the read, as the
    `PERF_SAMPLE_DATA_SRC` block of `__evsel__parse_sample()` does;
    `overflow()` compares against `endp`, the event plus `header.size`.
- `perf_event__attr_swap()`: in `tools/perf/util/session.c`; a new sized field
  needs its own `bswap_field_64()`, `bswap_field_32()` or `bswap_field_16()`
  line.
- `swap_bitfield()`: covers only the 8 bytes after `read_format`.
- Attr test: there is no tools/perf/tests/attr.c and no tools/perf/tests/attr/
  here; `store_event()` is in `tools/perf/util/evsel.c` and writes a fixed
  list of fields with `WRITE_ASS()`.
- Attr test files: `tools/perf/tests/shell/attr.sh`,
  `tools/perf/tests/shell/lib/attr.py`, expected values under
  `tools/perf/tests/shell/attr/`.
- `do_test()` in `tools/perf/tests/sample-parsing.c`: of the functions that
  walk the sample layout it calls only `perf_event__sample_event_size()`,
  `perf_event__synthesize_sample()`, `__evsel__sample_size()` and
  `evsel__parse_sample()`.
- Not covered by that test: `evsel__parse_sample_timestamp()`,
  `perf_evsel__parse_id_sample()`, `perf_event__synthesize_id_sample()`,
  `evsel__id_hdr_size()`, `aslr_tool__process_sample()`.
- Swap in that test: the same unswapped event is parsed again with
  `needs_swap` set, and only when `sample_type` equals
  `PERF_SAMPLE_BRANCH_STACK`; swap handling of a new field is not tested.
- `samples_same()`: compares only the fields it names, so a new field that is
  not added there passes whatever the parser returns.

**Walking directories**

- `for_each_drm_fdinfo_in_dir()` and `for_each_drm_fdinfo()`: walk with libc
  `fdopendir()` or `opendir()` and `readdir()`, not with `struct io_dir`.
- Other `fdopendir()` walks under `tools/perf`: search for `fdopendir`; for
  example `dump_perf_event_processes()` in `tools/perf/util/evsel.c`.
- Raw fd after `fdopendir()`: still passed to `fstatat()`, `readlinkat()` or
  `openat()` while the `DIR` is open; `for_each_drm_fdinfo_in_dir()` does
  `fstatat(fd_dir_fd, ...)` inside the loop.
- Descriptors `for_each_drm_fdinfo_in_dir()` opens:

| Descriptor | Opened | Released by |
|---|---|---|
| `fd_dir_fd` (`<pid>/fd`) | on entry | `closedir(fd_dir)`; `close()` only if `fdopendir()` failed |
| `fdinfo_dir_fd` (`<pid>/fdinfo`) | lazily, at the first DRM fd | `close()`, only if not -1 |

- Both `openat()` calls pass `O_DIRECTORY` only.
- Callback error path: `goto close_fdinfo`, the same label the loop falls
  into when `readdir()` ends.
- `<pid>/fd` open failure: returns 0 before anything else is open.
- `<pid>/fdinfo` open failure: `continue`; the open is tried again at the
  next DRM fd.
- Callback arguments: `args`, `fdinfo_dir_fd` and the entry name; the callback
  gets no per-file descriptor.
- `proc_dir`: borrowed; `for_each_drm_fdinfo()` passes `dirfd(proc_dir)` and
  goes on calling `readdir(proc_dir)`, `drm_pmu__read_for_pid()` closes its
  own.
- **Unsafe usage**: leaving the `readdir()` loop of
  `for_each_drm_fdinfo_in_dir()` with `return`, which skips both releases.
  - Safe: `continue`, or `goto close_fdinfo` as the callback error path does.
- **Unsafe usage**: a callback that closes or keeps `fdinfo_dir_fd`; the next
  entry reuses it and `close_fdinfo` closes it again.
  - Safe: open the entry with `openat(fdinfo_dir_fd, fd_name, O_RDONLY)` and
    close only that descriptor before returning, as `read_drm_event()` does.
- **Unsafe usage**: closing `proc_dir` inside `for_each_drm_fdinfo_in_dir()`.
  - Safe: leave it to the caller, as `for_each_drm_fdinfo()` does with
    `closedir(proc_dir)`.

## Optional features and portable builds

**Feature detection**

- `FEATURE_TESTS_EXTRA` in `tools/build/Makefile.feature`: not part of
  `FEATURE_TESTS` in a default build; `FEATURE_TESTS` defaults to
  `FEATURE_TESTS_BASIC`, and becomes both lists only for the `feature-dump`
  goal (`tools/perf/Makefile.perf`).
- Name in `FEATURE_TESTS_EXTRA` (in a default build) or in neither list:
  `feature-<name>` is empty unless something calls
  `$(call feature_check,<name>)`, as `tools/perf/Makefile.config` does for
  `libcapstone` (in `FEATURE_TESTS_EXTRA`) and `llvm-perf` (in neither).
- `FEATURES_DUMP=<file>` builds: `Makefile.config` includes the file
  instead of `Makefile.feature`, so `feature_check` is undefined and each
  `$(call feature_check,...)` expands to nothing.
- `FEATURE-DUMP` contents: only the names in `$(FEATURE_TESTS)`; a name in
  neither list is absent from it and reads as off in a `FEATURES_DUMP=`
  build, which is how the `build-test` target of `tools/perf/Makefile`
  runs `tools/perf/tests/make`.
- Names not derived from the feature name: the `HAVE_` macro, the `CONFIG_`
  symbol, the `NO_` switch and the `supported_features[]` name; for
  example feature `libaio` gives `HAVE_AIO_SUPPORT`, `NO_AIO` and "aio".
- `HAVE_` macro: must be spelled the same in the `-D` of `Makefile.config`,
  the `#ifdef` in sources and the second argument of `FEATURE_STATUS()`.
- `CONFIG_` symbol: must be spelled the same in `$(call detected,...)` and
  in the `Build` files.
- `supported_features[]` name: must match what shell tests pass to
  `perf check feature`; the table in
  `tools/perf/Documentation/perf-check.txt` repeats the names but lacks
  some, for example "rust".
- `FEATURE_STATUS(name_, macro_)`: name string first, macro second.
- `IS_BUILTIN()` in `tools/include/tools/config.h`: 1 only when the macro
  is visible in `tools/perf/builtin-check.c` and defined as 1; a misspelled
  macro compiles and prints `OFF`.
- Macro defined in a header, not by `-D`: `builtin-check.c` must include
  that header, as it does `util/bpf-utils.h` for
  `HAVE_LIBBPF_STRINGS_SUPPORT`.
- `tools/perf/scripts/install-build-deps.sh`: maps each `test-<name>`
  source to a distro package in `fedora_pkg_for()` and `debian_pkg_for()`;
  a name with no case there is skipped silently by
  `make install-build-deps`.

**All-in-one feature test**

- `test-all.bin` builds: every name in `FEATURE_TESTS` is set to 1 by
  `feature_set`, whether or not `test-all.c` includes its test.
- `FEATURE_TESTS=all` (the `feature-dump` goal): the fast path sets the
  `FEATURE_TESTS_EXTRA` names to 1 too.
- Re-tested by `tools/build/Makefile.feature` after the fast path: only the
  names under `ifeq ($(feature-all), 1)`, namely `compile-32`,
  `compile-x32`, `bionic`, `babeltrace2-ctf-writer`, `libunwind`,
  `libunwind-debug-frame` and the per-arch libunwind tests.
- Comment in `Makefile.feature` that both lists are included in
  `test-all.c`: does not match the file; compare the list with the
  `#include` lines instead.
- `fortify-source`: has no include in `test-all.c`; `BUILD_ALL` in
  `tools/build/feature/Makefile` passes `-O2 -D_FORTIFY_SOURCE=2` instead.
- Slow path: one `$(shell $(MAKE) ...)` per name inside `$(foreach ...)`.
- Link flags of `test-all.bin`: the flags written in `BUILD_ALL`, plus
  `FEATURE_CHECK_LDFLAGS-all`, which `set_test_all_flags` builds from
  `FEATURE_CHECK_LDFLAGS-<name>` of each name in `FEATURE_TESTS`.
- **Potentially unsafe usage**: a name in `FEATURE_TESTS_BASIC` whose test
  `test-all.c` does not include.
  - Unsafe: when nothing calls `feature_check` for the name before
    `Makefile.config` reads `feature-<name>`; where `test-all.bin` builds
    the value is 1 with the library absent, and the perf build fails later
    on the missing header or library.
  - Safe: test included in `test-all.c` and called from its `main()`, with
    the `-l` flag in `BUILD_ALL`, as `libzstd` is.
  - Safe: in a build without `FEATURES_DUMP=`, `Makefile.config` calls
    `$(call feature_check,<name>)` before every read, as it does for
    `libbfd` under `BUILD_NONDISTRO`.

**Guarding optional code**

| Header | Guard | Stub returns |
|---|---|---|
| `tools/perf/util/bpf-filter.h` | `HAVE_BPF_SKEL` | `-EOPNOTSUPP`; `perf_bpf_filter__lost_count()` 0 |
| `tools/perf/util/bpf_counter.h` | `HAVE_BPF_SKEL` | 0; `bpf_counter__read()` `-EAGAIN` |
| `tools/perf/util/compress.h` | `HAVE_LZMA_SUPPORT` | -1, `false` |
| `tools/perf/util/compress.h` | `HAVE_ZSTD_SUPPORT` | 0 from all four stubs |
| `tools/perf/util/compress.h` | `HAVE_ZLIB_SUPPORT` | no stubs |
| `tools/perf/util/unwind.h` | `HAVE_LIBDW_SUPPORT`, `HAVE_LIBUNWIND_SUPPORT` | `pr_warning_once()`, then 0; `unwind__prepare_access()` 0 with no warning |
| `tools/perf/util/cs-etm.h` | `HAVE_CSTRACE_SUPPORT` | -1 |

- Stub return values: no tree-wide convention; a stub that returns 0 is
  indistinguishable from success, so a caller that must refuse the
  operation cannot rely on the stub.
- `unwind__get_entries()`: always declared and built (`unwind.o` is
  `perf-util-y`); the stubs in `unwind.h` that warn are
  `libdw__get_entries()` and `libunwind__get_entries()`.
- `tools/perf/util/demangle-java.h` and `tools/perf/util/auxtrace.h`: have
  no feature guard; there is no bpf-loader.h.
- `LIBCAPSTONE_DLOPEN`: `Makefile.config` then omits `-lcapstone` and
  `tools/perf/util/capstone.c` loads `libcapstone.so` with `dlopen()`, so
  the binary runs where the library is not installed.
- **Potentially unsafe usage**: calling a function whose prototype sits
  under `#ifdef HAVE_..._SUPPORT` with no `#else` stub.
  - Unsafe: from code that is compiled when the feature is off; only the
    builds without the library fail.
  - Safe: the call is under the same `#ifdef`, as the "gz" entry using
    `gzip_decompress_to_file()` in `tools/perf/util/dso.c` is under
    `HAVE_ZLIB_SUPPORT`, the guard `compress.h` puts on the prototype.
  - Safe: the caller is in a file that `tools/perf/util/Build` builds only
    when the feature is on, as `tools/perf/util/bpf_ftrace.c`, which calls
    `set_max_rlimit()`, is `perf-util-$(CONFIG_PERF_BPF_SKEL)`;
    `Makefile.config` sets `CONFIG_PERF_BPF_SKEL` and `HAVE_BPF_SKEL`
    together.

**The Python module**

- There is no python-ext-sources file; `tools/perf/util/setup.py` lists
  only `util/python.c` as a source.
- Module contents: `LIBS_PY` in `tools/perf/Makefile.perf`, passed in
  `LDFLAGS`, links `PERFLIBS_PY` inside `-Wl,--whole-archive`, followed by
  `$(EXTLIBS)`.
- `PERFLIBS_PY`: `PERFLIBS` without `$(LIBPERF_BENCH)` and
  `$(LIBPERF_TEST)`; `libperf-util.a`, `libperf-ui.a` and
  `libpmu-events.a` are in it.
- `--whole-archive`: every object of those archives is in the module, so
  an unresolved symbol in any of them breaks `import perf`, even if
  `python.c` never reaches it.
- New file under `tools/perf/util`: any `perf-util-` entry in a `Build`
  file puts it in the module; it must not reference symbols defined only
  under `perf-y`, `perf-bench-y` or `perf-test-y` (`tools/perf/Build`).
- `tools/perf/util/python.c`: defines no stand-ins for perf internals; its
  only non-static function is `PyInit_perf()`.
- New optional library: add it to `EXTLIBS` in
  `tools/perf/Makefile.config`; `LIBS` for the perf binary and `LIBS_PY`
  both take `$(EXTLIBS)`.
- `CFLAGS`: `python.c` is compiled with the perf `CFLAGS`, so it sees the
  same `HAVE_` macros and header stubs.
- Test: `tools/perf/tests/shell/python-use.sh`, which only runs
  `import perf`; there is no tests/python-use.c.
- `make_python_perf_so` in `tools/perf/tests/make`: builds the module
  target and checks with `test -f` that the file exists; it does not
  import it.
- Module not built: when `import setuptools` fails, `Makefile.config`
  prints a warning and leaves the module out of `LANG_BINDINGS`.

**C library portability**

- Written rule: none found in `tools/perf` or `tools/build`; what exists
  are comments such as the one on `<linux/stddef.h>` in
  `tools/perf/util/event.h`.

| Feature | Macro | Fallback |
|---|---|---|
| `gettid` | `HAVE_GETTID` | `static inline gettid()` repeated in each file that needs it, for example `tools/perf/builtin-record.c` |
| `setns` | `HAVE_SETNS_SUPPORT`, `CONFIG_SETNS` | `tools/perf/util/setns.c`, built when `CONFIG_SETNS` is unset |
| `sched_getcpu` | `HAVE_SCHED_GETCPU_SUPPORT` | `sched_getcpu()` in `tools/perf/util/util.c` |
| `scandirat` | `HAVE_SCANDIRAT_SUPPORT` | `scandirat()` in `tools/perf/util/util.c` |
| `reallocarray` | `COMPAT_NEED_REALLOCARRAY`, set when the test fails | `tools/include/tools/libc_compat.h`; the file must include it |
| `pthread-attr-setaffinity-np` | `HAVE_PTHREAD_ATTR_SETAFFINITY_NP` | stub returning 0 in `tools/perf/bench/bench.h` |

- No fallback, code compiled out: `pthread-barrier`, `eventfd`,
  `backtrace`, `timerfd`, `file-handle`.
- `strlcpy()`: not feature-tested; `__weak` definition in
  `tools/lib/string.c`.
- get_current_dir_name: no feature test and no fallback file in this tree.
- `glibc`: `feature-glibc` is read only to pick the error message when
  libelf is missing.
- `bionic`: in `FEATURE_TESTS_EXTRA`, tested by `feature_check` in
  `Makefile.config`; sets `LACKS_SIGQUEUE_PROTOTYPE` and
  `LACKS_OPEN_MEMSTREAM_PROTOTYPE`, and drops `-lrt` and `-lpthread` from
  `EXTLIBS`.

**Copies of kernel headers**

- `tools/perf/check-headers.sh`: not run by any perf build;
  `tools/perf/Makefile.perf` never names it.
- Only caller: the `check-headers` target in `tools/perf/Makefile`, run as
  `make -C tools/perf check-headers`.
- Consequence: a perf build prints no warning when a copy has drifted from
  the original.
- `tools/include/uapi/README`: calls the script "part of the tools/ build
  process"; that does not match `Makefile.perf`.
- Exit status: 0 after printing the differences, so the `check-headers`
  target does not fail either.
- Working directory: the script tests `../../include`, so it must start in
  `tools/perf`.
- README on commits: says not to touch the copies when changing the
  originals, and that the update is done later, after `check-headers.sh`
  reports the change; it says nothing about how the later sync is split
  into commits.
- Scope: also compares the copies under `tools/perf/trace/beauty`
  (`BEAUTY_FILES`), and tolerates known differences through `diff -I`
  patterns and `tools/perf/check-header_ignore_hunks`.

## Tests

**Shell tests and workloads**

- Discovery: `create_script_test_suites()` in
  `tools/perf/tests/tests-scripts.c`; there is no run_shell_tests() or
  shell_tests__dir() here.
- `shell_tests__dir_fd()`: tries, in order, `./tools/perf/tests/shell`,
  `./tests/shell` and `./source/tests/shell` relative to the current
  directory, then `tests/shell` and `source/tests/shell` beside the
  executable, then `tests/shell` under `get_argv_exec_path()`.
- Current directory first: an installed perf run from the top of a kernel
  tree runs that tree's scripts, not the installed ones.
- `is_shell_script()`: a test needs the `.sh` suffix as well as read and
  execute permission.
- `append_scripts_in_dir()`: skips entries whose name starts with `.`, does
  not descend into directories whose name starts with `base_`, and descends
  into every other directory with no depth limit.
- `lib` and `common`: not excluded by name; a file there becomes a test if it
  ends in `.sh`, is executable and has a description line.
- `base_` directories: run by a driver script, for example
  `tools/perf/tests/shell/perftool-testsuite_probe.sh`.
- `shell_test__description()`: the description is the first line that starts
  with `#` (after optional whitespace), is not `#!`, is not an SPDX
  identifier line, and has text; it need not be line two.
- ` (exclusive)`: `append_script()` looks for it anywhere in the description,
  with the leading space, and cuts the description there; text after it is
  lost.
- `shell_test__run()`: runs the script with `system()`, by absolute path, with
  ` -v` appended when `verbose` is set; only exit status 2 maps to
  `TEST_SKIP`.
- `workloads[]` in `tools/perf/tests/builtin-test.c`: holds more than the
  commonly remembered names; `workload__code_with_type` is present only under
  `HAVE_RUST_SUPPORT`. `perf test --list-workloads` prints the set.
- `--record-ctl fifo:ctl-fifo[,ack-fifo]`: `run_workload()` writes `enable`
  to the FIFO before calling the workload and `disable` after it, and waits
  for `ack` when an ack FIFO is given; see
  `tools/perf/tests/shell/coresight/deterministic.sh`.
- Workload symbols: the workload code is part of the perf binary, so a script
  that greps for a workload symbol can first call
  `skip_test_missing_symbol()` from
  `tools/perf/tests/shell/lib/perf_has_symbol.sh`, which exits 2 when perf
  lacks the symbol, as `tools/perf/tests/shell/record.sh` does.

**Shell script temporary files**

- **Potentially unsafe usage**: a temporary file whose name is fixed in the
  script.
  - Unsafe: directly under a shared directory such as `/tmp`. `start_test()`
    in `tools/perf/tests/builtin-test.c` runs non-exclusive scripts in
    parallel, and the `runs_per_test` loop (`-r`) starts several copies of
    one such script together, so a name unique to the script still collides.
  - Safe: a fixed name inside a directory made by `mktemp -d`, as
    `tools/perf/tests/shell/script.sh` does.
- **Potentially unsafe usage**: `exit` after `trap trap_cleanup EXIT TERM INT`
  is installed.
  - Unsafe: when `cleanup` has not run first and `trap_cleanup` ends in
    `exit 1`. The EXIT trap runs `trap_cleanup`, so `exit 2` or `exit 0` is
    reported as failed by `shell_test__run()`.
  - Safe: call `cleanup`, which resets the trap, then exit; as
    `tools/perf/tests/shell/timechart.sh` does before `exit 2` and
    `tools/perf/tests/shell/record.sh` does before `exit $err`.
  - Safe: make the skip checks before the trap is installed, as
    `tools/perf/tests/shell/record.sh` does with `skip_test_missing_symbol`.
  - Safe: `trap cleanup EXIT` with a separate `TERM INT` trap that exits 1, as
    `tools/perf/tests/shell/data_validation.sh` does; the exit status is kept.
  - Safe: a `trap_cleanup` that ends in `exit ${err}`, with `err` set before
    each `exit`, as `check()` in `tools/perf/tests/shell/lock_contention.sh`
    does with `err=2`.
- `perf_record_with_retry()` in `tools/perf/tests/shell/lib/perf_record.sh`:
  makes its own `mktemp` log file on each call and records it in
  `PERF_RECORD_LOGS`; the script's `cleanup` has to call
  `perf_record_cleanup`, as `tools/perf/tests/shell/record.sh` does.
- `mktemp` templates: in-tree tests pass an absolute `/tmp/` template; the
  `__perf_test.` prefix is common but nothing checks for it.
- `rm -rf` of a directory variable: `tools/perf/tests/shell/script.sh` first
  checks that the path starts with its own `/tmp/` prefix.
- Removal on failure: not uniform in the tree;
  `tools/perf/tests/shell/inject_aslr.sh` keeps `temp_dir` when the exit code
  or `err` is non-zero.
- `__cmd_test()`: has no per-test timeout; on `SIGINT` or `SIGTERM` it sends
  the signal to each forked perf child, not to the script that child started
  with `system()`.

**C test suites**

- `DEFINE_SUITE()`: defines both the one-entry `struct test_case` array and
  the `struct test_suite`; a suite with several cases writes the array and
  the struct by hand.
- `TEST_SKIP`: is −2. A case that returns 1 is reported FAILED, through the
  `default:` case of `print_test_result()`.
- `check_leaks()`: `run_test_child()` calls it after the case returns; a file
  descriptor above 3 left open makes the child `abort()`, so the case is
  reported FAILED whatever it returned. Not run with `-F`.
- `setup` in `struct test_suite`: `build_suites()` calls it for every suite,
  also for `perf test list`; a negative return stops perf test before any
  test runs. It may replace `test_cases`, as `setup_pmu_events_suite()` in
  `tools/perf/tests/pmu-events.c` does.
- `arch_tests[]`: `tools/perf/tests/builtin-test.c` uses the arch file's array
  only when `__i386__`, `__x86_64__`, `__aarch64__` or `__powerpc64__` is
  defined; otherwise it defines its own empty static array, so a new
  architecture has to extend that `#if`.
- Exclusive and numbering: `build_suites()` puts every suite that has at
  least one exclusive case after all suites that have none, shell scripts
  included; marking a case exclusive changes the suite's number in
  `perf test list`.
- Suite with both kinds of case: `start_test()` decides per case, so the
  non-exclusive cases run in the parallel pass and the exclusive ones in the
  second pass; see `tests__basic_mmap` in `tools/perf/tests/mmap-basic.c`.
- `-F`: `cmd_test()` sets `sequential` too, so the exclusive flag then only
  affects list order.

## Model gaps

### Other mistakes models make

- Models take a default perf.data to carry `HEADER_BUILD_ID`. `struct record`
  starts with `buildid_mmap` true; `cmd_record()` sets `no_buildid` while it
  is still true, so `record__init_features()` clears the feature.
- Models take `sample->cpu` to arrive as recorded.
  `perf_session__deliver_event()` sets it to 0 when it is at or above a
  bound taken from the env's `nr_cpus_avail`, at most `MAX_NR_CPUS`, except
  for the `(u32)-1` sentinel.
- Models do not know the newest header features. `HEADER_CPU_DOMAIN_INFO` and
  `HEADER_CLN_SIZE` are in `tools/perf/util/header.h`, before
  `HEADER_LAST_FEATURE`.
- Models take libunwind to be the unwinder. `unwind__prepare_access()` is an
  empty stub without `HAVE_LIBUNWIND_SUPPORT`; `unwind__get_entries()` in
  `tools/perf/util/unwind.c` tries libdw first when both are built in and
  `symbol_conf.unwind_style` is unset.
- Models list the record types and tool callbacks of an older tree. This tree
  has `PERF_RECORD_BPF_METADATA`, `PERF_RECORD_SCHEDSTAT_CPU`,
  `PERF_RECORD_SCHEDSTAT_DOMAIN` and `PERF_RECORD_CALLCHAIN_DEFERRED`, each
  with a member in `struct perf_tool`, and `PERF_RECORD_COMPRESSED2`, which
  goes to `tool->compressed`.
- Models take `compressed` in `struct perf_tool` to have the signature of the
  other session callbacks. It is an `event_op4`, which also takes a file
  offset and a path (`tools/perf/util/tool.h`).
- Models take libunwind, libperl, GTK2 and libbfd to be built in when
  detected. Each is opt-in in `tools/perf/Makefile.config`: `LIBUNWIND=1`,
  `LIBPERL`, `GTK2`, `BUILD_NONDISTRO`.
- Models list a libbabeltrace feature test. There is none in
  `tools/build/Makefile.feature`; the CTF test is `babeltrace2-ctf-writer`,
  in `FEATURE_TESTS_EXTRA`.
