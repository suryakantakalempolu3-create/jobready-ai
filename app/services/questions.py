"""Interview question generation + answer evaluation (AI first, offline bank/heuristics as fallback)."""
import random
import re
from .scoring import ROLE_SKILLS

ROLES = list(ROLE_SKILLS.keys())


def Q(q, a, kw):
    return {"question": q, "sample_answer": a, "keywords": kw}


TECH = {
    "Java Developer": [
        Q("What is the difference between JDK, JRE and JVM?", "The JVM executes bytecode and provides platform independence. The JRE bundles the JVM with core libraries needed to run Java programs. The JDK includes the JRE plus development tools such as the compiler (javac) and debugger.", ["jvm", "bytecode", "jre", "jdk", "compiler"]),
        Q("Explain the four pillars of OOP with Java examples.", "Encapsulation hides state behind private fields and getters/setters. Inheritance lets a subclass reuse a parent class with extends. Polymorphism allows one interface with many behaviours via overriding and overloading. Abstraction exposes essentials through abstract classes and interfaces.", ["encapsulation", "inheritance", "polymorphism", "abstraction", "interface"]),
        Q("What is the difference between ArrayList and LinkedList?", "ArrayList is backed by a dynamic array with O(1) random access but O(n) insertion in the middle. LinkedList is a doubly linked list with O(1) insertion/removal at known nodes but O(n) access. I prefer ArrayList by default.", ["array", "linked", "o(1)", "o(n)", "access"]),
        Q("How does HashMap work internally?", "HashMap stores entries in buckets chosen by hashCode(). Collisions are handled with linked lists that become balanced trees when a bucket grows large (Java 8+). equals() finds the right key, and the table resizes when the load factor (0.75) is exceeded.", ["hashcode", "equals", "bucket", "collision", "load factor"]),
        Q("What is the difference between checked and unchecked exceptions?", "Checked exceptions (e.g. IOException) must be handled or declared and are verified at compile time. Unchecked exceptions extend RuntimeException (e.g. NullPointerException) and represent programming errors, so handling is optional.", ["compile", "runtimeexception", "throws", "try", "catch"]),
        Q("What are the advantages of Spring Boot?", "Spring Boot provides auto-configuration, starter dependencies, an embedded server and production-ready features like actuator, so I can build REST services quickly without heavy XML configuration.", ["auto-configuration", "starter", "embedded", "dependency injection", "rest"]),
        Q("Explain multithreading and how you avoid race conditions in Java.", "Multithreading runs tasks concurrently using Thread or ExecutorService. To avoid race conditions I use synchronized blocks, locks, atomic classes or concurrent collections so shared state is accessed safely.", ["thread", "synchronized", "lock", "atomic", "concurrent"]),
    ],
    "Python Developer": [
        Q("What is the difference between a list and a tuple in Python?", "Lists are mutable, so they can be changed after creation, while tuples are immutable and hashable, which makes them usable as dictionary keys and slightly faster and safer for fixed data.", ["mutable", "immutable", "hashable", "tuple", "list"]),
        Q("Explain decorators and give a use case.", "A decorator is a function that wraps another function to add behaviour without changing its code. Common uses are logging, authentication checks, caching and timing, applied with the @decorator syntax.", ["wrap", "function", "@", "logging", "authentication"]),
        Q("What is the GIL and how does it affect concurrency?", "The Global Interpreter Lock lets only one thread execute Python bytecode at a time in CPython. CPU-bound work needs multiprocessing, while I/O-bound work still benefits from threads or asyncio.", ["gil", "thread", "multiprocessing", "asyncio", "cpython"]),
        Q("What are generators and why are they useful?", "Generators use yield to produce values lazily, one at a time, so they use little memory and can represent large or infinite streams of data.", ["yield", "lazy", "memory", "iterator", "stream"]),
        Q("Compare Flask and Django.", "Flask is a lightweight micro-framework that gives flexibility and lets me pick components. Django is batteries-included with an ORM, admin and auth, which speeds up large projects. I choose Flask for small APIs and Django for full applications.", ["flask", "django", "orm", "micro", "admin"]),
        Q("How do you manage dependencies and virtual environments?", "I create a virtual environment with venv, install packages with pip, pin versions in requirements.txt and keep secrets in environment variables so projects stay reproducible and isolated.", ["venv", "pip", "requirements", "isolated", "version"]),
        Q("What is the difference between deep copy and shallow copy?", "A shallow copy creates a new container but references the same nested objects, so changes to nested items affect both. A deep copy recursively copies nested objects so the copies are fully independent (copy.deepcopy).", ["shallow", "deep", "reference", "nested", "copy"]),
    ],
    "Software Developer": [
        Q("Explain the difference between an array and a linked list.", "Arrays store elements contiguously and give O(1) index access but costly insertions. Linked lists store nodes with pointers, giving cheap insertions and deletions but O(n) access and extra memory per node.", ["contiguous", "pointer", "o(1)", "o(n)", "insertion"]),
        Q("What is time complexity? Compare O(n) and O(log n) with an example.", "Time complexity describes how runtime grows with input size. Linear search is O(n) because it may check every item, while binary search on sorted data is O(log n) because it halves the search space each step.", ["input size", "binary search", "linear", "log n", "sorted"]),
        Q("What is the difference between SQL and NoSQL databases?", "SQL databases are relational with fixed schemas, joins and ACID transactions. NoSQL databases like MongoDB store flexible documents and scale horizontally. The choice depends on data structure and consistency needs.", ["relational", "schema", "acid", "mongodb", "scal"]),
        Q("What is REST and what are common HTTP methods?", "REST is an architectural style where resources are identified by URLs and manipulated using stateless HTTP methods: GET reads, POST creates, PUT/PATCH updates and DELETE removes, returning status codes like 200, 201, 400 and 404.", ["stateless", "get", "post", "put", "status code"]),
        Q("Explain Git branching and how you resolve merge conflicts.", "Branches let me work on features in isolation. When a merge conflicts, I open the marked files, decide which changes to keep, test, commit the resolution and then complete the merge or rebase.", ["branch", "merge", "conflict", "commit", "rebase"]),
        Q("What are SOLID principles?", "SOLID is five design principles: Single responsibility, Open/closed, Liskov substitution, Interface segregation and Dependency inversion. They make code easier to maintain, test and extend.", ["single responsibility", "open", "liskov", "interface", "dependency"]),
        Q("How do you debug a failing production issue?", "I reproduce the issue, check logs and monitoring, isolate the failing component, form a hypothesis, fix it with a test, deploy carefully and then write a short post-mortem to prevent recurrence.", ["logs", "reproduce", "isolate", "test", "root cause"]),
    ],
    "Web Developer": [
        Q("What is the CSS box model?", "Every element is a box made of content, padding, border and margin. box-sizing: border-box makes width include padding and border, which simplifies layouts.", ["content", "padding", "border", "margin", "box-sizing"]),
        Q("Explain var, let and const in JavaScript.", "var is function-scoped and hoisted, while let and const are block-scoped. const prevents reassignment of the binding, and I default to const, using let when a value changes.", ["scope", "hoist", "block", "reassign", "const"]),
        Q("What are promises and async/await?", "A promise represents a future value that is pending, fulfilled or rejected. async/await is syntax over promises that makes asynchronous code read sequentially, with try/catch for errors.", ["promise", "async", "await", "asynchronous", "catch"]),
        Q("How do you make a website responsive?", "I use a mobile-first approach with flexible units, CSS grid/flexbox, media queries and responsive images, and test on multiple screen sizes.", ["media query", "flexbox", "grid", "mobile", "viewport"]),
        Q("What is the virtual DOM in React?", "React keeps a lightweight copy of the DOM, diffs it against the previous version when state changes and applies only the minimal real DOM updates, which improves performance.", ["virtual dom", "diff", "state", "render", "component"]),
    ],
    "Data Analyst": [
        Q("Explain different types of SQL joins.", "INNER JOIN returns matching rows, LEFT JOIN keeps all left rows with matches or NULLs, RIGHT JOIN does the reverse and FULL JOIN keeps all rows from both tables.", ["inner", "left", "right", "full", "null"]),
        Q("How do you handle missing data?", "I first understand why data is missing, then drop rows if few are affected, or impute using mean, median or mode, or model-based methods, and document the choice.", ["missing", "impute", "mean", "median", "drop"]),
        Q("What is the difference between mean, median and mode?", "Mean is the average, median is the middle value and is robust to outliers, and mode is the most frequent value. I choose based on distribution and outliers.", ["average", "middle", "outlier", "frequent", "distribution"]),
        Q("How would you present insights to non-technical stakeholders?", "I start with the business question, show a few clear visuals in Power BI or Tableau, highlight the key insight and recommended action, and avoid jargon.", ["stakeholder", "visual", "insight", "dashboard", "action"]),
    ],
}

HR = [
    Q("Tell me about yourself.", "I am a final-year student with a strong interest in software development. I have built projects that use [your key skills], completed [internship or course], and I enjoy learning quickly. I am looking for a role where I can contribute and grow as an engineer.", ["student", "projects", "skills", "learn", "role"]),
    Q("What are your strengths and weaknesses?", "My strength is problem solving, for example I debugged a tricky issue in my project by tracing logs step by step. A weakness is that I used to take on too much, so I now prioritise tasks and ask for help earlier.", ["strength", "example", "weakness", "improve", "learn"]),
    Q("Why should we hire you?", "I bring solid fundamentals, hands-on project experience and a fast learning attitude. I am dependable, communicate clearly and can start contributing quickly while continuing to grow with the team.", ["skills", "project", "learn", "team", "contribute"]),
    Q("Describe a challenge you faced in a project and how you handled it.", "In my final-year project our API was slow. I profiled it, found repeated database queries, added indexing and caching, and cut response time by about 60%. I learned to measure before optimising.", ["challenge", "solution", "result", "learned", "team"]),
    Q("Where do you see yourself in five years?", "I see myself as a skilled developer who has taken ownership of significant features, mentored newcomers and deepened expertise in areas the company values, possibly moving towards a senior or lead role.", ["grow", "skills", "senior", "contribute", "learn"]),
    Q("How do you handle pressure and tight deadlines?", "I break work into small tasks, prioritise by impact, communicate early about risks and stay focused. During exams and project submissions this approach helped me deliver on time.", ["prioritise", "plan", "communicate", "deadline", "calm"]),
    Q("Tell me about a time you worked in a team.", "In a college hackathon our team of four split the work by strengths. I built the backend while others did UI and testing. We held short daily syncs, resolved disagreements openly and finished with a working demo.", ["team", "role", "communication", "conflict", "result"]),
    Q("Why do you want to work for our company?", "I researched your products and values and admire your focus on quality and learning. My skills align with the role, and I believe I can contribute while growing in a supportive engineering culture.", ["company", "values", "skills", "contribute", "research"]),
]


def _bank(role, qtype):
    tech = TECH.get(role, TECH["Software Developer"])
    if qtype == "technical":
        return list(tech)
    if qtype == "hr":
        return list(HR)
    return tech + HR


def generate_questions(ai, role, qtype, count):
    """Returns (questions, source)."""
    kind = {"technical": "technical", "hr": "HR/behavioural", "mixed": "a mix of technical and HR/behavioural"}[qtype]
    data = ai.complete_json(
        f"Generate {count} {kind} interview questions for a fresher/junior <data>{role}</data> candidate. "
        'Return JSON: {"questions":[{"question":str,"sample_answer":str (3-5 sentences, first person),'
        '"keywords":[5 short lowercase key concepts a good answer mentions],"type":"technical"|"hr"}]}', 3500)
    qs = (data or {}).get("questions") if isinstance(data, dict) else None
    if qs:
        clean = [{"question": str(x["question"])[:300], "sample_answer": str(x.get("sample_answer", ""))[:1500],
                  "keywords": [str(k).lower()[:40] for k in x.get("keywords", [])][:8], "type": x.get("type", qtype)}
                 for x in qs if isinstance(x, dict) and x.get("question")]
        if clean:
            return clean[:count], "ai"
    bank = _bank(role, qtype)
    random.shuffle(bank)
    return bank[:count], "offline"


def evaluate_answer(ai, role, q, answer):
    """Returns feedback dict with score 0-10 plus 'source'."""
    data = ai.complete_json(
        f"Interview role: <data>{role}</data>\nQuestion: <data>{q['question']}</data>\n"
        f"Candidate answer: <answer>{answer}</answer>\nReference points: {q.get('keywords', [])}\n"
        'Evaluate fairly like a kind but honest interviewer. Return JSON: {"score":0-10 number,'
        '"strengths":[1-3 short strings],"improvements":[1-3 short actionable strings],"ideal_answer":str}', 1500)
    if isinstance(data, dict) and isinstance(data.get("score"), (int, float)):
        return {"score": max(0, min(10, round(float(data["score"]), 1))),
                "strengths": [str(x)[:250] for x in data.get("strengths", [])][:3],
                "improvements": [str(x)[:250] for x in data.get("improvements", [])][:3],
                "ideal_answer": str(data.get("ideal_answer") or q.get("sample_answer", ""))[:1500], "source": "ai"}
    return heuristic_evaluate(q, answer)


def heuristic_evaluate(q, answer):
    low = answer.lower()
    words = len(answer.split())
    kws = q.get("keywords", [])
    hits = [k for k in kws if k.lower() in low]
    missed = [k for k in kws if k.lower() not in low]
    cover = len(hits) / len(kws) if kws else 0.5
    length = min(words / 50, 1.0)
    structure = 1.0 if re.search(r"\b(for example|for instance|because|first|result|e\.g\.)\b", low) else 0.4
    score = round(10 * (0.6 * cover + 0.3 * length + 0.1 * structure), 1)
    strengths, improvements = [], []
    if hits:
        strengths.append(f"You covered key ideas: {', '.join(hits[:4])}.")
    if words >= 40:
        strengths.append("Good level of detail in your answer.")
    if missed:
        improvements.append(f"Mention important concepts you missed: {', '.join(missed[:4])}.")
    if words < 40:
        improvements.append("Your answer is short. Aim for 4-6 sentences with a definition and an example.")
    if structure < 1:
        improvements.append("Add a concrete example or reason (e.g. “for example, in my project…”).")
    return {"score": score, "strengths": strengths or ["You attempted the question — keep practising."],
            "improvements": improvements or ["Great answer! Practise delivering it confidently."],
            "ideal_answer": q.get("sample_answer", ""), "source": "offline"}
