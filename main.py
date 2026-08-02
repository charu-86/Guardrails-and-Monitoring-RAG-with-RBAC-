"""
FastAPI Web API & Interactive Dashboard for Guardrails and Monitoring RAG with RBAC.
Run with: python main.py
"""

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from rbac.access_control import RoleBasedAccessControl
from rag.pipeline import RAGPipeline

app = FastAPI(
    title="Guardrails and Monitoring RAG with RBAC API",
    description="Enterprise-grade RAG API with RBAC security, Guardrails safety, and Prometheus monitoring.",
    version="0.1.0"
)

# Global initializations
rbac = RoleBasedAccessControl()
pipeline = RAGPipeline(enable_guardrails=True, enable_monitoring=True)


# --- Pydantic Schemas ---

class UserRegisterSchema(BaseModel):
    username: str = Field(..., example="alice")
    password: str = Field(..., example="SecurePass123!")
    email: str = Field(..., example="alice@example.com")
    role_name: Optional[str] = Field("viewer", example="analyst")


class UserLoginSchema(BaseModel):
    username: str = Field(..., example="alice")
    password: str = Field(..., example="SecurePass123!")


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    roles: List[str]


class QueryRequestSchema(BaseModel):
    query: str = Field(..., example="What are the quarterly revenue numbers?")


class IngestRequestSchema(BaseModel):
    file_paths: List[str] = Field(..., example=["examples/sample_doc.txt"])
    access_level: Optional[str] = Field("public", example="public")


# --- Helper for Auth Dependency ---

def get_current_user_from_header(authorization: Optional[str] = Header(None)):
    """Extract and verify user from Bearer JWT token in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = rbac.verify_token(token)
        username = payload.get("sub")
        if username:
            return rbac.get_user(username)
    except Exception:
        pass
    return None


# --- Endpoints ---

@app.get("/", response_class=HTMLResponse)
def read_dashboard():
    """Serve interactive web dashboard at root URL."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Guardrails & Monitoring RAG with RBAC</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-primary: #0f172a;
                --bg-card: #1e293b;
                --accent-blue: #38bdf8;
                --accent-green: #34d399;
                --accent-purple: #a855f7;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --border-color: #334155;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-primary);
                color: var(--text-main);
                padding: 24px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            header {
                display: flex; justify-content: space-between; align-items: center;
                padding-bottom: 20px; margin-bottom: 24px;
                border-bottom: 1px solid var(--border-color);
            }
            h1 { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .badge {
                background-color: rgba(52, 211, 153, 0.15); color: var(--accent-green);
                padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;
                border: 1px solid rgba(52, 211, 153, 0.3);
            }
            .btn-docs {
                background-color: #0284c7; color: white; text-decoration: none;
                padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 0.9rem;
                transition: all 0.2s;
            }
            .btn-docs:hover { background-color: #0369a1; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
            .card {
                background-color: var(--bg-card); border: 1px solid var(--border-color);
                border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 16px;
            }
            .card-header { display: flex; align-items: center; justify-content: space-between; font-size: 1.1rem; font-weight: 600; color: var(--accent-blue); }
            .form-group { display: flex; flex-direction: column; gap: 6px; }
            label { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }
            input, textarea, select {
                background-color: var(--bg-primary); border: 1px solid var(--border-color);
                color: var(--text-main); padding: 10px; border-radius: 8px; font-family: inherit; font-size: 0.9rem;
            }
            button {
                background: linear-gradient(135deg, #38bdf8, #0284c7); color: white; border: none;
                padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer;
            }
            button:hover { opacity: 0.9; }
            .result-box {
                background-color: #090d16; border: 1px solid var(--border-color);
                border-radius: 8px; padding: 12px; font-family: monospace; font-size: 0.85rem;
                white-space: pre-wrap; word-break: break-all; max-height: 220px; overflow-y: auto; color: var(--accent-green);
            }
            .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
            .stat-card { background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); padding: 16px; border-radius: 10px; text-align: center; }
            .stat-value { font-size: 1.6rem; font-weight: 700; color: var(--accent-blue); }
            .stat-label { font-size: 0.8rem; color: var(--text-muted); }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>🛡️ Guardrails & Monitoring RAG with RBAC</h1>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Enterprise AI Security, Observability, and Access Control</p>
                </div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    <span class="badge">● System Healthy</span>
                    <a href="/docs" class="btn-docs" target="_blank">Swagger API Docs ↗</a>
                </div>
            </header>

            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-value">RBAC</div>
                    <div class="stat-label">JWT & Role Security</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">Guardrails</div>
                    <div class="stat-label">PII & Injection Shield</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">Monitoring</div>
                    <div class="stat-label">Prometheus & Audit Logs</div>
                </div>
            </div>

            <div class="grid">
                <!-- Card 1: RAG Query Playground -->
                <div class="card">
                    <div class="card-header">
                        <span>🔍 RAG Query Playground</span>
                    </div>
                    <div class="form-group">
                        <label>User Query</label>
                        <textarea id="queryInput" rows="3" placeholder="Enter query (e.g. What is the quarterly revenue?)"></textarea>
                    </div>
                    <button onclick="runQuery()">Execute Query</button>
                    <div class="form-group">
                        <label>Output Response & Metadata</label>
                        <div id="queryOutput" class="result-box">Ready to execute query...</div>
                    </div>
                </div>

                <!-- Card 2: User Authentication & RBAC -->
                <div class="card">
                    <div class="card-header">
                        <span>🔐 User Registration & Login</span>
                    </div>
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="username" value="alice_demo">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="password" value="SecurePass123!">
                    </div>
                    <div class="form-group">
                        <label>Role</label>
                        <select id="role">
                            <option value="admin">Admin</option>
                            <option value="analyst">Analyst</option>
                            <option value="viewer" selected>Viewer</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button style="flex: 1;" onclick="registerUser()">Register</button>
                        <button style="flex: 1; background: linear-gradient(135deg, #a855f7, #7e22ce);" onclick="loginUser()">Login</button>
                    </div>
                    <div class="form-group">
                        <label>Auth Token & Status</label>
                        <div id="authOutput" class="result-box">Not authenticated yet</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let jwtToken = "";

            async function runQuery() {
                const query = document.getElementById("queryInput").value || "What is the Q3 revenue?";
                const output = document.getElementById("queryOutput");
                output.innerText = "Processing query through Guardrails & RAG pipeline...";
                
                try {
                    const headers = { "Content-Type": "application/json" };
                    if (jwtToken) headers["Authorization"] = "Bearer " + jwtToken;

                    const res = await fetch("/rag/query", {
                        method: "POST",
                        headers: headers,
                        body: JSON.stringify({ query: query })
                    });
                    const data = await res.json();
                    output.innerText = JSON.stringify(data, null, 2);
                } catch (err) {
                    output.innerText = "Error: " + err;
                }
            }

            async function registerUser() {
                const username = document.getElementById("username").value;
                const password = document.getElementById("password").value;
                const role = document.getElementById("role").value;
                const output = document.getElementById("authOutput");

                try {
                    const res = await fetch("/auth/register", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            username: username,
                            password: password,
                            email: username + "@company.com",
                            role_name: role
                        })
                    });
                    const data = await res.json();
                    output.innerText = JSON.stringify(data, null, 2);
                } catch (err) {
                    output.innerText = "Error: " + err;
                }
            }

            async function loginUser() {
                const username = document.getElementById("username").value;
                const password = document.getElementById("password").value;
                const output = document.getElementById("authOutput");

                try {
                    const res = await fetch("/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ username: username, password: password })
                    });
                    const data = await res.json();
                    if (data.access_token) {
                        jwtToken = data.access_token;
                        output.innerText = "Login Successful! Token acquired.\\n\\nRoles: " + JSON.stringify(data.roles);
                    } else {
                        output.innerText = JSON.stringify(data, null, 2);
                    }
                } catch (err) {
                    output.innerText = "Error: " + err;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegisterSchema):
    """Register a new user with a specified role."""
    try:
        user = rbac.register_user(
            username = user_data.username,
            password=user_data.password,
            email=user_data.email,
            role_name=user_data.role_name
        )
        return {
            "status": "success",
            "message": f"User '{user.username}' registered successfully.",
            "role": user_data.role_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/auth/login", response_model=TokenResponseSchema)
def login_user(credentials: UserLoginSchema):
    """Authenticate user and return JWT access token."""
    user = rbac.authenticate(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    token = rbac.create_access_token(user)
    roles = [r.name for r in user.roles]
    return TokenResponseSchema(
        access_token=token,
        # username=user.username,
        roles=roles
    )


@app.post("/rag/query")
def query_rag(
    request: QueryRequestSchema,
    user: Optional[Any] = Depends(get_current_user_from_header)
):
    """
    Execute a RAG query through input validation, context retrieval, LLM generation, 
    output filtering, and Prometheus monitoring.
    """
    # Permission Check
    if user and not rbac.check_permission(user, "query_rag"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'query_rag' denied for your role."
        )

    result = pipeline.query(request.query, user=user)
    return result


@app.post("/rag/ingest")
def ingest_documents(
    request: IngestRequestSchema,
    user: Optional[Any] = Depends(get_current_user_from_header)
):
    """Ingest document files into the vector database."""
    if user and not rbac.check_permission(user, "ingest_documents"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'ingest_documents' denied for your role."
        )

    result = pipeline.ingest(
        file_paths=request.file_paths,
        user=user,
        access_level=request.access_level
    )
    return result


@app.get("/monitoring/analytics")
def get_analytics(user: Optional[Any] = Depends(get_current_user_from_header)):
    """Retrieve operational analytics summary."""
    if user and not rbac.check_permission(user, "view_analytics"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'view_analytics' denied for your role."
        )
    return pipeline.get_analytics()


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  🚀 Web Application Started Successfully!")
    print("  👉 Dashboard URL:  http://localhost:8000")
    print("  👉 API Docs URL:   http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
