- `slab_post_alloc_hook()`: calls `kmemleak_alloc_recursive()` only when
  `alloc_flags_allow_spinning(ac->alloc_flags)`; the test is on the slab
  alloc flags, not on gfp.
- Unregistered therefore: `kmalloc_nolock()` objects and internal
  `kmalloc_flags()` requests made with `SLAB_ALLOC_NOLOCK`.
- There is no __GFP_NOLEAKTRACE here; the other slab-side test is
  `SLAB_NOLEAKTRACE` on the cache, in `kmemleak_alloc_recursive()`.
- On an object that was never registered:

| Function | Lookup | Result | Locks taken |
|---|---|---|---|
| `kmemleak_free()` | `find_and_remove_object()` | silent return | `kmemleak_lock` |
| `kmemleak_not_leak()` | `paint_ptr()` | silent return | `rcu_read_lock()`, `kmemleak_lock` |
| `kmemleak_ignore()` | `paint_ptr()` | silent return | `rcu_read_lock()`, `kmemleak_lock` |
| `kmemleak_no_scan()` | `object_no_scan()` | `kmemleak_warn()` | `rcu_read_lock()`, `kmemleak_lock` |

- `delete_object_full()`: has no warning for an unknown object in any
  configuration.
- `kmemleak_lock`: one raw spinlock, taken on these paths with
  `raw_spin_lock_irqsave()`; there is no read side and no trylock.
- **Potentially unsafe usage**: a kmemleak call on a pointer from a no-spin
  allocation.
  - Unsafe: from a context that may not spin; the lookup spins on
    `kmemleak_lock` even though the object is unknown.
  - Unsafe: `kmemleak_no_scan()`; it prints a warning and a stack dump for
    the unknown object.
  - Safe: `kmemleak_not_leak()` behind `if (allow_spin)`, as in
    `alloc_slab_obj_exts()`.
  - Safe: `kmemleak_free()` and `kmemleak_ignore()` where spinning is
    allowed, as `kfree()` and `kvfree_call_rcu()` do; both return silently.
