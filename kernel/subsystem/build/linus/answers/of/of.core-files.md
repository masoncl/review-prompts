| Job | File under `drivers/of/` |
|---|---|
| MSI parsing: `of_msi_xlate()`, `of_msi_get_domain()`, `of_msi_configure()` | `irq.c`; there is no MSI file |
| `msi-map` id translation: `of_map_msi_id()` | `base.c` |
| Boot-time self-test, `CONFIG_OF_UNITTEST` | `unittest.c`, data in `unittest-data/` |
| KUnit tests, `CONFIG_OF_KUNIT_TEST` and `CONFIG_OF_OVERLAY_KUNIT_TEST` | `of_test.c`, `overlay_test.c` |
| KUnit helpers, built on `CONFIG_KUNIT` alone | `of_kunit_helpers.c` |
