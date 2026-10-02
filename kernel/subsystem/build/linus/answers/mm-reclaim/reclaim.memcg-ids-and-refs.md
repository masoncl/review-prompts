| Identifier | Read / lookup | After removal |
|---|---|---|
| private ID, `memcg->id.id`, 1 to `MEM_CGROUP_ID_MAX` | `mem_cgroup_private_id()` / `mem_cgroup_from_private_id()` | valid until `id.ref` reaches 0, then erased and reusable |
| cgroup ID, u64 | `mem_cgroup_id()` / `mem_cgroup_get_from_id()` | lookup fails once the kernfs node is not active or `cgroup_tryget()` fails |
| css ID, `memcg->css.id` | `css_from_id()` | lookup returns NULL from `css_release_work_fn()`; number freed in `css_free_rwork_fn()` |
| `memcg->kmemcg_id` | list_lru xarray index | copy of the private ID; -1 for root or when `mem_cgroup_kmem_disabled()` |

- `mem_cgroup_id()`: returns `cgroup_id()`, not the short ID.
- There is no mem_cgroup_idr, mem_cgroup_from_id() or
  mem_cgroup_id_get_many() here; the store is the xarray
  `mem_cgroup_private_ids` in `mm/memcontrol.c`.
- Private ID publication: reserved in `mem_cgroup_alloc()`, stored only at
  the end of `mem_cgroup_css_online()`; lookup returns NULL before that and
  for ID 0.
- Private ID base reference: dropped as the last step of
  `mem_cgroup_css_offline()`.
- At `id.ref` zero: `mem_cgroup_private_id_put()` erases the entry, sets
  `id.id` to 0 and drops the css reference the ID held.
- `mem_cgroup_private_id_get_online()`: takes the references on the memcg or
  on the nearest ancestor whose `id.ref` is not zero, and returns that one;
  its callers are `__mem_cgroup_try_charge_swap()` and `__memcg1_swapout()`.
- `mem_cgroup_get_from_id()`: searches the default hierarchy only, within the
  caller's cgroup namespace, and returns the memcg of the effective css,
  which can be an ancestor; `run_cmd()` in `mm/vmscan.c` compares
  `mem_cgroup_id()` afterwards.
- `mem_cgroup_from_private_id()` result may be NULL; `mem_cgroup_tryget()`
  returns true for NULL, so a NULL test is still needed before the result is
  dereferenced.
- `css_tryget(&memcg->css)`: needs the NULL test before it.
- **Unsafe usage**: dereferencing the `mem_cgroup_from_private_id()` result
  after `rcu_read_unlock()` with no css reference.
  - Safe: `mem_cgroup_tryget()` inside RCU plus a NULL test,
    `mem_cgroup_put()` later, as `workingset_test_recent()` does.
  - Safe: NULL test then `css_tryget_online()`, falling back to
    `get_mem_cgroup_from_mm()`, as `mem_cgroup_swapin_charge_folio()` does.
  - Safe: all use inside the RCU section with no tryget, as
    `__mem_cgroup_uncharge_swap()` does; the swap record's ID reference pins
    the css until `mem_cgroup_private_id_put()`.
