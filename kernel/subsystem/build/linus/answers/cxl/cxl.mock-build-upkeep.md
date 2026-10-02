- Nothing in the kernel's own Makefiles or Kconfig builds
  `tools/testing/cxl/`; a break there shows only when that directory is built
  as an external module.
- New core file with per-file flags: `drivers/cxl/core/Makefile` uses
  `CFLAGS_trace.o`, while Kbuild sets `-DTRACE_INCLUDE_PATH` and the include
  paths directory-wide in `ccflags-y`; a per-file flag is not picked up by the
  Kbuild copy unless added there.
- Kbuild's `cxl_core` list equals the Makefile list plus `config_check.o`,
  `cxl_core_test.o` and `cxl_core_exports.o`.
- Core symbol that `cxl_test` needs and the core does not export: add the
  export to `tools/testing/cxl/cxl_core_exports.c`, not to `drivers/cxl/`.
- Prototype change, what the compiler checks: `mock.c` includes `cxlmem.h` and
  `cxlpci.h`, so the wrapper's call to `<name>()` and its call to the op are
  checked; no header declares `__wrap_<name>()`, so the wrapper's own
  parameter list and return type are checked against nothing.
- Prototype change, places: `__wrap_<name>()` in `mock.c`; the member of
  `struct cxl_mock_ops` and the mock in `test/cxl.c` only where the wrapper
  has an op; there is no typedef or trampoline to update.
- Context passed to `acpi_table_parse_cedt()`: `mock_acpi_table_parse_cedt()`
  casts `arg` to `struct cxl_cedt_context` and reads its first member, so
  `struct cxl_cfmws_context`, `struct cxl_chbs_context` and
  `struct cxl_cxims_context` in `drivers/cxl/acpi.c` must keep
  `struct device *dev` first.
- New wrapper's export: the rebuilt module imports `__wrap_<name>`, so
  `cxl_mock` must export it; for a CXL core symbol use
  `EXPORT_SYMBOL_NS_GPL(..., "CXL")` as the existing wrappers do.
- **Unsafe usage**: adding a member to `struct cxl_mock_ops`, calling it from
  a wrapper, and not setting it in `cxl_mock_ops` in
  `tools/testing/cxl/test/cxl.c`.
  - Unsafe: wrappers test `ops` for NULL but never the member, so the call
    dereferences NULL once `cxl_test` has registered its ops.
  - Safe: set the member in the one `cxl_mock_ops` instance, as
    `.devm_cxl_add_dport_by_dev = mock_cxl_add_dport_by_dev` does.
