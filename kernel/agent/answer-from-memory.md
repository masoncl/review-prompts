# Answering questions about the kernel from memory

You are given one or more related questions about the Linux kernel. You have
**no kernel sources and no tools**. Answer from memory, for the **newest
mainline Linux kernel you know**.

`kernel/scripts/build-guides.py` runs you, and adds the questions after these
instructions.

Another model answers the same questions by reading the kernel sources. A
build then writes a guide for patch review from the difference between that
model's answers and yours. So say plainly what you believe. A confident wrong
answer and an honest "I do not know" are both useful. A vague answer is not.

## Ground rules

1. **No tools, no lookups.** Answer in one turn from memory.
2. **Newest mainline.** Describe the newest mainline kernel you know.
   Describe one version only, and give no history: no "since v6.x", no "used
   to", no commit ids.
3. **Give exact names.** Give the function, struct, field, config symbol and
   file names you believe are right.
   - Write a function as `name()`.
   - Write a struct, union or enum tag with its keyword, as in
     `struct folio`.
   - Write a path in backticks and include the directory, as in `mm/vma.c`.
   - Never write a line number.
   - If you remember that something exists but not its name, say so in words.
     Don't invent a plausible name.
   - If you believe a name does not exist in the kernel you describe, write
     the name as plain text, without backticks.
4. **The questions may name things you do not know.** They can name things
   newer than your knowledge. If you do not recognise a name, say so. Don't
   guess what it does from how it is spelled.

## What to write, for each question

- The questions belong together. Put each fact under the one question that
  asks for it. Don't repeat in one answer what another says.
- **Be brief.** Write a few lines for each question. Give the facts that
  answer the question, and leave out the rest of what you know about the
  subject. If you do not know, say so in one line.
- Say first what goes wrong. Then give the facts that someone who reviews a
  patch needs.
- Where a question asks what usage is unsafe, write a bullet that starts
  `**Unsafe usage**:`. Give the pattern and the precondition that makes it
  unsafe. Then give the usage that looks similar and is correct, and name a
  function you believe shows it.
- You are writing down knowledge, not reviewing the kernel. Don't list
  functions you think are buggy.
- Write each answer as a short bulleted list. One fact per bullet, the name
  or the condition first. Use a table where several things share the same
  attributes.
- Some questions have a line that says the question is a quick check. For
  those, write two or three short sentences, with no list.
- Each question comes with a title. Don't repeat the title, and don't add a
  heading.
- Don't open with "Yes" or "No". Don't open with a bold label, except
  `**Unsafe usage**:`.
- Wrap at 80 columns.
- End the last answer with one line that starts `Kernel assumed:`. On that
  line, give the version you had in mind and, in a few words, what you were
  least sure of.

## Output

For each question, in the order given, print a line containing only
`=== answer: <the question's id> ===` and then the markdown for that answer.
Print nothing else: no remarks between the answers and no code fence.
