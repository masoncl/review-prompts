- There is no KHDR_DIR in this tree.
- `KHDR_INCLUDES`: set and exported by `tools/testing/selftests/Makefile`.
  With `O=` or `KBUILD_OUTPUT` it is `-isystem ${abs_objtree}/usr/include`,
  otherwise `-isystem ${abs_srctree}/usr/include`.
- `lib.mk` assigns `KHDR_INCLUDES` only when it is empty, which is the case
  when a test directory is built directly.
- `kselftest` and `kselftest-%` in the top-level `Makefile` depend on
  `headers`. `make -C tools/testing/selftests` runs no header install.
- `headers` in `lib.mk`: a target that runs the top-level `headers` for the
  tree named by `KHDR_INCLUDES`. Nothing in `lib.mk` depends on it.
- A test opts in to `headers` with an order-only prerequisite, as
  `$(OUTPUT)/vdso_standalone_test_x86` does in `vDSO/Makefile`.
- **Potentially unsafe usage**: expanding `$(KHDR_INCLUDES)` with `:=` before
  the include.
  - Unsafe: when the directory is built directly; the variable is empty until
    `lib.mk` is read, so the flag is silently missing.
  - Safe: when built through `tools/testing/selftests/Makefile`, which exports
    the variable.
  - Safe: `:=` after the include, as in `x86/Makefile`.
  - Safe: `+=` or `=` before the include, on a variable not assigned with
    `:=`, as `CFLAGS` in `sync/Makefile`; the reference expands when the
    compiler runs.
- **Unsafe usage**: a header path into the source tree, such as
  `-I$(top_srcdir)/usr/include`, in place of `$(KHDR_INCLUDES)`. With `O=` the
  headers are under the object tree and the path misses them.
  - Safe: `CFLAGS += $(KHDR_INCLUDES)`, as in `sync/Makefile`;
    `tools/testing/selftests/Makefile` points it at the object tree.
