- `struct its_device`, `struct its_collection`, `struct its_ite`: defined in
  `arch/arm64/kvm/vgic/vgic.h`, next to `COLLECTION_NOT_MAPPED` and
  `its_is_collection_mapped()`; `struct vgic_its` is in
  `include/kvm/arm_vgic.h`.
- `struct vgic_its` list heads: `device_list` and `collection_list`;
  `dev_list` and `coll_list` are the link fields inside the objects.
- Unmapped collection, form 1: the object exists and `target_addr` is
  `COLLECTION_NOT_MAPPED`, as `vgic_its_alloc_collection()` leaves it.
- Unmapped collection, form 2: `ite->collection` is NULL, set by
  `vgic_its_free_collection()` for every ITE that used the freed collection.
- `its_is_collection_mapped()`: false for both forms; code that reads
  `ite->collection->collection_id` without that test needs its own NULL
  test.
- `its_lock`: also keeps the reference an ITE holds on `ite->irq`;
  `vgic_its_cache_translation()` asserts the lock for that reason.
