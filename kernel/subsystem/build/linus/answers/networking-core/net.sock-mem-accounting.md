- Unit of forward allocation: `PAGE_SIZE`, rounded by `sk_mem_pages()`; there
  is no SK_MEM_QUANTUM in this tree.
- `sk_bypass_prot_mem` set: `__sk_mem_raise_allocated()` and
  `__sk_mem_reduce_allocated()` leave the protocol's `memory_allocated` alone
  and skip the `sysctl_mem` limits; only the memory cgroup, if enabled for the
  socket, is charged.
- `sk_mem_reclaim()`: acts when `sk_forward_alloc` minus
  `sk_unused_reserved_mem()` is `>= PAGE_SIZE`; `sk_unused_reserved_mem()` is
  `sk_reserved_mem` less `sk_wmem_queued` and `sk_rmem_alloc`, not
  `sk_reserved_mem` itself.
- `__sk_mem_reclaim()`: gives back whole pages only; the remainder under
  `PAGE_SIZE` stays in `sk_forward_alloc`.
- `sk_stream_kill_queues()`: warns on `sk_wmem_queued` and on a non-empty write
  queue, not on `sk_forward_alloc`; `inet_sock_destruct()` warns on
  `sk_rmem_alloc`, `sk_wmem_alloc`, `sk_wmem_queued` and `sk_forward_alloc`.
- Which counters lose `skb->truesize` when a charged buffer is released:

| Released by | Subtracts `truesize` from |
|---|---|
| `sock_rfree()` | `sk_rmem_alloc`, then `sk_mem_uncharge()` |
| `sock_wfree()` | `sk_wmem_alloc` |
| `tcp_wmem_free_skb()` (TCP write and retransmit queues) | `sk_wmem_queued`, then `sk_mem_uncharge()`; for a `skb_zcopy_pure()` buffer the uncharge is `SKB_TRUESIZE(skb_end_offset(skb))` |
| `udp_skb_destructor()` (called at dequeue in `__skb_recv_udp()`) | uses `udp_skb_truesize()`, a copy taken at enqueue, not `skb->truesize` |

- **Potentially unsafe usage**: writing `skb->truesize` of a buffer that is
  charged to a socket.
  - Unsafe: when the counters in the table above are not changed by the same
    delta; the free path subtracts the new value and `inet_sock_destruct()`
    warns on the residue.
  - Safe: same delta applied to the same counters: `tcp_try_coalesce()` for
    `sock_rfree()` buffers, `skb_expand_head()` for `is_skb_wmem()` buffers,
    `tcp_trim_head()` for the TCP write queue.
  - Safe: moving bytes between two buffers charged to the same socket, as
    `tcp_fragment()` does.
  - Safe: before the charge, as `skb_condense()` runs ahead of
    `skb_set_owner_r()` in `tcp_data_queue_ofo()` and ahead of
    `sk_add_backlog()` in `tcp_add_backlog()`.
- `___pskb_trim()` in `net/core/skbuff.c`: calls `skb_condense()` only under
  the test that lets `pskb_expand_head()` change `truesize`, `!skb->sk` or
  destructor `sock_edemux()`.
- `__skb_unclone_keeptruesize()`: restores the saved `truesize` after
  `pskb_expand_head()`; TCP uses it on write-queue buffers.
