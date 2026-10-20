from pydantic import BaseModel


class SessionSaveRequest(BaseModel):
    sid: str = "s_unknown"
    data: dict = {}


class SearchRequest(BaseModel):
    novel: bool = True
    sid: str = "s0"
    query: str = ""
    top_k: int = 10


class ChatRequest(BaseModel):
    novel: bool = True
    sid: str = "s0"
    query: str = ""
    pipeline_context: str = ""


class InsightChatRequest(BaseModel):
    novel: bool = True
    sid: str = "s0"
    query: str = ""
    bk: str = ""
