from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# MongoDB connection settings
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "expense_tracker"
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

class Expense(BaseModel):
    amount: float = Field(..., gt=0)
    date: datetime
    month: int
    year: int
    category: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class ExpenseInDB(Expense):
    id: str
    created_date: datetime

# Dependency to get database session
def get_db():
    return db



