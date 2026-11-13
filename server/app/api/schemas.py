from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    kind: str
    title: str
    role: str
    is_head: bool
    avatar_tone: str
    now_doing: str
    schedule: str
    manual_status: Optional[str]
    status_message: str
    work_days: str = "1,2,3,4,5"
    ask_hour: Optional[int] = 19


class DevLoginIn(BaseModel):
    member_id: str


class MemberUpdate(BaseModel):
    now_doing: Optional[str] = None
    schedule: Optional[str] = None
    manual_status: Optional[str] = None
    status_message: Optional[str] = None
    work_days: Optional[str] = None
    ask_hour: Optional[int] = None
