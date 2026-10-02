- `NF_STOLEN`: `nf_hook_slow()` returns `NF_DROP_GETERR(verdict)`, which is 0
  for a plain steal and a negative errno when the hook used
  `NF_DROP_REASON()`. In the second case the hook has already freed the
  buffer.
- `NF_QUEUE`, queueing failed: `nf_queue()` frees with `kfree_skb()` and
  returns 0, so `nf_hook_slow()` returns 0, not the error.
- `NF_QUEUE`, bypass: continues with the next hook only when `__nf_queue()`
  returned `-ESRCH` and `NF_VERDICT_FLAG_QUEUE_BYPASS` is set. Any other
  queueing error frees the buffer even with the flag.
- `NF_REPEAT` and `NF_STOP`: `nf_hook_slow()` has no case for them. The
  default case does `WARN_ON_ONCE(1)` and returns 0 without freeing the
  buffer.
- `nf_reinject()` in `net/netfilter/nfnetlink_queue.c`: the place that
  handles `NF_REPEAT` (runs the hook again) and `NF_STOP` (calls okfn, like
  `NF_ACCEPT`).
- `NF_HOOK()`: frees nothing itself. On 1 from `nf_hook()` it returns
  whatever okfn returns, so the buffer is gone on accept only if okfn consumes
  it.
- `NF_HOOK_LIST()`: never calls okfn. Buffers that got 1 stay on the list for
  the caller; the others are removed from it.
