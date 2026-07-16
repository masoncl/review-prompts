# Selftests Subsystem Details

## Build System and Installation

When a new file is created in a selftests directory but not added to the
Makefile, tests fail with "No such file or directory" when run from an
installed location (via `make install`). Tests may appear to work when run
directly from the source tree because the file exists there.

The selftests build system uses several variables in each subsystem's Makefile
to control what gets installed:

| Variable | Purpose |
|----------|---------|
| `TEST_PROGS` | Executable test scripts that are run directly |
| `TEST_FILES` | Supporting files (libraries, data files, sourced scripts) |
| `TEST_GEN_FILES` | Generated binaries/files produced during build |
| `TEST_GEN_PROGS` | Generated executable test programs |

Key invariants:

- Any file referenced via `source <filename>` (bash) or `. <filename>` in
  test scripts must be added to `TEST_FILES`
- Any file referenced via `import <module>` (Python) in test scripts must be
  added to `TEST_FILES`
- Executable test scripts that are invoked directly go in `TEST_PROGS`
- Helper executables that are built during `make` go in `TEST_GEN_PROGS` or
  `TEST_GEN_FILES`

Common mistake: creating a new shared library or utility file (like
`_common.sh`, `utils.py`, `lib.sh`) that is sourced by test scripts but
forgetting to add it to `TEST_FILES`. The tests work in the source directory
but fail after `make install`.

## KVM Selftests: IRQ Chip Setup and `vm_create` vs `vm_create_with_one_vcpu`

Tests that use `KVM_IRQFD`, `KVM_IRQ_LINE`, or IRQ routing APIs after
`vm_create()` fail because `vm_create()` does not create vCPUs, and on arm64
VGIC finalization (`KVM_DEV_ARM_VGIC_CTRL_INIT`) requires all vCPUs to be
created first. On architectures without any in-kernel IRQ chip support (riscv,
loongarch), these ioctls fail with `-ENODEV`.

`vm_create(nr_runnable_vcpus)` allocates a VM and sizes memory for the given
number of vCPUs, but does **not** create any vCPUs. IRQ chip setup is
initiated during `vm_create()` via `kvm_arch_vm_post_create()`, but
finalization (via `kvm_arch_vm_finalize_vcpus()`) only happens in functions
that also create vCPUs, such as `vm_create_with_one_vcpu()` and
`__vm_create_with_vcpus()`.

`kvm_arch_has_default_irqchip()` returns whether the architecture sets up an
in-kernel IRQ chip by default:

| Architecture | Return value |
|--------------|-------------|
| x86 | `true` (creates IOAPIC/PIC/LAPIC via `vm_create_irqchip()`) |
| s390 | `true` |
| arm64 | `true` when GICv3 is supported and not disabled via `test_disable_default_vgic()` |
| riscv, loongarch | `false` (weak default in `lib/kvm_util.c`) |

Tests that need an in-kernel IRQ chip must:

1. Call `TEST_REQUIRE(kvm_arch_has_default_irqchip())` to skip on architectures
   that lack IRQ chip support.
2. Use `vm_create_with_one_vcpu()` (or `__vm_create_with_vcpus()`) rather than
   bare `vm_create()`, so that vCPUs are created and IRQ chip finalization
   completes before issuing IRQ-related ioctls.

```c
// WRONG: vm_create() does not create vCPUs or finalize the IRQ chip
vm = vm_create(1);
kvm_irqfd(vm, gsi, eventfd, 0);

// CORRECT: Skip unsupported architectures, then create VM with vCPU
TEST_REQUIRE(kvm_arch_has_default_irqchip());
vm = vm_create_with_one_vcpu(&vcpu, NULL);
kvm_irqfd(vm, gsi, eventfd, 0);
```

## Network Namespace Tests: Device Config Inherited from init_net

A new network namespace does not start from compiled defaults for IPv4. It
copies `conf/all` and `conf/default` from `init_net`. A test that asserts on a
device config knob it never sets is therefore asserting on the config of the
machine running the test.

The behavior is controlled by `net.core.devconf_inherit_init_net`, and IPv4 and
IPv6 disagree at the default value of 0:

| `devconf_inherit_init_net` | IPv4 (`devinet_init_net`) | IPv6 (`addrconf_init_net`) |
|----------------------------|---------------------------|----------------------------|
| 0 (default) | copy from `init_net` | compiled defaults |
| 1 | copy from `init_net` | copy from `init_net` |
| 2 | compiled defaults | compiled defaults |
| 3 | copy from current netns | copy from current netns |

So on any host with `net.ipv4.conf.all.forwarding=1` (a router, a container
host, most developer workstations that have ever run docker), devices created
inside a test's netns come up with forwarding already enabled. The same test on
a CI VM, where forwarding is off, sees the opposite. IPv6 is unaffected at the
default, which is why this class of bug often shows up in the IPv4 arms only.

This produces two distinct failures.

**False failure.** A test that expects an operation to be refused because
forwarding is off will see it succeed instead, and fail. It passes in CI and
fails for developers, which sends people looking for a kernel regression that
is not there.

**False pass.** A negative test asserting error code X can become a tautology
if the bug it targets would also produce X, for an unrelated reason. The
inherited config decides which gate the buggy path stops at, and therefore
which error code comes back. When the host makes an earlier gate fire, the test
discriminates; when it does not, the same test passes whether or not the kernel
is broken.

```c
// WRONG: forwarding is whatever the host had, so the arms below only mean
// what they say on a host with forwarding off
SYS(fail, "ip link add veth1 type veth peer name veth2");

// CORRECT: pin the state the assertions depend on, then enable per device
err = write_sysctl("/proc/sys/net/ipv4/conf/all/forwarding", "0");
if (!ASSERT_OK(err, "write_sysctl(net.ipv4.conf.all.forwarding)"))
	goto fail;
err = write_sysctl("/proc/sys/net/ipv4/conf/default/forwarding", "0");
if (!ASSERT_OK(err, "write_sysctl(net.ipv4.conf.default.forwarding)"))
	goto fail;

SYS(fail, "ip link add veth1 type veth peer name veth2");
```

For a negative test, the check that catches the tautology is to ask what a
kernel with the targeted bug would actually return, and whether that value
differs from the asserted one. If both the correct kernel and the broken kernel
can produce the asserted code, the test pins nothing. The fix is usually to
give the buggy path something to succeed at, so the two outcomes separate:
adding a route, an address, or an enabled device turns the broken kernel's
answer into a success code that the assertion then catches.

## Quick Checks

- **New shared files**: When a commit creates a file that is sourced or
  imported by test scripts, verify it is added to `TEST_FILES` in the Makefile
- **`TEST_PROGS` vs `TEST_FILES`**: Executable tests go in `TEST_PROGS`;
  supporting files go in `TEST_FILES`. Mixing these up causes either execution
  failures or missing installations
- **KVM IRQ chip tests**: When tests use `KVM_IRQFD`, `KVM_IRQ_LINE`, or IRQ
  routing, verify `vm_create_with_one_vcpu()` is used and
  `TEST_REQUIRE(kvm_arch_has_default_irqchip())` is present
- **netns config assumptions**: When a test asserts an outcome that depends on
  `forwarding`, `rp_filter`, `accept_local` or any other `conf/{all,default}`
  knob, verify the test writes that knob itself. IPv4 inherits it from
  `init_net`, so an unwritten knob makes the assertion depend on the test host
- **Negative tests**: When a test asserts an error code for a condition that
  should be refused, verify a kernel missing that check would return a
  different code. If the missing check and an unrelated missing precondition
  both yield the asserted code, the test passes whether or not the kernel is
  correct
