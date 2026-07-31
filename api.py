"""REST API for the OSINT research agent: an AI-driven endpoint and a direct Serper bypass.

Run locally with:
    uvicorn api:app --reload
"""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from agent_core import agent_executor, model
from serper_tool import serper_search_tool

app = FastAPI(title="OSINT AI Research Agent API")


def require_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="API_KEY is not configured on the server.")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


class AISearchRequest(BaseModel):
    query: str
    response_schema: Optional[dict] = None


class AISearchResponse(BaseModel):
    answer: str
    structured_answer: Optional[dict] = None
    tool_calls: list


class DirectSearchRequest(BaseModel):
    search_type: str
    query: str
    site: Optional[str] = None
    filetype: Optional[str] = None
    gl: str = "us"
    hl: str = "en"
    time_filter: Optional[str] = None
    num: int = 10


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/search/ai", response_model=AISearchResponse, dependencies=[Depends(require_api_key)])
def search_ai(request: AISearchRequest):
    """Equivalent to the chat panel: the agent decides how (and whether) to search.

    If `response_schema` (a JSON Schema object) is provided, a second pass formats
    the findings into that exact shape, returned as `structured_answer`.
    """
    response = agent_executor.invoke({"messages": [("user", request.query)]})
    messages = response["messages"]

    tool_calls = []
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            tool_calls.append({"tool": call["name"], "args": call["args"]})

    answer = messages[-1].content

    structured_answer = None
    if request.response_schema:
        structured_answer = model.with_structured_output(request.response_schema).invoke(
            f"Question: {request.query}\n\n"
            f"Research findings:\n{answer}\n\n"
            "Format these findings into the requested JSON structure."
        )

    return AISearchResponse(answer=answer, structured_answer=structured_answer, tool_calls=tool_calls)


@app.post("/search/direct", dependencies=[Depends(require_api_key)])
def search_direct(request: DirectSearchRequest):
    """Equivalent to the Manual Search panel: calls Serper directly, bypassing the AI agent."""
    payload = request.model_dump(exclude_none=True)
    return serper_search_tool.invoke(payload)
