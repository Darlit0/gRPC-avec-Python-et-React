from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetUserRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    def __init__(self, user_id: _Optional[int] = ...) -> None: ...

class ListUsersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Address(_message.Message):
    __slots__ = ("street", "city")
    STREET_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    street: str
    city: str
    def __init__(self, street: _Optional[str] = ..., city: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ("id", "name", "email", "nickname", "address")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    NICKNAME_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    email: str
    nickname: str
    address: Address
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., nickname: _Optional[str] = ..., address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class GetUserResponse(_message.Message):
    __slots__ = ("user",)
    USER_FIELD_NUMBER: _ClassVar[int]
    user: User
    def __init__(self, user: _Optional[_Union[User, _Mapping]] = ...) -> None: ...

class CreateUsersResponse(_message.Message):
    __slots__ = ("created_count",)
    CREATED_COUNT_FIELD_NUMBER: _ClassVar[int]
    created_count: int
    def __init__(self, created_count: _Optional[int] = ...) -> None: ...

class ChatMessage(_message.Message):
    __slots__ = ("text", "author", "sent_at_ms")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    SENT_AT_MS_FIELD_NUMBER: _ClassVar[int]
    text: str
    author: str
    sent_at_ms: int
    def __init__(self, text: _Optional[str] = ..., author: _Optional[str] = ..., sent_at_ms: _Optional[int] = ...) -> None: ...

class SubscribeChatRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SendChatMessageResponse(_message.Message):
    __slots__ = ("subscriber_count",)
    SUBSCRIBER_COUNT_FIELD_NUMBER: _ClassVar[int]
    subscriber_count: int
    def __init__(self, subscriber_count: _Optional[int] = ...) -> None: ...
