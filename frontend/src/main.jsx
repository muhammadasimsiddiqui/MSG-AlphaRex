import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import brandLogo from "../../skillsprint-favicon.png";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const stages = ["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"];

async function api(path, options) {
  const token = localStorage.getItem("skillsprint_token");
  const headers = new Headers(options?.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Request failed.");
  return body;
}

function App() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("skillsprint_user") || "null"));
  const [tab, setTab] = useState("overview");
  const [documents, setDocuments] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [plans, setPlans] = useState([]);
  const [report, setReport] = useState(null);
  const [roles, setRoles] = useState([]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [plan, setPlan] = useState(null);
  const [validation, setValidation] = useState(null);

  useEffect(() => { document.querySelector("#app-favicon")?.setAttribute("href", brandLogo); }, []);

  const reload = async () => {
    try {
      const [docs, matrix, people, savedPlans, overview, roleRows] = await Promise.all([api("/documents"), api("/requirements"), api("/employees"), api("/plans"), api("/reports/overview"), api("/roles/dashboard")]);
      setDocuments(docs); setRequirements(matrix); setEmployees(people); setPlans(savedPlans); setReport(overview); setRoles(roleRows);
    } catch (err) { setError(`Cannot reach API: ${err.message}`); }
  };
  useEffect(() => { if (user) reload(); }, [user]);
  const run = async (work, success) => {
    setError(""); setNotice("");
    try { await work(); setNotice(success); await reload(); } catch (err) { setError(err.message); }
  };

  if (!user) return <Login onLogin={setUser} />;
  return <main>
    <header><div className="brand"><div className="brand-mark"><img src={brandLogo} alt="SkillSprint AI" /></div><div><p className="eyebrow">ONBOARDING INTELLIGENCE</p><h1>SkillSprint <span>AI</span></h1></div></div><div className="live"><i /> {user.display_name} <span>{user.role}</span><button className="logout" onClick={() => { localStorage.clear(); setUser(null); }}>Sign out</button></div></header>
    <nav>{[["overview", "Overview"], ["documents", "Knowledge"], ["matrix", "Requirement matrix"], ["employees", "Employees"], ["generate", "Plan studio"], ["reviews", "Reviews"], ["reports", "Reports"]].map(([id, label]) => <button className={tab === id ? "active" : ""} onClick={() => setTab(id)} key={id}>{label}</button>)}</nav>
    {notice && <p className="notice">{notice}</p>}{error && <p className="error">{error}</p>}
    <section className="workspace">{tab === "overview" && <Overview documents={documents} requirements={requirements} report={report} roles={roles} />}
    {tab === "documents" && <Documents documents={documents} submit={(form) => run(() => api("/documents", { method: "POST", body: form }), "Document processed and versioned.")} />}
    {tab === "matrix" && <Matrix requirements={requirements} documents={documents} submit={(payload) => run(() => api("/requirements", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }), "Requirement added to the independent matrix.")} />}
    {tab === "employees" && <Employees employees={employees} roles={roles} submit={(payload) => run(() => api("/employees", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }), "Employee profile created.")} />}
    {tab === "generate" && <PlanStudio employees={employees} plan={plan} validation={validation} generate={async (payload) => run(async () => { const next = await api("/plans/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); setPlan(next); setValidation(null); }, "Structured onboarding plan generated. Validate before approval.")} validate={() => run(async () => setValidation(await api(`/plans/${plan.id}/validate`, { method: "POST" })), "Independent Python validation completed.")} />}
    {tab === "reviews" && <ReviewCenter plans={plans} run={run} />}
    {tab === "reports" && <Reports report={report} roles={roles} documents={documents} run={run} />}</section>
  </main>;
}

function Login({ onLogin }) {
  const [email, setEmail] = useState("admin@skillsprint.local"); const [password, setPassword] = useState("ChangeMe123!"); const [error, setError] = useState("");
  return <main className="login"><section className="panel"><p className="eyebrow">SKILLSPRINT AI</p><h1>Source-grounded onboarding.</h1><p>Sign in to access the controlled training workspace.</p><form onSubmit={async (e) => { e.preventDefault(); try { const result = await api("/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) }); localStorage.setItem("skillsprint_token", result.access_token); localStorage.setItem("skillsprint_user", JSON.stringify(result.user)); onLogin(result.user); } catch (err) { setError(err.message); } }}><label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label><label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>{error && <p className="error">{error}</p>}<button className="primary">Sign in</button></form><small>Demo administrator credentials are prefilled for local evaluation.</small></section></main>;
}

function Overview({ documents, requirements, report, roles }) {
  const mandatory = requirements.filter((item) => item.mandatory).length;
  return <section className="overview"><div className="hero"><div><p className="eyebrow">SOURCE-FIRST ONBOARDING</p><h2>Every plan must prove where it came from.</h2><p>Build role-specific onboarding from approved company knowledge, then independently verify coverage, citations, and sequencing.</p></div><div className="hero-badge"><b>Dual pipeline</b><span>GenAI + Python controls</span></div></div><div className="metrics"><Metric value={report?.employees ?? 0} label="Employees" /><Metric value={documents.length} label="Source documents" /><Metric value={mandatory} label="Mandatory controls" /><Metric value={report?.approved_plans ?? 0} label="Approved plans" /></div><section className="flow"><b><i>01</i> Ingest evidence</b><b><i>02</i> Define matrix</b><b><i>03</i> Generate JSON</b><b><i>04</i> Validate independently</b></section><section className="panel role-snapshot"><div className="section-title"><div><p className="eyebrow">ROLE INTELLIGENCE</p><h2>Role coverage</h2></div><span className="count">{roles.length} roles</span></div>{roles.length ? roles.slice(0, 5).map((role) => <p key={role.role}><b>{role.role}</b><span>{role.mandatory} mandatory requirements · {role.approved_plans}/{role.plans} approved plans</span></p>) : <EmptyState text="Role requirements will appear here once a matrix is created." />}</section></section>;
}
function Metric({ value, label }) { return <article className="metric"><strong>{value}</strong><span>{label}</span></article>; }

function Documents({ documents, submit }) {
  const [form, setForm] = useState({ document_id: "", title: "", category: "Policy", version: "1.0", effective_date: new Date().toISOString().slice(0, 10), department: "" });
  const [file, setFile] = useState(null);
  const send = (event) => { event.preventDefault(); const data = new FormData(); Object.entries(form).forEach(([key, value]) => value && data.append(key, value)); data.append("file", file); submit(data); };
  return <section><PageHeading eyebrow="KNOWLEDGE BASE" title="Company documents" text="Ingest approved policy and process documents. Every usable source is versioned and chunked for traceability." /><section className="split"><form className="panel form-panel" onSubmit={send}><h2>Ingest company knowledge</h2><p>PDF and DOCX only. Content is treated as data; suspicious embedded instructions are quarantined.</p><Fields state={form} setState={setForm} names={[["document_id", "Document ID"], ["title", "Title"], ["category", "Category"], ["version", "Version"], ["effective_date", "Effective date", "date"], ["department", "Department"]]} /><label className="file-input">Upload file<input required type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files[0])} /><span>{file?.name || "Choose PDF or DOCX"}</span></label><button className="primary">Process document</button></form><section className="panel"><div className="section-title"><h2>Knowledge registry</h2><span className="count">{documents.length} documents</span></div>{documents.length ? <div className="table-scroll"><table><thead><tr><th>ID</th><th>Version</th><th>Department</th><th>Status</th></tr></thead><tbody>{documents.map((doc) => <tr key={`${doc.document_id}-${doc.version}`}><td><b>{doc.document_id}</b><small>{doc.title}</small></td><td>v{doc.version}</td><td>{doc.department || "Company-wide"}</td><td><span className={doc.injection_flags.length ? "tag danger" : doc.is_active ? "tag" : "tag muted"}>{doc.injection_flags.length ? "Quarantined" : doc.is_active ? "Active" : "Obsolete"}</span></td></tr>)}</tbody></table></div> : <EmptyState text="No documents have been uploaded." />}</section></section></section>;
}

function Matrix({ requirements, documents, submit }) {
  const [form, setForm] = useState({ requirement_id: "", role: "", requirement: "", competency: "", mandatory: true, priority: "High", due_stage: "Week 1", source_document_id: "", source_document_version: "", source_section_id: "", source_chunk_id: "", assessment_topic: "", prerequisites: [] });
  return <section><PageHeading eyebrow="GROUND TRUTH" title="Role requirement matrix" text="Map each role to approved policies, competencies, tasks, and immutable source citations." /><section className="split"><form className="panel form-panel" onSubmit={(e) => { e.preventDefault(); submit(form); }}><h2>Add matrix requirement</h2><p>This is deterministic ground truth, not AI-generated content.</p><Fields state={form} setState={setForm} names={[["requirement_id", "Requirement ID"], ["role", "Role"], ["requirement", "Requirement"], ["competency", "Competency"], ["source_document_id", "Source document ID"], ["source_document_version", "Source version"], ["source_section_id", "Source section"], ["source_chunk_id", "Immutable chunk ID"], ["assessment_topic", "Assessment topic"]]} textarea="requirement" /><label>Due stage<select value={form.due_stage} onChange={(e) => setForm({ ...form, due_stage: e.target.value })}>{stages.map((s) => <option key={s}>{s}</option>)}</select></label><label className="checkbox-label"><input type="checkbox" checked={form.mandatory} onChange={(e) => setForm({ ...form, mandatory: e.target.checked })} /> Mandatory requirement</label><button className="primary">Add requirement</button></form><section className="panel"><div className="section-title"><h2>Approved requirements</h2><span className="count">{requirements.length} records</span></div>{requirements.length ? <div className="table-scroll"><table><thead><tr><th>Requirement</th><th>Role</th><th>Stage</th><th>Evidence</th></tr></thead><tbody>{requirements.map((item) => <tr key={`${item.requirement_id}-${item.role}`}><td><b>{item.requirement_id}</b><small>{item.mandatory ? "Mandatory" : "Optional"}</small></td><td>{item.role}</td><td>{item.due_stage}</td><td>{item.source_document_id}<small>v{item.source_document_version} · {item.source_chunk_id}</small></td></tr>)}</tbody></table></div> : <EmptyState text="No role requirements have been created." />}</section></section></section>;
}

function PageHeading({ eyebrow, title, text }) { return <div className="page-heading"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2><p>{text}</p></div>; }
function EmptyState({ text }) { return <div className="empty-state"><b>No records yet</b><span>{text}</span></div>; }
function Fields({ state, setState, names, textarea }) { return <>{names.map(([name, label, type]) => <label key={name}>{label}{textarea === name ? <textarea required value={state[name]} onChange={(e) => setState({ ...state, [name]: e.target.value })} /> : <input required={!["department", "competency", "assessment_topic", "manager"].includes(name)} type={type || "text"} value={state[name]} onChange={(e) => setState({ ...state, [name]: e.target.value })} />}</label>)}</>; }

function Employees({ employees, roles, submit }) {
  const [form, setForm] = useState({ employee_id: "", name: "", role: "", department: "", experience_level: "Beginner", joining_date: new Date().toISOString().slice(0, 10), manager: "" });
  return <section><PageHeading eyebrow="LEARNER DIRECTORY" title="Employees and onboarding status" text="Create employee profiles, assign their roles, and follow completion status across all onboarding plans." /><section className="split"><form className="panel form-panel" onSubmit={(e) => { e.preventDefault(); submit(form); }}><h2>Create employee profile</h2><Fields state={form} setState={setForm} names={[["employee_id", "Employee ID"], ["name", "Name"], ["department", "Department"], ["joining_date", "Joining date", "date"], ["manager", "Reporting manager"]]} /><label>Role<select required value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="">Select role</option>{roles.map((item) => <option key={item.role}>{item.role}</option>)}</select></label><label>Experience<select value={form.experience_level} onChange={(e) => setForm({ ...form, experience_level: e.target.value })}>{["Beginner", "Intermediate", "Advanced"].map((item) => <option key={item}>{item}</option>)}</select></label><button className="primary">Create employee</button></form><section className="panel"><div className="section-title"><h2>Employee learning status</h2><span className="count">{employees.length} employees</span></div>{employees.length ? <div className="table-scroll"><table><thead><tr><th>Employee</th><th>Role</th><th>Level</th><th>Status</th></tr></thead><tbody>{employees.map((employee) => <tr key={employee.employee_id}><td><b>{employee.name}</b><small>{employee.employee_id} · {employee.department}</small></td><td>{employee.role}</td><td>{employee.experience_level}</td><td><span className="tag">{employee.training_status}</span></td></tr>)}</tbody></table></div> : <EmptyState text="No employee profiles have been created." />}</section></section></section>;
}

function PlanStudio({ employees, plan, validation, generate, validate }) {
  const [employeeId, setEmployeeId] = useState("");
  const employee = employees.find((item) => item.employee_id === employeeId);
  return <section><PageHeading eyebrow="GENAI PIPELINE" title="Personalized plan studio" text="Generate a structured onboarding plan from approved source evidence, then validate it independently in Python." /><form className="panel plan-form" onSubmit={(e) => { e.preventDefault(); generate({ employee_id: employee.employee_id, employee_name: employee.name, role: employee.role, experience_level: employee.experience_level }); }}><h2>Configure generation</h2><label>Employee<select required value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}><option value="">Select an employee</option>{employees.map((item) => <option value={item.employee_id} key={item.employee_id}>{item.name} · {item.role}</option>)}</select></label><div className="readonly">{employee ? <><b>{employee.role}</b><small>{employee.experience_level} · {employee.department}</small></> : "Choose an employee to use their configured role."}</div><button className="primary" disabled={!employee}>Generate plan</button>{plan && <button type="button" onClick={validate}>Run validation</button>}</form>{plan ? <PlanDetail plan={plan} validation={validation} /> : <EmptyState text="Select an employee and generate a source-grounded onboarding plan." />}</section>;
}

function PlanDetail({ plan, validation }) {
  return <><section className="panel"><h2>{plan.payload.employee_name}'s {plan.role} plan</h2>{plan.payload.modules.map((module) => <article className="module" key={module.module_id}><span>{module.due_stage} · {module.mandatory ? "Mandatory" : "Optional"}</span><h3>{module.module_title}</h3><p>{module.requirement_id} · {module.source_document_id} v{module.source_document_version} / {module.source_section_id}</p><small>{module.learning_objectives[0]}</small></article>)}</section>{validation && <section className="validation"><h2>{validation.status}</h2><Metric value={`${validation.coverage_score}%`} label="Mandatory coverage" /><Metric value={`${validation.traceability_score}%`} label="Traceability" /><p>{validation.issues.length ? validation.issues.map((item) => item.message).join(" ") : "All matrix requirements and citations verified."}</p></section>}</>;
}

function ReviewCenter({ plans, run }) {
  const [selected, setSelected] = useState(null); const [evidence, setEvidence] = useState([]); const [recommendations, setRecommendations] = useState([]); const [comment, setComment] = useState("Verified by reviewer.");
  const inspect = async (plan) => { setSelected(plan); const [sources, advice] = await Promise.all([api(`/plans/${plan.id}/evidence`), api(`/plans/${plan.id}/recommendations`)]); setEvidence(sources); setRecommendations(advice); };
  const review = (decision) => run(async () => { const result = await api(`/plans/${selected.id}/review`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, comment }) }); setSelected(result); }, `Plan ${decision.toLowerCase()}.`);
  const updateProgress = (module) => run(async () => { const result = await api(`/plans/${selected.id}/progress`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ module_id: module.module_id, completed: true, checklist_complete: true, task_complete: true, quiz_score: 85, assessment_score: 85 }) }); setSelected(result); }, "Module progress updated.");
  return <section><PageHeading eyebrow="HUMAN IN THE LOOP" title="Review and approve onboarding" text="Inspect source citations, record progress, and retain every reviewer decision in the audit trail." /><section className="split review"><section className="panel"><div className="section-title"><h2>Saved plans</h2><span className="count">{plans.length} plans</span></div>{plans.length ? plans.map((item) => <button className={`plan-row ${selected?.id === item.id ? "selected" : ""}`} onClick={() => inspect(item)} key={item.id}><b>Plan #{item.id} · {item.role}</b><small>{item.employee_id} · {item.status}</small></button>) : <EmptyState text="Generated plans will be available for review here." />}</section><section className="panel"><h2>{selected ? `Plan #${selected.id} evidence` : "Select a plan"}</h2>{selected ? <><p className="status-line">Current status: <b>{selected.status}</b></p><label>Reviewer comment<textarea value={comment} onChange={(e) => setComment(e.target.value)} /></label><div className="actions"><button className="primary" onClick={() => review("Approved")}>Approve</button><button onClick={() => review("Rejected")}>Reject</button><button onClick={() => review("Override")}>Override</button></div><h3>Source evidence</h3>{evidence.map((item) => <article className="evidence" key={item.module_id}><b>{item.requirement_id}</b><small>{item.document_id} v{item.document_version} · {item.chunk_id}</small><p>{item.excerpt}</p></article>)}<h3>Progress</h3>{selected.payload.modules.map((module) => <button className="progress-row" onClick={() => updateProgress(module)} key={module.module_id}>{module.module_id} · {module.module_title}<span>{module.progress?.completed ? "Completed" : "Mark complete"}</span></button>)}<h3>Recommendations</h3>{recommendations.length ? recommendations.map((item) => <p className="recommendation" key={item.module_id}>{item.module_id}: {item.recommendation}</p>) : <p>No reinforcement recommendations.</p>}</> : <EmptyState text="Choose a plan to inspect citations and make a review decision." />}</section></section></section>;
}

function Reports({ report, roles, documents, run }) {
  const [impact, setImpact] = useState(null);
  const exportCsv = async () => { const response = await fetch(`${API}/reports/requirements.csv`, { headers: { Authorization: `Bearer ${localStorage.getItem("skillsprint_token")}` } }); if (!response.ok) throw new Error("Export failed."); const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "skillsprint-requirements.csv"; link.click(); URL.revokeObjectURL(url); };
  const analyze = (documentId) => run(async () => setImpact(await api(`/documents/${documentId}/impact`)), "Policy impact analysis completed.");
  return <section className="reports"><PageHeading eyebrow="ANALYTICS AND EXPORT" title="Compliance reporting" text="Monitor plan approval, policy risk, role coverage, and the impact of changing source documents." /><div className="metrics"><Metric value={report?.plans ?? 0} label="Generated plans" /><Metric value={report?.approved_plans ?? 0} label="Approved plans" /><Metric value={report?.quarantined_documents ?? 0} label="Quarantined docs" /><Metric value={report?.manual_review_plans ?? 0} label="Manual review flags" /></div><section className="split"><section className="panel"><div className="section-title"><h2>Role dashboard</h2><span className="count">{roles.length} roles</span></div><div className="table-scroll"><table><thead><tr><th>Role</th><th>Matrix</th><th>Plans</th></tr></thead><tbody>{roles.map((item) => <tr key={item.role}><td><b>{item.role}</b><small>{item.mandatory} mandatory</small></td><td>{item.requirements}</td><td>{item.approved_plans}/{item.plans} approved</td></tr>)}</tbody></table></div></section><section className="panel"><h2>Export and impact</h2><p>Download a complete requirement-level report, or identify only the plans affected by a policy update.</p><button className="primary" onClick={() => run(exportCsv, "Requirements CSV downloaded.")}>Export requirements CSV</button><label>Policy document<select onChange={(e) => e.target.value && analyze(e.target.value)} defaultValue=""><option value="">Select active policy</option>{documents.filter((doc) => doc.is_active).map((doc) => <option value={doc.document_id} key={`${doc.document_id}-${doc.version}`}>{doc.document_id} · {doc.title}</option>)}</select></label>{impact && <article className="impact"><b>{impact.document_id} v{impact.active_version}</b><p>{impact.affected_requirement_ids.length} requirements and {impact.affected_plan_ids.length} plans are affected.</p><small>{impact.action}</small></article>}</section></section></section>;
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
