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
