- **Unsafe usage**: calling a send function with `lock` of the same
  `struct its_node` held.
  - Unsafe: `BUILD_SINGLE_CMD_FUNC` takes `its->lock` with
    `raw_spin_lock_irqsave()`, so the call deadlocks.
  - Safe: drop `lock` first, as `its_create_device()` does between its
    `list_add()` and `its_send_mapd()`.
  - Safe: sending with other raw spinlocks held or IRQs off; the path only
    spins with `udelay()`. `its_send_vmovp()` sends under `vmovp_lock`.
- **Potentially unsafe usage**: returning from a builder without calling
  `its_fixup_cmd()`.
  - Unsafe: once an encode helper such as `its_encode_cmd()` has written
    the block; on a big-endian kernel the words stay in CPU byte order.
  - Safe: only as a `WARN_ON()` guard before anything is encoded, for a
    state callers exclude, because the zeroed slot is still posted.
    `its_build_invdb_cmd()` does this; its caller takes the ITS from
    `find_4_1_its()`.
  - Safe: reach one common `its_fixup_cmd()` through `goto out`, as
    `its_build_vmapp_cmd()` does.
- **Potentially unsafe usage**: returning a collection as the sync object
  without `valid_col()`.
  - Unsafe: when `its_cpu_init_collection()` may not have written the
    collection's `target_address`; `its_build_sync_cmd()` then encodes the
    `~0ULL` preset by `its_alloc_collections()`.
  - Safe: when the caller has just written `target_address`, as for
    `its_build_mapc_cmd()` and `its_build_invall_cmd()`, reached only from
    `its_cpu_init_collection()`.
- **Unsafe usage**: a builder reading a `struct its_cmd_desc` member that
  the sender did not set.
  - Unsafe: senders declare the descriptor on the stack without an
    initialiser, so the builder encodes stack garbage.
  - Safe: set every member the builder reads, as `its_send_vmapp()` does.
  - Safe: zero the descriptor with `desc = {}`, as `its_send_vmovp()` does
    for `seq_num` and `its_list` on its single-ITS path.
- Builders read live driver state, not only the descriptor:
  `dev_event_to_col()` reads `col_map`, and `valid_vpe()` reads
  `vpe->col_idx`.
- `col_map` ordering around a send: `its_irq_domain_activate()` writes it
  before `its_send_mapti()`; `its_set_affinity()` writes it after
  `its_send_movi()`.
