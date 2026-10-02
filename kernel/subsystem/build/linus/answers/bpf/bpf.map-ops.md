- There is no find_and_alloc_map() here; `map_create_alloc()` in
  `kernel/bpf/syscall.c` looks up `bpf_map_types[]`, runs the checks and calls
  `map_alloc`.
- `map_mem_usage` NULL: `map_create_alloc()` returns `-EINVAL`, with no
  warning. The test runs after `map_alloc_check`, and on
  `bpf_map_offload_ops` when `attr->map_ifindex` is set.
- New map type: needs a `case` in the `switch (map_type)` of
  `map_create_alloc()`; the `default:` does `WARN()` and returns `-EPERM`.
- While `map_alloc` runs: `map->ops`, `refcnt` and `usercnt` are not yet set;
  `map_create_alloc()` sets them after `map_alloc` returns.
- `map_free` on a creation error: `bpf_map_free()` calls it directly from
  `map_create_alloc()` and `map_create()`, in the calling task, with no
  workqueue and no grace period. The exception is a `bpf_map_new_fd()`
  failure, which goes through `bpf_map_put_with_uref()`.
- Ops the system call calls with no NULL test: `map_get_next_key`,
  `map_delete_elem`, and `map_lookup_elem` and `map_update_elem` unless
  `bpf_map_copy_value()` or `bpf_map_update_value()` routes the `map_type`
  elsewhere first.
- A type may omit `map_update_elem` only if routed that way; for example
  `prog_array_map_ops` and `reuseport_array_ops` have none.
- `map_btf_id`: optional; without it only direct access to the map pointer
  fails, with `-ENOTSUPP` in `kernel/bpf/verifier.c`.
- Ops a program calls through the generic map helpers: the nine that
  `bpf_do_misc_fixups()` in `kernel/bpf/fixups.c` patches, which include
  `map_redirect` and `map_lookup_percpu_elem`.
- Patched call: with `prog->jit_requested` on 64-bit the program calls
  `ops->map_update_elem` and the others directly, so the helper body in
  `kernel/bpf/helpers.c` and its `WARN_ON_ONCE()` do not run.
- Patched call has no NULL test: an op must be non-NULL for every type the
  verifier lets reach its helper.
- `check_map_func_compatibility()`: its first `switch` ends in
  `default: break`, so a type with no `case` there is accepted for
  `bpf_map_lookup_elem()`, `bpf_map_update_elem()` and
  `bpf_map_delete_elem()`.
- Sleepable programs: `check_map_prog_compatibility()` rejects every map type
  not in its `switch`; a new type needs a `case` to be usable there.
- `kernel/bpf/hashtab.c` bucket lock: an `rqspinlock_t`; `struct bpf_htab` has
  no `map_locked` member, and `htab_lock_bucket()` never returns `-EBUSY`.
- `htab_lock_bucket()` failure: returns `-EDEADLK` or `-ETIMEDOUT`; update and
  delete return that error, and `htab_lru_map_delete_node()` returns false.
- `map_gen_lookup`: may return `-EOPNOTSUPP` to fall back to the call; any
  other count `<= 0` or `>= INSN_BUF_SIZE` fails the load with `-EFAULT`.
- **Potentially unsafe usage**: `map_lookup_elem` returning `ERR_PTR()`.
  - Unsafe: when `check_map_func_compatibility()` admits
    `BPF_FUNC_map_lookup_elem` for the type; `bpf_map_lookup_elem_proto` is
    `RET_PTR_TO_MAP_VALUE_OR_NULL`, so the program tests for NULL only.
  - Safe: when the type's `case` excludes `BPF_FUNC_map_lookup_elem`, as for
    `fd_array_map_lookup_elem()`; `bpf_map_copy_value()` tests `IS_ERR()`.
- Context the system call gives each op:

| Op | Called under |
|---|---|
| `map_get_next_key` | `rcu_read_lock()` |
| `map_lookup_elem_sys_only`, `map_lookup_elem` | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_lookup_and_delete_elem` | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_update_elem`, default branch | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_update_elem` for `BPF_MAP_TYPE_CPUMAP`, `BPF_MAP_TYPE_ARENA`, `BPF_MAP_TYPE_STRUCT_OPS` | neither; may sleep |
| `map_delete_elem` for prog array and `BPF_MAP_TYPE_STRUCT_OPS` | neither; may sleep |
| `map_delete_elem`, other types | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_push_elem`, `map_peek_elem` | `bpf_disable_instrumentation()` only |
| `map_pop_elem` | neither |
| batch ops, `map_release_uref`, `map_mmap`, `map_poll` | neither |

- `bpf_disable_instrumentation()`: raises `bpf_prog_active`, which only the
  kprobe, tracepoint and perf event paths test; see `kernel/trace/bpf_trace.c`.
