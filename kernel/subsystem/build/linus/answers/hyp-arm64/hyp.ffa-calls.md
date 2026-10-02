- `FFA_MAX_FUNC_NUM`: 0xFF, not 0x7F (`arch/arm64/kvm/hyp/include/nvhe/ffa.h`);
  `is_ffa_call()` does not test the 32-bit/64-bit convention bit.
- `handle_host_smc()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, before
  `kvm_host_ffa_handler()` runs: clears `ARM_SMCCC_CALL_HINTS` from the id,
  answers `SMCCC_RET_NOT_SUPPORTED` for a non-zero SMC immediate or non-zero
  upper 32 bits of x0, and tries `kvm_host_psci_handler()` first.
- `ffa_call_supported()`: the `switch` compares the whole function id, so the
  32-bit and 64-bit forms of a call are separate entries; for example
  `FFA_MSG_SEND_DIRECT_RESP` is refused and `FFA_FN64_MSG_SEND_DIRECT_RESP`
  is not named.
- `FFA_RXTX_MAP` (32-bit): refused; `FFA_FN64_RXTX_MAP` is the handled form.
- `FFA_MEM_FRAG_TX`: handled by `do_ffa_mem_frag_tx()`; `FFA_MEM_FRAG_RX` is
  the refused one.
- `FFA_ID_GET`: passed through; EL2 has no `case` for it and only issues its
  own in `hyp_ffa_post_init()`.
- `FFA_MSG_SEND2`: not named in `ffa_call_supported()`.
- FF-A 1.2 group on the deny list: `FFA_MSG_SEND_DIRECT_REQ2`,
  `FFA_MSG_SEND_DIRECT_RESP2`, `FFA_CONSOLE_LOG`,
  `FFA_PARTITION_INFO_GET_REGS`; refused whatever version was agreed.
- `FFA_MSG_SEND_DIRECT_REQ2`: there is no do_ffa_direct_msg2() or other EL2
  handler for it here.
- `FFA_MEM_SHARE` and `FFA_MEM_LEND` (32-bit): handled, and re-issued to EL3
  as `FFA_FN64_MEM_SHARE` / `FFA_FN64_MEM_LEND`; `do_ffa_mem_xfer()` has a
  `BUILD_BUG_ON()` that allows only those two ids.
