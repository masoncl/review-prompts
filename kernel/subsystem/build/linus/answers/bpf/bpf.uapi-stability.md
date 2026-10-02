- Helper ids: not positional. Each `___BPF_FUNC_MAPPER` entry in
  `include/uapi/linux/bpf.h` carries its number as an explicit second
  argument, and `__BPF_ENUM_FN()` assigns it.
- New helpers: the list ends at `cgrp_storage_delete`, 211, followed by a
  comment that the list is "effectively frozen" and a kfunc should be added
  instead. `Documentation/bpf/bpf_design_QA.rst` words it more weakly ("generally
  added through the use of kfuncs"). Nothing in the build enforces the freeze;
  it is a review rule.
- `enum bpf_cmd`: `__MAX_BPF_CMD` is not the last enumerator.
  `BPF_COMMON_ATTRS = 1 << 16` follows it and is a flag ORed into `cmd`, which
  `__sys_bpf()` in `kernel/bpf/syscall.c` strips before the `switch`. A new
  command goes before `__MAX_BPF_CMD`.
- `bpf()` takes five arguments here (`SYSCALL_DEFINE5` in
  `kernel/bpf/syscall.c`); the last two are read only when `BPF_COMMON_ATTRS`
  is set.
- Enum size limit: `bpf_token_show_fdinfo()` in `kernel/bpf/token.c` has
  `BUILD_BUG_ON()` that `__MAX_BPF_CMD`, `__MAX_BPF_MAP_TYPE`,
  `__MAX_BPF_PROG_TYPE` and `__MAX_BPF_ATTACH_TYPE` are each below 64, because
  token and bpffs delegation masks are `u64` bitmaps indexed by enum value.
- `enum bpf_attach_type`: has 62 values here, so `__MAX_BPF_ATTACH_TYPE` is 62;
  a patch series that adds two or more attach types trips that
  `BUILD_BUG_ON()`.
- cgroup attach arrays: not indexed by `enum bpf_attach_type`. They are sized
  `MAX_CGROUP_BPF_ATTACH_TYPE` and indexed by `enum cgroup_bpf_attach_type`,
  mapped by `to_cgroup_bpf_attach_type()` in `include/linux/bpf-cgroup.h`. A
  new cgroup attach type needs an entry in both enums.
- `enum bpf_link_type`: values are written explicitly. A new value also needs a
  `BPF_LINK_TYPE()` line in `include/linux/bpf_types.h`, or
  `bpf_link_show_fdinfo()` (built under `CONFIG_PROC_FS`) hits `WARN_ONCE()`.
- Companion updates for a new prog, map, attach or link type:
  - `tools/include/uapi/linux/bpf.h` must match; `tools/lib/bpf/Makefile` only
    prints a warning when it differs.
  - name tables in `tools/lib/bpf/libbpf.c` (for example `attach_type_name[]`);
    `tools/testing/selftests/bpf/prog_tests/libbpf_str.c` walks the kernel BTF
    enum and fails on a missing name.
  - bpftool help and man pages, for a map type or a cgroup attach type;
    `tools/testing/selftests/bpf/test_bpftool_synctypes.py` compares them with
    `tools/include/uapi/linux/bpf.h`. It compares no prog type or link type
    with the header.
