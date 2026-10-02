- `skb_unshare()`: copies with `skb_copy()`, not `pskb_copy()`.
- `skb_unshare()` failure: also happens with memory available, when
  `skb_copy()` refuses unreadable frags or `SKB_GSO_FRAGLIST`. The original is
  freed with `kfree_skb()` in that case too.
- `skb_share_check()`: the clone has the same `head` and `data`, so pointers
  into packet data stay valid. Only the `struct sk_buff` pointer changes.
- `skb_unclone()`: makes the head and `struct skb_shared_info` private. Page
  frags stay shared with the former clone by page reference, and each
  `frag_list` member gets `skb_get()`, so it becomes `skb_shared()`.
