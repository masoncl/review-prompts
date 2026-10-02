- LUO state: a raw `struct luo_ser` (`include/linux/kho/abi/luo.h`), not an
  FDT; `luo_state_setup()` hands it to `kho_add_subtree()` under
  `LUO_KHO_ENTRY_NAME`.
- There is no LUO_FDT_KHO_ENTRY_NAME, LUO_FDT_COMPATIBLE, luo_fdt_setup() or
  struct luo_session_header_ser in this tree.
- ABI version: the `compatible` member of `struct luo_ser`, compared with
  `LUO_ABI_COMPATIBLE` in `luo_early_startup()`, which also rejects a blob
  shorter than `struct luo_ser`.
- `sessions_pa`: physical address of the first `struct kho_block_header_ser`
  in a chain of blocks of `struct luo_session_ser`; each session's files
  hang off `struct luo_file_set_ser` the same way
  (`kernel/liveupdate/kho_block.c`).
- `sessions_pa` is written only by `luo_session_serialize()`, and is 0 when
  there are no sessions; `luo_session_setup_outgoing()` at boot only records
  where to write it.
- `flbs_pa`: one preserved page, allocated at boot by
  `luo_flb_setup_outgoing()`.
- `liveupdate_enabled()`: false unless the `liveupdate` early parameter set
  `luo_global.enabled`; KHO being enabled is not enough.
- `luo_early_startup()`: clears `luo_global.enabled` when `kho_is_enabled()`
  is false.
- Disabled LUO: `liveupdate_ioctl_init()` does not register `/dev/liveupdate`.
- Incoming state: `liveupdate_early_init()`, an `early_initcall()`, calls
  `luo_early_startup()`.
- Any non-zero return of `luo_early_startup()` reaches `luo_restore_fail()`,
  which is `panic()`; this includes a compatible mismatch and a
  `kho_retrieve_subtree()` error other than `-ENOENT`.
- Sessions and files are not deserialized at boot: `luo_open()` calls
  `luo_session_deserialize()`, which does the work once and caches the
  result; on failure every open of `/dev/liveupdate` returns `-EIO`.
- Outgoing state: `luo_late_startup()`, a `late_initcall()`, calls
  `luo_state_setup()` only when `liveupdate_enabled()`; a failure clears
  `luo_global.enabled`.
