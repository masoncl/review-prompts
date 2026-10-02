# System Calls

## Main structures

### Objects and how they relate

- There is no syscall_enter_from_user_mode() in this tree;
  `syscall_enter_from_user_mode_randomize_stack()` (a macro) and
  `syscall_enter_from_user_mode_work()` in `include/linux/entry-common.h` do
  that job.
- `syscall_enter_from_user_mode_work()`: returns `bool` (run the syscall or
  skip it) and hands back the possibly changed number through its `long *`
  argument; `syscall_enter_from_user_mode_randomize_stack()` yields that same
  value, not the number.
- Generic syscall entry and exit work: inline in
  `include/linux/entry-common.h` (`syscall_trace_enter()`,
  `syscall_exit_work()`, `syscall_exit_to_user_mode()`), not in
  `kernel/entry/common.c`.
- `kernel/entry/common.c`: holds `exit_to_user_mode_loop()` and the
  `irqentry_enter()` family, and no syscall code;
  `kernel/entry/syscall-common.c` holds only the out-of-line tracepoint and
  audit helpers.
- `enter_from_user_mode()` and `exit_to_user_mode()`: shared with interrupt
  entry, defined in `include/linux/irq-entry-common.h`.
- x86 dispatch: a generated `switch`, not a table lookup; see
  `x64_sys_call()`, `x32_sys_call()` in `arch/x86/entry/syscall_64.c` and
  `ia32_sys_call()` in `arch/x86/entry/syscall_32.c`.
- `sys_call_table` in `arch/x86/entry/syscall_64.c`: holds native 64-bit
  stubs only and is read only by `arch_syscall_addr()` in
  `kernel/trace/trace_syscalls.c`; x86-64 has no table array for x32 or ia32.
- arm64 dispatch: indexes `sys_call_table` and `compat_sys_call_table` in
  `invoke_syscall()`, `arch/arm64/kernel/syscall.c`.
- `SYSCALL_WORK_*` and the `syscall_work` word: exist only under
  `CONFIG_GENERIC_ENTRY`; otherwise `set_syscall_work()` and its siblings in
  `include/linux/thread_info.h` act on `TIF_*` bits in `flags`.
- arm64: selects `CONFIG_GENERIC_IRQ_ENTRY` but not `CONFIG_GENERIC_ENTRY`, so
  its syscall path is its own (`el0_svc_common()`, tested against
  `_TIF_SYSCALL_WORK`).
- `syscall_trace_enter()`: the generic inline and unrelated per-architecture
  functions share the name. The generic inline returns true to run the
  syscall and false to skip it; the arm64 one in
  `arch/arm64/kernel/ptrace.c`, for example, returns the syscall number or
  `NO_SYSCALL`.
- Entry hooks: `ptrace_report_syscall_permit_entry()`,
  `seccomp_permit_syscall()` and `__seccomp_permit_syscall()` return `bool`,
  true meaning "run the syscall"; there is no ptrace_report_syscall_entry() or
  __secure_computing() in this tree.
- `SYSCALL_WORK_SYSCALL_RSEQ_SLICE`: an entry work bit that is not a tracer
  hook; set in `kernel/rseq.c`, handled by `rseq_syscall_enter_work()` after
  syscall user dispatch and before ptrace.
- `struct restart_block`: used as `current->restart_block`, a member of
  `struct task_struct`; the member of that name left in csky's
  `struct thread_info` is read by no code.
- `SYSCALL_DEFINEx()` layers on x86: the stub prefixed `__x64_` or `__ia32_`
  takes `const struct pt_regs *`, `__se_sys##name` takes each argument as
  `long` or `long long` and casts it to the declared type, `__do_sys##name`
  is the body; see `arch/x86/include/asm/syscall_wrapper.h`.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| Compat definition macros | `include/linux/compat.h` | `COMPAT_SYSCALL_DEFINEx()` is not in `include/linux/syscalls.h` |
| Entry point that is compat only when `CONFIG_COMPAT` | `include/linux/syscalls.h` | `SYSCALL32_DEFINE0()` to `SYSCALL32_DEFINE6()`; for example `fanotify_mark` in `fs/notify/fanotify/fanotify_user.c` |
| Table shared by several architectures | `scripts/syscall.tbl` | default `syscalltbl` in `scripts/Makefile.asm-headers`; used by each arch that has `arch/<arch>/kernel/Makefile.syscalls`, arm64 through the link `arch/arm64/tools/syscall_64.tbl` |
| ABI tags an arch selects from the shared table | `arch/<arch>/kernel/Makefile.syscalls` | sets only `syscall_abis_32`, `syscall_abis_64`, `syscalltbl`; holds no rules; absent on the arches that run the scripts from their own table `Makefile` |
| Older generic list | `include/uapi/asm-generic/unistd.h` | no `#include` of it outside `tools/`; a call added only here reaches no kernel table |
| Documentation | `Documentation/process/adding-syscalls.rst` | its first generic section still says to edit `include/uapi/asm-generic/unistd.h`; the "Since 6.11" section names `scripts/syscall.tbl` instead |
| Tables of one architecture | `arch/<arch>/kernel/syscalls/`, `arch/x86/entry/syscalls/`, `arch/arm/tools/`, `arch/arm64/tools/` | all but arm64 have a `Makefile` beside the table that runs the scripts, run from `archheaders` in `arch/<arch>/Makefile` (arm: table and count from `archprepare`); `arch/arm64/tools/Makefile` has no rule for the tables, `scripts/Makefile.asm-headers` builds them |
| arm64 tables | `arch/arm64/tools/syscall_32.tbl`, `arch/arm64/tools/syscall_64.tbl` | `syscall_64.tbl` is a symbolic link to `scripts/syscall.tbl`, so searches skip it; compat needs its own row in `syscall_32.tbl` |
| Table to headers | `scripts/syscallhdr.sh`, `scripts/syscalltbl.sh` | run by every per-arch table `Makefile`, s390 included, and by `scripts/Makefile.asm-headers` |
| Table to count of calls, arm and mips | `arch/arm/tools/syscallnr.sh`, `arch/mips/kernel/syscalls/syscallnr.sh` | `scripts/syscallnr.sh` exists but no Makefile names it |
| Size-supplied struct copy | `include/linux/uaccess.h` | besides `copy_struct_from_user()`: `copy_struct_to_user()`, `copy_struct_from_bounce_buffer()`, `copy_struct_to_bounce_buffer()` |
| Same copy through a `sockptr_t` | `include/linux/sockptr.h` | `copy_struct_from_sockptr()`, `copy_struct_to_sockptr()`; a kernel pointer takes the bounce-buffer form |

## Defining an entry point

**Definition macro expansion**

- `SYSCALL_METADATA()`: emitted by `SYSCALL_DEFINEx()`, before and outside
  `__SYSCALL_DEFINEx()`.
- `sys##name`: declared with
  `__attribute__((alias(__stringify(__se_sys##name))))`; there is no SyS_
  symbol here, and `__SYSCALL_DEFINEx()` does not use `SYSCALL_ALIAS()` from
  `include/linux/linkage.h`.
- `sys##name` and `__se_sys##name`: one function under two symbols that differ
  only in declared parameter types, so the body in `__do_sys##name` sits
  behind one wrapper, not two.
- `ALLOW_ERROR_INJECTION(sys##name, ERRNO)`: always part of the expansion;
  expands to nothing without `CONFIG_FUNCTION_ERROR_INJECTION`.
- `__PROTECT()`: expands to `asmlinkage_protect()`, which is
  `do { } while (0)` from `include/linux/linkage.h` unless the architecture
  defines it; only `arch/m68k/include/asm/linkage.h` does.

**Architecture wrappers**

- x32 entry of a compat definition: __x64_compat_sys_foo;
  `__X32_COMPAT_SYS_STUBx()` passes `x64` to `__SYS_STUBx()`.
- __x32_ prefix: emitted by no code; it appears only in
  `Documentation/process/adding-syscalls.rst` and its translations.
- x86 `.tbl` files: hold unprefixed names (sys_foo, compat_sys_foo);
  `__SYSCALL()` in `arch/x86/entry/syscall_64.c` and
  `arch/x86/entry/syscall_32.c` pastes `__x64_` or `__ia32_` in front.
- s390: only the `__s390x_` prefix exists;
  `arch/s390/include/asm/syscall_wrapper.h` defines no compat macros and
  `__S390_SYS_STUBx()` is empty.
- powerpc: the entry symbol is sys_foo with no prefix, taking
  `const struct pt_regs *`; see `__SYSCALL_DEFINEx()` in
  `arch/powerpc/include/asm/syscall_wrapper.h`.
- powerpc selects `ARCH_HAS_SYSCALL_WRAPPER` only `if !SPU_BASE && !COMPAT`;
  otherwise it uses the generic macros and sys_foo takes the C arguments.
- x86, arm64, riscv, s390: no symbol named sys_foo is emitted; `__se_sys##name`
  and `__do_sys##name` are `static`.
- Generic prototypes: compiled out under the wrapper; the sys_ block in
  `include/linux/syscalls.h` and the compat_sys_ block in
  `include/linux/compat.h` are both inside
  `#ifndef CONFIG_ARCH_HAS_SYSCALL_WRAPPER`.
- Argument type: `const struct pt_regs *` on x86, arm64, riscv and powerpc;
  `struct pt_regs *` without `const` on s390.
- `COND_SYSCALL()`: there is no SYS_NI macro here; the x86, arm64, riscv and
  powerpc overrides emit a `__weak` function under the entry name that
  returns `sys_ni_syscall()`; s390 applies `cond_syscall()` to the prefixed
  name.

**Argument count and types**

- `__SC_TEST()`: is
  `(void)BUILD_BUG_ON_ZERO(!__TYPE_IS_LL(t) && sizeof(t) > sizeof(long))`;
  it has no `CONFIG_COMPAT` term.
- `long long` and `unsigned long long`: pass `__SC_TEST()` on every
  architecture; it refuses only a type wider than `long` that is neither.
- `__SC_LONG()`: chooses `long long` by `__TYPE_IS_LL(t)`, which is type
  identity through `__same_type()`, not by `sizeof(t)`.
- Struct or union by value: fails to compile at `(__force t)0` in
  `__TYPE_AS()`, whatever its size; the size comparison in `__SC_TEST()` is
  not what rejects it.

**Calls from kernel code**

- Where stated: `Documentation/process/adding-syscalls.rst`, section "Do not
  call System Calls in the Kernel"; two comments in
  `include/linux/syscalls.h` (above the sys_ prototypes, above the `ksys_`
  block); one comment in `include/linux/compat.h` above the compat_sys_
  prototypes.
- `ksys_` helpers: the documentation does not restrict them to legacy or
  early-boot users; it names a helper as the way to share the work between
  the syscall, its compat variant and other kernel code.
- **Potentially unsafe usage**: calling a sys_ or compat_sys_ entry point
  that a definition macro emits from kernel code.
  - Unsafe: by the plain sys_ or compat_sys_ name with C arguments, from code
    that is built on an architecture selecting `ARCH_HAS_SYSCALL_WRAPPER`,
    which includes generic code outside `arch/`; the generic prototypes are
    compiled out and the entry takes a register frame.
  - Safe: from `arch/` code of an architecture that does not select
    `ARCH_HAS_SYSCALL_WRAPPER`, passing on the arguments userspace gave, as
    `parisc_madvise()` does with `sys_madvise()`; the prototypes under
    `#ifndef CONFIG_ARCH_HAS_SYSCALL_WRAPPER` and the exception for `arch/` in
    `Documentation/process/adding-syscalls.rst` define this.
  - Safe: from `arch/` code that calls the prefixed entry with a
    `struct pt_regs` of the user task, as `__emulate_vsyscall()` does with
    `__x64_sys_gettimeofday()`; `arch/x86/include/asm/syscall_wrapper.h`
    declares `__x64_sys_getcpu()`, `__x64_sys_gettimeofday()` and
    `__x64_sys_time()` for it.
- **Unsafe usage**: passing a kernel buffer to a `__user` parameter of a
  `ksys_` helper; `ksys_read()` reaches `vfs_read()`, which tests the buffer
  with `access_ok()` and returns `-EFAULT` when that fails.
  - Safe: `kernel_read()` in `fs/read_write.c`, which takes `void *` and
    builds a kvec iterator in `__kernel_read()`.
- do_mkdirat() and do_unlinkat(): not in this tree; `filename_mkdirat()` and
  `filename_unlinkat()` in `fs/namei.c` do that, declared in `fs/internal.h`
  only.
- `ksys_lseek()`: `static` in `fs/read_write.c`, not callable from elsewhere.
- ksys_dup(): not in this tree.
- `ksys_truncate()`: defined out of line in `fs/open.c`; the static inline
  helpers are in `include/linux/syscalls.h` after the comment "just wrappers
  to fs-internal functions".
- `init_mount()` and the other helpers in `include/linux/init_syscalls.h`:
  take kernel pointers and are `__init`, so only boot-time code can call them.

## Numbers and tables

**Shared table and ABI tags**

- Tags in `scripts/syscall.tbl`: `common`, `32`, `64`, `time32`, `stat64`,
  `renameat`, `rlimit`, `memfd_secret`, and the architecture tags `arc`, `csky`,
  `nios2`, `or1k`, `riscv`.
- newstat: no such tag here; `newfstatat` (79) and `fstat` (80) are tagged `64`.
- `nospu`, `spu`, `x32`, `i386`, `oabi`, `eabi`, `n32`, `n64`, `o32`: tags of
  the powerpc, x86, arm and mips tables, not of the shared one.
- `hexagon`: requested in `arch/hexagon/kernel/Makefile.syscalls`, but no line
  carries it.
- Where an architecture chooses: `arch/<arch>/kernel/Makefile.syscalls`, which
  `scripts/Makefile.asm-headers` includes; it appends to `syscall_abis_32` and
  `syscall_abis_64`. There is no `arch/<arch>/kernel/syscalls/Makefile` on
  these architectures.
- 32 or 64 list: picked by the stem of each header named in `syscall-y` in
  `arch/<arch>/include/asm/Kbuild` and `arch/<arch>/include/uapi/asm/Kbuild`.
- Users of the shared table: the architectures that have
  `arch/*/kernel/Makefile.syscalls` (eight files).
- Lines that share a number (244 under `arc`, `csky`, `nios2`, `or1k`):
  selecting two tags that hold the same number makes `scripts/syscalltbl.sh`
  fail with "not sorted or duplicates the same syscall number".
- arm64: `arch/arm64/kernel/Makefile.syscalls` sets `syscalltbl` to
  `arch/arm64/tools/syscall_%.tbl`. `arch/arm64/tools/syscall_32.tbl` is its
  own compat table. `arch/arm64/tools/syscall_64.tbl` reads line for line as
  `scripts/syscall.tbl`; file searches over `arch/` do not list it.
- Own tables: `arch/<arch>/kernel/syscalls/` (alpha, m68k, microblaze, mips,
  parisc, powerpc, s390, sh, sparc, xtensa), `arch/x86/entry/syscalls/`, and
  `arch/arm/tools/` for arm.

**Number allocation**

- From 424 on, a call has the same number in every table except alpha, where
  it is that number plus 110.
- Last three calls in every table: 470 `listns`, 471 `rseq_slice_yield`,
  472 `fchroot` (alpha 580, 581, 582). Next free: 473 (alpha 583).

| Table | Last common line | Userspace passes |
|---|---|---|
| `scripts/syscall.tbl` | 472 | the table number |
| `arch/alpha/kernel/syscalls/syscall.tbl` | 582 | the table number |
| `arch/mips/kernel/syscalls/syscall_n64.tbl` | 472 | `__NR_Linux` + 472 |
| `arch/x86/entry/syscalls/syscall_64.tbl` | 472 | 472; x32 adds `__X32_SYSCALL_BIT` |

- `__NR_Linux`: 4000 for o32, 5000 for n64, 6000 for n32, in
  `arch/mips/include/uapi/asm/unistd.h`.
- `arch/x86/entry/syscalls/syscall_64.tbl`: the file's last entry is 547 `x32`;
  a new call goes after the last `common` line, as the comment above 424 says.

**Closed number ranges**

| File | Range | Reason the comment gives |
|---|---|---|
| `scripts/syscall.tbl` | 244–259 | architectures may provide up to 16 calls of their own |
| `scripts/syscall.tbl` | 295–402 | "unassigned to sync up with generic numbers" |
| `arch/x86/entry/syscalls/syscall_64.tbl` | 387–423 | none given |
| `arch/x86/entry/syscalls/syscall_64.tbl` | 512–547 | "historical design error": x32 numbering differs from native |

- 337–386 in `arch/x86/entry/syscalls/syscall_64.tbl`: no line and no comment;
  the 387–423 comment does not cover them.
- 548 and above in `arch/x86/entry/syscalls/syscall_64.tbl`: the comment after
  547 says they "are not to be used for x32-specific syscalls"; the comment
  before 512 says they are available for non-x32 use.

**asm-generic unistd header**

- `include/uapi/asm-generic/unistd.h`: hand-written and current; it holds
  `__NR_fchroot` 472 and `__NR_syscalls` 473, matching `scripts/syscall.tbl`.
- Nothing in the build compares the header with `scripts/syscall.tbl`; outside
  `tools/` and `Documentation/` nothing includes it and only comments name its
  path.
- `tools/include/uapi/README`: speaks of kernel headers in general and names
  neither this header nor the tables; it says not to touch the copies when
  changing the originals.
- `tools/perf/check-headers.sh`: this is what names
  `include/uapi/asm-generic/unistd.h`, `scripts/syscall.tbl` and the per-arch
  tables; a difference only prints a warning.
- Copies under `tools/` may lag: for example
  `tools/perf/arch/parisc/entry/syscalls/syscall.tbl` ends at 462 `mseal`
  while `arch/parisc/kernel/syscalls/syscall.tbl` ends at 472.

**Count of system calls**

- `scripts/syscallhdr.sh` with `--emit-nr`: writes the number on the last
  selected line plus one; it neither sorts nor takes a maximum.
- Order is enforced elsewhere: `scripts/syscalltbl.sh` fails the build on a
  table that is out of order.
- `scripts/Makefile.asm-headers`: sets `syshdr-args := --emit-nr`, so every
  user of the shared table gets a generated `__NR_syscalls`.
- mips: passes no `--emit-nr`; `arch/mips/kernel/syscalls/syscallnr.sh` writes
  `__NR_64_Linux_syscalls`, `__NR_N32_Linux_syscalls` and
  `__NR_O32_Linux_syscalls`, and `NR_syscalls` in
  `arch/mips/include/asm/unistd.h` adds the base.

**Stubs for absent calls**

- Generic `COND_SYSCALL()`: defined in `kernel/sys_ni.c` as
  `cond_syscall(sys_##name)`; `cond_syscall()` in `include/linux/linkage.h` is
  an assembler weak alias to `sys_ni_syscall()`, with no function body.
- Wrapper architectures (`CONFIG_ARCH_HAS_SYSCALL_WRAPPER`): x86, arm64, riscv,
  s390, and powerpc only `if !SPU_BASE && !COMPAT`.
- What the wrapper's macro must provide: a symbol under the exact name the
  architecture's table macro builds, once for each ABI built in.

| Architecture | Symbol from `COND_SYSCALL(name)` | Kind |
|---|---|---|
| x86 | __x64_sys_name, __ia32_sys_name | `__weak` function, `const struct pt_regs *` |
| arm64 | __arm64_sys_name | `__weak` function, `const struct pt_regs *` |
| riscv | __riscv_sys_name | `__weak` function, `const struct pt_regs *` |
| powerpc | sys_name (no prefix) | `__weak` function, `const struct pt_regs *` |
| s390 | __s390x_sys_name | alias through `cond_syscall()` |

- `__COND_SYSCALL()`: exists on x86 only, in
  `arch/x86/include/asm/syscall_wrapper.h`.
- `COND_SYSCALL_COMPAT()`: x86 defines it only under `CONFIG_COMPAT`; s390 and
  powerpc define none, so the generic alias of compat_sys_name is used there.
- A call listed in every table but defined by some architectures only needs
  the line: `map_shadow_stack` is defined under `arch/x86`, `arch/arm64` and
  `arch/riscv`, and `COND_SYSCALL(map_shadow_stack)` lets the others link.
- No line needed: where the table entry names `sys_ni_syscall` itself, as
  powerpc does for `map_shadow_stack`.
- A number with no selected line: `scripts/syscalltbl.sh` fills it with
  `sys_ni_syscall`; on x86 the `default:` case of `x64_sys_call()` and
  `ia32_sys_call()` returns `-ENOSYS`.

**The adding-syscalls document**

| Subject in the document | Document | Tree |
|---|---|---|
| x86 numbers | examples differ (333 and 380) | same number in both tables (472 for `fchroot`) |
| x86 compat column | name with the `__ia32_compat_sys_` prefix | plain `compat_sys_` name |
| x32 line | for a pointer-to-pointer argument, the `syscall_64.tbl` entry split into a `333 64` row plus a `555 x32` row naming an __x32_compat_sys_ function | no such prefix; no `x32` line above 547 |
| Returning elsewhere | stub_ and stub32_ entry points in assembly | none under `arch/x86/entry/` |
| um mapping | a stub_ define in `arch/x86/um/sys_call_table_64.c` | file has no stub_ define |

- New x32-specific line: ruled out by the comments in
  `arch/x86/entry/syscalls/syscall_64.tbl`; 512–547 is closed and 548 and above
  "are not to be used for x32-specific syscalls". A new call gets one `common`
  line.
- `execve`, `clone`, `rt_sigreturn`: the tables name `sys_execve`, `sys_clone`
  and `sys_rt_sigreturn` directly.
- `noreturn`: an optional sixth column that the document does not describe,
  used by `exit` and `exit_group`, with `-` as the placeholder in the compat
  column.

**Adding a call**

- Tables: 470 `listns`, 471 `rseq_slice_yield` and 472 `fchroot` each have a
  line in `scripts/syscall.tbl` and in all 16 table files under `arch/`; none
  of those is fed from another. `arch/arm64/tools/syscall_64.tbl` is not a
  17th; it reads as `scripts/syscall.tbl`.
- ABI word on the new line differs per table: `common` in most, `i386` in
  `arch/x86/entry/syscalls/syscall_32.tbl`, `n32`, `n64` and `o32` in the mips
  tables; powerpc uses `common` or `nospu` (`rseq_slice_yield` is `nospu`).
- Calls needing architecture support still take a number in every table:
  `map_shadow_stack` has a line at 453 (563 on alpha) in every table; 447
  (557 on alpha) `memfd_secret` is a line or a "reserved" comment everywhere.
- One table only: `uretprobe` 335 and `uprobe` 336, in
  `arch/x86/entry/syscalls/syscall_64.tbl` alone, below the common sequence.
- Option and stub, calls 463–472: none has an option of its own, and nine of
  the ten have no line in `kernel/sys_ni.c`, because their files are always
  built.
- `rseq_slice_yield`: defined inside `#ifdef CONFIG_RSEQ_SLICE_EXTENSION` in
  `kernel/rseq.c`, an option for the feature, with
  `COND_SYSCALL(rseq_slice_yield)`.
- `mseal`: no option; `mm/Makefile` builds `mm/mseal.c` only with
  `CONFIG_64BIT` and `CONFIG_MMU`, so it has `COND_SYSCALL(mseal)`.
- `Documentation/process/adding-syscalls.rst` says a new call should normally
  have its own option and lists wiring up one particular architecture, usually
  x86, as a separate commit; calls 463–472 are in every table, and only
  `rseq_slice_yield` sits under an option.

## Arguments and structures

**Unknown flag bits**

- Newest calls in this tree that show the zero-flags form: the `fchroot` entry
  point in `fs/open.c` and the `listns` entry point in `kernel/nstree.c`; both
  open with `if (flags) return -EINVAL;`.
- `mseal` in `mm/mseal.c`: tests `flags` before anything else.
- `cachestat` in `mm/filemap.c`: tests `flags` only after the fd lookup, the
  `copy_from_user()` of the range, `is_file_hugepages()` and
  `can_do_cachestat()`, so `-EBADF`, `-EFAULT`, `-EOPNOTSUPP` or `-EPERM` can
  be returned for a call that also has an unknown flag.
- `openat2`: `build_open_flags()` in `fs/open.c` tests `how->flags` against
  `VALID_OPENAT2_FLAGS`, not `VALID_OPEN_FLAGS`; both are in
  `include/linux/fcntl.h`.
- `VALID_OPENAT2_FLAGS`: adds `OPENAT2_REGULAR`, which is bit 32, so a
  `how->flags` value that does not fit an `int` can pass.
- `build_open_flags()`: has no separate test that `how->flags` fits an `int`;
  it swaps `OPENAT2_REGULAR` for the internal `__O_REGULAR` before it assigns
  `op->open_flag`.

**Extensible structure arguments**

- `copy_struct_from_user()` first test: `WARN_ON_ONCE(ksize >
  __builtin_object_size(dst, 1))` returns `-E2BIG` before any user access.
- `usize` below the first published size, including 0, when the caller makes
  no minimum check: the helper zero-fills `dst` from `usize` on, copies
  `usize` bytes and returns 0, so the caller sees a valid structure of
  defaults.
- `build_open_how()` in `fs/open.c`: reads no user memory; it builds a
  `struct open_how` from `int` flags and a mode, as `do_sys_open()` does for
  `open` and `openat`. The `openat2` copy and both size checks are in the
  `openat2` entry point.
- Field appended later and selected by a flag, where 0 is a valid value of
  the field: the caller also tests that `usize` covers the field, because
  after the copy a zero that userspace wrote looks the same as a zero the
  helper filled in.
  - `copy_clone_args_from_user()` in `kernel/fork.c`: `CLONE_INTO_CGROUP` with
    `usize < CLONE_ARGS_SIZE_VER2` returns `-EINVAL`.
  - `sched_copy_attr()` in `kernel/sched/syscalls.c`: `SCHED_FLAG_UTIL_CLAMP`
    with `size < SCHED_ATTR_SIZE_VER1` returns `-EINVAL`.

**Structure layout rules**

- `OPEN_HOW_SIZE_VER0` and `OPEN_HOW_SIZE_LATEST`: defined in
  `include/linux/fcntl.h`, which is not a uapi header;
  `include/uapi/linux/openat2.h` defines `struct open_how` but no size
  constant.
- `CLONE_ARGS_SIZE_VER0`, `CLONE_ARGS_SIZE_VER1` and `CLONE_ARGS_SIZE_VER2`:
  defined in `include/uapi/linux/sched.h`, next to `struct clone_args`.

**Adding an argument**

- Models have this right; see the `membarrier` entry point in
  `kernel/sched/membarrier.c`.

**Flag-gated arguments**

- `vrm->new_addr` when `vrm_implies_new_addr()` is false: not left alone;
  `check_prep_vma()` in `mm/mremap.c` overwrites it with `vrm->addr`, and
  `vrm_set_new_addr()` passes 0 as the hint instead of the field.
- **Unsafe usage**: testing or using `vrm->new_addr` in code that runs before
  the overwrite in `check_prep_vma()` and where neither
  `vrm_implies_new_addr()` nor `MREMAP_FIXED` has been tested; the field still
  holds the caller's raw fifth argument, so the test fails callers that never
  set it.
  - Safe: after the `if (!vrm_implies_new_addr(vrm)) return 0;` in
    `check_mremap_params()`, where the range, alignment and `vrm_overlaps()`
    tests sit.
  - Safe: in `remap_move()`, which `do_mremap()` calls only when
    `vrm_move_only()` has seen `MREMAP_FIXED`.
  - Safe: through `vrm_set_new_addr()`, which tests the helper itself.

**Reading arguments from user memory**

- `copy_clone_args_from_user()` in `kernel/fork.c`: copies into a local
  `struct clone_args`, tests that copy, and only then fills
  `struct kernel_clone_args`; the unknown-flag test comes later, in
  `clone3_args_valid()`.
- `sched_copy_attr()` in `kernel/sched/syscalls.c`: never writes `attr->size`
  after the copy; it differs from `perf_copy_attr()` in that.
- **Unsafe usage**: reading a size field with `get_user()`, checking it,
  copying the whole structure, then using the size field of the copy;
  `copy_struct_from_user()` copies from offset 0 of `src`, so it fetches the
  field a second time and the copied value was never checked.
  - Safe: store the checked value over the copied field, as `perf_copy_attr()`
    in `kernel/events/core.c` and `user_reg_get()` in
    `kernel/trace/trace_events_user.c` do.
  - Safe: never read the copied field and keep using the checked local, as
    `sched_copy_attr()` does for its `SCHED_ATTR_SIZE_VER1` test.

## Compat and 64-bit arguments

**Arguments needing a compat entry**

- s390: has no compat support in this tree; `compat_ptr()` has one
  definition, in `include/linux/compat.h`, a widening cast with no masking.
- Pointer argument without a compat entry, x86: the ia32 stub that
  `__IA32_SYS_STUBx()` emits for a native definition reads the 32-bit
  registers through `__SC_COMPAT_CAST()` in
  `arch/x86/include/asm/syscall_wrapper.h`, so the pointer arrives
  zero-extended.
- Pointer argument without a compat entry, arm64: the stub from the native
  `__SYSCALL_DEFINEx()` serves both tables and passes `regs->orig_x0` and
  `regs->regs[1]` to `regs->regs[5]` whole; `kernel_entry` in
  `arch/arm64/kernel/entry.S` zero-extends `x0` only.
- `long`-typed argument on x86: `__SC_COMPAT_CAST()` casts to `int` when
  `__TYPE_IS_L(t)`, so `long`, `off_t` and `ssize_t` are sign-extended in the
  ia32 stub of a native definition; every other type is zero-extended.
- Signed `long`-sized argument elsewhere: needs a compat entry declared with
  a 32-bit signed type where the stub passes registers whole;
  `compat_sys_lseek` in `fs/read_write.c` takes `compat_off_t` for this.
- Pointer to a struct that holds a pointer: needs no separate entry when the
  shared code picks the layout itself; `readv` and `writev` are wired to
  `sys_readv` and `sys_writev` for 32-bit callers and `import_iovec()` in
  `lib/iov_iter.c` tests `in_compat_syscall()`.
- 32-bit time type as the only difference: handled by native
  `SYSCALL_DEFINEx` entries such as `sys_clock_gettime32`, named in the native
  column of the 32-bit tables, not by a compat entry.
- Compat column of a table row: may name a native function, for example
  `sys_ni_syscall` for `vm86` in `arch/x86/entry/syscalls/syscall_32.tbl`; a
  name there does not prove a `COMPAT_SYSCALL_DEFINEx` exists.

**Compat definitions**

- `__SC_DELOUSE`: used by the compat macro only; the native macro uses
  `__SC_CAST`.
- `__SC_DELOUSE` and `compat_ptr()`: one definition each, both in
  `include/linux/compat.h`; no architecture overrides either.
- `__SC_DELOUSE(t, v)`: casts through `unsigned long` to the declared type and
  masks nothing; the macro narrows or sign-extends an argument only if it is
  declared with a 32-bit type such as `compat_long_t` or `compat_off_t`.
- Pointer arguments of a compat definition: declared as `__user` pointers, to
  the compat struct where the layout differs, and used without
  `compat_ptr()`.
- `compat_uptr_t` by value as an argument type: only the `msgsnd`, `msgrcv`,
  `shmat` and `ipc` compat definitions under `ipc/` take it, and they call
  `compat_ptr()` on it.
- Generic `COMPAT_SYSCALL_DEFINEx`: emits `ALLOW_ERROR_INJECTION()`, the
  `__se_compat_sys##name` wrapper and `__SC_TEST`; it leaves out
  `SYSCALL_METADATA()` and `__PROTECT()`.
- x86, arm64 and riscv `COMPAT_SYSCALL_DEFINEx` in their
  `asm/syscall_wrapper.h`: also leave out `__SC_TEST`, which their native
  `__SYSCALL_DEFINEx` keeps.
- `arch_trace_is_compat_syscall()`: makes syscall tracing skip 32-bit calls
  only where `ARCH_TRACE_IGNORE_COMPAT_SYSCALLS` is defined, which x86 (only
  under `CONFIG_IA32_EMULATION`), arm64 and riscv do.
- x86 `in_compat_syscall()` in `arch/x86/include/asm/compat.h`: returns
  `in_32bit_syscall()`, which is `in_ia32_syscall() || in_x32_syscall()`.
- `in_compat_syscall()` on x86: true inside a native handler too when the
  call came by a 32-bit ABI; under `CONFIG_IA32_EMULATION`
  `syscall_32_enter()` in `arch/x86/entry/syscall_32.c` sets `TS_COMPAT` for
  every 32-bit call, and `in_x32_syscall()` tests `__X32_SYSCALL_BIT` in
  `orig_ax`.
- `CONFIG_X86_32`: `in_ia32_syscall()` and `in_32bit_syscall()` are constant
  true while `in_compat_syscall()` is false, since `CONFIG_COMPAT` is off.
- sparc: the second override; `in_compat_syscall()` in
  `arch/sparc/include/asm/compat.h` tests the trap type, while
  `is_compat_task()` there tests `TIF_32BIT`.
- **Unsafe usage**: `is_compat_task()` in shared code to pick the user-memory
  layout of the current call.
  - Unsafe: x86 defines no `is_compat_task()` when `CONFIG_COMPAT` is set, and
    on x86 and sparc the ABI belongs to the call, not the task.
  - Safe: `in_compat_syscall()`, as `import_iovec()` in `lib/iov_iter.c` does.
  - Safe: `is_compat_task()` for a property of the task's address space, as
    `arch_mmap_rnd()` in `mm/util.c` does; that code is built only under
    `CONFIG_ARCH_WANT_DEFAULT_TOPDOWN_MMAP_LAYOUT`, which x86 does not
    select.

**Compat entries in the tables**

- `scripts/syscalltbl.sh`: generates the x86 `syscalls_32.h`, `syscalls_64.h`
  and `syscalls_x32.h` too, run from `arch/x86/entry/syscalls/Makefile`; there
  is no script under `arch/x86/entry/syscalls/`.
- `__SYSCALL_WITH_COMPAT` in `arch/x86/entry/syscall_32.c`: picks the compat
  name under `CONFIG_IA32_EMULATION` and the native name otherwise; `__SYSCALL`
  then pastes `__ia32_` on whichever was picked.
- Compat column `-`: `scripts/syscalltbl.sh` treats it as empty; x86 rows use
  it to reach the sixth column, `noreturn`.
- `arch/arm64/tools/syscall_32.tbl`: every row has abi `common`.
- x32 rows of `arch/x86/entry/syscalls/syscall_64.tbl`: the entry point is in
  the fourth column, whether it is a compat name such as `compat_sys_execve`
  or a native one such as `sys_readv`; no row of that file names an entry in
  the compat column.
- `arch/x86/entry/syscall_64.c`: defines no `__SYSCALL_WITH_COMPAT`, so a
  compat column in `syscall_64.tbl` has nothing to expand it.
- `syscalls_x32.h`: built from the `common` and `x32` rows; `x32_sys_call()`
  pastes `__x64_`, so an x32 row naming `compat_sys_execve` calls
  __x64_compat_sys_execve.
- Rows in `syscall_64.tbl` numbered 329 and above, outside 512-547: all are
  `common`.
- `common` call entered from x32: runs the native x64 stub with
  `in_compat_syscall()` true, so shared code that tests it parses user memory
  in the 32-bit layout.

**64-bit arguments on 32-bit kernels**

- `SC_ARG64(name)` and `SC_VAL64(type, name)`: defined unconditionally in
  `include/linux/syscalls.h`; `SC_ARG64` always expands to two `u32` type/name
  pairs, on 64-bit kernels too.
- `compat_arg_u64_dual(name)`: always two `u32` type/name pairs; defined in
  `include/asm-generic/compat.h` inside `#ifndef compat_arg_u64`, and no
  architecture supplies its own.
- `compat_arg_u64(name)`: the same two halves written as parameter
  declarations, for prototypes; `compat_arg_u64_glue(name)` rebuilds the
  value.
- Half order: `SC_ARG64` tests `__LITTLE_ENDIAN`; `compat_arg_u64_dual()` tests
  `CONFIG_CPU_BIG_ENDIAN`.
- `loff_t` declared in `SYSCALL_DEFINEx` on a 32-bit kernel: arrives whole
  only where the C calling convention is kept; `__SC_LONG` then declares the
  parameter as `long long`.
- x86-32 and PPC32 pt_regs stubs: hand one register to each declared
  argument (`SC_IA32_REGS_TO_ARGS`, `SC_POWERPC_REGS_TO_ARGS`), so a 64-bit
  argument must be declared as two halves, as in `arch/x86/kernel/sys_ia32.c`
  and `arch/powerpc/kernel/sys_ppc32.c`.
- riscv32: `__SYSCALL_SE_DEFINEx` in
  `arch/riscv/include/asm/syscall_wrapper.h` aliases the wrapper to a
  seven-`ulong` function so that wider arguments still follow the C
  convention.
- `CONFIG_ARCH_SPLIT_ARG64`: selected by `X86_32`, PPC32 and 32-bit parisc; its
  only users are the `fanotify_mark` definition in
  `fs/notify/fanotify/fanotify_user.c` and its prototype in
  `include/linux/syscalls.h`.
- `SYSCALL32_DEFINE6(fanotify_mark, ...)`: emits `compat_sys_fanotify_mark`
  under `CONFIG_COMPAT` and the split `sys_fanotify_mark` otherwise; the
  unsplit `SYSCALL_DEFINE5` is compiled only without
  `CONFIG_ARCH_SPLIT_ARG64`.
- Generic users of `compat_arg_u64_dual()`: each is compiled only if the
  architecture defines the matching macro, for example
  `__ARCH_WANT_COMPAT_PREAD64`; riscv defines all eight, powerpc only
  `__ARCH_WANT_COMPAT_FALLOCATE`, arm64 none.
- **Unsafe usage**: `SC_ARG64()` or `compat_arg_u64_dual()` at parameter 2 or
  4 for an ABI that aligns a 64-bit argument to a register pair.
  - Unsafe: the macros add no padding, so both halves are read one register
    before the ones userspace filled.
  - Safe: at parameter 1, 3 or 5, as `compat_sys_fallocate` in `fs/open.c`,
    the one generic entry powerpc opts into; the rule is stated in
    `Documentation/process/adding-syscalls.rst`.
  - Safe: an architecture entry with an explicit pad argument before the
    halves, as `ppc_pread64` in `arch/powerpc/kernel/sys_ppc32.c` and
    `compat_sys_aarch32_pread64` in `arch/arm64/kernel/sys32.c`.

## Model gaps

### Other mistakes models make

- Models name secure_computing() as the seccomp entry hook. It is defined
  nowhere here; `seccomp_permit_syscall()` in `include/linux/seccomp.h` is the
  hook.
- Models know the generic `syscall_trace_enter()` from other trees. In
  `include/linux/entry-common.h` it takes `(regs, work, syscall)`, in that
  order.
- Models know `futex_cmd_has_timeout()` as the only argument gate in the
  `futex` entry point. `FUTEX_ROBUST_UNLOCK` in the `op` word gives `uaddr2` a
  meaning for `FUTEX_WAKE`, `FUTEX_WAKE_BITSET` and `FUTEX_UNLOCK_PI`;
  `do_futex()` returns `-ENOSYS` for the flag with any other command.
- Models know the helpers behind `mkdirat` and `unlinkat` under other names.
  `filename_mkdirat()` and `filename_unlinkat()` in `fs/namei.c` take a
  `struct filename *` and leave dropping it to the caller.
- Models take `ksys_ftruncate()` to take two arguments. It takes a third
  `flags` argument, `FTRUNCATE_LFS` in `include/linux/syscalls.h`.
- Models take `scripts/syscall.tbl` to have a newstat tag. The tag beside `64`
  on numbers 79 and 80 is `stat64`, on `fstatat64` and `fstat64`.
