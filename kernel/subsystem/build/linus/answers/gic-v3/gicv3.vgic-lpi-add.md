- At entry: `vgic_get_irq()`; an LPI that already exists is returned at once
  with that reference, skipping everything below.
- Before the lock, besides allocating and initialising the object:
  `xa_reserve_irq()` with `GFP_KERNEL_ACCOUNT`; on failure the object is freed
  and `ERR_PTR()` returned.
- Store under the lock: `__xa_store()` with `GFP_NOWAIT | __GFP_ACCOUNT`.
- Slot holds a zero-count object: `__xa_store()` replaces it, and the old
  object is freed with `kfree_rcu()` under the lock.
- If the displaced object's count is not zero, `WARN_ON_ONCE()` fires and it is
  not freed.
- `__xa_store()` failure: unlock, `kfree()` the new object, `ERR_PTR()`. It
  does not call `xa_release()`.
- Later failures are `update_lpi_config()` and
  `vgic_v3_lpi_sync_pending_status()`; each is undone with `vgic_put_irq()`,
  which removes a new object from `lpi_xa` and frees it when that was the last
  reference.
- Those two steps also run when a live object was found under the lock; the put
  on failure then drops only the reference just taken.
- Callers allocate the ITE before the call. On `IS_ERR()` they call
  `its_free_ite()`, whose `irq` is still NULL so no put happens;
  `vgic_its_cmd_handle_mapi()` also frees a collection it created.
