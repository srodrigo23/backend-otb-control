from pydantic import BaseModel


class ItemBase(BaseModel):
  title: str
  # description: str | None = None


class ItemCreate(ItemBase):
  pass


class Item(ItemBase):
  id: int
  owner_id: int

  class Config:
    from_attributes = True


class UserBase(BaseModel):
  email: str | None = None


class UserCreate(UserBase):
  password: str


class UserUpdate(BaseModel):
  first_name: str | None = None
  second_name: str | None = None
  last_name: str | None = None
  ci: str | None = None
  phone_number: int | None = None
  email: str | None = None


class User(BaseModel):
  id: int
  first_name: str
  second_name: str | None = None
  email: str | None = None
  last_name: str
  ci: str
  phone_number: str | int

  # items: list[Item] = []

  class Config:
    from_attributes = True 