- Plain `#[cfg(CONFIG_X)]` on a tristate `X` is also true for `X=m`; see
  "Kconfig in Rust code".
- Three forms keep an abstraction for a tristate subsystem built-in only:

| Form | Abstraction gate | Driver carries | Examples |
|---|---|---|---|
| direct | `#[cfg(CONFIG_X = "y")]` | `depends on X=y` | `DRM` (`DRM_NOVA`, `DRM_TYR`), `I2C`, `USB` (samples) |
| bool that depends | plain `#[cfg]` on a bool symbol that has `depends on X=y` | `depends on` the bool | `RUST_PHYLIB_ABSTRACTIONS` (`AX88796B_RUST_PHY`), `RUST_FWCTL_ABSTRACTIONS` |
| bool that selects | plain `#[cfg]` on a bool symbol that has `select X` | `select` or `depends on` the bool | `RUST_FW_LOADER_ABSTRACTIONS` (`NOVA_CORE`, `DRM_TYR` select; `AMCC_QT2025_PHY` depends), `RUST_SERIAL_DEV_BUS_ABSTRACTIONS` |

- `RUST_FW_LOADER_ABSTRACTIONS`: `depends on RUST` and `select FW_LOADER`; it
  has no `depends on FW_LOADER=y`.
- `RUST_DRM_GPUVM` and `RUST_DRM_GEM_SHMEM_HELPER`: the "bool that selects"
  form for the tristate helpers `DRM_GPUVM` and `DRM_GEM_SHMEM_HELPER`,
  inside the `drm` module.
- `CONFIG_PCI`, `CONFIG_NET`, `CONFIG_BLOCK`, `CONFIG_AUXILIARY_BUS`: bool
  symbols, gated with plain `#[cfg(CONFIG_X)]`; drivers use `depends on PCI`
  or `select AUXILIARY_BUS`.
- `CONFIG_GPU_BUDDY = "y"`: `GPU_BUDDY` is a bool, so this equals the plain
  form.
- `phy` gate: `#[cfg(CONFIG_RUST_PHYLIB_ABSTRACTIONS)]` is in
  `rust/kernel/net/mod.rs`, not in `rust/kernel/lib.rs`.
- The driver itself may stay tristate in all three forms.
