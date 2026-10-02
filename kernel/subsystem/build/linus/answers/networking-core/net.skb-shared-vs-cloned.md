- `skb_cloned()`: tests `skb->cloned` and that the low half of `dataref` is not
  1. Nothing clears `cloned` on the survivor when its sibling is freed, so the
  bit alone does not say the data is shared.
- `cb[]`: each clone has its own; `__copy_skb_header()` copies the contents at
  clone time.
- `pskb_expand_head()` in `net/core/skbuff.c`: has `BUG_ON(skb_shared(skb))` and
  accepts a clone. Helpers that reallocate the head through it inherit both,
  for example `skb_cow_head()`, `skb_unclone()`, `skb_ensure_writable()` and
  `__pskb_pull_tail()`.
- `CONFIG_FAIL_SKB_REALLOC`: when the fault attribute fires,
  `skb_might_realloc()` calls `pskb_expand_head()` from
  `pskb_may_pull_reason()`, `pskb_trim()` and `pskb_trim_rcsum()` even when the
  bytes are already linear, so the `BUG_ON()` and the stale-pointer cases can
  be reached on any call.
