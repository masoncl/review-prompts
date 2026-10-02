- One competition: `pick_next_entity(rq, protect)` runs `pick_eevdf()` on
  `rq->cfs` only; eligibility and deadlines compare tasks of all groups.
- `pick_eevdf()` early returns, in order:

| Test | Returns |
|---|---|
| `cfs_rq->h_nr_queued == 1` | `curr` if on_rq, else the leftmost |
| `PICK_BUDDY`, `protect`, `cfs_rq->next` set and eligible | `cfs_rq->next` |
| `curr` on_rq and eligible, `protect`, `protect_slice(curr)` | `curr` |

- Buddy test: lives in `pick_eevdf()`, not in `pick_next_entity()`; it comes
  before the slice protection of `curr`.
- Leftmost eligible entity: skips the tree search but not the final
  comparison; `curr` is returned instead if `entity_before(curr, best)`.
- `protect` false: skips both the buddy and the slice protection;
  `wakeup_preempt_fair()` passes false for `PREEMPT_WAKEUP_SHORT`,
  `pick_task_fair()` passes true.
- `protect_slice()`: true while `se->vruntime` is before `se->vprot`; it
  does not compare `vlag` with `deadline`.
- `set_protect_slice()`: with `PREEMPT_SHORT` and, under `RUN_TO_PARITY`, a
  shorter slice queued, `vprot` is capped at `ineligible_vruntime()`, the
  point where `curr` stops being eligible.
- `set_next_buddy()`: refuses an entity for which `se_is_idle()` is true.
- Delayed pick: `pick_next_entity()` calls `__dequeue_task()` with
  `DEQUEUE_SLEEP | DEQUEUE_DELAYED` and returns NULL.
- **Unsafe usage**: calling `pick_next_entity()` when `rq->cfs.h_nr_queued`
  may be 0; it dereferences the result of `pick_eevdf()` unchecked.
  - Safe: test `h_nr_queued` first and retry on NULL, as `pick_task_fair()`
    and `wakeup_preempt_fair()` do.
