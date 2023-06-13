from typing import Optional, Union

from sqlmodel import Field, SQLModel


class Forward(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_chat: Union[int, str]
    to_chat: Union[int, str]


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
