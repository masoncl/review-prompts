| Field | Type |
|---|---|
| `wptr` in `struct amdgpu_ring` | `u64` |
| `sync_seq` in `struct amdgpu_fence_driver` | `uint32_t` |
| `last_seq` in `struct amdgpu_fence_driver` | `atomic_t` |

- Ring index: `wptr & buf_mask`; `ptr_mask` only limits the stored `wptr`.
- `ptr_mask` with `support_64bit_ptrs`: all ones, so `wptr` is a running dword
  count and not a ring index.
- Slot reuse: `amdgpu_fence_emit()` waits on an unsignalled fence still in the
  slot; `amdgpu_fence_emit_polling()` waits for `seq - num_fences_mask`.
- **Potentially unsafe usage**: a masked `do`/`while (last_seq != seq)` walk
  over the fence array; it visits every slot when both masked values are equal
  on entry.
  - Unsafe: when the unmasked counters can be equal on entry and the body acts
    on a fence without testing it; `dma_fence_signal()` then runs on fences
    the hardware has not reached.
  - Safe: return before the loop when the unmasked values are equal, as
    `amdgpu_fence_process()` does; it signals every fence it visits.
  - Safe: test each fence with `dma_fence_is_signaled()` before acting on it,
    as `amdgpu_ring_find_guilty_fence()` does.
  - Safe: walk the whole array from 0 to `num_fences_mask` under
    `fence_drv.lock` and test each fence, as `amdgpu_fence_driver_set_error()`
    does; that form does not depend on the counters.
