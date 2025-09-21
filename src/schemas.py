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
    orm_mode = False


class UserBase(BaseModel):
  email: str


class UserCreate(UserBase):
  password: str


class User(UserBase):
  id: int
  # is_active: bool
  first_name:str
  second_name:str
  email:str
  last_name:str
  ci:str
  phone_number:str
  
  # items: list[Item] = []

  class Config:
    orm_mode =False 