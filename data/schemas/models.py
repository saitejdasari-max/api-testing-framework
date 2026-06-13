"""
data/schemas/models.py
───────────────────────
Pydantic v2 response models used for schema validation.
Import these in tests:  from data.schemas.models import UserSchema
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Geo / Address / Company sub-models ───────────────────────────────────────

class GeoSchema(BaseModel):
    lat: str
    lng: str


class AddressSchema(BaseModel):
    street: str
    suite: Optional[str] = None
    city: str
    zipcode: str
    geo: Optional[GeoSchema] = None


class CompanySchema(BaseModel):
    name: str
    catchPhrase: Optional[str] = None
    bs: Optional[str] = None


# ── User ──────────────────────────────────────────────────────────────────────

class UserSchema(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    username: str = Field(min_length=1)
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[AddressSchema] = None
    company: Optional[CompanySchema] = None


# ── Post ──────────────────────────────────────────────────────────────────────

class PostSchema(BaseModel):
    id: int = Field(gt=0)
    userId: int = Field(gt=0)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class CreatePostResponseSchema(BaseModel):
    id: int = Field(gt=0)
    userId: int
    title: str
    body: str


# ── Comment ───────────────────────────────────────────────────────────────────

class CommentSchema(BaseModel):
    id: int = Field(gt=0)
    postId: int = Field(gt=0)
    name: str
    email: str
    body: str


# ── Album ─────────────────────────────────────────────────────────────────────

class AlbumSchema(BaseModel):
    id: int = Field(gt=0)
    userId: int = Field(gt=0)
    title: str


# ── Generic error envelope ────────────────────────────────────────────────────

class ErrorSchema(BaseModel):
    message: Optional[str] = None
    error: Optional[str] = None
    statusCode: Optional[int] = None
