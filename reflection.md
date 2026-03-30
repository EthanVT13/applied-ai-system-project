# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
The user need to be able to add owner and pet information, add and manage tasks, create and view a schedule.
- What classes did you include, and what responsibilities did you assign to each?
I included four classes: Owner, Pet, Task, and Scheduler. Owner stores user info and manages a list of pets, Pet holds basic animal details, and Task represents a single care activity with a priority and duration. Scheduler is the central class that brings everything together, generating a daily plan and explaining its reasoning.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
Yes, the design changed during implementation. The most notable addition was a pet field on Task so each task knows which pet it belongs to. We also added add_task() to Scheduler since there was previously no way to populate tasks before generating a schedule.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
The scheduler sorts tasks by priority, fits them into the owner's time budget, and warns about time conflicts. Time and priority were chosen first because they reflect real-world limits. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
The scheduler greedily picks tasks by priority and stops when time runs out, which means a long low-priority task might get skipped even if shorter ones could have fit around it. For a pet care app this is fine — you'd always rather make sure meds and feeding happen before worrying about enrichment activities.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used it for design ideas and using descriptive prompts clearly outlining my issue worked well.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
Claude Code's first version of generate_schedule() returned every pending task without checking available time. I caught it, added the time-tracking loop, and tested it with a short availability window to confirm it worked.


---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
Sorting by time, priority ordering, spawning recurring tasks, conflict detection, enforcing time budgets, and pet and status filtering.
Why were these tests important? This is precisely where the bug would cause the wrong schedule to be silently computed – a pet could be missed medication or double-booked without any error message.


**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
High for the core logic. All 18 tests pass. Tests include priority, time budgeting, recurrence, and conflicts. Less confident in the UI layer. Also less confident in multi-pet conflict scenarios, which have not been tested yet.
Pet with 100+, 2 recurring tasks that conflict after auto-spawning, and an owner with zero available minutes.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I was the most satisfied with seeing the result of the app and using it myself.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would try to make a sleeker design, I feel like the organization of this project can be more efficient.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
Designing the system on paper first made the AI's output significantly better — when I gave Claude Code a clear UML with defined relationships, it generated cleaner and more accurate code than when I described things vaguely. The AI is only as good as the context you give it.
