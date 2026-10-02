- Programs: after a successful load, `bpf_program__autoload()` true means
  `bpf_program__fd()` is a loaded program; `bpf_object__load_progs()` skips
  only subprograms and programs with autoload off.
- libbpf drops no program for being unreferenced or for a missing attach
  target; such an error fails the whole load.
- `bpf_program__fd()` on a program that was not loaded: returns `-ENOENT`.
- struct_ops programs: libbpf rewrites autoload during load.
  `bpf_object_adjust_struct_ops_autoload()` turns it on for a
  `SEC("?struct_ops")` program used by an autocreated map and off when no map
  that uses it is autocreated; `bpf_map__init_kern_struct_ops()` turns it off
  when the member is absent from kernel BTF or the slot was repointed.
- Maps with autocreate off: `bpf_map__fd()` still returns a non-negative fd
  after load. It is the memfd from `create_placeholder_fd()`, not a BPF map.
- Internal maps such as `.rodata` and `.bss`: `bpf_object__create_maps()`
  clears autocreate itself when the kernel lacks `FEAT_GLOBAL_DATA` or
  `FEAT_PERCPU_DATA`, so these can be placeholders without any call to
  `bpf_map__set_autocreate()`.
- **Potentially unsafe usage**: taking `bpf_map__fd(map) >= 0` after load as
  proof that the map exists in the kernel.
  - Unsafe: for a map with autocreate off the test passes and the fd is the
    placeholder.
  - Safe: test `bpf_map__autocreate()` first, as `run_subtest()` in
    `tools/testing/selftests/bpf/test_loader.c` does before
    `bpf_map__attach_struct_ops()`; `map_is_created()` in
    `tools/lib/bpf/libbpf.c` is what lets `bpf_map__fd()` return the
    placeholder.
  - Safe: a `SEC(".maps")` map of a skeleton that is opened and loaded in one
    call, as in `check_stack()` in
    `tools/testing/selftests/bpf/prog_tests/bpf_loop.c`;
    `bpf_object__add_map()` sets autocreate and nothing clears it.
