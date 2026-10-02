- `8250.o` and `8250_base.o`: both are `obj-$(CONFIG_SERIAL_8250)`; there is no
  separate Kconfig symbol for the base module.
- `8250_rsa.o`: part of `8250_base` (`8250_base-$(CONFIG_SERIAL_8250_RSA)`),
  not of `8250`.
- 8250_alpha.o: not in this tree; `8250` holds only `8250_core.o`,
  `8250_platform.o` and `8250_pnp.o`.
- `drivers/tty/serial/8250/8250.h`: declares unexported symbols of both
  modules, so a prototype there does not show that a cross-module call links.
  - In `8250.ko`, for example `nr_uarts`, `serial8250_reg`,
    `serial8250_setup_port()`, `serial8250_isa_config`.
  - In `8250_base.ko`, for example `rsa_enable()`, `fintek_8250_probe()`,
    `serial8250_tx_dma()`.
- Function moved so that its caller is in the other module: check for an
  `EXPORT_SYMBOL` line next to each `8250_base` symbol that `8250.ko` code
  then uses; the header alone tells nothing.
- Export in `8250.ko`, for example `serial8250_get_port()`: no `8250_base`
  source file uses one; `8250.ko` already needs `8250_base` exports, so with
  `CONFIG_SERIAL_8250=m` neither module could then load first.
- Exports of `8250_base`: most are plain `EXPORT_SYMBOL_GPL()`.
  - `"SERIAL_8250"` namespace: only `serial8250_clear_fifos()`,
    `serial8250_handle_irq_locked()`, `serial8250_fifo_wait_for_lsr_thre()`.
  - `"SERIAL_8250_PCI"` namespace: the two exports of `8250_pcilib.c`.
  - Import form is the quoted string, `MODULE_IMPORT_NS("SERIAL_8250")`.
  - No source file of `8250.ko` imports a namespace; code moved into `8250.ko`
    that calls one of the namespaced functions needs the import added.
- `univ8250_rsa_support()` in `8250_rsa.c`: exported with
  `EXPORT_SYMBOL_FOR_MODULES(univ8250_rsa_support, "8250")`, so only the module
  named `8250` may use it; `kernel/module/main.c` rejects an explicit import
  of a `module:` namespace.
- `serial8250_console_write()`, `serial8250_console_setup()`,
  `serial8250_console_exit()`: defined in `8250_port.c`, called from
  `8250_core.c`, not exported.
  - These three calls link because both sides sit under
    `#ifdef CONFIG_SERIAL_8250_CONSOLE`, and that option
    `depends on SERIAL_8250=y`.
- **Potentially unsafe usage**: a call between `8250.ko` and `8250_base.ko`
  files to a function that has no export.
  - Unsafe: when the code can be built with `CONFIG_SERIAL_8250=m`; modpost
    reports the symbol undefined.
  - Safe: when caller and callee are both inside
    `#ifdef CONFIG_SERIAL_8250_CONSOLE`, as `univ8250_console_setup()` calling
    `serial8250_console_setup()`; `drivers/tty/serial/8250/Kconfig` makes the
    option depend on `SERIAL_8250=y`.
- `struct uart_8250_ops`: has three hooks, `setup_irq`, `release_irq` and
  `setup_timer`; `serial8250_do_startup()` also calls
  `up->ops->setup_timer()`.
- `up->ops`: set only in `serial8250_setup_port()` in `8250_core.c`; these
  three hooks are the only `8250.ko` functions that the `8250_base` source
  files call.
- `univ8250_port_ops`: the variable lives in `8250_core.c`, but every function
  in it belongs to `8250_base`: a copy of the base ops, plus, with
  `CONFIG_SERIAL_8250_RSA`, the three overrides from `8250_rsa.c`. It is not a
  route from base into `8250.ko`.
- `serial8250_isa_config`: set by `serial8250_set_isa_configurator()` and
  called from `8250_platform.c` and `8250_core.c`, all inside `8250.ko`;
  `8250_port.c` does not reference it.
- `dl_read`, `dl_write`: defaults are installed in `8250_port.c`;
  `serial8250_register_8250_port()` only copies what the registering driver
  supplied.
- Base code that needs data owned by `8250.ko`: gets it as a pointer argument
  to an exported base function that `8250.ko` calls. See
  `univ8250_rsa_support()`: `__serial8250_isa_init_ports()` passes
  `&univ8250_port_ops` and `univ8250_port_base_ops`, and `8250_rsa.c` keeps
  the second in its static `core_port_base_ops`.
