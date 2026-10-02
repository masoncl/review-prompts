# Libbpf

## Main structures

### Objects and how they relate

- `struct bpf_program`: one per `STT_FUNC` symbol, so `.text` subprograms are
  entries of `obj->programs` too; `prog_is_subprog()` in
  `tools/lib/bpf/libbpf.c` tells them apart.
- Subprogram entries: hidden by `bpf_object__next_program()` and
  `bpf_object__for_each_program()`, skipped by `bpf_object__load_progs()`;
  internal loops over `obj->programs[i]` see them.
- `prog->insns`: a private malloc'd copy per program, made in
  `bpf_object__init_prog()`; there is no instruction array shared by the
  object.
- `obj->maps` and `obj->programs`: arrays of structs, not arrays of pointers;
  inside `bpf_object_open()` `obj->programs` is realloc'd while
  `bpf_object__elf_collect()` runs and `obj->maps` while
  `bpf_object__init_maps()` runs, so element pointers are stable only after
  those steps; `struct reloc_desc` stores `map_idx`, not a pointer.
- `map->inner_map`: a separately allocated `struct bpf_map` template that is
  not in `obj->maps`; `bpf_object__create_map()` destroys it once the outer
  map is created.
- `enum bpf_object_state`: three states, `OBJ_OPEN`, `OBJ_PREPARED`,
  `OBJ_LOADED`; `bpf_object__prepare()` is an exported step between open and
  load.
- `bpf_object_prepare()`: resolves externs, relocates (subprogram code is
  appended here), loads BTF and creates maps; program fds are the only kernel
  objects made by `bpf_object_load()` itself.
- ELF state: `bpf_object__elf_finish()` runs at the end of `bpf_object_open()`,
  so `efile.elf`, `efile.symbols` and `efile.secs` are gone at prepare and load
  time; scalar indexes such as `efile.text_shndx` survive and are still read.
- `enum libbpf_map_type`: the maps libbpf makes from data sections; besides
  data, bss, rodata and kconfig it has `LIBBPF_MAP_PERCPU` for `PERCPU_SEC`,
  a `BPF_MAP_TYPE_PERCPU_ARRAY` that is never mmapable.
- `bpf_map__is_internal()`: false for struct_ops maps and for the arena map;
  both keep `LIBBPF_MAP_UNSPEC`.
- struct_ops map: holds pointers to the `struct bpf_program` of each member;
  `bpf_object_adjust_struct_ops_autoload()` overwrites those programs'
  `autoload` from the maps' `autocreate`.
- `obj->jumptable_maps`: `BPF_MAP_TYPE_INSN_ARRAY` fds made by
  `create_jt_map()` during relocation; owned and closed by the object, with no
  `struct bpf_map` behind them.
- `obj->btf_vmlinux` and `obj->btf_modules`:
  `bpf_object_post_load_cleanup()` frees them at the end of
  `bpf_object_load()`, and they are never loaded when `obj->gen_loader` is set.
- `obj->btf_custom_path`: when set, CO-RE matches against
  `obj->btf_vmlinux_override` instead of vmlinux BTF.
- `struct bpf_gen` (`obj->gen_loader`): BTF load, map creation and program
  load are recorded instead of sent to the kernel; maps and programs are
  referred to by array index, map fds stay placeholders, program fds stay -1.
- `struct bpf_link`: also made from a map, by `bpf_map__attach_struct_ops()`;
  `struct bpf_map_skeleton` has a `link` slot for it.
- Links that reach into the object: `struct bpf_link_usdt` points at the
  object's `struct usdt_manager`, which `bpf_object__close()` frees; a
  struct_ops link without `BPF_F_LINK` borrows `map->fd`. Both detach paths
  use them, so these links have to go before the object.
- `bpf_object__destroy_skeleton()`: the one place libbpf ties links to an
  object; it destroys every link in the skeleton's slots, then closes the
  object.
- Subskeleton: there is no struct bpf_subskeleton; the type is
  `struct bpf_object_subskeleton` in `tools/lib/bpf/libbpf.h`.

## Where to look

**Core files:** Rows only where this tree differs from the usual map; file
names without a directory are under `tools/lib/bpf/`, other paths start at the
tree root.

| Job | File | Easy to miss |
|---|---|---|
| BTF handling, beyond `btf.c` and `btf_dump.c` | `btf_iter.c`, `btf_relocate.c` | Both are also built into the kernel under `CONFIG_BPF_SYSCALL`: `kernel/bpf/btf_iter.c` and `kernel/bpf/btf_relocate.c` `#include` them, as `kernel/bpf/relo_core.c` does `relo_core.c`. Each has a `#ifdef __KERNEL__` block, so a change must build both ways. |
| Probing the running kernel, internal | `features.c` | Holds `feature_probes[]`, the global `feature_cache` and `feat_supported()`. `kernel_supports()` is the per-object wrapper and is defined in `libbpf.c`. |
| `feature_probes[]` entries that are not defined in `features.c` | `bpf.c`, `libbpf.c` | `probe_memcg_account()` is in `bpf.c`; `probe_kern_syscall_wrapper()` is in `libbpf.c`. Both are entries of `feature_probes[]`. |
| Perf buffer | `libbpf.c` | `perf_buffer__new()` is not in `ringbuf.c`; `ringbuf.c` holds `ring_buffer__new()` and `user_ring_buffer__new()`. |
| Public headers | `SRC_HDRS` and `GEN_HDRS` in `Makefile` | That is the installed set. It includes `skel_internal.h` despite the name. `bpf_helper_defs.h` is not a file in the tree; `Makefile` generates it with `scripts/bpf_doc.py`. |
| Error strings | `libbpf_utils.c` | There is no str_error.c, str_error.h or libbpf_errno.c here. `libbpf_strerror()` and `libbpf_errstr()` are in `libbpf_utils.c`; `errstr()` is a macro in `libbpf_internal.h`. |

## Error reporting

**Error convention**

- Failure value of an `int` function is not always negative: `btf__align_of()`
  in `tools/lib/bpf/btf.c` returns `0` on failure, with `errno` set.
- `bpf_map__fd()` in `tools/lib/bpf/libbpf.c`: returns `-1` and does not write
  `errno` when the map is not created yet; for a `NULL` map it returns
  `libbpf_err(-EINVAL)`.
- The helpers are not the only accepted form. Public functions also use:
  - the comma form, `return errno = EINVAL, NULL;`, as in `btf__type_by_id()`;
  - returning `-errno` directly, right after a failing libc call or public
    libbpf call that already set `errno`, as in `bpf_link__unpin()` and
    `bpf_link__detach()`.
- `errno` can hold a libbpf code, not only a system one: `enum libbpf_errno` in
  `tools/lib/bpf/libbpf.h` starts at `__LIBBPF_ERRNO__START` (4000), and
  `bpf_object_load()` returns `libbpf_err(-LIBBPF_ERRNO__ENDIAN)`.
- Kerneldoc in `tools/lib/bpf/btf.h` for `btf__new()` and the functions next
  to it still says an error-encoded pointer is returned; the code returns
  `NULL` through `libbpf_ptr()`.

**The error helpers**

- The set is exactly four `static inline` functions: `libbpf_err()`,
  `libbpf_err_errno()`, `libbpf_err_ptr()`, `libbpf_ptr()`.
- None of them tests any mode; the comment above `libbpf_err_errno()` that
  mentions strict mode settings does not match its body.
- Inputs a helper does not expect:

| Helper | Given | Result |
|---|---|---|
| `libbpf_err()` | raw `-1` from a syscall or libc call | `errno` becomes 1; returns `-1` |
| `libbpf_err_errno()` | any negative value, including a real `-Exxx` | value discarded; returns `-errno`; never writes `errno` |
| `libbpf_err_ptr()` | 0 or a positive value | `errno` becomes 0 or negative; still returns `NULL` |
| `libbpf_ptr()` | plain `NULL` | returns `NULL`; `errno` untouched |

**Using the error helpers**

- `pr_warn()`, `pr_info()`, `pr_debug()`: do not change `errno`;
  `libbpf_print()` in `tools/lib/bpf/libbpf.c` saves it before the print
  callback and restores it after.
- `free()` is treated as leaving `errno` alone: `bpf_prog_load()` in
  `tools/lib/bpf/bpf.c` calls `free()` and then `libbpf_err_errno(fd)` without
  saving `errno`.
- Save-first, `err = -errno;` before the cleanup call and the code handed on
  after it: see `bpf_link__pin()` and `btf_parse_raw_mmap()`.
- Internal `int` function ending in `libbpf_err()` or `libbpf_err_errno()`:
  it still returns a negative code (`libbpf_err()` returns its argument,
  `libbpf_err_errno()` returns `-errno`), so internal callers are not affected.
  `btf_load_into_kernel()` ends in `libbpf_err()` and is called both by
  `btf__load_into_kernel()` and by internal
  `bpf_object__sanitize_and_load_btf()`.
- `bpf_object_load()` (static) ends in `libbpf_err()`; its only caller is
  `bpf_object__load()`.
- **Potentially unsafe usage**: ending an internal pointer-returning function
  in `libbpf_err_ptr()` or `libbpf_ptr()`.
  - Unsafe: when an internal caller tests the result with `IS_ERR()`; the
    result is `NULL` on failure and `IS_ERR()` is false for it.
  - Safe: when every internal caller that tests the result uses
    `libbpf_get_error()` or a `NULL` test, as `libbpf_find_prog_btf_id()` does
    for `btf_load_from_kernel()` and `bpf_program__attach_usdt()` does for
    `usdt_manager_attach_usdt()`; `libbpf_get_error()` accepts both a `NULL`
    and an `ERR_PTR()` value.
- **Unsafe usage**: `libbpf_ptr()` around a callee that can return plain
  `NULL` on failure; `NULL` is returned with whatever `errno` held before.
  - Safe: the callee returns `ERR_PTR()` on every failure path, as `btf_new()`,
    `btf_parse_elf()` and `bpf_object_open()` do.
  - Safe: for a `NULL`-returning callee, read `-errno` and use
    `libbpf_err_ptr()` or `ERR_PTR()`; `btf_parse_elf()` does this after
    `btf_ext__new()`.
- **Unsafe usage**: `libbpf_err()` on a raw `-1` from a syscall or libc call;
  `errno` becomes 1.
  - Safe: `libbpf_err_errno(ret)`, as `bpf_map_update_elem()` does.
  - Safe: `libbpf_err(-errno)`, as `ring_buffer__poll()` does after
    `epoll_wait()`.
- **Potentially unsafe usage**: a call between the failing call and the read
  of `errno` (`libbpf_err_errno()`, `-errno`, or `libbpf_get_error()` on
  `NULL`).
  - Unsafe: when the call in between can set `errno`, such as `close()`, and
    `errno` is not saved before it and restored after it.
  - Safe: save and restore around it, as `ensure_good_fd()` in
    `tools/lib/bpf/libbpf_internal.h` does around `close()`.
  - Safe: plain stores such as `OPTS_SET()`, as in `bpf_prog_query_opts()`.
  - Safe: a helper that takes the code (`libbpf_err()`, `libbpf_err_ptr()`,
    `libbpf_ptr()`) applied after the cleanup; `btf_load_from_kernel()` calls
    `close()` and then `libbpf_ptr(btf)`.

**Low-level syscall wrappers**

- `bpf_map_create()` and `bpf_prog_load()` end in `libbpf_err_errno(fd)`;
  neither has a `close()` path nor captures `-errno`. `bpf_link_create()` is
  the wrapper that captures `err = -errno` and returns `libbpf_err(err)`.
- `sys_bpf_ext()` and `sys_bpf_ext_fd()` in `tools/lib/bpf/bpf.c`: a second raw
  entry to the system call, with the same raw `-1` and `errno` result; they
  pass a `struct bpf_common_attr` and its size as a fourth and fifth argument,
  so not every wrapper issues the three-argument call through `sys_bpf()`.
  `bpf_map_create()` uses `sys_bpf_ext_fd()` when `log_opts` is set and
  `feat_supported(NULL, FEAT_BPF_SYSCALL_COMMON_ATTRS)` is true; otherwise it
  uses `sys_bpf_fd()`.
- `bpf_prog_load()` writes `errno = E2BIG` by hand when
  `alloc_zero_tailing_info()` fails, so the final `libbpf_err_errno(fd)`
  reports `-E2BIG`.
- `sys_bpf()`, `sys_bpf_fd()` and `sys_bpf_prog_load()` return `-1`, not
  `-errno`. `sys_bpf_prog_load()` is not static and is called from
  `tools/lib/bpf/features.c`; a caller that wants the code must read `errno`.
- `sys_bpf_prog_load()`: retries while `fd < 0 && errno == EAGAIN`, bounded by
  its `attempts` argument; `bpf_prog_load()` passes `PROG_LOAD_ATTEMPTS` when
  the option is 0.
- `libbpf_err_errno()` on an already converted value: `bpf_prog_query()`
  applies it to the result of `bpf_prog_query_opts()`; the result is the same
  because only plain stores run in between.

## Objects and descriptors

**The phases of an object**

- Phase record: `obj->state` (`enum bpf_object_state` in
  `tools/lib/bpf/libbpf.c`) is the only one; there is no bpf_object__loaded()
  and no loaded field in `struct bpf_object`.
- `map_is_created()`: returns `map->obj->state >= OBJ_PREPARED || map->reused`;
  it does not read `map->fd`.
- `map->fd` in `OBJ_OPEN`: already an open descriptor, a memfd from
  `create_placeholder_fd()` in `bpf_object__add_map()`; `bpf_map__fd()` returns
  -1 until `map_is_created()` is true.
- `bpf_object_prepare()` order: `bpf_object__relocate()` runs before
  `bpf_object__sanitize_and_load_btf()` and `bpf_object__create_maps()`;
  relocation uses the placeholder fd numbers, and `reuse_fd()` puts the created
  map on the same number.
- Failed `bpf_object_prepare()` or `bpf_object_load()`, once past the state
  test and the endianness test at entry: leaves `obj->state` at `OBJ_LOADED`,
  not `OBJ_OPEN`, with every `map->fd` and `prog->fd` at -1. `OBJ_LOADED`
  therefore means "may not be loaded again", not "is loaded": a later
  `bpf_object__load()` returns `-EINVAL` from the state test in
  `bpf_object_load()`.
- `bpf_object__prepare()` on a prepared or loaded object: `-EINVAL`.
- Setter tests and error codes (search `map_is_created(` and `>= OBJ_LOADED`
  for the members):

| Test | Rejected from | Error | Exceptions |
|---|---|---|---|
| `map_is_created()` | `OBJ_PREPARED`, or earlier if `map->reused` | `-EBUSY` | `bpf_map__set_exclusive_program()`: `-EINVAL` |
| `obj->state >= OBJ_LOADED` | `OBJ_LOADED` | `-EBUSY` | `bpf_program__set_autoload()`, `bpf_program__set_attach_target()`, `bpf_object__set_kversion()`: `-EINVAL` |

- `bpf_map__set_inner_map_fd()`: does not call `map_is_created()`; it returns
  `-EINVAL` for a map that is not map-in-map and when
  `map->inner_map_fd != -1`.
- `bpf_map__reuse_fd()`: has no phase test; it sets `map->reused`, after which
  the `map_is_created()` setters fail even in `OBJ_OPEN`.
- `bpf_program__fd()`: returns `-ENOENT` while `prog->fd` is negative, which
  includes all of `OBJ_PREPARED`; `-EINVAL` only for a NULL `prog`.
- `OBJ_PREPARED` or later is required by `bpf_program__clone()` (`-EINVAL`
  otherwise) and `bpf_object__pin_maps()` (`-ENOENT`);
  `bpf_object__pin_programs()` requires `OBJ_LOADED`.
- **Unsafe usage**: turning a program on with `bpf_program__set_autoload()`
  after `bpf_object__prepare()`. The setter returns 0 in `OBJ_PREPARED`, but
  `bpf_object__relocate()` and `obj_needs_vmlinux_btf()` have already skipped
  programs whose `prog->autoload` was false, and `bpf_object__load_progs()`
  loads by the flag.
  - Safe: set it in `OBJ_OPEN`, as `process_obj()` in
    `tools/testing/selftests/bpf/veristat.c` does before
    `bpf_object__prepare()`.
- **Potentially unsafe usage**: a map setter that does not test
  `map_is_created()`.
  - Unsafe: when the field is read only during prepare, by
    `bpf_object__create_map()` or earlier; the call returns 0 in
    `OBJ_PREPARED` and the map keeps the old value.
  - Safe: when the field is read after creation, as
    `bpf_map__set_autoattach()`, whose flag is read by
    `bpf_object__attach_skeleton()`.
  - Safe: `bpf_map__set_pin_path()`; `map->pin_path` is read again after
    creation, by `bpf_map__pin()` when its `path` is NULL.

**File descriptor ownership**

- `prog->fd`: one per `struct bpf_program`; there are no program instances in
  this tree.
- `bpf_object_unload()`: closes every `map->fd` and `prog->fd` when prepare or
  load fails, so a borrowed fd is stale before `bpf_object__close()` runs.
- `bpf_program__unload()`: exported; closes `prog->fd` and sets it to -1.
- `bpf_program__clone()`: returns an fd the caller owns and must close; it is
  not stored in `prog->fd`.
- `bpf_program__attach_perf_event_opts()`: the link takes the caller's `pfd`
  on success only; on failure `pfd` is left open for the caller.
- `link->fd` is not always owned by the link:

| Link from | `link->fd` | `link->detach` does |
|---|---|---|
| attach functions that set `bpf_link__detach_fd()`, and `bpf_link__open()` | own link fd | closes `link->fd` |
| `bpf_program__attach_perf_event_opts()` | link fd, or `pfd` itself without `FEAT_PERF_LINK` or with `force_ioctl_attach` | `PERF_EVENT_IOC_DISABLE`, closes `perf_event_fd` and `link->fd`, removes a legacy probe |
| `bpf_map__attach_struct_ops()` with `BPF_F_LINK` | own link fd | closes `link->fd` |
| `bpf_map__attach_struct_ops()` without `BPF_F_LINK` | `map->fd`, borrowed from the map | `bpf_map_delete_elem()`; closes nothing |
| `usdt_manager_attach_usdt()` | never set | destroys the child links it owns |

- `bpf_link__destroy()` after `bpf_link__disconnect()`: closes no fd; neither
  `bpf_link_perf_dealloc()` nor `bpf_link_usdt_dealloc()` closes anything.
- Disconnected perf link: `link->fd` and `perf_event_fd` stay open and a legacy
  probe is not removed.
- Disconnected USDT link: its child links are never destroyed.
- Disconnected struct_ops link without `BPF_F_LINK`: the map element is not
  deleted.
- `bpf_link__pin()` then `bpf_link__destroy()`: destroy still runs
  `link->detach`; a link using `bpf_link__detach_fd()` is left untouched apart
  from the closed fd, but `bpf_link_perf_detach()` still disables the event
  and removes a legacy probe.
- **Potentially unsafe usage**: `close(bpf_link__fd(link))` followed by
  `bpf_link__destroy()`.
  - Unsafe: when the link is not disconnected; `link->detach` closes or uses
    the same number again, or for a USDT link the closed number was never the
    link's.
  - Safe: after `bpf_link__disconnect()`, which makes `bpf_link__destroy()`
    skip `link->detach`, on a link whose `link->fd` is its own link fd, as
    `pe_subtest()` in `tools/testing/selftests/bpf/prog_tests/bpf_cookie.c`
    does.

## Public API and compatibility

**Adding a public function**

- `check_abi` in `tools/lib/bpf/Makefile`: runs in the default build (`all_cmd`
  depends on `check`); it compares two counts, `GLOBAL_SYM_COUNT` from the
  shared `libbpf-in.o` and `VERSIONED_SYM_COUNT` from `libbpf.so`.
- `check_abi` on mismatch: prints "Warning" but does `exit 1`, so the build
  fails.
- `check_abi` accepts any `@LIBBPF_` version: a name added to an older node
  passes the build.
- `LIBBPF_VERSION` in the Makefile: taken from the highest `LIBBPF_` node name
  in `tools/lib/bpf/libbpf.map`, not from `tools/lib/bpf/libbpf_version.h`.
- `check_version`: fails the build unless `LIBBPF_MAJOR_VERSION` and
  `LIBBPF_MINOR_VERSION` in `libbpf_version.h` equal that node's version; a
  patch that opens a new node must bump the header too.
- Released or not: `libbpf.map` carries no marker for it; the last node in
  this tree is `LIBBPF_1.8.0` and the header says 1.8.
- New node frequency:
  `Documentation/bpf/libbpf/libbpf_naming_convention.rst` says the ABI version
  is bumped at most once per kernel development cycle.
- Order of names inside a node: not checked by the build; nodes `LIBBPF_1.5.0`
  and `LIBBPF_1.7.0` are not alphabetical.
- `COMPAT_VERSION()` and `DEFAULT_VERSION()`: defined in
  `tools/lib/bpf/libbpf_internal.h`; no source file under `tools/lib/bpf` uses
  them.

**Options structures**

- Size `OPTS_VALID()` treats as known: `offsetofend()` of the field named by
  the `<type>__last_field` define next to the struct (for example
  `bpf_prog_load_opts__last_field`), not `sizeof` the struct.
- Field added without updating the `__last_field` define:
  `libbpf_validate_opts()` counts it as extra bytes and rejects every caller
  that sets it non-zero, with the warning "has non-zero extra bytes".
- Struct with no `__last_field` define: `OPTS_VALID()` on it does not compile.
- Zero check range: from the end of the last known field to the caller's `sz`,
  so it includes the caller's tail padding even when caller and library match;
  `struct bpf_log_opts` has such bytes on 64-bit.
- `LIBBPF_OPTS()`: its `memset()` is what zeroes that padding.
- `size_t :0;`: not present in every options struct (`struct
  bpf_test_run_opts` has none); `OPTS_VALID()` does not depend on it.
- `OPTS_VALID()` returning true: does not show that `opts` is non-NULL or that
  `sz` covers any field after `sz`; it accepts NULL, and an `sz` as small as
  `sizeof(size_t)`.
- Function that requires the struct: tests NULL itself before `OPTS_VALID()`,
  as `bpf_tc_hook_create()` in `tools/lib/bpf/netlink.c` does.
- Nested options pointer: validated with its own `OPTS_VALID()`, as
  `bpf_map_create()` does for `log_opts` before `OPTS_GET()` on it.
- `OPTS_ZEROED(opts, field)`: true for NULL; otherwise checks that every byte
  after `field` up to `sz` is zero; `bpf_link_create()` uses it to reject
  fields that belong to another attach type.
- **Potentially unsafe usage**: `opts->field` read or written directly on a
  struct that came from the caller.
  - Unsafe: when nothing earlier on the path showed that `opts` is non-NULL
    and that `sz` covers the field; a passed `OPTS_VALID()` shows neither, and
    the access dereferences NULL or reads or writes past the caller's object.
  - Safe: after `OPTS_HAS()` was true for that field, as `bpf_xdp_query()`
    does for `feature_flags`.
  - Safe: after `OPTS_GET()` of that field returned a value that differs from
    the fallback, as `btf_dump__dump_type_data()` does for `indent_str`.
  - Safe: on a struct libbpf declared itself with `LIBBPF_OPTS()`, as
    `load_attr` in `bpf_object_load_prog()`, which
    `libbpf_prepare_prog_load()` then writes directly.

**Old kernels and feature probes**

- `kernel_supports()`: defined in `tools/lib/bpf/libbpf.c`; it dereferences
  `obj` first, so it cannot take NULL.
- Code with no `struct bpf_object`: calls `feat_supported(NULL, ...)`, which
  uses the global cache, as `bpf_prog_load()` and `bpf_map_create()` in
  `tools/lib/bpf/bpf.c` do.
- Per-object cache: exists only when `bpf_object_prepare_token()` obtained a
  token, or a test installed one with `bpf_object_set_feat_cache()`.
- `obj->feat_cache` timing: set in the first step of `bpf_object_prepare()`;
  a `kernel_supports()` call before that probes without the token.
- `obj->gen_loader` set: `kernel_supports()` returns true for every feature
  and runs no probe, so the new path is always taken for a light skeleton.
- Probe return value: positive is supported, zero is missing, negative logs a
  warning and is cached as `FEAT_MISSING`.
- `feat_supported()`: takes no lock and uses `READ_ONCE()` and `WRITE_ONCE()`
  only; two threads can run the same probe at once.
- `enum kern_feature_id` value with no `feature_probes[]` entry:
  `feat_supported()` calls the NULL `probe` pointer without a test.
- Probe signature: takes `token_fd`; a probe that creates a map, a program or
  BTF passes it on and sets `BPF_F_TOKEN_FD` when it is non-zero, as
  `probe_kern_global_data()` does.
- **Unsafe usage**: a probe that reaches its own feature test through a
  `tools/lib/bpf/bpf.c` wrapper; the cache entry is still `FEAT_UNKNOWN` while
  the probe runs, so `feat_supported()` recurses without end.
  - Safe: issue the raw syscall, as `probe_kern_prog_name()` does with
    `sys_bpf_prog_load()` because `bpf_prog_load()` tests `FEAT_PROG_NAME`.
  - Safe: `probe_memcg_account()` uses `sys_bpf_fd()` because
    `bump_rlimit_memlock()` tests `FEAT_MEMCG_ACCOUNT`.
  - Safe: call a wrapper that tests a different feature, as
    `probe_kern_arg_ctx_tag()` does by passing a program name.
- `FEAT_ARRAY_MMAP`: tested in `bpf_object__sanitize_maps()`, which clears
  `BPF_F_MMAPABLE`; `bpf_object__init_internal_map()` does not test it.
- `bpf_object__create_map()`: gates only the map name on `FEAT_PROG_NAME`;
  `map_extra` is set unconditionally.
- Not every fallback uses a probe; some paths try and react to the failure:
  - `bpf_object__create_map()` retries `bpf_map_create()` without BTF ids
    after a failure.
  - `bpf_link_create()` falls back to `bpf_raw_tracepoint_open()` on `-EINVAL`
    only when `OPTS_ZEROED(opts, sz)` holds, no target is set, and the attach
    type is one of the five in its last `switch`, for example
    `BPF_TRACE_FENTRY`.
  - `bpf_program__attach_kprobe_opts()` picks the legacy path from
    `determine_kprobe_perf_type()`, which is not a `feature_probes[]` entry.
- Feature the caller asked for explicitly:
  `bpf_program__attach_perf_event_opts()` returns `-EOPNOTSUPP` when
  `bpf_cookie` is set and `FEAT_PERF_LINK` is missing, instead of dropping the
  cookie.
- Testing a fallback: `bpf_object_set_feat_cache()` installs a cache with a
  feature preset to `FEAT_MISSING`; see
  `tools/testing/selftests/bpf/prog_tests/btf_sanitize.c`.

## Model gaps

### Other mistakes models make

- Models take an integer-returning public function never to return a bare
  `-1`. `bpf_object__btf_fd()` without BTF and `bpf_object__token_fd()`
  without a token return `-1` and do not write `errno`.
- Models take libbpf to accept any modern C. `tools/lib/bpf/Makefile` adds
  `-std=gnu89` and `-Werror`, and `EXTRA_WARNINGS` in
  `tools/scripts/Makefile.include` adds `-Wdeclaration-after-statement`, so a
  declaration after a statement breaks the build.
- Models take kernel typedefs and libc `reallocarray()` to be usable.
  `tools/lib/bpf/libbpf_internal.h` poisons `u8`, `u16`, `u32`, `u64`, `s8`,
  `s16`, `s32`, `s64` and `reallocarray`; use `__u32` style types and
  `libbpf_reallocarray()`.
- Models take a BPF token to exist only when the caller asks for one.
  `bpf_object_prepare_token()` is the first step of `bpf_object_prepare()` for
  every object and tries `BPF_FS_DEFAULT_PATH` when no path is set;
  `bpf_object_open()` takes the path from `bpf_token_path` or else from the
  `LIBBPF_BPF_TOKEN_PATH` environment variable; only an empty path skips the
  attempt.
- Models take the object to own only map and program fds.
  `bpf_object__close()` also closes `obj->token_fd` and the `fd` of each
  `obj->jumptable_maps` entry.
- Models take the internal maps to be `.data`, `.rodata`, `.bss` and
  `.kconfig`. A `LIBBPF_MAP_PERCPU` map is internal too; without
  `FEAT_PERCPU_DATA` `bpf_object__create_maps()` clears its `autocreate`
  instead of failing.
- Models take options structures to be the only size-versioned ABI.
  `struct bpf_object_skeleton` carries `map_skel_sz` and `prog_skel_sz`;
  libbpf steps through skeleton arrays by those sizes and must test them before
  reading a newer field, as `bpf_object__attach_skeleton()` does for `link` in
  `struct bpf_map_skeleton`.
- Models take the `EAGAIN` retry count of `sys_bpf_prog_load()` to be fixed.
  `attempts` in `struct bpf_prog_load_opts` overrides `PROG_LOAD_ATTEMPTS`;
  with a negative value `bpf_prog_load()` fails with `-EINVAL`.
- Models take the doc comments in `tools/lib/bpf/btf.h` as the contract. Those
  above `btf__new()` and the three functions after it name
  `libbpf_set_strict_mode()` as what selects the return form; it is a no-op in
  `tools/lib/bpf/libbpf.c`.
- Models format an error code for a message with libbpf_strerror_r(). There is
  no libbpf_strerror_r() here; `errstr()` does the job.
