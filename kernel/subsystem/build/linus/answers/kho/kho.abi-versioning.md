- Macro to bump with each definition, and what a mismatch does:

| Header in `include/linux/kho/abi/` | Macro | Value | Checked in | On mismatch |
|---|---|---|---|---|
| `kexec_handover.h` | `KHO_FDT_COMPATIBLE` | `"kho-v4"` | `kho_populate()` | boots as a non-KHO boot |
| `block.h` | `KHO_FDT_COMPATIBLE` | `"kho-v4"` | `kho_populate()` | boots as a non-KHO boot |
| `luo.h` | `LUO_ABI_COMPATIBLE` | `"luo-v5"` | `luo_early_startup()` | `panic()` via `luo_restore_fail()` |
| `memfd.h` | `MEMFD_LUO_FH_COMPATIBLE` | `"memfd-v2"` | `luo_file_deserialize_one()` | `-ENOENT`; `luo_open()` then fails with `-EIO` |
| `memblock.h` | `MEMBLOCK_KHO_NODE_COMPATIBLE` | `"memblock-v1"` | `reserve_mem_kho_retrieve_fdt()` | region allocated afresh |
| `memblock.h` | `RESERVE_MEM_KHO_NODE_COMPATIBLE` | `"reserve-mem-v1"` | `reserve_mem_kho_revive()` | region allocated afresh |
| `kexec_metadata.h` | `KHO_KEXEC_METADATA_VERSION` | 1 | `kho_in_kexec_metadata()` | warning, metadata ignored |

- `luo.h`: one macro covers every struct in the file. There is no
  LUO_FDT_COMPATIBLE, LUO_FDT_SESSION_COMPATIBLE or LUO_FDT_FLB_COMPATIBLE.
- `LUO_ABI_COMPATIBLE`: stored in `luo_ser->compatible` and compared with
  `strncmp()`, not `fdt_node_check_compatible()`.
- `LUO_ABI_COMPAT_LEN`: derived from the string, so a longer string can
  change the layout of `struct luo_ser`.
- `KHO_KEXEC_METADATA_VERSION`: a `u32` in the struct, compared with `!=`; it
  is not a compatible string.
- `block.h`: the pairing with `KHO_FDT_COMPATIBLE` is stated only in its
  header comment; the only user of the blocks is LUO.
- `KHO_FDT_COMPATIBLE`: the `DOC:` comment in the same header shows "kho-v3"
  twice; the definition is `"kho-v4"`.
- `MEMFD_LUO_FH_COMPATIBLE`: the example in a comment in
  `include/linux/liveupdate.h` shows "memfd-v1"; the definition is
  `"memfd-v2"`.
- `__packed`: used by the structs in `luo.h`, `memfd.h`, `block.h` and
  `kexec_metadata.h`. The structs in `kexec_handover.h` are not `__packed`,
  and `DECLARE_KHOSER_PTR()` is a union of a `u64` and a pointer.
- `Documentation/core-api/kho/abi.rst` renders the header `DOC:` comments, so
  a stale value in a comment reaches the published ABI text.
