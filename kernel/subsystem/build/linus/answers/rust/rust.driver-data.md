- Probe return: `impl PinInit<Self::Data<'bound>, Error> + 'bound`; the data
  type is `type Data<'bound>: Send + 'bound`, which need not be `Self` and
  need not be `'static`; `serdev::Driver` also requires `Sync`.
- PCI `probe()` arguments: `dev: &'bound Device<device::Core<'_>>` and
  `id_info: Option<&'bound Self::IdInfo>`; see `rust/kernel/pci.rs`.
- `'bound` is the span of the binding; driver data may hold `&'bound`
  references to the device and resources that borrow it.
- Unbind order: bus remove calls `unbind()` (`disconnect()` on USB), then
  `post_unbind_callback()` in `rust/kernel/driver.rs` drops the data, then
  `devres_release_all()` runs.
- The last two steps are in `device_unbind_cleanup()` in `drivers/base/dd.c`;
  a `Devres` inside driver data is therefore not yet revoked when the data's
  `Drop` runs.
- The resource constructors below return lifetime-bound values, not `Devres`;
  of them only `irq::Registration::new()` returns a `PinInit`:

| Resource | Constructor | Returns |
|---|---|---|
| PCI BAR | `iomap_region_sized()` on `pci::Device<Bound>` | `Result<pci::Bar<'a, SIZE>>` |
| Platform MMIO | `io_request_by_index()` on `platform::Device<Bound>`, then `iomap_sized()` on the `IoRequest` | `Result<IoMem<'a, SIZE>>` |
| PCI IRQ vectors | `alloc_irq_vectors()` on `pci::Device<Bound>` | `Result<IrqVectorRegistration<'_>>` |
| IRQ handler | `irq::Registration::new()`, from an `IrqRequest<'a>` | `impl PinInit<Self, Error> + 'a` |

- `samples/rust/rust_driver_pci.rs`: `SampleDriverData<'bound>` holds
  `bar: Bar0<'bound>` and `pdev: &'bound pci::Device`; no `Devres`.
- The sample does I/O directly on the `Bar`, in `probe()` and `unbind()`, with
  no `access()` call; `probe()` returns `Ok(SampleDriverData { .. })`.
- `irq::Registration<'a, T>` and `irq::ThreadedRegistration<'a, T>`: hold an
  `IrqRequest<'a>`, no `Devres`; `free_irq()` runs in their drop.
- `irq::Registration::new()` is `unsafe`: the caller must not `mem::forget()`
  the registration.
- `irq::Handler`: `handle(&self)` takes no device argument.
- There is no `request_irq()` method on a bus device.
  - Platform: `request_irq_by_index()` and its siblings, all `unsafe fn`.
  - PCI: `IrqVectorRegistration::index()` gives an `IrqVector`, which converts
    to `IrqRequest` by `From`.
- A wrapper is not needed for a resource held in `Data<'bound>`.
- A wrapper is needed where the holder must be `'static`, for example data
  owned by a `pwm::Chip`, as in `drivers/pwm/pwm_th1520.rs`.
- `Devres<T>` requires `T: Send + 'static`, so it cannot hold a
  `pci::Bar<'bound, SIZE>`; `DevresLt<F: ForLt>` in `rust/kernel/devres.rs` can.
- `into_devres()` on `pci::Bar`, `IoMem` and `ExclusiveIoMem` is the safe way
  to a `DevresLt`.
- The results are aliased `DevresBar`, `DevresIoMem` and
  `DevresExclusiveIoMem`; `DevresLt::new()` itself is `unsafe`.
- `Devres::new()`: returns `Result<Self>`; `Devres` is not a pinned type.
- `new_foreign_owned()` is a method of `cpufreq::Registration`, not of
  `Devres`; the drop-on-unbind helper is `devres::register()`.
- Access through `DevresLt`:
  - `access()` takes `&Device<Bound>`, returns `Result<&F::Of<'a>>`, and needs
    `F: CovariantForLt`.
  - `access_with()` does the same through a closure, for any `ForLt`.
  - `try_access()` returns `Option<DevresGuard>`; `try_access_with()` takes a
    closure.
  - `try_access_with_guard()`: `Devres` has it, `DevresLt` does not.
- `access()` on a device other than the one the wrapper was created with:
  returns `EINVAL`.
- `try_access()` after revocation: returns `None`, not an error code.
