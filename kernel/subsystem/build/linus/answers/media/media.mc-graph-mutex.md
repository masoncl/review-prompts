- ioctls: every entry of `ioctl_info[]` in `drivers/media/mc/mc-device.c` has
  `MEDIA_IOC_FL_GRAPH_MUTEX` except `MEDIA_IOC_REQUEST_ALLOC`; that includes
  `MEDIA_IOC_DEVICE_INFO`, `MEDIA_IOC_ENUM_ENTITIES` and
  `MEDIA_IOC_ENUM_LINKS`.
- `MEDIA_IOC_ENUM_LINKS32`: not in the table; `media_device_compat_ioctl()`
  takes the mutex itself.
- `lockdep_assert_held()`: in `drivers/media/mc`, only in
  `__media_pipeline_start()` and `media_graph_walk_iter()`.
  `__media_pipeline_stop()`, `__media_entity_setup_link()`,
  `__media_entity_remove_links()`, `__media_remove_intf_link()` and
  `__media_remove_intf_links()` check nothing.
- Streaming state under the mutex: `pipe` of `struct media_pad` and
  `start_count` of `struct media_pipeline`; `struct media_entity` and
  `struct media_pad` have no `stream_count` field.
- Functions that lock: search `graph_mutex` in `drivers/media/mc` and
  `drivers/media/v4l2-core/v4l2-mc.c`. `media_device_unregister()` locks before
  it tests whether the device was registered.
- Lock only when `graph_obj.mdev` is non-NULL, else no lock:
  `media_entity_pads_init()`. `media_entity_remove_links()`,
  `media_remove_intf_link()` and `media_remove_intf_links()` return at once
  when it is NULL.
- `v4l_enable_media_source()` and `v4l_disable_media_source()`: take the mutex
  and call `enable_source` and `disable_source` of `struct media_device` under
  it.
- `media_gobj_create()`: writes the `mdev` lists, `id` and `topology_version`
  with no lock and no assert. `media_create_pad_link()`,
  `media_create_ancillary_link()`, `media_create_intf_link()` and
  `media_devnode_create()` call it without taking the mutex.
- Callbacks the core runs with the mutex held: `link_setup`, `link_notify`,
  `link_validate`, `has_pad_interdep`, `notify` of
  `struct media_entity_notify`, `enable_source`, `disable_source`.
- **Unsafe usage**: calling a function that takes `graph_mutex` from one of
  those callbacks, for example `media_entity_setup_link()`,
  `media_pipeline_start()` or `v4l2_pipeline_pm_get()`; the mutex is not
  recursive.
  - Safe: the `__` form, as `au0828_enable_source()` does with
    `__media_entity_setup_link()` and `__media_pipeline_start()`;
    `__media_pipeline_start()` asserts the mutex.
  - Safe: `media_create_pad_link()` from a `notify` callback, as
    `au0828_media_graph_notify()` does; it takes no lock.
