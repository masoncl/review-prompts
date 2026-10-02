- `dax_hmem`: also rebuilt by `tools/testing/cxl/Kbuild`, from
  `drivers/dax/hmem/hmem.c`, and linked with the same `ldflags-y`.
- `--wrap=walk_hmem_resources`, `--wrap=region_intersects`,
  `--wrap=region_intersects_soft_reserve`: their only callers among the
  rebuilt sources are in `drivers/dax/hmem/hmem.c`.
- `cxl_mock_accel` in `tools/testing/cxl/test/accel.c`: a platform driver for
  `"cxl_type2_accel"` devices (`CXL_DEVTYPE_DEVMEM`); it stands in for no
  driver under `drivers/cxl/`.
- There is no mock_pmem.c; `cxl_pmem` is rebuilt from `drivers/cxl/pmem.c`
  and `drivers/cxl/security.c`.
- HDM decoder setup is redirected at `devm_cxl_switch_port_decoders_setup()`
  and `devm_cxl_endpoint_decoders_setup()`; `devm_cxl_setup_hdm()`,
  `devm_cxl_enumerate_decoders()` and `devm_cxl_add_passthrough_decoder()` are
  `static` in `drivers/cxl/core/hdm.c` and are not wrapped.
- Dport enumeration is redirected at `devm_cxl_add_dport_by_dev()`, with a
  plain `--wrap=` line; there is no devm_cxl_port_enumerate_dports() here.
- There is no DECLARE_TESTABLE() in this tree, and no `exports.h` under
  `tools/testing/cxl/` or `drivers/cxl/`; `--wrap` and `__mock` are the only
  two redirection mechanisms.
- `tools/testing/cxl/cxl_core_exports.c`: holds no trampoline; it only adds an
  `EXPORT_SYMBOL_NS_GPL()` for `cxl_num_decoders_committed()`, which
  `drivers/cxl/core/port.c` does not export.
- `CXL_TEST_ENABLE`: defined by Kbuild, tested by no source file.
- `__mock`: `static` by default (`drivers/cxl/cxl.h`), `__weak` in the mock
  build; `to_cxl_host_bridge()` in `drivers/cxl/acpi.c` is the only `__mock`
  function, and `tools/testing/cxl/mock_acpi.c`, linked into the rebuilt
  `cxl_acpi`, supplies the strong copy.
- Fallback: the wrapper calls `<name>()` itself; no `__real_` name is used.
  `mock.c` is built by `tools/testing/cxl/test/Kbuild`, which sets no
  `ldflags-y`.
- Wrapper exports: `EXPORT_SYMBOL_NS_GPL(..., "CXL")` for the CXL core
  symbols, `"ACPI"` for `__wrap_acpi_table_parse_cedt()`, and no namespace for
  the rest; there is no "cxl_test" namespace.
- Where mock-or-real is decided differs per wrapper in `mock.c`:

| Shape | Decided by | For example |
|---|---|---|
| op called whenever ops are registered | the op in `test/cxl.c`, which calls the real function itself for a non-mock device | `__wrap_acpi_table_parse_cedt()`, `__wrap_acpi_pci_find_root()` |
| predicate, then op | `is_mock_port()` or `is_mock_dev()` in the wrapper | `__wrap_devm_cxl_add_dport_by_dev()` |
| predicate, no op | wrapper has the mock behaviour inline | `__wrap_cxl_await_media_ready()`, `__wrap_devm_cxl_add_rch_dport()` |
| real function always called | wrapper only edits an argument first | `__wrap_nvdimm_bus_register()` |
| op return value | op returns negative to ask for the real function | `__wrap_region_intersects()` |
| device name | `"hmem_platform.1"`; real function for any other host | `__wrap_walk_hmem_resources()` |

- Every redirected CXL core function is defined in `cxl_core` and called only
  from another module (for example `drivers/cxl/port.c`,
  `drivers/cxl/acpi.c`); the tree has no example of `--wrap` redirecting a
  call made inside one module.
