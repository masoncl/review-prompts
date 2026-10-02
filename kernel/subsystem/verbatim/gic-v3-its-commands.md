From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **That ordering requirement comes from the base architecture, not from the
    GIC specification.** IHI 0069 contains no sentence requiring a barrier or
    cache maintenance on the queue before `GITS_CWRITER` is written; the GIC
    specification defers explicitly, saying "For more information on
    endianness, memory ordering, and barrier instructions, see Arm®
    Architecture Reference Manual for A-profile architecture". Do not ask a
    patch to cite a GIC-specification rule for this, and do not treat the
    absence of such a citation as evidence the barrier is unnecessary.

*   **The analogous requirement that *is* in the GIC specification concerns the
    ITS tables, not the queue.** For a two-level table, "A write to a level 1
    table entry that changes the valid bit from 0 to 1 must be globally visible
    before software adds a command to the ITS command queue that relies on that
    entry. Otherwise it is UNKNOWN if the command will succeed or if it will be
    ignored." A patch that publishes a new level 2 table and immediately queues
    a command referencing it needs that visibility, and this one you can cite.

*   **A command error has three architecturally permitted outcomes and software
    may assume none of them.** The specification states that "If the ITS
    detects an error in the data provided to a command, the resulting behavior
    is a CONSTRAINED UNPREDICTABLE choice of: • Ignoring the command ... •
    Stalling the ITS command queue ... • Treating the data as valid data". Code
    or a commit message that reasons "the ITS will just ignore the bad command"
    is relying on one arm of a CONSTRAINED UNPREDICTABLE choice.

*   **A `GITS_CWRITER` value outside the range implied by `GITS_CBASER` is a
    separate failure mode.** Behavior is a CONSTRAINED UNPREDICTABLE choice
    between treating the command queue as invalid until a valid value is
    written, and treating the value as valid and UNKNOWN. Validate the offset
    before forwarding a value that did not come from the driver's own ring
    arithmetic.

*   **Without one of the two, no ordering exists at all.** "In the absence of a
    SYNC or VSYNC command the ordering of ITS commands and translation requests
    is not defined by the architecture." There is no weaker in-between
    guarantee to rely on.

*   **On GICv4.1, unmapping a vPE is self-synchronizing and must not be
    followed by a VSYNC.** The specification states that "A VMAPP with {V,
    Alloc}=={0, x} is self-synchronizing. This means the ITS command queue does
    not show the command as consumed until all of its effects are completed."
    A VSYNC after it would name a vPE that no longer exists, which is a command
    error; the architected error code is `VSYNC_VCPU_INVALID`, and where
    `GITS_TYPER.SEIS` is 1 the implementation may report it as a System error.
    `its_build_vmapp_cmd()` implements this by setting its returned vPE to
    `NULL` on the unmap path, with the comment "Unmapping a VPE is
    self-synchronizing on GICv4.1, no need to issue a VSYNC".

*   **INVALL is completed by a SYNC.** INVALL "specifies that the ITS must
    ensure any caching associated with the interrupt collection defined by ICID
    is consistent with the LPI Configuration tables held in memory for all
    Redistributors", and the specification is explicit that "A SYNC command
    completes the INV and INVALL commands". An INVALL issued without its SYNC
    leaves a window in which the configuration in memory and the configuration
    the ITS is using disagree.

*   INVDB or VSGI with no explicit VSYNC at the call site. The specification
    states "INVDB is synchronized by a VSYNC command" and "VSGI is synchronized
    by VSYNC", and the driver reaches both through the virtual send path, which
    appends it.
