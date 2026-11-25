import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import time, json, io
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Smart Exam Scheduler", page_icon="🎓", layout="wide")
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#081225,#101b35 55%,#0a1020);}
[data-testid="stMetric"] {background:#14213b;border:1px solid #263c63;padding:14px;border-radius:14px}
section[data-testid="stSidebar"] {background:#0c162a}
h1,h2,h3 {color:#eaf2ff}
</style>
""", unsafe_allow_html=True)

DEFAULT_SUBJECTS = ["Data Structures","Algorithms","Database Systems","Operating Systems","Computer Networks","AI & ML"]
DEFAULT_ENROLL = {
 "Data Structures":["S001","S002","S003","S004","S005"],
 "Algorithms":["S001","S002","S006","S007"],
 "Database Systems":["S003","S004","S006","S008"],
 "Operating Systems":["S001","S005","S009","S010"],
 "Computer Networks":["S002","S007","S008","S010"],
 "AI & ML":["S003","S005","S009","S011"]
}
if "subjects" not in st.session_state:
    st.session_state.subjects=DEFAULT_SUBJECTS.copy()
    st.session_state.enroll={k:v.copy() for k,v in DEFAULT_ENROLL.items()}
    st.session_state.result=None
    st.session_state.room_capacity=60
    st.session_state.exam_date=date.today()+timedelta(days=14)

def graph_from_data(subjects,enroll):
    G=nx.Graph(); G.add_nodes_from(subjects)
    for i,a in enumerate(subjects):
        for b in subjects[i+1:]:
            if set(enroll.get(a,[])) & set(enroll.get(b,[])): G.add_edge(a,b)
    return G

def color_with_k(G,k,ordered=None,collect=False):
    nodes=ordered or sorted(G.nodes(),key=lambda n:G.degree(n),reverse=True)
    colors={}; steps=[]
    def rec(i):
        if i==len(nodes): return True
        n=nodes[i]
        for c in range(k):
            conflict=[x for x in G.neighbors(n) if colors.get(x)==c]
            steps.append({"Subject":n,"Try Slot":c+1,"Result":"Rejected (conflict)" if conflict else "Assigned","Conflicts with":", ".join(conflict)})
            if not conflict:
                colors[n]=c
                if rec(i+1): return True
                steps.append({"Subject":n,"Try Slot":c+1,"Result":"Backtrack","Conflicts with":""})
                del colors[n]
        return False
    ok=rec(0)
    return (colors if ok else None),steps

def min_coloring(G):
    if not G.nodes: return {},0,[]
    order=sorted(G.nodes(),key=lambda n:(G.degree(n),n),reverse=True)
    for k in range(1,len(G)+1):
        colors,steps=color_with_k(G,k,order)
        if colors is not None:return colors,k,steps
    return None,0,[]

def timetable_rows(colors, subjects, enroll, examdate, slot_times, rooms):
    rows=[]
    for s in subjects:
        c=colors[s]
        stu=len(set(enroll.get(s,[])))
        room=rooms[c % len(rooms)] if rooms else "Room TBD"
        rows.append({"Subject":s,"Date":examdate.strftime("%d %b %Y"),"Slot":f"Slot {c+1}",
          "Time":slot_times[c % len(slot_times)],"Room":room,"Registered Students":stu})
    return pd.DataFrame(rows).sort_values(["Slot","Subject"])

def reset_sample():
    st.session_state.subjects=DEFAULT_SUBJECTS.copy()
    st.session_state.enroll={k:v.copy() for k,v in DEFAULT_ENROLL.items()}
    st.session_state.result=None

with st.sidebar:
    st.title("🎓 Smart Scheduler")
    page=st.radio("Navigation",["Dashboard","Data Management","Conflict Graph","Generate Timetable","Algorithm Lab","Reports & Export","About"])
    st.divider()
    st.caption("DAA Capstone • Graph Coloring")
    if st.button("Restore sample data"):
        reset_sample(); st.success("Sample data restored.")

G=graph_from_data(st.session_state.subjects,st.session_state.enroll)
st.title("🎓 Smart Exam Scheduling System")
st.caption("Graph Coloring • Backtracking • Conflict-Free Scheduling")
if page=="Dashboard":
    st.subheader("Overview")
    students=set().union(*(set(x) for x in st.session_state.enroll.values()) if st.session_state.enroll else set())
    a,b,c,d=st.columns(4)
    a.metric("Subjects",len(st.session_state.subjects))
    b.metric("Students",len(students))
    c.metric("Conflicts",G.number_of_edges())
    d.metric("Graph Density",f"{nx.density(G):.2f}" if G.number_of_nodes()>1 else "0")
    st.markdown("### Project workflow")
    st.markdown("**Manage Data → Build Conflict Graph → Run Backtracking → Validate → Export timetable**")
    st.info("Use the left navigation to manage enrollment data, visualize conflicts, generate schedules, and study algorithm performance.")
    st.subheader("Current subjects")
    st.dataframe(pd.DataFrame({"Subject":st.session_state.subjects,"Enrollment":[len(st.session_state.enroll.get(s,[])) for s in st.session_state.subjects]}),use_container_width=True,hide_index=True)
    st.subheader("Quick graph view")
    if G.nodes:
        fig,ax=plt.subplots(figsize=(9,4)); pos=nx.spring_layout(G,seed=8)
        nx.draw_networkx(G,pos,ax=ax,node_color="#62b6ff",edge_color="#95a5bd",node_size=1700,font_size=8)
        ax.set_axis_off(); st.pyplot(fig); plt.close(fig)
elif page=="Data Management":
    st.subheader("📚 Subject and Enrollment Management")
    st.write("Edit subjects and enter student IDs separated by commas. Students enrolled in multiple subjects create conflict edges.")
    data=[{"Subject":s,"Student IDs":", ".join(st.session_state.enroll.get(s,[]))} for s in st.session_state.subjects]
    edit=st.data_editor(pd.DataFrame(data),num_rows="dynamic",use_container_width=True)
    if st.button("Save enrollment data",type="primary"):
        subs=[]; enroll={}
        for _,r in edit.iterrows():
            name=str(r.get("Subject","")).strip()
            if name and name.lower()!="nan":
                subs.append(name); enroll[name]=[x.strip() for x in str(r.get("Student IDs","")).split(",") if x.strip()]
        st.session_state.subjects=subs; st.session_state.enroll=enroll; st.session_state.result=None
        st.success("Saved. Conflict graph will update.")
    st.markdown("#### Upload enrollment CSV")
    up=st.file_uploader("CSV columns: Subject, Student IDs",type=["csv"])
    if up:
        uploaded=pd.read_csv(up)
        st.dataframe(uploaded,hide_index=True)
        if st.button("Import CSV"):
            subs=[]; enroll={}
            for _,r in uploaded.iterrows():
                n=str(r["Subject"]).strip()
                subs.append(n); enroll[n]=[x.strip() for x in str(r["Student IDs"]).split(",") if x.strip()]
            st.session_state.subjects=subs; st.session_state.enroll=enroll; st.session_state.result=None
            st.success("CSV imported.")
elif page=="Conflict Graph":
    st.subheader("🕸️ Conflict Graph")
    st.write("Vertices represent subjects. An edge exists if at least one student is registered in both subjects.")
    st.metric("Conflict edges",G.number_of_edges())
    if G.nodes:
        fig,ax=plt.subplots(figsize=(10,6)); pos=nx.spring_layout(G,seed=12)
        nx.draw_networkx_nodes(G,pos,node_color="#72c7ff",node_size=1900,ax=ax)
        nx.draw_networkx_edges(G,pos,width=2,edge_color="#8492a8",ax=ax)
        nx.draw_networkx_labels(G,pos,font_size=9,font_weight="bold",ax=ax)
        ax.set_axis_off(); st.pyplot(fig); plt.close(fig)
    edge_df=pd.DataFrame([{"Subject 1":u,"Subject 2":v,"Shared students":", ".join(sorted(set(st.session_state.enroll.get(u,[]))&set(st.session_state.enroll.get(v,[]))))} for u,v in G.edges()])
    st.subheader("Conflict list")
    st.dataframe(edge_df,use_container_width=True,hide_index=True)
elif page=="Generate Timetable":
    st.subheader("🗓️ Timetable Generator")
    examdate=st.date_input("Exam date",st.session_state.exam_date)
    times=st.text_input("Slot times (comma separated)","09:00-12:00, 13:00-16:00, 16:30-19:30")
    rooms_text=st.text_input("Rooms (comma separated)","Exam Hall A, Exam Hall B, Lab 1, Lab 2")
    if st.button("Generate minimum-slot timetable",type="primary"):
        start=time.perf_counter(); colors,k,steps=min_coloring(G); elapsed=time.perf_counter()-start
        st.session_state.result={"colors":colors,"k":k,"steps":steps,"elapsed":elapsed,"date":examdate,"times":[x.strip() for x in times.split(",") if x.strip()],"rooms":[x.strip() for x in rooms_text.split(",") if x.strip()]}
    result=st.session_state.result
    if result and result["colors"] is not None:
        colors=result["colors"]; k=result["k"]
        df=timetable_rows(colors,st.session_state.subjects,st.session_state.enroll,result["date"],result["times"],result["rooms"])
        st.success(f"Timetable generated with {k} slot(s).")
        st.metric("Execution time",f"{result['elapsed']*1000:.3f} ms")
        st.dataframe(df,use_container_width=True,hide_index=True)
        valid=all(colors[u]!=colors[v] for u,v in G.edges())
        st.success("Validation passed: no conflicting subjects share a slot." if valid else "Conflict validation failed.")
        st.subheader("Slot-wise view")
        for slot in range(k):
            st.markdown(f"**Slot {slot+1} ({result['times'][slot%len(result['times'])]}):** "+", ".join([s for s in st.session_state.subjects if colors[s]==slot]))
        st.download_button("Download timetable CSV",df.to_csv(index=False).encode(),file_name="exam_timetable.csv",mime="text/csv")
        st.download_button("Download timetable JSON",json.dumps(df.to_dict(orient="records"),indent=2).encode(),file_name="exam_timetable.json",mime="application/json")
elif page=="Algorithm Lab":
    st.subheader("🧪 Backtracking Algorithm Lab")
    st.write("Run graph coloring and inspect recursive assignment attempts and backtracking decisions.")
    if st.button("Run algorithm and show trace",type="primary"):
        colors,k,steps=min_coloring(G); st.session_state.lab={"colors":colors,"k":k,"steps":steps}
    if "lab" in st.session_state:
        lab=st.session_state.lab
        st.metric("Minimum slots found",lab["k"])
        trace=pd.DataFrame(lab["steps"])
        st.dataframe(trace,use_container_width=True,hide_index=True)
        if lab["colors"]:
            st.write("Final assignment")
            st.dataframe(pd.DataFrame([{"Subject":s,"Slot":lab["colors"][s]+1} for s in st.session_state.subjects]),hide_index=True)
    st.subheader("Complexity")
    st.markdown("**Worst-case time:** exponential, often bounded broadly by O(k^V) for V vertices and k colors. **Space:** O(V+E) for graph storage, plus O(V) recursion/color state.")
elif page=="Reports & Export":
    st.subheader("📊 Analysis & Reports")
    degrees=dict(G.degree())
    x,y,z=st.columns(3); x.metric("Vertices",G.number_of_nodes()); y.metric("Edges",G.number_of_edges()); z.metric("Max degree",max(degrees.values(),default=0))
    st.subheader("Subject conflict degree")
    if G.nodes:
        deg=pd.DataFrame({"Subject":list(degrees),"Conflict degree":list(degrees.values())}).sort_values("Conflict degree",ascending=False)
        st.bar_chart(deg.set_index("Subject"))
        st.dataframe(deg,use_container_width=True,hide_index=True)
    st.subheader("Performance experiment")
    n_runs=st.slider("Runs for timing average",1,20,5)
    if st.button("Benchmark current dataset"):
        vals=[]
        for i in range(n_runs):
            t=time.perf_counter(); colors,k,_=min_coloring(G); vals.append((time.perf_counter()-t)*1000)
        st.metric("Average execution time",f"{sum(vals)/len(vals):.4f} ms")
        st.line_chart(pd.DataFrame({"Run":range(1,len(vals)+1),"Time (ms)":vals}).set_index("Run"))
        st.write("Timing values vary by machine and dataset; use repeated runs and report the average.")
    st.download_button("Download enrollment data CSV",pd.DataFrame([{"Subject":s,"Student IDs":", ".join(st.session_state.enroll.get(s,[]))} for s in st.session_state.subjects]).to_csv(index=False).encode(),file_name="enrollment_data.csv")
elif page=="About":
    st.subheader("📘 Project Details")
    st.markdown("""
**Problem:** Create an examination timetable while preventing students enrolled in overlapping subjects from having simultaneous exams.

**Model:** Subjects = vertices; shared students = edges; exam slots = colors.

**Algorithm:** Backtracking graph coloring. The solver tries increasing numbers of colors and uses a degree-based ordering to reduce search.

**Validation:** Every conflict edge is checked to confirm its endpoints receive different slots.

**Time complexity:** Worst-case exponential (commonly expressed as O(k^V) for V subjects and k slots).

**Space complexity:** O(V+E) graph storage, plus O(V) color and recursion state.

**Limitations / future improvements:** Room capacity checks, multiple exam dates, faculty availability, student-specific schedules, persistent database, and more advanced heuristics can be added.
""")
