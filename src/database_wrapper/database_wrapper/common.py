from typing import TypeVar

from .db_data_model import DBDataModel

# Bound T to DBDataModel
DataModelType = TypeVar("DataModelType", bound=DBDataModel)

# OrderByItem type
OrderByItem = list[tuple[str, str | None]]


# NoParam class
class NoParam:
    pass
