- `__bpf_kfunc`: expands to `__used __retain __noclone noinline`, in
  `include/linux/btf.h`.
- BTF annotations: `btf2btf()` in `tools/bpf/resolve_btfids/main.c` emits the
  `bpf_kfunc` decl tag for each entry of a `BTF_SET8_KFUNCS` set, not pahole.
- Function missing from BTF: `collect_kfuncs()` only warns `no BTF func for
  kfunc` and skips the entry.
- Hooks: `bpf_prog_type_to_kfunc_hook()` in `kernel/bpf/btf.c` maps several
  program types to one hook, so registering for one type offers the kfunc to
  every type on that hook.
- Program type with no case in `bpf_prog_type_to_kfunc_hook()`: maps to
  `BTF_KFUNC_HOOK_MAX` and `register_btf_kfunc_id_set()` returns `-EINVAL`.
- Module: `btf_populate_kfunc_set()` accepts one set per hook per module; a
  second registration on the same hook warns and returns `-EINVAL`.
- Module kfunc name: `btf_check_kfunc_name()` rejects a name that is already a
  function in vmlinux BTF or in another module's BTF.
- Return value 0: `check_btf_kconfigs()` returns 0 with nothing registered when
  a module has no BTF, or when vmlinux has none and `CONFIG_DEBUG_INFO_BTF`
  is off.
- Filter call site: `__btf_kfunc_is_allowed()`, reached from
  `bpf_fetch_kfunc_arg_meta()` through `btf_kfunc_is_allowed()`;
  `btf_kfunc_flags()` runs no filter.
- **Unsafe usage**: a `.filter` callback that returns non-zero for a
  `kfunc_id` that is not in its own set; `__btf_kfunc_is_allowed()` calls
  every filter on the hook for every kfunc on that hook.
  - Safe: return 0 first when `btf_id_set8_contains()` misses the own set, as
    `bpf_session_filter()` in `kernel/trace/bpf_trace.c` does.
