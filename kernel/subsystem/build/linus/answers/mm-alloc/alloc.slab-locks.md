- Order: as in the comment at the top of `mm/slub.c`: `cpu_hotplug_lock`,
  `slab_mutex`, `cpu_sheaves->lock`, `barn->lock`, `list_lock`,
  `slab_lock()`, `object_map_lock`. There is no cpu_slab lock.
- `flush_lock`: a mutex in `mm/slub.c` that the comment omits; taken inside
  `cpu_hotplug_lock` and `slab_mutex`, see `flush_all_rcu_sheaves()`.

| Lock | Kind | Only tried |
|---|---|---|
| `cpu_sheaves->lock` | `local_trylock_t` | in every alloc and free path |
| `barn->lock` | `spinlock_t`, irqsave | when `allow_spin` is false |
| `list_lock` | `spinlock_t`, irqsave | when `allow_spin` is false |
| `slab_lock()` | bit spinlock on `SL_locked` | never |
| `object_map_lock` | `spinlock_t` | never |

- `cpu_sheaves->lock`: also taken with `local_lock()`, in flush and prefill
  code; search `mm/slub.c` for `local_lock(&s->cpu_sheaves->lock)`. Those
  sites must not run in a context that can interrupt a holder.
- `allow_spin`: comes from `alloc_flags_allow_spinning()` or
  `free_flags_allow_spinning()` in `mm/slab.h`, that is `SLAB_ALLOC_NOLOCK`
  or `SLAB_FREE_NOLOCK`. `mm/slub.c` does not call
  `gfpflags_allow_spinning()`.
- `allow_spin` false does not prove a nolock context:
  `__refill_objects_any()` passes false to `__refill_objects_node()` from
  normal context, to skip a contended remote `list_lock`.
- Functions with no trylock form, for example: `__slab_free()`,
  `free_to_partial_list()`, `barn_put_empty_sheaf()`,
  `barn_put_full_sheaf()`, `barn_get_full_or_empty_sheaf()`. A nolock path
  must not reach them; `kfree_nolock()` uses `defer_free()` instead of
  `__slab_free()`.
- `slab_lock()`: one caller, `__update_freelist_slow()`, reached when the
  cache lacks `__CMPXCHG_DOUBLE`. Debug caches change the freelist under
  `list_lock` and do not take `slab_lock()`.
- `slab_update_freelist()`: wraps the slow path in `local_irq_save()` on
  every configuration. `__slab_update_freelist()` expects the caller to have
  IRQs off, and asserts it only without `CONFIG_PREEMPT_RT`.
- `CONFIG_PREEMPT_RT`: `kvfree_call_rcu()` skips `kfree_rcu_sheaf()`;
  `__kfree_rcu_sheaf()` has a `VM_WARN_ON_ONCE()` for being called there
  with spinning allowed.
