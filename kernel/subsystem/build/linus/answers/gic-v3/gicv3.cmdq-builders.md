- `its_fixup_cmd()` only stores the four words through `cpu_to_le64()`;
  cache maintenance is `its_flush_cmd()`, called by the sender.
- `its_build_sync_cmd()` and `its_build_vsync_cmd()` return `void`; they are
  of neither builder type.
- `its_build_mapd_cmd()` is the only builder that always returns NULL.
- `its_build_invall_cmd()` returns `desc->its_invall_cmd.col`, so a SYNC
  follows INVALL.
- `its_build_mapc_cmd()` and `its_build_invall_cmd()` return the
  descriptor's collection directly, without `valid_col()`.
- NULL that depends on the hardware:

| Builder | Returns NULL when |
|---|---|
| `its_build_vmapp_cmd()` | unmap on an ITS where `is_v4_1(its)` |
| `its_build_invdb_cmd()` | `WARN_ON(!is_v4_1(its))` fires |
| `its_build_vsgi_cmd()` | `WARN_ON(!is_v4_1(its))` fires |

- `its_build_invdb_cmd()` and `its_build_vsgi_cmd()` on that `WARN_ON()`
  path return before encoding anything and before `its_fixup_cmd()`; the
  sender still flushes and posts the all-zero slot.
- Every other builder returns NULL only when `valid_col()` or `valid_vpe()`
  rejects the target.
- `valid_col()` rejects a collection whose `target_address`
  `its_cpu_init_collection()` has not written: `its_alloc_collections()`
  presets `target_address` to `~0ULL`.
- `valid_col()` or `valid_vpe()` returning NULL drops only the sync; the
  command itself is still posted.
- There is no MOVALL builder; `GITS_CMD_MOVALL` is used only by
  `arch/arm64/kvm/vgic/vgic-its.c`.
