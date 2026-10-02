- `struct memcg_stock_pcp`: `NR_MEMCG_STOCK` slots, `cached[]` and
  `nr_pages[]`. `nr_pages[]` is `uint8_t`.
- `struct obj_stock_pcp`: a separate per-CPU `obj_stock` with its own lock and
  `NR_OBJ_STOCK` slots, `cached[]` and `nr_bytes[]`.
- Slab stat deltas in `struct obj_stock_pcp`: held for one slot and one node
  at a time, named by `index` and `node_id`.
- Css reference: dropped in `drain_stock()` and also in `consume_stock()`
  when it takes a slot to zero pages and clears the slot.
- Objcg reference: taken in `__refill_obj_stock()`, dropped in
  `drain_obj_stock_slot()`.
- Full stock: `refill_stock()` evicts round robin through `drain_idx`, not at
  random. `__refill_obj_stock()` does the same.
- `refill_stock()`: uncharges directly when `nr_pages` exceeds
  `MEMCG_CHARGE_BATCH` or the trylock fails.
- `!gfpflags_allow_spinning()`: `try_charge_memcg()` charges exactly
  `nr_pages`, so nothing is refilled.
- `drain_all_stock()`: returns without draining when `percpu_charge_mutex` is
  already held.
- `drain_all_stock()`: does not wait for remote work and skips isolated
  remote CPUs, so stocks can be non-empty on return.
- Remote drain: `schedule_drain_work()` uses `queue_work_on()` on `memcg_wq`.
- Work functions: `drain_local_memcg_stock()` and `drain_local_obj_stock()`.
  There is no drain_local_stock() here.
- CPU selection: `is_memcg_drain_needed()` wants a slot with nonzero pages in
  the target subtree. The work then drains every slot of that CPU.
- CPU hotplug: `memcg_hotplug_cpu_dead()` calls `drain_obj_stock()` and
  `drain_stock_fully()` directly. It does not call `drain_all_stock()`.
- `drain_all_stock()`: also called from `mm/memcontrol-v1.c`, for example
  `mem_cgroup_resize_max()`.
