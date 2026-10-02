- Fields: `zero_vruntime`, `sum_w_vruntime` (sum of key times weight) and
  `sum_weight`, plus `curr` when it is on_rq.
- Weights in the sums: `avg_vruntime_weight(cfs_rq, se->h_load.weight)`; not
  `se->load.weight`, and not passed through `scale_load_down()`.
- `avg_vruntime()` writes: it calls `update_zero_vruntime()` with the
  computed offset and returns the new `cfs_rq->zero_vruntime`.
- `zero_vruntime` moves on every `avg_vruntime()` call: `place_entity()`,
  `update_entity_lag()`, `update_deadline()` once the deadline is passed,
  `reweight_eevdf()` for a queued entity, `update_protect_slice()` and
  `print_cfs_rq()`.
- `place_entity()`: also calls `update_zero_vruntime()` directly when the
  placed entity is heavier than everything queued.
- `__enqueue_entity()` and `__dequeue_entity()`: do not move
  `zero_vruntime`.
- `entity_tick()`: moves `zero_vruntime` only through `update_curr()`, when
  `update_deadline()` finds the deadline passed.
- `vruntime_eligible()`: reads the same fields and writes nothing.
- `update_zero_vruntime(cfs_rq, delta)`: takes the shift and compensates
  `sum_w_vruntime` itself; there is no avg_vruntime_update().
- `sum_w_vruntime_add()` and `sum_w_vruntime_sub()`: the only writers of the
  sums besides the shift; called from `__enqueue_entity()` and
  `__dequeue_entity()`. There is no avg_vruntime_add() or
  avg_vruntime_sub().
- `reweight_eevdf()`: the function that takes a queued entity out, changes
  `h_load` and `vruntime`, and puts it back.
- `cfs_rq->sum_shift`: with `PARANOID_AVG`, an overflow in
  `sum_w_vruntime_add_paranoid()` raises it and rebuilds both sums from the
  tree.
- **Unsafe usage**: adding `se->h_load.weight` to `sum_weight` or a
  comparison without `avg_vruntime_weight()`.
  - Safe: take every weight through `avg_vruntime_weight()`, as
    `vruntime_eligible()` and `place_entity()` do; it applies `sum_shift`
    under `CONFIG_64BIT`.
