Produce a report of regressions found based on this template.

- The report must be in plain text only.  No markdown, no special characters,
absolutely and completely plain text fit for the U-Boot mailing list.

- Any long lines present in the unified diff should be preserved, but
any summary, comments or questions you add should be wrapped at 78 characters

- Never include bugs filtered out as false positives in the report

- Always end the report with a blank line.

- The report must be conversational with undramatic wording, fit for sending
as a reply to the patch introducing the regression on the LKML mailing list
  - Report must be **factual**.  just technical observations
  - Report should be framed as **questions**, not accusations
  - Call issues "regressions", never use the word critical
  - NEVER EVER USE ALL CAPS

- Explain the regressions as questions about the code, but do not mention
the author.
  - don't say: Did you corrupt memory here?
  - instead say: Can this corrupt memory? or Does this code ...

- Vary your question phrasing.  Don't start with "Does this code ..." every time.

- If the bug came from SR-* patterns, it is a subjective review.  Don't put a big
  SUBJECTIVE header on it, simply say something similar to: "this isn't a bug, but ..."

- Ask your question specifically about the sources you're referencing:
  - If the regression is a leak, don't call it a 'resource leak', ask
    specifically about the resource you seek leaking.  'Does this code leak the
    page?'
  - Don't say: 'Does this loop have a bounds checking issue?' Name the
    variable you think we're overflowing: "Does this code overflow xyz[]?"
- When the issue is in the commit message itself, quote the exact portions of
  the commit message that are incorrect, in the same way you're report a bug
  in the diff.
  - There's no need to include the diff hunks if the only issue is in the commit message.

- The issue description may include extra details such as later commits that fix
  the bug, or lore discussions upstream.  These MUST be included in the summary,
  but should be reworded to fit the template requirements.

- You MUST include every issue sent, even if the additional details explain the
  issue was fixed in a later commit.  Your job is to format issues, not decide
  which ones are worth including.

- Do not add additional explanatory content about why something matters or what
  benefits it provides. State the issue and the suggestion, nothing more.

- Do not explain why typos or grammar mistakes are a problem. Just point them out.

## Ensure clear, concise paragraphs

**Never make long or dense confusing paragraphs, ask short questions backed up by
code snippets (in plain text), or call chains if needed.**

## NEVER EVER ALL CAPS

The only time it is acceptable to use ALL CAPS in the review-inline.txt
is when you're directly quoting code.

## Don't over explain

Some bugs are extremely nuanced, and require a lot of details to explain.

Some bugs are just completely obvious, especially cutting and pasting errors,
or areas where the author clearly just missed updating some code.   If you
expect a reasonable maintainer to understand a short explanation, use
a short explanation.

## NEVER QUOTE LINE NUMBERS

- Never mention line numbers when referencing code locations, instead indicate
the function name and also call chain if that makes it more clear.  Avoid
complex paragraphs and instead use call chains funcA()->funcB() to explain.
  - The line numbers present in the code you're reading here are unique
    to the code base setup for review.  Your audience doesn't know exactly
    what code base you're reading, so line numbers are meaningless to them.
  - YOU MUST NOT REFERENCE LINE NUMBERS IN THIS REPORT
  - Instead, use small code snippets any time you feel the urge to say a line
    number out loud.

## Structure
Create a TodoWrite for these items, all of which your report should include:

- [ ] git sha of the commit
- [ ] Author: line from the commit
- [ ] One line subject from the commit
- [ ] A brief (max 3 sentence) summary of the commit.
- [ ] Any Link: tags from the commit header
- [ ] A unified diff of the commit, quoted as though it's in an email reply.
  - [ ] The diff must not be generated from existing context.
  - [ ] You must regenerate the diff by calling out to semcode's commit function,
    using git log, or re-reading any patch files you were asked to review.
  - [ ] You must ensure the quoted portions of the diff exactly match the
    original commit or patch.

- [ ] Place your questions about the regressions you found alongside the code
  in the diff that introduced them.  Do not put the quoting '> ' characters in
  front of your new text.
- [ ] Place your questions as close as possible to the buggy section of code.
- [ ] Snip portions of the quoted content unrelated to your review
  - [ ] Create a TodoWrite with every hunk in the diff.  Check every hunk
        to see if it is relevant to the review comments.
  - [ ] ensure diff headers are retained for the files owning any hunks keep
    - Never include diff headers for entirely snipped files
  - [ ] Replace any content you snip with [ ... ]
  - [ ] aggressively snip entire files unrelated to the review comments
  - [ ] aggressively snip entire hunks from quoted files if they are unrelated to the review
  - [ ] aggressively snip entire functions from the quoted hunks unrelated to the review
  - [ ] aggressively snip any portions of large functions from quoted hunks if unrelated to the review
  - [ ] ensure you only keep enough quoted material for the review to make sense
  - [ ] aggressively snip trailing hunks and files after your last review comments unless
        you need them for the review to make sense
  - [ ] The review should contain only the portions of hunks needed to explain the review's concerns.

Sample:

```
commit 06e4fcc91a224c6b7119e87fc1ecc7c533af5aed
Author: Ilias Apalodimas <ilias.apalodimas@linaro.org>

efi_loader: reserve FF-A shared buffer for runtime variables

<brief description>

>
>  /**
> - * setup_mm_hdr() -	Allocate a buffer for StandAloneMM and initialize the
> - *			header data.
> + * get_comm_buf() - Obtain a communication buffer for MM/FF-A exchange
> + * @payload_size: size of the payload that will be appended to the
> + *                MM communication header
> + *
> + * This helper returns a buffer suitable for constructing an
> + * EFI_MM_COMMUNICATE message. During the boot phase a new buffer is
> + * dynamically allocated. After ExitBootServices(), dynamic
> + * allocation is no longer permitted, and all runtime communication must
> + * use the statically reserved FF-A shared buffer.
> + *
> + * The caller owns the returned buffer only during the boot phase and
> + * must release it with free(). During the runtime phase, the returned
> + * pointer aliases the static FF-A shared buffer and must not be freed.
> + *
> + * Return:
> + *   Pointer to a valid communication buffer on success.
> + *   NULL if no suitable communication buffer is available.
> + */
> +static __efi_runtime u8 *get_comm_buf(efi_uintn_t payload_size)
> +{
> +	efi_uintn_t comm_buf_size;
> +	u8 *comm_buf;
> +
> +	comm_buf_size = MM_COMMUNICATE_HEADER_SIZE +
> +			MM_VARIABLE_COMMUNICATE_SIZE +
> +			payload_size;
> +
> +	/*
> +	 * After ExitBootServices(), dynamic allocation is no longer permitted.
> +	 * Use the predefined FF-A shared buffer at runtime; otherwise allocate
> +	 * a fresh buffer during the boot phase.
> +	 */
> +	if (efi_at_runtime()) {
> +#if CONFIG_IS_ENABLED(ARM_FFA_TRANSPORT)
> +		if (IS_ENABLED(CONFIG_ARM_FFA_RT_MODE)) {
> +			if (comm_buf_size > CONFIG_FFA_SHARED_MM_BUF_SIZE)
> +				return NULL;
> +			comm_buf = ffa_shared_buf;
> +			if (!comm_buf)
> +				return NULL;
> +			efi_memset_runtime(comm_buf, 0, comm_buf_size);
> +		} else {
> +			return NULL;

This is problematic for the existing use case. With  the changes in the later patches
that swap all runtime call unconditionally every call to setup_mm_hdr() will return
EFI_OUT_OF_RESOURCES and none of the runtime services will work without FF-A.
There's nothing elegant we can do about this. We either Let the fucntions from efi_var_common.c
deal with the runtime part (which I think I prefer), or we define a similar runtime
available buffer for comm_buf.

<any additional details sent when the prompt was executed>

<any additional details from the code required to support your question>

> +		}
> +#else
> +		return NULL;
> +#endif
> +	} else {
> +		comm_buf = calloc(1, comm_buf_size);
> +		if (!comm_buf)
> +			return NULL;
> +	}
> +	return comm_buf;
> +}
> +
> +/**
> +static __efi_runtime u8 *setup_mm_hdr(void **dptr, efi_uintn_t payload_size,
> +				      efi_uintn_t func, efi_status_t *ret)
>  {
> -	const efi_guid_t mm_var_guid = EFI_MM_VARIABLE_GUID;
```

Sample commit message issue:

In this case, we keep the header and the summary of the commit and then
directly quote the part of the commit message that are incorrect.

```
commit 535a36aad18ce99e3270486fdb073bb5eb1f1c59
Author: Ilias Apalodimas <ilias.apalodimas@linaro.org>
MAITNAINERS: Add entry for ARM

Since I've added various features in the arm architecture
support and review most of the patches nowadays, add myself
as a co-maintainer

> MAITNAINERS: Add entry for ARM

This isn't a bug, but there's a typo (MAITNAINERS) in the subject line.
```
