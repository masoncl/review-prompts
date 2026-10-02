- `regmap_irq_map()` installs no flow handler: it calls `irq_set_chip()`,
  `irq_set_nested_thread()`, `irq_set_parent()` and `irq_set_noprobe()`. It
  does not call `handle_edge_irq()` or set it.
- `IRQF_ONESHOT` on the child request: not required. `__setup_irq()` replaces
  the handler with `irq_nested_primary_handler()` before its test for a NULL
  handler without `IRQF_ONESHOT`, so that test never fires for a nested
  interrupt.
- **Potentially unsafe usage**: `request_threaded_irq()` with a NULL handler
  and no `IRQF_ONESHOT`.
  - Unsafe: on an interrupt that is not nested and whose chip lacks
    `IRQCHIP_ONESHOT_SAFE`; `__setup_irq()` returns `-EINVAL`.
  - Safe: on a child of a regmap interrupt chip, which `regmap_irq_map()`
    marks nested; `axp20x_usb_power_probe()` requests with flags 0 through
    `devm_request_any_context_irq()`.
- `request_any_context_irq()` and `devm_request_any_context_irq()`: return
  `IRQC_IS_NESTED`, which is 1, on success for such a child. The caller must
  test `< 0`; a test for non-zero treats success as failure.
- Trigger flags in the child request: `regmap_irq_set_type()` returns 0
  without doing anything when the type is not in
  `irqs[i].type.types_supported`, so an unsupported trigger is accepted
  silently.
