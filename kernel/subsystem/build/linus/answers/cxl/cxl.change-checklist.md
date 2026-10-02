| Option | Objects | Stubs when off |
|---|---|---|
| `CONFIG_CXL_REGION` | `region.o`, `region_pmem.o`, `region_dax.o` | `drivers/cxl/core/core.h`, `drivers/cxl/cxl.h`, `drivers/cxl/cxlmem.h` |
| `CONFIG_CXL_RAS` | `ras.o`, `ras_rch.o` | `drivers/cxl/core/core.h`, `drivers/cxl/cxlpci.h` |
| `CONFIG_CXL_ATL` | `atl.o` | `drivers/cxl/cxl.h` |
| `CONFIG_CXL_FEATURES` | `features.o` | `include/cxl/features.h` only |
| `CONFIG_CXL_MCE` | `mce.o` | `drivers/cxl/core/mce.h` |
| `CONFIG_CXL_EDAC_MEM_FEATURES` | `edac.o` | `drivers/cxl/cxlmem.h` |
| `CONFIG_CXL_SUSPEND` | `suspend.o`, its own `obj-`, not part of `cxl_core` | `drivers/cxl/cxlmem.h`, `include/linux/pm.h` |

- `drivers/cxl/core/core.h` holds stubs for `CONFIG_CXL_REGION` and
  `CONFIG_CXL_RAS` only; it has none for MCE, features or EDAC.
- `CONFIG_CXL_FEATURES` block in `drivers/cxl/core/core.h`: declarations with
  no `#else`; `cxl_get_feature()`, `cxl_set_feature()` and
  `cxl_feature_info()` are called only from `features.c` and `edac.c`, and a
  call from an always-built file breaks the build with the option off.
- `devm_cxl_add_dax_region()` and `devm_cxl_add_pmem_region()`: same pattern,
  declared under `CONFIG_CXL_REGION` with no stub, called only from the region
  files.
- `cxlfs` in `struct cxl_dev_state` (`include/cxl/cxl.h`): exists only under
  `CONFIG_CXL_FEATURES`; outside `features.c` use `to_cxlfs()`, which has a
  stub that returns NULL.
- `cxl_region_attach()` is `static` in `drivers/cxl/core/region.c` and has no
  stub; `cxl_decoder_detach()` has one.
- There is no cxl_port_get_spa_cache_alias() and no
  devm_cxl_memdev_edac_release() in this tree.
- `CONFIG_CXL_RAS`, PCI side: `aer_cxl_rch.o` in `drivers/pci/pcie/Makefile`,
  stubs in `drivers/pci/pcie/portdrv.h`.
- `CONFIG_CXL_PMU`: defined in `drivers/perf/Kconfig`, not
  `drivers/cxl/Kconfig`; `pmu.o` is in `cxl_core-y` unconditionally and has no
  stubs.
- `CONFIG_CXL_EDAC_SCRUB`, `CONFIG_CXL_EDAC_ECS`, `CONFIG_CXL_EDAC_MEM_REPAIR`,
  `CONFIG_CXL_MEM_RAW_COMMANDS`: no objects and no stubs; tested with
  `IS_ENABLED()` or `#ifdef` inside `drivers/cxl/core/edac.c` and
  `drivers/cxl/core/mbox.c`.
- Event record structures decoded by the trace events: defined in
  `include/cxl/event.h`, not in `drivers/cxl/cxlmem.h`.
- Trace events: all are in `drivers/cxl/core/trace.h`; search it for
  `TRACE_EVENT(`. Easy to miss: `cxl_port_aer_uncorrectable_error`,
  `cxl_port_aer_correctable_error` and `cxl_memory_sparing`.
- Region trace events: none; `cxl_general_media`, `cxl_dram` and `cxl_poison`
  read `cxlr->params.uuid` and the region name, and `cxl_poison` calls
  `cxl_dpa_to_hpa()`, so a change to `struct cxl_region` or to that helper's
  stub in `core.h` also touches `trace.h`.
- EDAC attributes published by `edac.c`: documented in
  `Documentation/ABI/testing/sysfs-edac-scrub`,
  `Documentation/ABI/testing/sysfs-edac-ecs` and
  `Documentation/ABI/testing/sysfs-edac-memory-repair`, not in
  `Documentation/ABI/testing/sysfs-bus-cxl`.
- Debugfs files: `Documentation/ABI/testing/debugfs-cxl`.
