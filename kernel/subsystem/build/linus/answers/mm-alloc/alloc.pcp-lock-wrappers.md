- There is no pcp_trylock_prepare(), pcp_trylock_finish() or
  pcp_spin_lock_maybe_irqsave() here. `pcp_spin_trylock(ptr)` takes one
  argument and no flags.

| Wrapper | `CONFIG_SMP` | `!CONFIG_SMP` |
|---|---|---|
| `pcp_spin_trylock()` | `pcpu_task_pin()`, `this_cpu_ptr()`, `spin_trylock()`; unpins and gives NULL on failure | always `NULL` |
| `pcp_spin_unlock()` | `spin_unlock()`, `pcpu_task_unpin()` | `BUG_ON(1)` |
| `pcp_spin_lock_nopin()` | `spin_lock(&(ptr)->lock)` only | same |
| `pcp_spin_unlock_nopin()` | `spin_unlock(&(ptr)->lock)` only | same |

- `pcpu_task_pin()`: `preempt_disable()` without `CONFIG_PREEMPT_RT`,
  `migrate_disable()` with it.
- Uniprocessor: no wrapper disables IRQs. Every allocation takes
  `rmqueue_buddy()` and every free takes `free_one_page()`, except that
  `__free_frozen_pages()` with `FPI_NOLOCK` and `can_spin_trylock()` false
  calls `add_page_to_zone_llist()` directly.
- Uniprocessor lists stay empty: the only code that adds a page,
  `free_frozen_page_commit()` and `rmqueue_bulk()` from
  `__rmqueue_pcplist()`, runs after a successful `pcp_spin_trylock()`.
- `pcp_spin_lock_nopin()` callers hold the pcp pointer of one given CPU,
  which may be a remote one: `__drain_all_pages()` calls
  `drain_pages_zone()` for each CPU in its mask from the calling CPU.
- Pairing: `pcp_spin_unlock()` also unpins, so it pairs only with
  `pcp_spin_trylock()`; `pcp_spin_unlock_nopin()` pairs only with
  `pcp_spin_lock_nopin()`.
- Lock order: `zone->lock` nests inside the pcp lock, taken irqsave, in
  `rmqueue_bulk()` and `free_pcppages_bulk()`.
- **Potentially unsafe usage**: taking the lock with
  `pcp_spin_lock_nopin()`.
  - Unsafe: from hard or soft IRQ context. `pcp_spin_trylock()` holders keep
    IRQs enabled, so the spin can interrupt the holder on the same CPU and
    never finish.
  - Safe: from task context, as `drain_pages_zone()` and `decay_pcp_high()`
    do; an IRQ that arrives meanwhile uses `pcp_spin_trylock()`, fails, and
    falls back to the buddy lists.
- **Unsafe usage**: calling `pcp_spin_unlock()` after
  `free_frozen_page_commit()` returned false.
  - Safe: test the return value and treat the lock as gone, as
    `__free_frozen_pages()` does; `free_unref_folios()` also resets its
    `pcp` and `locked_zone`.
