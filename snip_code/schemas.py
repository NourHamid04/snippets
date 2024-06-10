from ninja import ModelSchema
from typing import List
from pydantic import BaseModel
from typing import Optional
from ninja import Schema,FilterSchema,Field
from datetime import datetime



class SortingSchema(Schema):
    sort_by: Optional[str] = None
    sort_order: Optional[str] = 'asc'
