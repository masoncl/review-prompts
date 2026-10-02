- `include/linux/slab.h` defines four wrappers: `kfree`, `kvfree`,
  `kvfree_atomic` and `kfree_sensitive`.
- `kmem_cache_destroy()`: has no `DEFINE_FREE()` wrapper in this tree.

| Wrapper | Test | Not released at scope exit |
|---|---|---|
| `kfree` | `if (!IS_ERR_OR_NULL(_T)) kfree(_T)` | NULL, error pointer |
| `kvfree` | `if (!IS_ERR_OR_NULL(_T)) kvfree(_T)` | NULL, error pointer |
| `kvfree_atomic` | `if (!IS_ERR_OR_NULL(_T)) kvfree_atomic(_T)` | NULL, error pointer |
| `kfree_sensitive` | `if (_T) kfree_sensitive(_T)` | NULL only |

- `kfree_sensitive` holding an error pointer: `kfree_sensitive()` in
  `mm/slab_common.c` passes it to `ksize()` and `kfree()`, whose pointer test
  is `ZERO_OR_NULL_PTR()`, not `IS_ERR()`.
