| `Allocator` function | Arguments |
|---|---|
| `alloc()` | `layout`, `flags`, `nid: NumaNode` |
| `realloc()` | `ptr: Option<NonNull<u8>>`, `layout`, `old_layout`, `flags`, `nid` |
| `free()` | `ptr: NonNull<u8>`, `layout`; no flags, no node |

- `Allocator::MIN_ALIGN`: a required associated constant; every implementation
  must define it.
- `Kmalloc`, `Vmalloc`, `KVmalloc`: implement only `realloc()`, through
  `krealloc_node_align()`, `vrealloc_node_align()` and
  `kvrealloc_node_align()`; see `ReallocFunc` in
  `rust/kernel/alloc/allocator.rs`.
- `Box` and `Vec`: no public function takes a `NumaNode`; they pass
  `NumaNode::NO_NODE` on every allocation.
- `PushError`, `InsertError`, `RemoveError` in
  `rust/kernel/alloc/kvec/errors.rs`: convert to `EINVAL`, not `ENOMEM`.
- `Vec` has no set_len(); the unsafe way to grow the length is `inc_len()`.
