from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sqlite3
from typing import List, Optional


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

# Serve React static files if built
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.isdir(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="static")
