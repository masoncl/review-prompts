- list_empty_rcu() and list_first_entry_rcu(): not defined. Readers call
  `list_empty()`, which is one `READ_ONCE()`.
- **Potentially unsafe usage**: in a reader, `list_empty()` followed by
  `list_first_entry()`.
  - Unsafe: when nothing excludes writers between the two calls;
    `list_first_entry()` loads `next` again and can return the head.
  - Safe: with the update-side lock held across both calls, as
    `mt76_txq_schedule_pending()` in
    `drivers/net/wireless/mediatek/mt76/tx.c` does under `phy->tx_lock`
    although it is inside `rcu_read_lock()`.
  - Safe: `list_first_or_null_rcu()`, one load, NULL when empty.
- `INIT_LIST_HEAD()`: the same two `WRITE_ONCE()` stores as
  `INIT_LIST_HEAD_RCU()` in this tree.
- `list_first_entry_or_null()`: one `READ_ONCE()` of `next`, not two plain
  loads.
- `hlist_del_init()` on a reader-visible node: sets `next` to NULL, so a reader
  standing on the node ends its walk early and silently misses the rest of the
  chain.
- Splice helpers, by which list readers may see:

| Helper | Source list | Destination | Blocks |
|---|---|---|---|
| `list_splice_rcu()` | must not be visible to readers | may be traversed | no |
| `list_splice_init_rcu()` | may be traversed | may be traversed | yes, calls `sync()` |
| `list_splice_tail_init_rcu()` | may be traversed | may be traversed | yes, calls `sync()` |
