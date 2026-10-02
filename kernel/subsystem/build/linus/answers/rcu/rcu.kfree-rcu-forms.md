| Form | Handed | Context |
|---|---|---|
| `kfree_rcu(ptr, rhf)`, `kvfree_rcu(ptr, rhf)` | object and name of its head field | atomic, irqs off, `raw_spinlock_t` held; not NMI |
| `kfree_rcu_mightsleep(ptr)`, `kvfree_rcu_mightsleep(ptr)` | object only | sleepable only |
| `kfree_rcu_nolock(ptr, kvrhf)` | object and name of its `struct kvfree_rcu_head` field | any, including NMI |

- `kfree_rcu()` and `kvfree_rcu()`: the same macro, `kvfree_rcu_arg_2()`; no
  difference in context or in what may be passed.
- `kfree_rcu_nolock()`: calls `kfree_call_rcu_nolock()` in `mm/slab_common.c`;
  two-argument only; there is no kvfree or headless nolock form.
- `kfree_rcu_nolock()` on a vmalloc, large-kmalloc or remote-node object: not
  queued directly; `defer_kfree_rcu()` hands it to `irq_work`, which calls
  `kvfree_call_rcu()`.
- `struct kvfree_rcu_head` in `include/linux/types.h`: one pointer under
  `CONFIG_KVFREE_RCU_BATCHED`, a wrapped `struct rcu_head` otherwise. There is
  no struct rcu_ptr.
- Field type for `kfree_rcu()` and `kvfree_rcu()`: `struct rcu_head` or
  `struct kvfree_rcu_head`; `kvfree_rcu_arg_2()` casts the field's address, so
  the compiler checks neither.
- Field type for `kfree_rcu_nolock()`: `struct kvfree_rcu_head` only; the
  address is passed uncast.
- Object freed by both `kfree_rcu()` and `kfree_rcu_nolock()`: a union of the
  two head types, as `struct test_kfree_rcu_struct` in
  `lib/tests/slub_kunit.c`.
- Offset limit: `BUILD_BUG_ON(offsetof(typeof(*(ptr)), kvrhf) >= 4096)` in
  `kvfree_rcu_arg_2()` and in `kfree_rcu_nolock()`.
- There is no __is_kvfree_rcu_offset() here, and the offset is not stored in
  the head's `func`.
- Reason for the limit: `kvmalloc_obj_start_addr()` in `mm/slab.h` recovers
  the object start from the head address alone; for vmalloc and large-kmalloc
  objects it subtracts `offset_in_page()`, so the head must lie in the first
  page.
