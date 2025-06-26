import re
from sqlalchemy import UUID, Column, MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    pass
