from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sqlite3
from typing import List, Optional
import base64
import io
import smtplib
from email.message import EmailMessage

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!"}


# --------- Demo: Ideas API (SQLite) ---------

class IdeaIn(BaseModel):
    title: str
    description: str = ""


class Idea(BaseModel):
    id: int
    title: str
    description: str
    score: int
    created_at: str


def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT "",
                score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        # Clients and tasks for homepage overview
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                owner TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'awaiting', -- awaiting | in_progress | done
                due_date TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
            );
            """
        )
        # Assignees (client employees) and workpapers (tracked per assignee)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workpapers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignee_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft', -- draft | review | final
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(assignee_id) REFERENCES assignees(id) ON DELETE CASCADE
            );
            """
        )
        # Calculator persisted data per assignee and calculator key
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calculator_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignee_id INTEGER NOT NULL,
                calc_key TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(assignee_id, calc_key),
                FOREIGN KEY(assignee_id) REFERENCES assignees(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()

        # Seed sample data if empty
        cur = conn.execute("SELECT COUNT(*) FROM clients")
        (count_clients,) = cur.fetchone()
        if count_clients == 0:
            sample_clients = [
                ("Contoso Ltd", "demo"),
                ("Fabrikam Inc", "demo"),
                ("Northwind Traders", ""),
                ("Adventure Works", ""),
                ("Globex Corp", "demo"),
            ]
            conn.executemany("INSERT INTO clients (name, owner) VALUES (?, ?)", sample_clients)
            conn.commit()

            # Map names to ids
            rows = conn.execute("SELECT id, name FROM clients").fetchall()
            id_by_name = {name: cid for cid, name in rows}

            sample_tasks = [
                (id_by_name["Contoso Ltd"], "Security review", "awaiting"),
                (id_by_name["Contoso Ltd"], "Q2 roadmap sync", "in_progress"),
                (id_by_name["Fabrikam Inc"], "Cost optimization plan", "awaiting"),
                (id_by_name["Globex Corp"], "Performance tuning", "done"),
                (id_by_name["Northwind Traders"], "Kickoff meeting", "awaiting"),
            ]
            conn.executemany(
                "INSERT INTO tasks (client_id, title, status) VALUES (?, ?, ?)", sample_tasks
            )
            conn.commit()

        cur = conn.execute("SELECT COUNT(*) FROM assignees")
        (count_assignees,) = cur.fetchone()
        if count_assignees == 0:
            # Create one sample assignee per first 3 clients
            clients = conn.execute("SELECT id, name FROM clients ORDER BY id LIMIT 3").fetchall()
            assignees = []
            for cid, cname in clients:
                assignees.append((cid, f"{cname.split()[0]} Employee", f"employee@{cname.split()[0].lower()}.example"))
            conn.executemany(
                "INSERT INTO assignees (client_id, name, email) VALUES (?, ?, ?)", assignees
            )
            conn.commit()
    finally:
        conn.close()


def compute_score(text: str) -> int:
    text_l = text.lower()
    score = 0
    # Simple keyword weights for demo purposes
    weights = {
        "risk": 5,
        "impact": 4,
        "cost": 3,
        "urgent": 6,
        "security": 5,
        "performance": 4,
        "reliability": 4,
        "innovation": 3,
    }
    for kw, w in weights.items():
        if kw in text_l:
            score += w
    # Add small length factor, capped
    score += min(len(text) // 50, 6)
    return score


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/ideas", response_model=List[Idea])
def list_ideas():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, title, description, score, created_at FROM ideas ORDER BY id DESC"
        ).fetchall()
        return [
            Idea(
                id=row[0], title=row[1], description=row[2], score=row[3], created_at=row[4]
            )
            for row in rows
        ]
    finally:
        conn.close()


@app.post("/api/ideas", response_model=Idea, status_code=201)
def create_idea(body: IdeaIn):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    score = compute_score(body.description or "")
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO ideas (title, description, score) VALUES (?, ?, ?)",
            (body.title.strip(), body.description.strip(), score),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, title, description, score, created_at FROM ideas WHERE id = ?",
            (new_id,),
        ).fetchone()
        return Idea(
            id=row[0], title=row[1], description=row[2], score=row[3], created_at=row[4]
        )
    finally:
        conn.close()


@app.delete("/api/ideas/{idea_id}")
def delete_idea(idea_id: int):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Idea not found")
        return {"status": "ok"}
    finally:
        conn.close()


# --------- Clients + Home Overview API ---------

class Client(BaseModel):
    id: int
    name: str
    owner: str
    created_at: str


class OverviewResponse(BaseModel):
    my_clients: List[Client]
    awaiting_clients: List[Client]
    stats: dict


def row_to_client(row) -> Client:
    return Client(id=row[0], name=row[1], owner=row[2], created_at=row[3])


@app.get("/api/home/overview", response_model=OverviewResponse)
def home_overview(owner: str = "demo"):
    conn = get_db()
    try:
        my_rows = conn.execute(
            "SELECT id, name, owner, created_at FROM clients WHERE owner = ? ORDER BY name",
            (owner,),
        ).fetchall()
        awaiting_rows = conn.execute(
            """
            SELECT DISTINCT c.id, c.name, c.owner, c.created_at
            FROM clients c
            JOIN tasks t ON t.client_id = c.id
            WHERE t.status = 'awaiting'
            ORDER BY c.name
            """
        ).fetchall()
        awaiting_count = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'awaiting'"
        ).fetchone()[0]
        return OverviewResponse(
            my_clients=[row_to_client(r) for r in my_rows],
            awaiting_clients=[row_to_client(r) for r in awaiting_rows],
            stats={
                "my_clients_count": len(my_rows),
                "awaiting_tasks_count": awaiting_count,
            },
        )
    finally:
        conn.close()


@app.get("/api/clients/search", response_model=List[Client])
def search_clients(q: str = ""):
    conn = get_db()
    try:
        like = f"%{q.strip()}%"
        rows = conn.execute(
            "SELECT id, name, owner, created_at FROM clients WHERE name LIKE ? ORDER BY name",
            (like,),
        ).fetchall()
        return [row_to_client(r) for r in rows]
    finally:
        conn.close()


class AssignBody(BaseModel):
    owner: str


@app.post("/api/clients/{client_id}/assign")
def assign_client(client_id: int, body: AssignBody):
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE clients SET owner = ? WHERE id = ?",
            (body.owner.strip(), client_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found")
        return {"status": "ok"}
    finally:
        conn.close()


# --------- Tools API ---------

class CoverLetterRequest(BaseModel):
    candidate_name: str
    role: str
    company: str
    highlights: List[str] = []


class CoverLetterResponse(BaseModel):
    content: str


@app.post("/api/tools/cover-letter", response_model=CoverLetterResponse)
def generate_cover_letter(body: CoverLetterRequest):
    lines = [
        f"Dear {body.company} Hiring Team,",
        "",
        f"I am excited to apply for the {body.role} role. With a strong track record in relevant domains and a passion for impact, I believe I can contribute immediately.",
    ]
    if body.highlights:
        lines.append("")
        lines.append("Highlights:")
        for h in body.highlights:
            lines.append(f"- {h}")
    lines.extend([
        "",
        "Thank you for your consideration.",
        f"Sincerely,",
        f"{body.candidate_name}",
    ])
    return CoverLetterResponse(content="\n".join(lines))


class PdfFillRequest(BaseModel):
    title: str = "Generated Form"
    fields: dict


class PdfFillResponse(BaseModel):
    filename: str
    content_b64: str


@app.post("/api/tools/pdf-fill", response_model=PdfFillResponse)
def pdf_fill(body: PdfFillRequest):
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(status_code=501, detail="PDF generation not available (reportlab missing)")
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER
    c.setTitle(body.title)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, body.title)
    c.setFont("Helvetica", 11)
    y = height - 108
    for k, v in body.fields.items():
        c.drawString(72, y, f"{k}: {v}")
        y -= 18
        if y < 72:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 11)
    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    buf.close()
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return PdfFillResponse(filename="generated_form.pdf", content_b64=b64)


class Attachment(BaseModel):
    filename: str
    content_b64: str
    mimetype: Optional[str] = None


class SendEmailRequest(BaseModel):
    to: List[str]
    subject: str
    body: str
    attachments: List[Attachment] = []


@app.post("/api/tools/send-email")
def send_email(body: SendEmailRequest):
    # Build message
    msg = EmailMessage()
    msg["Subject"] = body.subject
    msg["To"] = ", ".join(body.to)
    from_addr = os.environ.get("SMTP_FROM", "noreply@example.com")
    msg["From"] = from_addr
    msg.set_content(body.body)
    for att in body.attachments:
        data = base64.b64decode(att.content_b64)
        maintype, subtype = (att.mimetype or "application/octet-stream").split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=att.filename)

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_tls = os.environ.get("SMTP_TLS", "true").lower() == "true"

    # If SMTP not configured, return preview only
    if not smtp_host:
        return {"status": "preview", "from": from_addr, "to": body.to, "subject": body.subject, "body": body.body, "attachments": [a.filename for a in body.attachments]}

    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        if smtp_tls:
            server.starttls()
        if smtp_user:
            server.login(smtp_user, smtp_pass or "")
        server.send_message(msg)
        server.quit()
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP error: {e}")


# --------- Client/Assignee/Workpaper API ---------

class Assignee(BaseModel):
    id: int
    client_id: int
    name: str
    email: str
    created_at: str


class Workpaper(BaseModel):
    id: int
    assignee_id: int
    title: str
    status: str
    notes: str
    created_at: str


class AssigneeBrief(BaseModel):
    id: int
    name: str
    client_name: str


class ClientDetail(Client):
    pass


class AssigneeDetail(Assignee):
    client: ClientDetail


@app.get("/api/clients", response_model=List[Client])
def list_clients():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, owner, created_at FROM clients ORDER BY name"
        ).fetchall()
        return [row_to_client(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/home/my-assignees", response_model=List[AssigneeBrief])
def my_assignees(owner: str = "demo"):
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT a.id, a.name, c.name as client_name
            FROM assignees a
            JOIN clients c ON c.id = a.client_id
            WHERE c.owner = ?
            ORDER BY a.name
            """,
            (owner,),
        ).fetchall()
        return [AssigneeBrief(id=r[0], name=r[1], client_name=r[2]) for r in rows]
    finally:
        conn.close()


class AssigneeCreate(BaseModel):
    name: str
    email: str = ""


@app.get("/api/clients/{client_id}/assignees", response_model=List[Assignee])
def list_assignees(client_id: int):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, client_id, name, email, created_at FROM assignees WHERE client_id = ? ORDER BY name",
            (client_id,),
        ).fetchall()
        return [Assignee(id=r[0], client_id=r[1], name=r[2], email=r[3], created_at=r[4]) for r in rows]
    finally:
        conn.close()


@app.post("/api/clients/{client_id}/assignees", response_model=Assignee, status_code=201)
def create_assignee(client_id: int, body: AssigneeCreate):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO assignees (client_id, name, email) VALUES (?, ?, ?)",
            (client_id, body.name.strip(), body.email.strip()),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, client_id, name, email, created_at FROM assignees WHERE id = ?",
            (new_id,),
        ).fetchone()
        return Assignee(id=row[0], client_id=row[1], name=row[2], email=row[3], created_at=row[4])
    finally:
        conn.close()


class WorkpaperCreate(BaseModel):
    title: str
    notes: str = ""


@app.get("/api/assignees/{assignee_id}/workpapers", response_model=List[Workpaper])
def list_workpapers(assignee_id: int):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, assignee_id, title, status, notes, created_at FROM workpapers WHERE assignee_id = ? ORDER BY id DESC",
            (assignee_id,),
        ).fetchall()
        return [Workpaper(id=r[0], assignee_id=r[1], title=r[2], status=r[3], notes=r[4], created_at=r[5]) for r in rows]
    finally:
        conn.close()


@app.post("/api/assignees/{assignee_id}/workpapers", response_model=Workpaper, status_code=201)
def create_workpaper(assignee_id: int, body: WorkpaperCreate):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO workpapers (assignee_id, title, notes) VALUES (?, ?, ?)",
            (assignee_id, body.title.strip(), body.notes.strip()),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, assignee_id, title, status, notes, created_at FROM workpapers WHERE id = ?",
            (new_id,),
        ).fetchone()
        return Workpaper(id=row[0], assignee_id=row[1], title=row[2], status=row[3], notes=row[4], created_at=row[5])
    finally:
        conn.close()


@app.get("/api/assignees/{assignee_id}", response_model=AssigneeDetail)
def get_assignee(assignee_id: int):
    conn = get_db()
    try:
        a = conn.execute(
            "SELECT id, client_id, name, email, created_at FROM assignees WHERE id = ?",
            (assignee_id,),
        ).fetchone()
        if not a:
            raise HTTPException(status_code=404, detail="Assignee not found")
        c = conn.execute(
            "SELECT id, name, owner, created_at FROM clients WHERE id = ?",
            (a[1],),
        ).fetchone()
        if not c:
            raise HTTPException(status_code=404, detail="Client not found")
        return AssigneeDetail(
            id=a[0], client_id=a[1], name=a[2], email=a[3], created_at=a[4],
            client=ClientDetail(id=c[0], name=c[1], owner=c[2], created_at=c[3])
        )
    finally:
        conn.close()


@app.get("/api/assignees/{assignee_id}/calc/{calc_key}")
def get_calc_data(assignee_id: int, calc_key: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT data FROM calculator_data WHERE assignee_id = ? AND calc_key = ?",
            (assignee_id, calc_key),
        ).fetchone()
        return {"data": {} if not row else __import__('json').loads(row[0])}
    finally:
        conn.close()


class SaveCalcBody(BaseModel):
    data: dict


@app.put("/api/assignees/{assignee_id}/calc/{calc_key}")
def put_calc_data(assignee_id: int, calc_key: str, body: SaveCalcBody):
    import json
    conn = get_db()
    try:
        payload = json.dumps(body.data or {})
        conn.execute(
            """
            INSERT INTO calculator_data (assignee_id, calc_key, data)
            VALUES (?, ?, ?)
            ON CONFLICT(assignee_id, calc_key)
            DO UPDATE SET data = excluded.data, updated_at = datetime('now')
            """,
            (assignee_id, calc_key, payload),
        )
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@app.get("/api/assignees/{assignee_id}/overview")
def assignee_overview(assignee_id: int):
    import json
    conn = get_db()
    try:
        def get_data(key):
            row = conn.execute(
                "SELECT data FROM calculator_data WHERE assignee_id = ? AND calc_key = ?",
                (assignee_id, key),
            ).fetchone()
            return {} if not row else json.loads(row[0])

        income = get_data("income-tax")
        ded = get_data("deductions")
        income_total = float(income.get("salary", 0)) + float(income.get("bonus", 0)) + float(income.get("other", 0))
        deductions_total = float(ded.get("retirement", 0)) + float(ded.get("health", 0)) + float(ded.get("charity", 0))
        taxable = max(0, income_total - deductions_total)
        est_tax = round(taxable * 0.25, 2)
        return {
            "income_total": income_total,
            "deductions_total": deductions_total,
            "taxable_income": taxable,
            "estimated_tax": est_tax,
            "inputs": {
                "income": income,
                "deductions": ded,
            },
        }
    finally:
        conn.close()

# Serve React static files if built
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.isdir(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="static")
