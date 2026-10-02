- `kho_enable`: `__ro_after_init`, so it cannot change once init memory is
  sealed; every function that writes it is `__init`.
- `kho_is_enabled()` true to false: `kho_reserve_scratch()` on allocation
  failure, and the error path of `kho_init()`; besides the `kho=` parser
  `kho_parse_enable()`, nothing else writes `kho_enable`, `kho_populate()`
  included.
- `kho_reserve_scratch()`: reached only when `kho_in.scratch_phys` is 0, so on
  a handover boot whose `kho_memory_init_early()` succeeded only `kho_init()`
  can clear `kho_enable`.
- `kho_is_enabled()` is final only after `kho_init()` (`fs_initcall`); a true
  read at `early_initcall`, as in `luo_early_startup()`, can be overtaken.
- `is_kho_boot()`: independent of `kho_enable`; with `kho=off` on a handover
  boot it is still true.
- `is_kho_boot()` true to false: `kho_in.fdt_phys = 0` in the error path of
  `kho_memory_init_early()` and in the error path of `kho_mem_retrieve()`
  (called by `kho_memory_init()`); final once `kho_memory_init()` returns.
- `is_kho_boot()` read between `kho_populate()` and
  `kho_memory_init_early()`: done by `reserve_regions()` in
  `drivers/firmware/efi/efi-init.c`; the value can still be withdrawn.
