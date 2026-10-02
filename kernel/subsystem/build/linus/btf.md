# BTF Special Fields in BPF Maps

## Main structures

### Objects and how they relate

- There is no struct btf_field_offs in this tree, and no separate offset
  table. `bpf_obj_memcpy()` and `bpf_obj_memzero()` in
  `include/linux/bpf.h` walk `rec->fields[]` directly and rely on it being
  sorted by offset.
- Map keys: no record describes a key; `map_check_btf()` parses only the
  value type.
- `struct btf_field`: one entry per occurrence, with offsets relative to the
  outermost value. Fields inside nested structs and arrays are flattened by
  `btf_find_nested_struct()` and `btf_repeat_fields()`, and every entry counts
  against `BTF_FIELDS_MAX`.
- `struct btf_struct_meta`: exists only for user-loaded BTF;
  `btf->struct_meta_tab` is set to a table only in `btf_parse()`, so kernel
  and module BTF have no table.
- Program to `struct btf_struct_meta`: `bpf_fixup_kfunc_call()` in
  `kernel/bpf/verifier.c` patches the address of the meta into the instruction
  stream as a hidden kfunc argument, for example for `bpf_obj_new()` and
  `bpf_obj_drop()`. A loaded program therefore points into the BTF's table.
- `struct btf_field_kptr`, BTF reference: held only when
  `btf_is_kernel(kptr.btf)`. For a local type `kptr.btf` is the BTF the record
  was parsed from, with no reference taken; see `btf_parse_kptr()`,
  `btf_record_dup()` and `btf_record_free()`.
- `struct btf_field_kptr`, module reference: taken only for `BPF_KPTR_REF`
  whose type is in module BTF; `kptr.module` is NULL for the other kptr kinds.
- Copies of a map record: two places call `btf_record_dup()`.
  `bpf_map_meta_alloc()` in `kernel/bpf/map_in_map.c` makes the inner-map
  template. `bpf_ma_set_dtor()` in `kernel/bpf/hashtab.c` makes a copy held in
  `struct htab_btf_record`, used as the `struct bpf_mem_alloc` destructor
  context of non-preallocated hash maps and of `BPF_MAP_TYPE_RHASH` maps.
- A copied record still borrows from the program BTF: `graph_root.value_rec`
  and a local-type `kptr.btf` are copied as plain pointers.
  `btf_record_dup()` does not pin that BTF; `bpf_map_meta_alloc()` takes its
  own `btf_get()` on `inner_map->btf` for this reason.
- Ownership cycles: `btf_check_and_fixup_fields()` does not check them. It
  validates `BPF_UPTR` pointees and fills `graph_root.value_rec`.
- `btf_check_ownership_depth()` in `kernel/bpf/btf.c`: run by `btf_parse()`
  after every struct-meta record is fixed up; rejects cycles and chains deeper
  than `BTF_MAX_OWNERSHIP_DEPTH` with `-ELOOP`.
- Ownership edges counted by `btf_owned_type_idx()`: graph roots, and
  `BPF_KPTR_REF` or `BPF_KPTR_PERCPU` fields that point at a local type that
  has a `struct btf_struct_meta`.
- Map records are not part of the ownership-depth walk; it covers only the
  struct-meta table of the BTF being loaded.

## Field kinds and the record

**Field kinds**

- `BPF_RES_SPIN_LOCK`: a kind of its own (`struct bpf_res_spin_lock`); holds
  nothing; `bpf_obj_free_fields()` does nothing for it.
- `BPF_TASK_WORK`: a kind (`struct bpf_task_work`); holds a reference on a
  `struct bpf_task_work_ctx`; released by `bpf_task_work_cancel_and_free()`.
- `BPF_GRAPH_NODE`: `BPF_RB_NODE | BPF_LIST_NODE` only; `BPF_REFCOUNT` is not
  part of it.
- `BPF_UPTR`: not part of `BPF_KPTR`; code that means both passes
  `BPF_KPTR | BPF_UPTR`, as `check_mem_access()` does.
- Map value: may hold every kind except `BPF_LIST_NODE` and `BPF_RB_NODE`; see
  the mask in `map_check_btf()`.
- Allocated object: may hold locks, graph roots and nodes, `BPF_REFCOUNT` and
  `BPF_KPTR`; not `BPF_TIMER`, `BPF_WORKQUEUE`, `BPF_TASK_WORK` or `BPF_UPTR`;
  see the mask in `btf_parse_struct_metas()`.
- Kind outside the mask: `btf_get_field_type()`, or `btf_find_kptr()` for a
  tagged pointer, ignores it, so the member is not recorded and is treated as
  plain data.

**The field record**

- `map->record`: built inside `map_check_btf()`, which `map_create_alloc()`
  calls after `ops->map_alloc()`; it is `NULL` while `map_alloc` runs.
- Map created without `attr->btf_value_type_id`: `map_check_btf()` is not
  called and `map->record` stays `NULL`.
- Map type that needs the record at setup: uses its `map_check_btf` op, as
  `htab_map_check_btf()` does.
- `struct btf_record`: also caches `res_spin_lock_off` and `task_work_off`;
  each cached offset is `-EINVAL` when the kind is absent.
- `btf_parse_struct_metas()`: gives a struct an entry only if a direct member
  has, as its type id, one of the structs named in `alloc_obj_fields` or a
  kptr-tagged pointer.
- `btf_find_struct_meta()`: returns `NULL` for any other type; callers such as
  `bpf_obj_free_fields()` and `reg_btf_record()` then use a `NULL` record.
- Record in a `struct btf_struct_meta`: never `NULL` or an error;
  `btf_parse_struct_metas()` fails the BTF load instead.

**Map types per field kind**

- `BPF_MAP_TYPE_RHASH`: allowed for the lock kinds, for `BPF_TIMER`,
  `BPF_WORKQUEUE`, `BPF_TASK_WORK`, and for the kptr kinds and `BPF_REFCOUNT`;
  not for `BPF_LIST_HEAD` or `BPF_RB_ROOT`.
- `BPF_TASK_WORK`: same map types as `BPF_TIMER` and `BPF_WORKQUEUE`.
- `BPF_MAP_TYPE_CGROUP_STORAGE`: listed only for the lock kinds.
- `BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`: listed for no kind.
- `BPF_F_LOCK` update of an existing key in `htab_map_update_elem()`: both
  in-place paths return after `copy_map_value_locked()` and do not call
  `bpf_obj_cancel_fields()`; `array_map_update_elem()` and
  `rhtab_map_update_existing()` call it after the same locked copy.
- `bpf_obj_free_fields()`: runs once, when the element memory is released.

| Map | Where `bpf_obj_free_fields()` runs |
|---|---|
| non-preallocated hash, rhash | destructor set by `bpf_ma_set_dtor()`, run from `free_all()` in `kernel/bpf/memalloc.c` |
| preallocated hash, LRU hash | `htab_free_prealloced_fields()` from `htab_map_free()` |
| array, percpu array | `array_map_free()` |
| local storage | `bpf_selem_free()`, `bpf_selem_free_trace_rcu()`, `bpf_selem_unlink_nofail()` |

**Map creation requirements**

- `btf_parse_fields()` error: does not fail creation; the `ERR_PTR()` stays in
  `map->record`, the per-kind checks are skipped, and `map_check_btf()` goes on
  to the `map_check_btf` op.
- Examples that end this way: two `struct bpf_timer` members (`-E2BIG`), both
  lock kinds, a graph root with no lock, a `BPF_KPTR_REF` to a kernel type with
  no registered dtor.
- Value type: a struct or a datasec; any other kind makes `btf_find_field()`
  return `-EINVAL`, which is a parse error as above.
- Any valid record, whatever the kinds: needs
  `bpf_token_capable(token, CAP_BPF)`, else `-EPERM`.
- `BPF_F_RDONLY_PROG` or `BPF_F_WRONLY_PROG` with a valid record: `-EACCES`.
- Order of the checks: `-EPERM`, then `-EACCES`, then the per-kind
  `-EOPNOTSUPP`.
- `btf_check_and_fixup_fields()` errors: `-EFAULT` when a graph root's value
  type has no struct meta; `-EINVAL` when a `BPF_UPTR` points to a kernel type
  or a type of size 0; `-E2BIG` when the `BPF_UPTR` type is larger than
  `PAGE_SIZE`.
- `bpf_local_storage_map_check_btf()`: checks only that the key is a 32-bit
  int.
- Not checked in `map_check_btf()`: `BPF_F_MMAPABLE`, special fields in the
  key, use as an inner map.
- `bpf_map_mmap()` and `map_freeze()`: return `-ENOTSUPP` for a map with a
  valid record.

**Kptr fields**

- `BPF_KPTR_REF` to a program-BTF type: `bpf_obj_free_fields()` calls
  `__bpf_obj_drop_impl()` with the pointee's record, not `field->kptr.dtor`,
  which is `NULL` for such a field.
- `BPF_KPTR_PERCPU` to a program-BTF type: `__bpf_obj_drop_impl()` with
  `percpu` true, which frees with `bpf_mem_free_rcu()` on
  `bpf_global_percpu_ma`.
- Pointee with `BPF_REFCOUNT`: the field holds one reference;
  `__bpf_obj_drop_impl()` decrements it and frees the object and its fields
  only when the count reaches zero.
- `field->kptr.dtor`: `btf_parse_kptr()` looks it up only for `BPF_KPTR_REF` to
  a kernel or module type; `BPF_KPTR_UNREF` and `BPF_KPTR_PERCPU` fields have
  none.
- `bpf_kptr_xchg()` body: not executed when `prog->jit_requested`, the kernel
  is 64-bit and `bpf_jit_supports_ptr_xchg()` is true; `kernel/bpf/fixups.c`
  replaces the call with a `BPF_XCHG` atomic instruction.

**Kptr access from programs**

- `check_map_kptr_access()`: reached only for a `PTR_TO_MAP_VALUE` register.
- Kptr field in an allocated object: `btf_struct_access()` rejects every direct
  load and store that overlaps it with `-EACCES`; `bpf_kptr_xchg()` is the only
  access.
- Load from `BPF_KPTR_REF` or `BPF_KPTR_PERCPU`, `rcu_safe_kptr()` and
  `in_rcu_cs()` both true: `btf_ld_kptr_type()` gives
  `PTR_MAYBE_NULL | MEM_RCU`, plus `MEM_PERCPU` for percpu, or else `MEM_ALLOC`
  for a program-BTF type.
- Same load, pointee record has `BPF_GRAPH_NODE`: `NON_OWN_REF` is added too.
- Same load, either test false: `PTR_MAYBE_NULL | PTR_UNTRUSTED` and nothing
  else, also for percpu.
- `in_rcu_cs()`: true when `env->cur_state->in_sleepable` is false, and in a
  sleepable state while `active_rcu_locks`, `active_preempt_locks`,
  `active_locks` or `active_irq_id` is set.
- `rcu_safe_kptr()`: true for every `BPF_KPTR_REF` to a program-BTF type;
  `rcu_protected_types` is consulted only for kernel types.
- Store into `BPF_KPTR_UNREF`, kernel-BTF register: `PTR_MAYBE_NULL`,
  `PTR_TRUSTED`, `MEM_RCU` and `PTR_UNTRUSTED` are all permitted flags.
- Store into `BPF_KPTR_UNREF`, register offset: a constant non-zero offset is
  accepted; `btf_struct_ids_match()` runs non-strict and walks the struct.
- `BPF_KPTR_REF` and `BPF_KPTR_PERCPU` through `bpf_kptr_xchg()`: strict type
  match and offset 0.
- `map_kptr_match_type()`: rejects a register whose `MEM_PERCPU` flag does not
  match whether the field is `BPF_KPTR_PERCPU`.

## Copying and initialising values

**Copying a value**

- `copy_map_value_long()` with a valid `map->record`: `bpf_obj_memcpy()`
  ignores `long_memcpy` and uses plain `memcpy()` between the fields.
- `copy_map_value_long()` length: `round_up(map->value_size, 8)` with or
  without a record; `bpf_long_memcpy()` runs only when the record is NULL or
  an error pointer.
- `copy_map_value_long()` callers: every one is a read-side loop over all
  possible CPUs that copies a per-CPU slot into a staging buffer, for example
  `bpf_percpu_hash_copy()` and `__bpf_array_map_seq_show()`.
- Per-CPU update paths use `copy_map_value()`: `pcpu_copy_value()`,
  `pcpu_init_value()`, `bpf_percpu_array_update()`,
  `bpf_percpu_cgroup_storage_update()`.
- **Unsafe usage**: `copy_map_value_long()` where source or destination holds
  only `map->value_size` bytes; it reads and writes up to 7 bytes past the end.
  - Safe: slots of `round_up(map->value_size, 8)` bytes, which is what
    `bpf_map_value_size()` in `kernel/bpf/syscall.c` sizes per CPU without
    `BPF_F_CPU`, as in `bpf_percpu_array_copy()`.
  - Safe: `copy_map_value()` when `BPF_F_CPU` is set; `bpf_map_value_size()`
    then returns `map->value_size`, as in `bpf_percpu_hash_copy()`.
- `copy_map_value_locked()` without `BPF_F_LOCK`:
  `bpf_sk_storage_clone_elem()` and `diag_get()` in
  `net/core/bpf_sk_storage.c` call it with `lock_src` true whenever the record
  has `BPF_SPIN_LOCK`.
- `copy_map_value_locked()` from BPF programs: `bpf_map_update_elem()` in
  `kernel/bpf/helpers.c` passes `flags` straight to `map_update_elem`, so
  `array_map_update_elem()` and `htab_map_update_elem()` reach it in program
  context.
- `BPF_RES_SPIN_LOCK`: `copy_map_value_locked()` reads
  `map->record->spin_lock_off` only; `btf_parse_fields()` leaves it at
  `-EINVAL` when the value has only a `struct bpf_res_spin_lock`.
- `BPF_F_LOCK` with a `BPF_UPTR` field: `bpf_pid_task_storage_update_elem()`
  returns `-EOPNOTSUPP`; the locked in-place copy does not call
  `bpf_obj_swap_uptrs()`.
- **Potentially unsafe usage**: `memcpy()` of a whole value when
  `map->record` is a valid record.
  - Unsafe: when source or destination is a map element that programs or
    other syscalls can reach; the destination's lock, timer or kptr is
    overwritten, or the source's is copied out.
  - Safe: source is the caller's buffer and destination is a zeroed buffer
    not yet published, with `check_and_init_map_value()` before publishing,
    as `cgroup_storage_update_elem()` in `kernel/bpf/local_storage.c` does.

**Initialising fresh values**

- `bpf_obj_init_field()` in `include/linux/bpf.h`: zeroes the field, then
  sets a non-zero state for four types: `BPF_REFCOUNT` to 1, `BPF_LIST_HEAD`
  and `BPF_LIST_NODE` with `INIT_LIST_HEAD()`, `BPF_RB_NODE` with
  `RB_CLEAR_NODE()`.
- Map values: `map_check_btf()` in `kernel/bpf/syscall.c` does not parse
  `BPF_LIST_NODE` or `BPF_RB_NODE`, so in a map value only `BPF_LIST_HEAD`
  and `BPF_REFCOUNT` end up non-zero.
- `kernel/bpf/hashtab.c` and `kernel/bpf/arraymap.c`: every call to
  `check_and_init_map_value()` is on an output or staging buffer, none on a
  map element.
- `alloc_htab_elem()`, `pcpu_init_value()`, `prealloc_lru_pop()` and
  `prealloc_init()`: do not call `check_and_init_map_value()`.
- Zeroed memory needs no call: `bpf_selem_alloc()` allocates with
  `__GFP_ZERO` and calls `copy_map_value()` with no
  `check_and_init_map_value()`.
- `bpf_map_area_alloc()` and `__alloc()` in `kernel/bpf/memalloc.c`: also
  zero new memory; `unit_alloc()` returns a recycled object without zeroing
  it.
- Zeroed `BPF_LIST_HEAD` in a map element: initialised on first use, for
  example in `__bpf_list_add()` in `kernel/bpf/helpers.c`.
- `check_and_init_map_value()` on any element that can hold a resource, a
  live array or hash element included: also unsafe; `bpf_obj_init_field()`
  overwrites each field with `memset()` and releases nothing.
- **Unsafe usage**: `check_and_init_map_value()` on an element taken from the
  hash map freelist or from `bpf_mem_cache_alloc()`, even after its fields
  were freed; `free_htab_elem()` recycles with no grace period, and
  `htab_map_update_elem()` with `BPF_F_LOCK` finds elements with
  `lookup_nulls_elem_raw()` and takes their lock, which the call would zero.
  - Safe: a staging buffer that only the caller can reach, as in
    `bpf_map_copy_value()` and `bpf_percpu_hash_copy()`.
  - Safe: a buffer fresh from `bpf_map_kmalloc_node()` and not yet published,
    as in `cgroup_storage_update_elem()` (before its `xchg()`) and
    `bpf_cgroup_storage_alloc()` in `kernel/bpf/local_storage.c`.
- `bpf_obj_new()` in `kernel/bpf/helpers.c`: calls `bpf_obj_init()` on a new
  program-allocated object when `meta` is not NULL; `bpf_obj_new_impl()` only
  calls `bpf_obj_new()`.

**Copying out to user space**

- `bpf_map_copy_value()` generic branch: picks `copy_map_value_locked()` on
  `flags & BPF_F_LOCK` alone; without the flag a value that has a
  `struct bpf_spin_lock` is copied with `copy_map_value()` and the lock is
  not taken.
- Special fields in the copy: hold the initial state written by
  `check_and_init_map_value()`, which is not zero for `BPF_LIST_HEAD` and
  `BPF_REFCOUNT`.
- `BPF_F_CPU` in `bpf_percpu_hash_copy()` and `bpf_percpu_array_copy()`: the
  CPU is `map_flags >> 32`; one `copy_map_value()` and one
  `check_and_init_map_value()` on a buffer of `map->value_size` bytes.
- `BPF_F_CPU` validation: `bpf_map_check_op_flags()` in
  `include/linux/bpf.h`, called from `map_lookup_elem()`, rejects it for maps
  that are not per-CPU and for a CPU that is not possible.
- `BPF_MAP_TYPE_RHASH`: lookup goes through the generic branch of
  `bpf_map_copy_value()` with `rhtab_map_lookup_elem()`.
- `BPF_MAP_TYPE_RHASH` copy-out of its own: `rhtab_delete_elem()` (when
  `copy` is not NULL) and `__rhtab_map_lookup_and_delete_batch()` in
  `kernel/bpf/hashtab.c` call `rhtab_read_elem_value()` then
  `check_and_init_map_value()`.
- **Potentially unsafe usage**: copying a value into a buffer bound for user
  space without `check_and_init_map_value()` on the buffer.
  - Unsafe: when the map type can have a record and the buffer is not
    zeroed; the bytes the copy skipped reach user space as uninitialised
    heap from `kvmalloc()`.
  - Safe: a map type for which `map_check_btf()` in `kernel/bpf/syscall.c`
    rejects every special field, as `bpf_percpu_cgroup_storage_copy()` in
    `kernel/bpf/local_storage.c` and the `map_peek_elem` branch of
    `bpf_map_copy_value()`.

## Freeing and cancelling fields

**Freeing fields by context**

- `btf_field_is_nmi_safe()` in `include/linux/bpf.h`: the tree's per-kind
  context classification for freeing, read only through
  `btf_record_has_nmi_unsafe_fields()` in `check_kfunc_call()`;
  `bpf_obj_free_fields()` itself tests no context, and the timer, wq and task
  work callees can move their cancel to irq_work.

| Kind | `btf_field_is_nmi_safe()` | Easy to miss in `bpf_obj_free_fields()` |
|---|---|---|
| `BPF_SPIN_LOCK`, `BPF_RES_SPIN_LOCK`, `BPF_REFCOUNT` | true | no action |
| `BPF_KPTR_UNREF` | true | `WRITE_ONCE()` of 0; no destructor |
| `BPF_TIMER`, `BPF_WORKQUEUE` | true | cancel is inline unless `defer_timer_wq_op()`, then queued to an irq_work |
| `BPF_TASK_WORK` | true | `task_work_cancel()` runs only from irq_work |
| `BPF_KPTR_REF`, `BPF_KPTR_PERCPU` | false | `field->kptr.dtor` or `__bpf_obj_drop_impl()` runs inline |
| `BPF_UPTR` | false | unpins the page; does not clear the slot |
| `BPF_LIST_HEAD`, `BPF_RB_ROOT` | false | takes the `bpf_spin_lock` with irqs off |
| `BPF_LIST_NODE`, `BPF_RB_NODE` | false (default case) | no action |

- `bpf_obj_drop()` and `bpf_percpu_obj_drop()`: `check_kfunc_call()` in
  `kernel/bpf/verifier.c` rejects them with `-EINVAL` when
  `btf_record_has_nmi_unsafe_fields()` is true for the type and the program is
  an `is_tracing_prog_type()` type, or a non-sleepable `BPF_PROG_TYPE_TRACING`
  program other than `BPF_TRACE_ITER`.
- Local storage: `bpf_selem_unlink()` returns `-EOPNOTSUPP` under `in_nmi()`;
  otherwise `bpf_selem_free()` with `reuse_now` false runs
  `bpf_obj_free_fields()` from `bpf_selem_free_trace_rcu()`, an RCU tasks
  trace callback.
- `migrate_disable()`: not called by `bpf_obj_free_fields()`;
  `__bpf_obj_drop_impl()` requires it from the caller, and `bpf_map_free()` in
  `kernel/bpf/syscall.c` provides it around `map_free`.
- `__bpf_obj_drop_impl()`: frees with `bpf_mem_free_rcu()`; it does not call
  `bpf_mem_free()`.

**Cancelling without freeing**

- `bpf_obj_cancel_fields()`: exists, defined in `kernel/bpf/syscall.c`; takes
  a `struct bpf_map *` and a value, and only calls
  `bpf_map_free_internal_structs()` in `kernel/bpf/helpers.c`.
- `BPF_TIMER`, `BPF_WORKQUEUE`, `BPF_TASK_WORK`: same calls as
  `bpf_obj_free_fields()` makes (`bpf_timer_cancel_and_free()`,
  `bpf_wq_cancel_and_free()`, `bpf_task_work_cancel_and_free()`); the slot
  ends up NULL.
- Every other kind: not touched.
- Left in the value, where `bpf_obj_free_fields()` would have released it:
  - `BPF_KPTR_REF`, `BPF_KPTR_PERCPU`: the pointer and the reference it owns.
  - `BPF_LIST_HEAD`, `BPF_RB_ROOT`: all linked nodes.
  - `BPF_UPTR`: the pinned page; no caller passes a map that can hold one,
    since `map_check_btf()` allows `BPF_UPTR` only for
    `BPF_MAP_TYPE_TASK_STORAGE`.
  - `BPF_KPTR_UNREF`: the stale pointer value.
- Callers: all in `kernel/bpf/arraymap.c` (update) and
  `kernel/bpf/hashtab.c`, for example the update and delete paths through
  `check_and_cancel_fields()`.

**Timers and work items**

- Map reference: none is held by any of the three kinds; `cb->map` in
  `struct bpf_async_cb` and `ctx->map` in `struct bpf_task_work_ctx` are plain
  pointers.
- Program reference for `BPF_TIMER` and `BPF_WORKQUEUE`: taken by
  `bpf_async_update_prog_callback()` at set_callback time, not at start.
- `bpf_timer_start()` and `bpf_wq_start()`: take a temporary reference on
  `cb->refcnt` and drop it once the start was issued; they return `-ENOENT`
  once `refcnt` has reached zero.
- `bpf_timer_cancel_and_free()` and `bpf_wq_cancel_and_free()`: both are
  `bpf_async_cancel_and_free()`; it does not read `hrtimer_running` and does
  not queue the cancel to a workqueue.
- `bpf_async_cancel_and_free()`: calls `hrtimer_try_to_cancel()` or
  `cancel_work()` inline, or queues `BPF_ASYNC_CANCEL` with
  `bpf_async_schedule_op()` when `defer_timer_wq_op()` is true; neither waits
  for a running callback.
- `bpf_async_schedule_op()` failing in `kmalloc_nolock()`: the cancel is
  skipped and the last reference dropped; `bpf_async_cb_rcu_tasks_trace_free()`
  cancels later.
- `bpf_async_cb_rcu_tasks_trace_free()`: runs after an RCU tasks trace grace
  period, cancels again, and requeues itself for another grace period while
  the callback is still running; only then is the `struct bpf_async_cb` freed.
- `bpf_task_work_cancel_and_free()`: does not wait; it queues
  `task_work_cancel()` to irq_work only if the state was `BPF_TW_SCHEDULED`; a
  callback that later sees `BPF_TW_FREED` returns without calling the program.
- Last user reference: `bpf_map_put_uref()` calls `map_release_uref`, which
  for the map types that can hold these fields is
  `array_map_free_internal_structs()`, `htab_map_free_internal_structs()` or
  `rhtab_map_free_internal_structs()`; there is no
  htab_map_free_timers_and_wq, htab_free_malloced_timers_and_wq or
  array_map_free_timers_wq.
- `bpf_map_free_internal_structs()`: what each of them calls per element; it
  covers `BPF_TASK_WORK` as well as timer and wq.
- `htab_free_malloced_internal_structs()`: walks only elements linked in a
  bucket; `htab_free_prealloced_internal_structs()` walks every preallocated
  element, the extra ones included.
- `bpf_task_work_acquire_ctx()` after `usercnt` is 0: returns `-EBUSY` and
  calls `bpf_task_work_cancel_and_free()` on the field.

**Updated and deleted elements**

- check_and_free_fields is not in this tree; `check_and_cancel_fields()` in
  `kernel/bpf/hashtab.c` replaces it and calls `bpf_obj_cancel_fields()`.
- Update and delete: cancel timer, wq and task work only; no path below calls
  `bpf_obj_free_fields()`.

| Path | Function that cancels | When |
|---|---|---|
| array, per-CPU array update | `array_map_update_elem()`, `bpf_percpu_array_update()` | in place, after the copy |
| per-CPU hash, existing key | `pcpu_copy_value()` | in place, under the bucket lock |
| rhash, existing key | `rhtab_map_update_existing()` | in place, after the copy |
| preallocated hash update | `htab_map_update_elem()` | under the bucket lock, after the old element is in `extra_elems` |
| non-preallocated hash update, delete | `htab_elem_free()` | after unlock, before `bpf_mem_cache_free()` |
| preallocated hash delete | `free_htab_elem()` | before `pcpu_freelist_push()` |
| LRU hash update, delete, eviction | `htab_lru_push_free()`, `htab_lru_map_delete_node()` | after unlock |
| rhash delete | `rhtab_delete_elem()` | before `bpf_mem_cache_free_rcu()` |

- Full free with `bpf_obj_free_fields()`:
  - array: `array_map_free()` only.
  - preallocated hash: `htab_free_prealloced_fields()` from `htab_map_free()`
    only.
  - non-preallocated hash and rhash: the allocator destructor
    `htab_mem_dtor()`, `htab_pcpu_mem_dtor()` or `rhtab_mem_dtor()`.
- Allocator destructor: called only from `free_all()` in
  `kernel/bpf/memalloc.c`, when the object returns to slab; `unit_alloc()` and
  `alloc_bulk()` hand an object out again without calling it.
- `free_all()` callers: for example `__free_rcu()`, the RCU tasks trace
  callback, and `drain_mem_cache()` from `bpf_mem_alloc_destroy()`.
- Destructor context: a `struct htab_btf_record` holding a `btf_record_dup()`
  copy, set by `bpf_ma_set_dtor()` from `map_check_btf`; the destructor does
  not use `map->record`.
- Reuse timing: a preallocated element and a `bpf_mem_cache_free()` element
  are reusable at once, with no grace period; a rhash element freed with
  `bpf_mem_cache_free_rcu()` is not reusable before an RCU grace period.
- Guarantee on reuse: only the timer, wq and task work slots were cancelled;
  `BPF_KPTR_REF`, `BPF_KPTR_PERCPU`, `BPF_LIST_HEAD` and `BPF_RB_ROOT` keep
  what the old value held, and `alloc_htab_elem()` does not clear them.
- Timer, wq and task work in a reused element: cancelled at delete, but
  `__bpf_async_init()` does not test whether the element is still linked, so a
  program holding the old value pointer can initialise a timer or wq again.
- `BPF_MAP_TYPE_RHASH`: `rhtab_map_ops` in `kernel/bpf/hashtab.c`; always
  `BPF_F_NO_PREALLOC`, updates an existing key in place.

## Model gaps

### Other mistakes models make

- Models take `map->record` to be NULL or a valid record. After a
  `btf_parse_fields()` error `map_check_btf()` leaves an `ERR_PTR()` there;
  users such as `btf_record_has_field()` and `bpf_obj_free_fields()` test
  `IS_ERR_OR_NULL()` and treat the map as having no special fields.
- Models take `bpf_timer_cancel()` to work wherever a program runs. It returns
  `-EOPNOTSUPP` when `defer_timer_wq_op()` is true; `bpf_timer_cancel_async()`
  is the non-waiting kfunc.
- Models take non-preallocated hash map free to release kptrs element by
  element. `delete_all_elements()` and `rhtab_free_elem()` in
  `kernel/bpf/hashtab.c` do not call `bpf_obj_free_fields()`; kptrs are
  released by the `bpf_mem_alloc` destructor.
- Models take `pcpu_init_value()` to reset the special fields of the other
  CPUs' slots. It zeroes those slots with `zero_map_value()`, which leaves
  special fields alone.
- Models do not know `BPF_MAP_TYPE_RHASH`. `rhtab_map_update_elem()` in
  `kernel/bpf/hashtab.c` returns `-EBUSY` for the insert of a new key while
  `rhtab_map_free_internal_structs()` walks the table.
- Models take a kptr field to pin the pointee's `struct btf`. A program BTF
  is kept alive by `map->btf`, which `bpf_map_free()` in
  `kernel/bpf/syscall.c` puts after it frees the record.
- Models do not know the limits on nested and array fields.
  `btf_repeat_fields()` in `kernel/bpf/btf.c` lets only the kptr kinds,
  `BPF_UPTR`, `BPF_LIST_HEAD` and `BPF_RB_ROOT` repeat; more than
  `BTF_FIELDS_MAX` (11) entries makes `btf_parse_fields()` return
  `ERR_PTR(-E2BIG)`.
- Models do not know the ownership depth limit. `BTF_MAX_OWNERSHIP_DEPTH` in
  `kernel/bpf/btf.c` is 8.
- Models take the struct meta to be passed only to `bpf_obj_new_impl()` and
  `bpf_obj_drop_impl()`. Here `bpf_obj_new()` and `bpf_obj_drop()` are kfuncs
  with `KF_IMPLICIT_ARGS` that take `struct btf_struct_meta *`; the impl names
  are wrappers.
