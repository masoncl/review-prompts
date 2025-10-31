Produce a report of regressions found based on this template.

- The report must be in plain text only.  No markdown, no special characters,
absolutely and completely plain text fit for the linux kernel mailing list.

- Any long lines present in the unified diff should be preserved, but
any summary, comments or questions you add should be wrapped at 78 characters

- Never mention line numbers when referencing code locations, instead indicate
the function name and also call chain if that makes it more clear.  Avoid
complex paragraphs and instead use call chains funcA()->funcB() to explain.

- Never include bugs filtered out as false positives in the report

- Always end the report with a blank line.

- The report must be conversational with undramatic wording, fit for sending
as a reply to the patch introducing the regression on the LKML mailing list

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
    folio?'
  - Don't say: 'Does this loop have a bounds checking issue?' Name the
    variable you think we're overflowing: "Does this code overflow xyz[]?"

- Don't make long confusing paragraphs, ask short questions backed up by
code snippets (in plain text), or call chains if needed.

Create a TodoWrite for these items, all of which your report should include:

- [ ] git sha of the commit
- [ ] Author: line from the commit
- [ ] One line subject from the commit

- [ ] A brief (max 3 sentence) summary of the commit.  Use the full commit
message if the bug is in the commit message itself.

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
  - [ ] snip entire files unrelated to the review comments
  - [ ] snip entire hunks from quoted files if they unrelated to the review
  - [ ] snip entire functions from the quoted hunks unrelated to the review
  - [ ] snip any portions of large functions from quoted hunks if unrelated to the review
  - [ ] ensure you only keep enough quoted material for the review to make sense
  - [ ] snip trailing hunks and files after your last review comments unless
        you need them for the review to make sense
  - [ ] The review should contain only the portions of hunks needed to explain the review's concerns.

Sample:

```
commit 06e4fcc91a224c6b7119e87fc1ecc7c533af5aed
Author: Kairui Song <kasong@tencent.com>

mm, swap: only scan one cluster in fragment list
    
<brief description>

> diff --git a/mm/swapfile.c b/mm/swapfile.c
> index b4f3cc7125804..1f1110e37f68b 100644
> --- a/mm/swapfile.c
> +++ b/mm/swapfile.c

[ ... ] <-- only if you've snipped text

> @@ -926,32 +926,25 @@ static unsigned long cluster_alloc_swap_entry(struct swap_info_struct *si, int o
>  		swap_reclaim_full_clusters(si, false);
>  
>  	if (order < PMD_ORDER) {
> -		unsigned int frags = 0, frags_existing;
> -
>  		while ((ci = isolate_lock_cluster(si, &si->nonfull_clusters[order]))) {
>  			found = alloc_swap_scan_cluster(si, ci, cluster_offset(si, ci),
>  							order, usage);
>  			if (found)
>  				goto done;
> -			/* Clusters failed to allocate are moved to frag_clusters */
> -			frags++;
>  		}
>  
> -		frags_existing = atomic_long_read(&si->frag_cluster_nr[order]);
> -		while (frags < frags_existing &&
> -		       (ci = isolate_lock_cluster(si, &si->frag_clusters[order]))) {
> -			atomic_long_dec(&si->frag_cluster_nr[order]);
                        ^^^^

Is it ok to remove this atomic_long_dec()?  It looks like the counter
updates are getting lost.

<any additional details from the code required to support your question>

> -			/*
> -			 * Rotate the frag list to iterate, they were all
> -			 * failing high order allocation or moved here due to
> -			 * per-CPU usage, but they could contain newly released
> -			 * reclaimable (eg. lazy-freed swap cache) slots.
> -			 */
> +		/*
> +		 * Scan only one fragment cluster is good enough. Order 0
> +		 * allocation will surely success, and large allocation
> +		 * allocation will surely success, and large allocation
                 ^^^^^^^^ this isn't a bug, but you've duplicated this line

> +		 * failure is not critical. Scanning one cluster still
> +		 * keeps the list rotated and reclaimed (for HAS_CACHE).
> +		 */
> +		ci = isolate_lock_cluster(si, &si->frag_clusters[order]);
> +		if (ci) {
>  			found = alloc_swap_scan_cluster(si, ci, cluster_offset(si, ci),
>  							order, usage);
>  			if (found)
>  				goto done;
> -			frags++;
>  		}
>  	}
>  
```
