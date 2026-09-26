# 📘 User Guide to Aestra

Welcome to Aestra! This guide explains how to use Aestra as your automated local judge for competitive programming, algorithmic contests, and technical coding interviews.

---

## 1. Where do I keep my code and files?

**Anywhere on your computer!** 

You do **NOT** need to save your files inside Aestra's installation folder. You can work wherever you normally write code—for example, on your Desktop, inside your Documents, or in your VS Code workspace:

```text
C:\Users\YourName\Documents\Contest\Problem_A\
├── solution.cpp             <-- Your code (or .py, .rs, .go)
└── cases\                   <-- Your sample test cases folder
    ├── 01.in
    ├── 01.out
    ├── 02.in
    └── 02.out
```

---

## 2. How to set up Test Cases?

When you open an algorithmic problem statement or online judge task, there are usually 1 to 3 "Sample Tests".

1. In your problem folder, create a new folder named **`cases`** (or `tests`).
2. Inside `cases/`, create matching pairs of files for each sample test:
   - **`01.in`**: Paste the sample input from the problem description.
   - **`01.out`** (or `01.ans`): Paste the expected output from the problem description.
3. For sample 2, create `02.in` and `02.out`, and so on.

### Example

Suppose the problem asks you to calculate the sum and maximum of an array:

**`cases/01.in`**:
```text
5 10 25 30 15
```

**`cases/01.out`**:
```text
SUM: 85 | MAX: 30
```

---

## 3. How to Test Your Solution

### Method A: Command-Line (Fastest in VS Code / Terminal)

Open your terminal in your problem directory and run:

```bash
aestra test solution.cpp --cases cases
```

*(You can test `.cpp`, `.py`, `.rs`, `.go`, or `.exe` files. Aestra automatically compiles C++, Rust, and Go in milliseconds with built-in caching!)*

**Expected output:**
```text
  +-- [Batch Runner] -------------------------------------------+
  |  Binary : solution.exe                                      |
  |  Cases  : 2 testcases from cases/                           |
  |  Limits : 2000ms CPU, 512MB RAM                             |
  +-------------------------------------------------------------+

  [ACCEPTED]        01.in          14.2ms    3.1MB
  [ACCEPTED]        02.in          12.8ms    3.2MB

  Summary: 2/2 accepted (ALL PASSED)
```

---

### Method B: Interactive Terminal (Zero Typing / Drag-and-Drop)

1. Open your terminal and simply type:
   ```bash
   aestra
   ```
2. Press **`2`** for **Batch Test Suite**.
3. When prompted for target file, simply **drag and drop** your `solution.cpp` from File Explorer into the terminal window and press **Enter**.
4. When prompted for testcases directory, **drag and drop** your `cases` folder into the terminal and press **Enter**.
5. Press **Enter** to accept default limits. Done!

---

## 4. Understanding Verdicts

Aestra grades each test case against hardware limits with microsecond accuracy:

| Verdict | Meaning | What to do |
| :--- | :--- | :--- |
| **`[ACCEPTED]`** (Green) | Correct! Output matches expected answer. | Ready to submit to the online judge! |
| **`[WRONG ANSWER]`** (Red) | Output does not match expected answer. | Inspect the highlighted diff to fix logic. |
| **`[TIME LIMIT EXCEEDED]`** (Yellow) | Code ran longer than time limit (default: 2000ms). | Optimize complexity (e.g. from $O(N^2)$ to $O(N \log N)$). |
| **`[MEMORY LIMIT EXCEEDED]`** (Magenta) | Exceeded RAM limit (default: 512MB). | Reduce vector/array sizes or memory allocations. |
| **`[RUNTIME ERROR]`** (Red) | Crashed (division by zero, out-of-bounds, segmentation fault). | Check array bounds and edge cases. |

### Visual Diff on Wrong Answer
When an answer is wrong, Aestra pinpoints the exact line difference:
```text
  [WRONG ANSWER]    02.in          15.1ms    3.1MB
      - Expected: 42
      + Output:   40
```

---

## 5. Running with Custom Input & Live Telemetry

If you want to manually run your code with custom input without creating files:

```bash
aestra run solution.py --input "10 20 30"
```

Or interactively:
1. Type `aestra`, select **`[1] Run Solution`**.
2. Enter `solution.py`.
3. Type or paste your input into `Standard input`.
4. Aestra prints execution time, peak memory usage, and program output.

---

## 6. Automated Stress Testing & Fuzzing (Finding Hidden Bugs)

Before submitting to an online judge, you might worry: *"What if my code crashes on large numbers or strange edge cases?"*

Aestra includes an automated **Fuzzer**:
1. Run `aestra` and select **`[3] Stress & Fuzz`**.
2. Enter your solution file (e.g., `solution.cpp`).
3. Enter iterations (e.g., `50` or `100`).

Aestra will generate dozens of randomized, boundary-pushing inputs directly in memory to verify your code doesn't crash, enter infinite loops, or leak memory.

---

## 7. Supported Programming Languages

Aestra comes with transparent multi-language compilation. You don't need Makefiles or build scripts:

| Language | Supported Extensions | Automatic Compiler Used |
| :--- | :--- | :--- |
| **Python** | `.py` | System `python` (Pure zero-compiler fallback) |
| **C++** | `.cpp`, `.cc`, `.cxx` | `g++`, `clang++`, or `MSVC cl.exe` |
| **C** | `.c` | `gcc` or `clang` |
| **Rust** | `.rs` | `rustc` |
| **Go** | `.go` | `go build` |
| **Binaries** | `.exe` | Direct native execution |

*Compiled binaries are automatically cached in `.aestra/build` by SHA-256 hash. Re-running unchanged code compiles in **0ms**.*
