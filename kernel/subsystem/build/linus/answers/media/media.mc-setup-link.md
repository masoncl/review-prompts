- Test order in `__media_entity_setup_link()`: NULL link, then any flag
  difference outside `MEDIA_LNK_FL_ENABLED` (`-EINVAL`), then
  `MEDIA_LNK_FL_IMMUTABLE`, then equal flags, then streaming.
- Requested flags: never masked; the caller must pass the link's other bits
  unchanged.
- `MEDIA_LNK_FL_IMMUTABLE` link with different flags: `-EINVAL`. The core's
  own `-EBUSY` comes only from the streaming test; a `link_notify` or
  `link_setup` callback can return it too, as `ccdc_link_setup()` does.
- Streaming test: `media_pad_is_streaming()` on both pads, which is `pipe` of
  `struct media_pad`; `struct media_entity` and `struct media_pad` have no
  `stream_count` field.
- `MEDIA_LNK_FL_DYNAMIC`: read from `link->flags`, not from the requested
  flags.
- Link type: `__media_entity_setup_link()` has no test for it and, past the
  flag tests, reads `link->source` and `link->sink` as pads.
  `MEDIA_IOC_SETUP_LINK` reaches only data links, through
  `media_entity_find_link()`.
- `link_notify`: called directly by `__media_entity_setup_link()`, before and
  after `__media_entity_setup_link_notify()`, which calls only `link_setup`.
- `MEDIA_DEV_NOTIFY_POST_LINK_CH`: sent also when a `link_setup` failed, with
  the requested flags while `link->flags` still holds the old ones; its return
  value is ignored.
- `MEDIA_DEV_NOTIFY_PRE_LINK_CH`: never undone by the core; the only undo is
  the second source `link_setup` call after a sink failure.
