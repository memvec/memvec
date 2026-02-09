from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    I keep a single Base so all models hang off the same metadata.
    """
