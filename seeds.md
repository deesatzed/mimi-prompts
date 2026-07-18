# Mini-Prompt Panel

## Refined Core Prompts

### 1. Explain It Simply

You lost me. Explain `[topic]` to a college freshman with no prior background. Start with the basic purpose, use a concrete example, and avoid jargon unless you define it.

### 2. Required or Scope Drift?

Explain why `[change or task]` is necessary to achieve the stated goal. Identify the specific requirement, user need, or risk it supports. Then determine whether it is essential work, useful but optional work, or scope drift.

### 3. Why Should I Care?

Why should an actual user care about `[feature or idea]`? Describe the practical benefit, what becomes easier or better, and what happens if the user does not have it.

### 4. Work Backward from Real Problems

Start with real, known end-user problems—not proposed features. For each problem:

1. Identify who experiences it and how often.
2. Describe the current workaround and its weaknesses.
3. Determine whether data is available to test the problem.
4. Define measurable success and failure criteria.
5. Propose three solutions: a practical improvement, a better workflow or UX, and a more novel approach.

Explain everything in simple terms.

### 5. Interactive Terminal Guide

Help me set up and run this in another terminal. Give me one step at a time, or two steps only when they are extremely simple.

After each step, stop and wait for:

* `C` — continue
* `T` — troubleshoot the current step
* `E` — explain the step to a novice

Do not provide later steps until I respond.

### 6. Confirm We Are in Sync

Before continuing, explain `[project or feature]` at a college-freshman level:

* What problem it solves
* What it actually does
* Who would use it
* Why they would want it
* The normal workflow
* What the user sees and experiences
* What it does not do

Use one concrete example from beginning to end.

### 7. Alien-Goggles Brainstorm

Treat ideas as living organisms that must survive, adapt, compete, and provide value. Examine `[problem space]` through “alien goggles,” ignoring familiar assumptions about how it is normally solved.

Generate insights from:

1. First principles
2. Second-order consequences
3. Unusual but plausible user behavior
4. Environmental pressures
5. Ways the idea could evolve into something more useful

Separate practical insights from speculative ones.

### 8. Find Real Unmet Needs

Identify important user needs in `[space]` that are unmet, poorly met, or handled through frustrating workarounds. Do not start with technology or a proposed product.

For each need, explain:

* Who has the problem
* What they do now
* Why existing solutions are insufficient
* How serious or frequent the problem is
* What evidence would confirm it

Reject ideas that are merely impressive technology looking for a use.

### 9. Contrarian Product Review

Act as an independent contrarian reviewer hired to uncover weaknesses in `[project]`.

Review every major purpose, feature, workflow, assumption, and design choice for:

* Unnecessary complexity
* Poor UX
* Weak user value
* Redundancy
* Hidden maintenance costs
* Unsafe assumptions
* Features that are clever but unnecessary

For every criticism, propose a mitigation. Then produce a revised assessment, prioritized recommendations, and the next three actions.

### 10. Update, Commit, and Push

Update the project handoff document to reflect the work completed, decisions made, unresolved questions, tests performed, and recommended next steps.

Then:

1. Review the changes for accidental or unrelated edits.
2. Run the appropriate tests.
3. Summarize the files changed.
4. Create a clear commit message.
5. Commit and push the changes to the current branch.

Stop and explain any test failure, merge conflict, credential issue, or potentially destructive action before proceeding.

---

## Expanded Prompt Panel

### 11. Define the Actual User

Identify the primary user for `[product or feature]`. Describe the situation they are in, the task they are trying to complete, their current workaround, their technical ability, and what a successful outcome looks like. Do not use vague labels such as “users” or “developers.”

### 12. State the Job to Be Done

Express the need behind `[feature]` as a job-to-be-done:

> When `[situation]`, the user wants to `[motivation or task]`, so they can `[desired outcome]`.

Then determine whether the proposed feature directly helps complete that job.

### 13. Separate Problem from Solution

Separate the current proposal into:

1. The underlying user problem
2. The assumed solution
3. Evidence supporting the problem
4. Evidence supporting this particular solution
5. Alternative solutions that could solve the same problem more simply

Call out where we may be confusing enthusiasm for the solution with evidence of demand.

### 14. Assumption Audit

List the assumptions behind `[plan or feature]`. Classify each as:

* Confirmed
* Reasonable but untested
* High-risk
* Probably false

For every important untested assumption, propose the fastest and cheapest way to test it.

### 15. Try to Falsify It

Assume our current belief about `[idea]` is wrong. Design tests that could disprove its usefulness, feasibility, safety, or demand. Define what result would cause us to stop, redesign, or continue.

### 16. Define Success Before Building

Before proposing implementation, define measurable success for `[project]`.

Include:

* Primary user outcome
* Adoption or usage signal
* Time or effort saved
* Quality or accuracy measure
* Failure threshold
* Evidence that would justify further investment

Avoid vanity metrics.

### 17. Compare Three Solution Levels

Propose three ways to address `[need]`:

1. **Minimum:** the simplest credible improvement
2. **Strong:** the best balance of value, effort, and UX
3. **Ambitious:** a more novel approach with greater potential and risk

Compare user value, complexity, dependencies, risks, and testability.

### 18. Simplify the Workflow

Map the current workflow for `[task]` step by step. Identify unnecessary decisions, repeated work, context switching, confusing terminology, and avoidable waiting.

Then redesign it to minimize:

* Number of steps
* Cognitive load
* Required configuration
* Opportunities for mistakes
* Time to first useful result

### 19. UX Friction Audit

Walk through `[workflow]` as a first-time user. At every step, ask:

* What does the user need to understand?
* What could confuse them?
* What could go wrong?
* How would they recover?
* Is the next action obvious?

Produce a prioritized list of UX problems and specific improvements.

### 20. Novice-versus-Expert Design

Evaluate `[tool or workflow]` separately for a novice and an expert. Identify where their needs conflict.

Propose defaults that protect and guide novices while allowing experts to move quickly, customize behavior, and bypass unnecessary guidance.

### 21. Minimum Lovable Version

Define the smallest version of `[product]` that solves a meaningful problem well enough that users would voluntarily use it again. Remove features that do not contribute directly to that repeatable value.

Explain what belongs in version one, what should wait, and what should be rejected.

### 22. Feature Necessity Test

For each proposed feature in `[project]`, answer:

1. Which user problem does it solve?
2. How frequently does that problem occur?
3. What evidence supports it?
4. What happens without the feature?
5. Could a simpler solution work?
6. How will we know the feature is successful?

Recommend keep, simplify, defer, combine, or remove.

### 23. Existing-Solution Comparison

Identify how users currently solve `[problem]`, including manual workarounds, general-purpose tools, direct competitors, and doing nothing.

Compare them by convenience, cost, learning curve, reliability, flexibility, and user trust. State clearly why a new solution would be meaningfully better.

### 24. Duplication and Overlap Audit

Review `[tool, app, or feature set]` for duplicated capabilities. Identify features that overlap with the operating system, existing applications, AI assistants, command-line tools, or one another.

Recommend which capability should be primary, integrated, optional, or removed.

### 25. Edge-Case Review

Identify the most important edge cases for `[workflow or feature]`, including incomplete data, incorrect permissions, unusual environments, interrupted operations, novice mistakes, and conflicting settings.

For each edge case, define expected behavior, user messaging, recovery steps, and required tests.

### 26. Safety and Reversibility Review

Evaluate `[operation or automation]` for potential harm. Identify anything that could delete data, expose private information, alter configuration, create costs, or become difficult to reverse.

Prefer read-only inspection, previews, backups, explicit confirmation, and reversible changes. Clearly mark any action that cannot be safely undone.

### 27. Pre-Mortem

Assume `[project]` failed six months after launch. Generate the most plausible reasons, including lack of demand, confusing UX, excessive setup, unreliable results, weak differentiation, maintenance burden, and loss of user trust.

Rank the failure modes and propose preventive actions for the most serious ones.

### 28. Novelty Reality Check

Evaluate whether `[idea]` is genuinely useful, merely technically novel, or a familiar feature with new terminology.

Explain:

* What is actually new
* What user outcome improves
* Whether the novelty is necessary
* Whether simpler existing methods provide the same value
* What evidence would justify pursuing it

### 29. Decision Memo

Create a concise decision memo for `[decision]` containing:

* The problem
* Relevant evidence
* Options considered
* Trade-offs
* Recommended choice
* Why the alternatives were rejected
* Risks and mitigations
* What would cause us to revisit the decision

Clearly separate facts, assumptions, and opinions.

### 30. Implementation Handoff

Create or update a handoff document so another developer or AI agent can continue the work without relying on prior conversation history.

Include:

* Project purpose
* End-user problem
* Current state
* Architecture and important files
* Decisions already made
* Completed work
* Tests and results
* Known issues
* Safety constraints
* Exact next steps
* Acceptance criteria
* Commands needed to resume work

Do not include obsolete plans or work already completed.

### 31. Git Clone test
After a commit and push, lets test a git clone and performa a real local run through after a new git clone in a new location with a new setip

### 32. Not sure
 not sure, but it needs to be user friendly, adds value or fulfulls an existing need, and be used or useful

### 33. Update Doc
Update all relative docuemtns such as README, setup, landing pages, etc that redlect the current state, recent eresults, and updated features.

### 34. Current Status
Explain teh current status in terms of what was built, what was tested, those results, current problems or obstacles, and remaining steps
