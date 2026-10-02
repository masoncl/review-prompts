- **Potentially unsafe usage**: a constructor that registers with C and
  relies on `Drop` to unregister.
  - Unsafe: when the constructor is a safe `fn` and the data C keeps a
    pointer to may hold borrows (the type carries a lifetime that is not
    `'static`); `mem::forget()` is safe, skips `Drop`, and C then calls back
    after the borrow has ended. Pinning keeps the registration's own memory
    alive, not what it borrows.
  - Safe: the constructor is an `unsafe fn` whose `# Safety` section forbids
    `mem::forget()`, as `Registration::new()` in `rust/kernel/irq/request.rs`
    and `Registration::new_with_lt()` in `rust/kernel/auxiliary.rs` are.
  - Safe: the data is bounded `'static`, as in `Registration::new()` in
    `rust/kernel/auxiliary.rs` (`F::Of<'a>: 'static`; its `// SAFETY:` states
    the reason), `Registration::new()` in `rust/kernel/driver.rs`
    (`T: 'static`) and `struct Devres` (`T: Send + 'static`).
  - Safe: C keeps no pointer to Rust data, so a leak only leaves the C object
    registered forever, as `Registration::new()` in `rust/kernel/faux.rs`
    (the type has no lifetime, the ops pointer is `null()`, and
    `faux_device_create_with_groups()` copies the name).
- `rust/kernel/time/hrtimer.rs`: the same split as two traits. `HrTimerPointer`
  has a safe `start()` and its handle may be leaked; `UnsafeHrTimerPointer`
  has `unsafe fn start()` for timers that die with a borrow.
- `Queue::enqueue()` in `rust/kernel/workqueue.rs`: safe because it requires
  `W: RawWorkItem<ID> + Send + 'static`; `RawWorkItem::__enqueue()` lists what
  the caller owes without those bounds.
- `WorkItem` in `rust/kernel/workqueue.rs`: a safe trait. The unsafe traits
  there are `RawWorkItem`, `RawDelayedWorkItem`, `WorkItemPointer`, `HasWork`
  and `HasDelayedWork`.
- Trampolines: both forms occur. `unsafe extern "C" fn` with a `# Safety`
  section in `rust/kernel/miscdevice.rs` and `rust/kernel/irq/request.rs`;
  plain `extern "C" fn` in bus adapters, for example `probe_callback()` in
  `rust/kernel/platform.rs` and `post_unbind_callback()` in
  `rust/kernel/driver.rs`.
- Bounds on callback data: match the context C calls from, for example
  `Handler: Sync` in `rust/kernel/irq/request.rs`,
  `MiscDevice::Ptr: ForeignOwnable + Send + Sync`, and
  `Driver::Data<'bound>: Send` in `rust/kernel/platform.rs`.
- Precondition a safe function cannot check: taken as a typed argument that
  only unsafe code can create. `Devres::new()` takes `&Device<Bound>`;
  `Device::as_bound()` is the `unsafe fn` that makes one.
- References built in bus callbacks: typed `Device<CoreInternal<'_>>`, handed
  to drivers as `Device<Core<'_>>`; the lifetime in `struct Core`
  (`rust/kernel/device.rs`) is invariant so the reference cannot outlive the
  callback.
