- `i_state` in `struct inode`: a `struct inode_state_flags` whose only member
  is `enum inode_state_flags_enum __state`; all access goes through the
  helpers in `include/linux/fs.h`.
- Locked writers: `inode_state_set()`, `inode_state_clear()`,
  `inode_state_assign()`, `inode_state_replace()`; each has a `_raw` twin that
  only drops the lockdep assertion.
- Unlocked read: `inode_state_read_once()` is the only one; there is no `_raw`
  read and no accessor with an _unlocked suffix.
- `I_FREEING` alone does not stop other writers: a writeback pass that holds
  `I_SYNC`, and `inode_unpin_lru_isolating()`, still change the word under
  `i_lock`.
- **Potentially unsafe usage**: changing the state with a `_raw` writer.
  - Unsafe: while another task can still change the state; the `_raw` writers
    store the whole word with a plain `WRITE_ONCE()`, so a change made under
    `i_lock` elsewhere is lost.
  - Safe: on a freshly allocated inode, as `inode_init_always_gfp()` does.
  - Safe: in `clear_inode()` called from the eviction method, because
    `evict()` has already waited for `I_LRU_ISOLATING` and `I_SYNC`.
