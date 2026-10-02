- `vlag` and `vprot`: two separate members of `struct sched_entity`; they
  share no storage.
- `se->vlag` of a queued entity: the stale value from the last
  `update_entity_lag()` or `reweight_eevdf()`, not a protection value.
- Each rbtree node carries three subtree values: `min_vruntime`, `min_slice`
  and `max_slice`; see `min_vruntime_update()`.
- `cfs_rq_max_slice()`: reads `max_slice` of the root node and `curr->slice`.
- `entity_lag()`: clamps to plus or minus
  `calc_delta_fair(cfs_rq_max_slice(cfs_rq) + TICK_NSEC, se)`; the limit
  depends on the longest slice queued, not on `se->slice`.
- `calc_delta_fair()`: scales by `se->h_load`, so the clamp follows the
  hierarchical weight.
- `update_entity_lag()` on a `sched_delayed` entity: the new lag is not
  below the stored `se->vlag`, and with `DELAY_ZERO` not above 0.
- `update_entity_lag()`: returns true when the stored lag differs from
  `avg_vruntime() - se->vruntime`; `requeue_delayed_entity()` then places
  the entity again.
- `rescale_entity()`: called from `reweight_eevdf()`; scales `vlag`, a
  relative `deadline` and a relative `vprot` by old over new `h_load` weight.
