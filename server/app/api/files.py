"""Fichiers et images joints aux messages (stockés sur le disque en local)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.api.chat import channel_or_404
from app.config import settings
from app.db import get_session
from app.domain.models import Attachment, Member, Message

router = APIRouter(prefix="/api/uploads", tags=["files"])
INLINE = ("image/", "application/pdf", "text/plain", "video/", "audio/")


def _path(att_id: str) -> str:
    return os.path.join(settings.upload_dir, att_id)


@router.post("", status_code=201)
async def upload(file: UploadFile, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    os.makedirs(settings.upload_dir, exist_ok=True)
    limit = settings.max_upload_mb * 1024 * 1024
    att = Attachment(uploader_id=me.id, filename=os.path.basename(file.filename or "fichier")[:255],
                     content_type=(file.content_type or "application/octet-stream")[:120], size=0)
    session.add(att)
    await session.flush()
    size = 0
    with open(_path(att.id), "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                out.close()
                os.remove(_path(att.id))
                raise HTTPException(413, f"Fichier trop lourd (maximum {settings.max_upload_mb} Mo)")
            out.write(chunk)
    att.size = size
    await session.commit()
    return {"id": att.id, "filename": att.filename, "content_type": att.content_type, "size": size,
            "url": f"/api/uploads/{att.id}/{att.filename}"}


@router.get("/{att_id}/{filename}")
async def download(att_id: str, filename: str, me: Member = Depends(current_member),
                   session: AsyncSession = Depends(get_session)):
    att = await session.get(Attachment, att_id)
    if att is None or not os.path.exists(_path(att.id)):
        raise HTTPException(404)
    if att.message_id:
        msg = await session.get(Message, att.message_id)
        await channel_or_404(session, msg.channel_id, me)
    elif att.uploader_id != me.id:
        raise HTTPException(404)
    inline = att.content_type.startswith(INLINE)
    return FileResponse(_path(att.id), media_type=att.content_type, filename=att.filename,
                        content_disposition_type="inline" if inline else "attachment")
