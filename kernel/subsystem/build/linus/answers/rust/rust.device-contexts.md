- `DeviceContext` has five implementors in `rust/kernel/device.rs`: `Normal`,
  `Bound`, `BoundInternal`, `Core<'a>` and `CoreInternal<'a>`.

| Context | Proves | Reserved for bus abstractions |
|---|---|---|
| `Bound` | device is bound while the reference lives | no; class abstractions hand it out too, e.g. `PwmOps` callbacks |
| `BoundInternal` | same as `Bound` | yes; only use is `receive_buf_callback()` in `rust/kernel/serdev.rs` |
| `Core<'a>` | inside a bus callback; gates e.g. `enable_device_mem()` | no; it is what drivers receive |
| `CoreInternal<'a>` | same as `Core<'a>` | yes; adapters cast the raw pointer to it |

- `Core<'a>` and `CoreInternal<'a>`: `'a` is an invariant brand lifetime;
  callbacks write `Core<'_>`, separate from `'bound`.
- `set_drvdata()` and `drvdata_obtain()`: on `Device<CoreInternal<'a>>` only.
- `drvdata_borrow()`: on any `Ctx: InternalBoundContext`, that is
  `CoreInternal<'a>` and `BoundInternal`.
- `&'bound Device<Bound>` is stored in driver data, not only passed to a
  callback: `pci::Bar` and `IoMem` hold one.
- Context conversion is by `Deref`, not `From`; there are two chains:
  - `CoreInternal<'a>` → `Core<'a>` → `Bound` → `Normal`
  - `BoundInternal` → `Bound` → `Normal`
- To `ARef<Device>`: the generated `From` impls take `&Device<Ctx>`; no
  `ARef<Device<Ctx>>` exists for a non-`Normal` context.
- Upward: `Device::as_bound()` is an `unsafe fn` on `Device<Normal>` returning
  `&Device<Bound>`; the caller guarantees the device stays bound.
- `as_bound()` callers, for example: `parent()` on `auxiliary::Device<Bound>`
  (a safe fn) and `bound_parent_device()` in `rust/kernel/pwm.rs`.
- `AsBusDevice::from_device()`: `unsafe fn from_device(dev: &Device<Ctx>) ->
  &Self`; keeps `Ctx`, subtracts `OFFSET`, makes no bus-type check.
