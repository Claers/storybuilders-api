from datetime import datetime
import uuid
from typing import List
from pydantic import BaseModel, EmailStr, constr
from pydantic.schema import Optional

# Default


class DeleteId(BaseModel):
    id: int


class DeleteByName(BaseModel):
    name: str


class DefaultResponse(BaseModel):
    message: str


# User


class TokenSchema(BaseModel):
    status: str
    access_token: str


class UserBaseSchema(BaseModel):
    name: str
    email: EmailStr
    photo: str
    scopes: str = "me"

    class Config:
        orm_mode = True


class CreateUserSchema(UserBaseSchema):
    password: constr(min_length=8)
    passwordConfirm: str
    role: str = "user"
    verified: bool = False
    created_by: uuid.UUID = None


class LoginUserSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class UserResponse(UserBaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Card Type


class CardTypeSchema(BaseModel):
    name: str
    color: Optional[str]

    class Config:
        orm_mode = True


class CardTypeEdit(CardTypeSchema):
    id: int


class CardTypeResponse(CardTypeSchema):
    id: int


class CardTypeCollection(BaseModel):
    __root__: List[CardTypeSchema]


class CardTypeResponseCollection(BaseModel):
    __root__: List[CardTypeResponse]


# Extension
class ExtensionBaseSchema(BaseModel):
    name: str

    class Config:
        orm_mode = True


class ExtensionResponse(ExtensionBaseSchema):
    id: int


class ExtensionBaseCollection(BaseModel):
    __root__: List[ExtensionBaseSchema]


class ExtensionResponseCollection(BaseModel):
    __root__: List[ExtensionResponse]


# Card


class CardBaseSchema(BaseModel):
    name: str
    description: str
    difficulty: int
    card_type: int
    extension: int

    class Config:
        orm_mode = True


class CardBaseCollection(BaseModel):
    __root__: List[CardBaseSchema]


class CardResponse(CardBaseSchema):
    id: int


class CardCollection(BaseModel):
    __root__: List[CardResponse]
