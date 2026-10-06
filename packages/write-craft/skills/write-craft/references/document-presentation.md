# Document presentation

Use this reference when a substantive Write Craft draft must be delivered as a
formatted document, or when the user asks to improve both the writing and the
visual hierarchy. It defines platform-neutral presentation decisions. The
destination platform's document Skill or editor still owns the actual write,
styles, permissions, and readback.

## Make formatting carry meaning

Formatting should help the reader locate the conclusion, status, evidence,
boundary, and requested action. It should not compensate for an unclear
argument or make an unsupported claim look authoritative.

Finish the information structure before styling it. When editing an existing
document, preserve its useful visual language and change only the elements that
obscure hierarchy, status, or comparison.

## Keep the first screen useful

For a decision entry or business-facing summary, the opening view should make
the source-supported core easy to locate:

- a concise title that normally fits within one or two lines at the expected
  reading width;
- the recommendation, current conclusion, or scope boundary;
- the current evidence state or most consequential uncertainty; and
- the reader's real decision or input, when the source supplies one.

Do not shorten a title by deleting a scope-bearing condition. If a long project
name is required, shorten the explanatory subtitle instead.

## Use a restrained hierarchy

- Use headings for real sections that belong in navigation, not for every
  field, sentence, or method.
- Keep heading levels consistent and avoid adding bold markup inside every
  heading merely to make it look stronger.
- Give each paragraph one job. Split a dense paragraph when it combines, for
  example, current status with the limits of historical evidence.
- Use lists for genuine steps, choices, materials, or checks. Keep reasoning,
  explanation, and transitions as prose.
- For a long document that serves two audiences, keep a self-contained
  decision entry first and a clearly named engineering appendix afterward.

## Budget emphasis

Treat emphasis as a limited resource:

- Use one strong summary treatment near the top when it materially improves
  scanning. A callout, shaded lead, or equivalent is enough; do not create one
  for every section.
- Bold a short label or the few words that carry the decision. Do not bold whole
  paragraphs or repeat the same conclusion in several visual forms.
- Apply the editorial pass in `clear-chinese.md` across visual forms too: a
  callout, heading, and table should not each retell the same paragraph without
  a useful navigation, comparison, or independent-reading role.
- Prefer the platform's default typeface, body size, spacing, and native
  heading styles. Mixed fonts and manual size changes usually weaken
  consistency and portability.
- Use emoji only when it has a stable navigation or semantic role. Do not add an
  emoji to every heading, convert status into decorative icons, or use star
  ratings without a defined scale.
- Do not insert horizontal rules between every section. Heading spacing already
  provides separation in most native document editors.

## Use color semantically

Color is optional. When it helps, use one primary accent family and a small,
consistent status vocabulary:

- blue for neutral information or explanation;
- yellow for attention or an unresolved item;
- red for a blocker, error, or material risk; and
- green only for a genuinely verified or approved state.

Always state the meaning in words. Color must never be the only way to
distinguish `已验证`, `待确认`, `风险`, or `不通过`. Avoid coloring ordinary prose
for decoration, and do not turn goals or recommendations green merely because
they are desirable.

## Choose tables and diagrams deliberately

Use a native table for compact, static row-and-column relationships such as
scope, options, stages, responsibilities, or acceptance criteria. Keep the
number of columns small enough to read at the destination width, use a clear
header row, and avoid placing long narrative paragraphs into cells.

Use a diagram only when it makes a real sequence, branching decision, system
relationship, or timeline easier to understand than prose. A decorative
architecture picture does not make an unsupported workflow true.

Prefer the platform's native heading navigation for long documents. Do not add
a manually maintained table of contents when it merely duplicates reliable
native navigation.

## Separate content from platform operations

Write Craft may choose semantic structure such as a lead summary, heading
levels, a comparison table, or labels for status and uncertainty. It does not
own Feishu permissions, browser editing, font controls, block IDs, or document
write operations. Route those actions to the destination platform's document
capability.

If the user asks only to beautify or operate an existing platform document,
without substantive decision writing, the platform document Skill should lead.
If the user asks for both, Write Craft owns the content hierarchy and the
platform Skill applies it safely.

## Verify the rendered result

When a real destination document is available and visual inspection is in
scope, check the rendered result at a representative reading width:

- title wrapping and first-screen hierarchy;
- paragraph density and heading rhythm;
- table width, overflow, and cell readability;
- whether callouts, bold, color, and emoji still reflect their intended
  semantics; and
- whether native navigation and the appendix boundary remain clear.

After a platform write, read back the affected content. A successful write
response does not by itself prove that the document is complete or visually
sound. If rendered inspection was not available, report structure as verified
and visual quality as unverified rather than guessing.
