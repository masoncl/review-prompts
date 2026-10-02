- One command: only when `its_list_map` is zero; the number of ITSs is not
  tested.
- `its_list_map` non-zero, even with one bit set: the loop over `its_nodes`
  runs, with `vmovp_seq_num` and `get_its_list()`.
- `vmovp_lock`: taken with `guard(raw_spinlock)`, not irqsave.
- Skipped ITSs: exactly two tests, `!is_v4(its)` and
  `!require_its_list_vmovp()`; there is no test for a shared collection or
  for an ITS already handled.
- `has_rvpeid` set: `require_its_list_vmovp()` is true for every ITS, but the
  `is_v4()` test still skips an ITS that is not v4.
- **Unsafe usage**: calling `its_send_vmovp()` with `its_list_map` set and
  without the VM's `vmapp_lock`; `vlpi_count[]` is read in `get_its_list()`
  and again in the loop, and `its_map_vm()` and `its_unmap_vm()` change it
  under `vmapp_lock`.
  - Safe: take `vmapp_lock`, then `vpe_lock`, then call it, as
    `its_vpe_set_affinity()` does.
