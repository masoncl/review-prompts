- Models take an incompatible incoming blob to be rejected cleanly. For LUO
  it is a `panic()`. `liveupdate_early_init()` does not call
  `liveupdate_enabled()`, and `luo_early_startup()` calls it only in the
  branch where `kho_is_enabled()` is false, so with KHO enabled the panic
  does not need `liveupdate=`.
- Models do not know that LUO has no exported symbols:
  `kernel/liveupdate/luo_file.c`, `kernel/liveupdate/luo_flb.c` and
  `kernel/liveupdate/kho_block.c` contain no `EXPORT_SYMBOL`, and
  `CONFIG_LIVEUPDATE_MEMFD` is bool, so a file handler has to be built in.
- Models do not know that the `struct kho_block_set` code in
  `kernel/liveupdate/kho_block.c` does no locking of its own, and that
  `kho_block_set_shrink()` frees blocks from the end of the chain.
- Models do not know that a failure to register the `KHO_METADATA_NODE_NAME`
  subtree fails `kho_init()` and clears `kho_enable`; see
  `kho_kexec_metadata_init()`.
- Models do not know the limits of `kho_preserve_vmalloc()`: it returns
  `-EOPNOTSUPP` for an area with flags outside
  `KHO_VMALLOC_SUPPORTED_FLAGS` and `-EINVAL` when `find_vm_area()` fails.
  `kho_unpreserve_vmalloc()` frees the chunk pages, not the area.
- Models do not know that `luo_preserved_files` is one xarray for all
  sessions, so the `-EBUSY` of `luo_preserve_file()` applies to a file
  preserved in any session; `memfd_luo_get_id()` uses the inode.
- Models do not know the FLB rules in `liveupdate_register_flb()`: all four
  `struct liveupdate_flb_ops` callbacks are required, the file handler must
  already be registered, and at most `LUO_FLB_MAX` FLBs exist.
  `liveupdate_flb_get_incoming()` takes a count that
  `liveupdate_flb_put_incoming()` drops; the last drop runs `finish`.
- Models take incoming sessions to be deserialized in early boot. Early boot
  only runs `kho_block_set_restore()` in `luo_session_setup_incoming()`;
  `luo_open()` returns `-EBUSY` to a second opener while the first still
  holds `/dev/liveupdate` open.
- Models take LUO to be on whenever Kexec HandOver is on. `memfd_luo_init()`
  ignores the `-EOPNOTSUPP` that `liveupdate_register_file_handler()` returns
  when `liveupdate_enabled()` is false.
- Models do not know that `kexec_calculate_store_digests()` in
  `kernel/kexec_file.c` skips the purgatory checksum for a non-crash image
  whenever `kho_is_enabled()`.
- Models trust comments that name things this tree does not define, for
  example LIVEUPDATE_IOCTL_PREPARE and LIVEUPDATE_STATE_UPDATED in
  `include/uapi/linux/liveupdate.h`.
