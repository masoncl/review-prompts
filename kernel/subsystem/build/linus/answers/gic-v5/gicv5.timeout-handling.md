- Both variants: print with `pr_err_ratelimited()` and return `-ETIMEDOUT`.
- There is no gicv5_irs_spi_set_type() here; `gicv5_spi_irq_set_type()`
  returns the wait error.
- `gicv5_irs_register_cpu()`: replaces a failed select wait by `-ENXIO`;
  only the wait after `GICV5_IRS_PE_CR0` returns `-ETIMEDOUT` unchanged.
- **Unsafe usage**: reading the status value that
  `gicv5_wait_for_op_atomic()` hands back after it returned an error.
  - Unsafe: `gicv5_wait_for_op_s_atomic()` writes `*val` only on success.
  - Safe: test the return first, as `gicv5_irs_wait_for_spi_op()` does.
- **Unsafe usage**: calling `gicv5_wait_for_op()` where sleeping is not
  allowed.
  - Unsafe: `poll_timeout_us()` in `include/linux/iopoll.h` has
    `might_sleep_if()` for a non-zero sleep time.
  - Safe: `gicv5_wait_for_op_atomic()`, as `gicv5_irs_wait_for_spi_op()`
    uses under `spi_config_lock`.
- Unwinding in tree, IRS: on a failed `gicv5_irs_ist_synchronise()`,
  `gicv5_irs_iste_alloc()` clears the L1 entry, frees the L2 table and
  returns the error; `gicv5_irq_lpi_domain_alloc()` then calls
  `release_lpi()`.
- Void callers: the result is dropped, for example in `gicv5_irs_syncr()`
  and `gicv5_irs_init_bases()`.
