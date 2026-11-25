# Smart Exam Scheduling System (Complete Capstone Starter)

## Assignment
Project 8: Exam Timetable Generation Using Graph Coloring.

## Features
- Multi-page Streamlit navigation
- Dashboard and KPIs
- Subject/student enrollment editor
- CSV import for enrollment data
- Conflict graph visualization
- Shared-student conflict list
- Backtracking graph-coloring solver
- Searches increasing color counts to find a minimum-slot coloring
- Timetable with date, slot, time and room labels
- Conflict validation
- Slot-wise timetable
- CSV and JSON timetable export
- Algorithm trace with assignment and backtracking events
- Conflict-degree chart
- Benchmark repeated runs
- Enrollment export

## Run locally
1. Extract the ZIP.
2. Open folder in VS Code.
3. Create/activate virtual environment (optional but recommended).
4. Install dependencies:
   `python -m pip install -r requirements.txt`
5. Run:
   `streamlit run app.py`

## Sample data
Sample subjects and enrollment IDs are loaded automatically. Use the Data Management page to edit them or upload a CSV with columns:
- `Subject`
- `Student IDs` (comma-separated IDs)

## Algorithm explanation
Each subject is a graph vertex. If two subjects share at least one student, an edge is added. The solver orders subjects by degree and attempts graph coloring with k colors, starting at k=1 and increasing until a solution is found. Colors correspond to exam slots.

## Complexity
Backtracking graph coloring has exponential worst-case runtime. A broad bound is O(k^V), where V is the number of subjects and k is the number of candidate colors. Graph storage is O(V+E), with O(V) recursion and assignment state.

## Capstone checklist
- Add your own larger test datasets.
- Capture screenshots of every page.
- Run benchmark experiments at multiple dataset sizes.
- Include the algorithm pseudocode, dry run, complexity, test cases, results, limitations and future scope in the report.
- Be prepared to explain the graph model and why backtracking is used.
