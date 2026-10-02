- Fragmented transfers (`fraglen` below `len`): accepted; `fraglen > len` and
  `fraglen` above `KVM_FFA_MBOX_NR_PAGES * PAGE_SIZE` are refused, with
  `FFA_RET_INVALID_PARAMETERS`. The rest arrives through
  `do_ffa_mem_frag_tx()`.
- `addr_range_cnt` and `total_pg_cnt`: not read by `__do_ffa_mem_xfer()`; the
  range count comes from `fraglen` and `composite_off`.
- Minimum `fraglen`: `FFA_MEM_REGION_SZ(hyp_ffa_version)` plus
  `ffa_emad_size_get(hyp_ffa_version)`, both in `include/linux/arm_ffa.h`;
  smaller than the `sizeof` of the two structs below `FFA_VERSION_1_2`.
- `ep_mem_offset`: bounded; the result of `ffa_mem_desc_offset()` plus
  `ffa_emad_size_get()` must not exceed `fraglen`, tested in 64 bits before
  `composite_off` is read.
- Also refused with `FFA_RET_INVALID_PARAMETERS`: non-zero x3 or non-zero low
  32 bits of x4, `sender_id` other than `HOST_FFA_ID`, no `host_buffers.tx`.
- `len > ffa_desc_buf.len`: `FFA_RET_NO_MEMORY`; `do_ffa_mem_reclaim()` needs
  the whole descriptor to fit there later.
- `hyp_buffers.tx`: the copy that is checked is also the one EL3 reads; it is
  the buffer `ffa_map_hyp_buffers()` registered. EL3 never sees
  `host_buffers.tx`.
- Not checked in the copy: receiver id, permissions, `attributes`, `flags`,
  `tag`, `handle`. The proxy filters on page ownership.
