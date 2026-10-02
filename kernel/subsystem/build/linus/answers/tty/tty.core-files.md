| Job | File, and what is easy to get wrong |
|---|---|
| flip buffers | `drivers/tty/tty_buffer.c` holds `__tty_insert_flip_string_flags()`; `tty_insert_flip_string_fixed_flag()` is a static inline wrapper in `include/linux/tty_flip.h` |
| termios ioctls | `drivers/tty/tty_ioctl.c`; `user_termios_to_kernel_termios()` and `kernel_termios_to_user_termios()` are `__weak` there, with a strong definition in, for example, `arch/sparc/kernel/termios.c`; `drivers/tty/tty_baudrate.c` holds only baud-rate encode and decode |
| ptys | `drivers/tty/pty.c`; `ptmx_open()` and `ptmx_fops` are in it, inside `#ifdef CONFIG_UNIX98_PTYS` |
| serial core | `drivers/tty/serial/serial_core.c`; `uart_add_one_port()` is not in it but in `drivers/tty/serial/serial_port.c`, and reaches `serial_core_register_port()` in `serial_core.c` through `serial_ctrl_register_port()` |
| bus the serial core puts its own devices on | `drivers/tty/serial/serial_base_bus.c`: `serial_base_bus_type`, whose `.name` is `"serial-base"`; `serial_core.c`, `serial_base_bus.c`, `serial_ctrl.c` and `serial_port.c` link into one module, `serial_base.o` |
| shared parts of the 8250 driver | two objects in `drivers/tty/serial/8250/Makefile`: `8250_base.o` is `8250_port.c` plus the optional lib files listed there; `8250.o` is `8250_core.c` plus `8250_platform.c` (and `8250_pnp.c`) |
| 8250 module init | `drivers/tty/serial/8250/8250_platform.c`: `serial8250_init()`, its `uart_register_driver()` call, `nr_uarts`, `serial8250_isa_init_ports()`; `serial8250_reg` and `serial8250_register_8250_port()` are in `8250_core.c` |
| selftests | `tools/testing/selftests/tty/` builds two programs: `tty_tstamp_update.c` and `tty_tiocsti_test.c`; a pty test is in `tools/testing/selftests/filesystems/devpts_pts.c` |
| serial and serdev selftests, KUnit tests | no file: `tools/testing/selftests/` has no serial or serdev directory, and nothing under `drivers/tty/` mentions KUnit |
| the other jobs (file operations, line discipline switching, default line discipline, tty ports, job control, serdev) | the files are the objects listed in `drivers/tty/Makefile` and `drivers/tty/serdev/Makefile` |
