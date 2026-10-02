- Setters: `svc_xprt_init()` (a new transport starts busy),
  `svc_xprt_enqueue()` and `svc_xprt_close()`. Only `svc_xprt_received()`
  clears; no transport code touches the bit.
- `XPT_HANDSHAKE` branch: `svc_handle_xprt()` calls `svc_xprt_received()`
  after `xpo_handshake` returns; `svc_tcp_handshake()` does not, so the bit
  is held for the whole handshake wait.
- Deferred branch: `svc_deferred_recv()` calls `svc_xprt_received()`;
  `svc_handle_xprt()` does not.
- `svc_xprt_received()`: after clearing the bit it calls
  `svc_xprt_enqueue()` only if one of `XPT_CONN`, `XPT_CLOSE`,
  `XPT_HANDSHAKE`, `XPT_DATA`, `XPT_DEFERRED` is set.
- A bit added to `svc_xprt_ready()` and not to the mask in
  `svc_xprt_received()`: an event that sets it while the transport is busy
  is not picked up when the owner releases the transport.
- `svc_xprt_received()` does not change `xpt_reserved` or `xpt_nr_rqsts`.
- **Potentially unsafe usage**: changing state that `svc_xprt_ready()` reads
  and relying on the busy owner's `svc_xprt_received()` to notice it,
  without setting one of the five bits.
  - Unsafe: when the change alone is meant to make the transport ready, with
    none of the five bits set; `svc_xprt_received()` then skips
    `svc_xprt_enqueue()`.
  - Safe: set the bit, then call `svc_xprt_enqueue()`, as
    `svc_data_ready()` and `svc_revisit()` do; the mask in
    `svc_xprt_received()` then covers the case where the transport was busy.
  - Safe: when the state only gates `XPT_DATA` or `XPT_DEFERRED` in
    `svc_xprt_ready()` (write space, `xpt_nr_rqsts`), as in
    `svc_xprt_resource_released()` and `svc_write_space()`; both bits are
    in the mask in `svc_xprt_received()`.
