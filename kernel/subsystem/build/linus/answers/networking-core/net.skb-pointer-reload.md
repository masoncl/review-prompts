- `CONFIG_FAIL_SKB_REALLOC` (`lib/Kconfig.debug`, needs
  `FAULT_INJECTION_DEBUG_FS`): the debugging aid. `skb_might_realloc()` in
  `net/core/skb_fault_injection.c` calls
  `pskb_expand_head(skb, 0, 0, GFP_ATOMIC)` when the fault attribute fires.
- `skb_might_realloc()` call sites: `pskb_may_pull_reason()`, `pskb_trim()`
  and `pskb_trim_rcsum()`, before their fast-path tests. It is not called
  from `__pskb_pull_tail()`.
- `skb_might_realloc()` controls: debugfs directory `fail_skb_realloc` with a
  `devname` filter file, and the `fail_skb_realloc=` boot parameter.
- `__pskb_pull_tail()`: calls `pskb_expand_head()` when tailroom is short or
  when `skb_cloned()`, even with enough tailroom.
- `pskb_trim()` without the fault injection: reaches `pskb_expand_head()`
  only via `___pskb_trim()`, so only when `skb->data_len` is non-zero and the
  skb is cloned.
- `skb_realloc_headroom()`: reallocates a clone or copy and returns it; the
  head of the skb passed in is untouched.
- Further direct callers of `pskb_expand_head()` that are easy to miss:
  `__skb_grow()`, `__skb_pad()`, `skb_ensure_writable_head_tail()`. Search
  for `pskb_expand_head(` and `__pskb_pull_tail(` for the rest.
- `skb_header_pointer()` result: points into the head when the bytes were
  linear, so it goes stale like any other pointer.
