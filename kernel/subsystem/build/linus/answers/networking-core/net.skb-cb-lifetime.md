- `skb_orphan()`: does not write `skb->cb`; it runs `skb->destructor` at that
  moment, so a destructor can run long before the buffer is freed and sees
  whatever the current holder has put in `cb`.
- Destructor reading `cb`: done in-tree by `unix_wfree()` in
  `net/unix/af_unix.c`, installed by `unix_scm_to_skb()`; it calls
  `unix_destruct_scm()`, which reads `UNIXCB()`.
- `skb_scrub_packet()`: leaves `cb` alone, and calls `skb_ext_reset()`.
- skb extensions: do not always survive until free; `skb_ext_reset()` drops
  them, for example in `skb_scrub_packet()` and `napi_reuse_skb()`.
- `enum skb_ext_id`: every id is under its own configuration option; there is
  no general-purpose id. Without `CONFIG_SKB_EXTENSIONS` the enum is not
  defined, `skb_ext_reset()`, `skb_ext_del()`, `skb_ext_put()` and
  `skb_ext_copy()` are empty stubs, and `skb_ext_add()` and `skb_ext_find()`
  are not declared.
- `skb->sk` and `skb->destructor`: both cleared by `skb_orphan()`, and by
  `skb_steal_sock()` except in its syncookie request-sock branch.
- `skb_shinfo(skb)->destructor_arg`: lives in `struct skb_shared_info`, so
  every clone sees the same value; it shares a union with `xdp_frags_size`
  and `xdp_frags_truesize`.
- `msg_zerocopy_alloc()` in `net/core/skbuff.c`: keeps
  `struct ubuf_info_msgzc` in the `cb` of a buffer from `sock_omalloc()` that
  is handed to no other layer while the `struct ubuf_info` is referenced;
  `destructor_arg` of the data buffers points into that `cb`.
- `__skb_gso_segment()`: overwrites `cb` from `SKB_GSO_CB_OFFSET` (32) on;
  state carried across segmentation has to fit below it, as the
  `BUILD_BUG_ON()` in `ip_finish_output_gso()` checks.
- `skb_segment()`: copies the original's `cb` into every segment through
  `__copy_skb_header()`.
