| Kind | List that holds it | Valid fields |
|---|---|---|
| data, forward | `links` of the source entity | `source`, `sink`, `reverse` |
| data, backlink | `links` of the sink entity | same `source` and `sink`, `reverse`, `is_backlink` set |
| ancillary | `links` of the primary entity only | `gobj0`, `gobj1`: graph objects of the two entities; `reverse` NULL |
| interface | `links` of `struct media_interface` | `intf`, `entity` |

- Ancillary link: holds no pad pointer; `link->source->entity` reads a field
  of `struct media_entity` through the wrong type.
- Backlink: gets its own `media_gobj_create()`, so it has an id and sits in
  `mdev->links`; `media_device_get_topology()` skips it by `is_backlink`.
- `entity->links` before registration: the list head is not initialised, so
  any walk, `for_each_media_entity_data_link()` included, is invalid until
  `media_device_register_entity()` has run.
- `graph_mutex`: excludes link removal by `media_entity_remove_links()`,
  `media_device_unregister_entity()` and `media_device_unregister()`, which
  take it; it does not exclude creation, because `media_create_pad_link()` and
  `media_create_ancillary_link()` add to `links` without it.
- `for_each_media_entity_data_link()`: not safe against removal of the current
  link; `__media_entity_remove_links()` uses `list_for_each_entry_safe()`.
- **Potentially unsafe usage**: `list_for_each_entry()` over `entity->links`
  that uses `link->source` or `link->sink`.
  - Unsafe: dereferencing them with no type test when the entity can be the
    primary of an ancillary link; `v4l2_async_create_ancillary_links()` adds
    one to the notifier's sub-device when it binds a `MEDIA_ENT_F_LENS` or
    `MEDIA_ENT_F_FLASH` sub-device.
  - Safe: test `MEDIA_LNK_FL_LINK_TYPE` against `MEDIA_LNK_FL_DATA_LINK`
    first, as `media_entity_remote_pad_unique()` does.
  - Safe: `for_each_media_entity_data_link()`, as `media_entity_find_link()`
    does; `__media_entity_next_link()` filters by type.
  - Safe: only comparing the two pointers with a pad before any dereference,
    as `media_pad_remote_pad_unique()` does.
- **Potentially unsafe usage**: walking `entity->links` without `graph_mutex`.
  - Unsafe: while an entity at either end can be unregistered or have its
    links removed; `__media_entity_remove_link()` frees the link and its
    `reverse` in the remote entity's list.
  - Safe: with `graph_mutex` held, as in `__media_pipeline_start()`, which
    asserts it, and so in a `link_validate` callback.
