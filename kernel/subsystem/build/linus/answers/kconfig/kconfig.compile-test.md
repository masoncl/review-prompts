- Documents with guidance: `Documentation/kbuild/kconfig-language.rst`
  (sections "Compile-testing" and "Architecture and platform dependencies"),
  the help text of `COMPILE_TEST` in `init/Kconfig`, and
  `Documentation/driver-api/gpio/consumer.rst`.
- `Documentation/kbuild/kconfig.rst` and `Documentation/process/`: say nothing
  about `COMPILE_TEST`.
- Asked of compile-tested code: only that it "should avoid crashing when run
  on a system where the dependency is not met".
- Building with the dependency unmet: the precondition for adding the clause,
  not a demand on the code; no document says the code must build on every
  architecture.
- Narrowing and ANDing: the documents give one form,
  `depends on ARCH_FOO_VENDOR || COMPILE_TEST`, and no rule on which
  dependencies stay outside it. In-tree entries narrow it, for example
  `HISI_PTT` with `depends on ARM64 || (COMPILE_TEST && 64BIT)`.
- `Documentation/driver-api/gpio/consumer.rst`: names compile coverage with
  `COMPILE_TEST` as one of two uses of the stubs in
  `include/linux/gpio/consumer.h`; it does not matter that the platform does
  not enable `GPIOLIB`.
- `COMPILE_TEST` in `init/Kconfig`: has `depends on HAS_IOMEM`.
