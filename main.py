from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from database import get_db, Expense, ExpenseInDB
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import Query
app = FastAPI()


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from database import db
# Helper functions
def parse_expense(expense):
    return {
        "id": str(expense["_id"]),
        "amount": expense["amount"],
        "date": expense["date"],
        "month": expense["month"],
        "year": expense["year"],
        "category": expense["category"],
        "description": expense.get("description"),
        "created_date": expense["created_date"],
    }

expenses_collection = db.expenses

# Routes
@app.post("/expenses/", response_model=ExpenseInDB)
async def create_expense(expense: Expense ):
    expense_data = expense.dict()
    expense_data["created_date"] = datetime.now()
    result = await expenses_collection.insert_one(expense_data)
    created_expense = await expenses_collection.find_one({"_id": result.inserted_id})
    return parse_expense(created_expense)

@app.get("/expenses/{expense_id}", response_model=ExpenseInDB)
async def get_expense(expense_id: str ):
    try:
        expense = await expenses_collection.find_one({"_id": ObjectId(expense_id)})
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return parse_expense(expense)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid expense ID")


@app.get("/expenses/", response_model=list[ExpenseInDB])
async def list_expenses():
    cursor = expenses_collection.find()
    expenses = await cursor.to_list(length=None)
    return [parse_expense(expense) for expense in expenses]

@app.get("/expenses/ls_month_year/", response_model=list[ExpenseInDB])
async def list_expenses_by_month_and_year(
        month: Optional[int] = Query(None, ge=1, le=12),
        year: Optional[int] = Query(None)):
    cursor = expenses_collection.find({"month": month, "year": year})
    expenses = await cursor.to_list(length=None)
    return [parse_expense(expense) for expense in expenses]


@app.delete("/expenses/{expense_id}", response_model=dict)
async def delete_expense(expense_id: str ):
    try:
        result = await expenses_collection.delete_one({"_id": ObjectId(expense_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"message": "Expense deleted successfully"}
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid expense ID")


@app.get("/expenses/summary/")
async def get_expense_summary(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
):
    """
    Summarize expenses grouped by month, year, and category.
    Optional query parameters for filtering by month and year.
    """
    match_stage = {}
    if month:
        match_stage["month"] = month
    if year:
        match_stage["year"] = year

    pipeline = [
        {"$match": match_stage} if match_stage else {},  # Match stage if filters are provided
        {
            "$group": {
                "_id": {
                    "month": "$month",
                    "year": "$year",
                    "category": "$category",
                },
                "total_amount": {"$sum": "$amount"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "month": "$_id.month",
                "year": "$_id.year",
                "category": "$_id.category",
                "total_amount": 1,
            }
        },
        {"$sort": {"year": 1, "month": 1, "category": 1}},  # Sort results for better readability
    ]

    cursor = expenses_collection.aggregate(pipeline)
    result = await cursor.to_list(length=None)  # Await and convert results to a list
    return result


@app.get("/month_year/", response_model=list[ExpenseInDB])
async def list_expenses_by_month_and_year(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None)
):
    # Build the query filter
    query_filter = {}
    if month is not None:
        query_filter["month"] = month
    if year is not None:
        query_filter["year"] = year

    # Perform the query and sort by category
    cursor = expenses_collection.find(query_filter).sort("category", 1)  # 1 for ascending, -1 for descending
    expenses = await cursor.to_list(length=None)

    # Parse the expenses to handle ObjectId conversion
    return [parse_expense(expense) for expense in expenses]


@app.put("/expenses/{expense_id}", response_model=ExpenseInDB)
async def update_expense(expense_id: str, updated_data: Expense):
    """
    Updates an expense document in the MongoDB collection.

    Args:
        expense_id (str): The unique identifier of the expense to update.
        updated_data (Expense): The fields to update.

    Returns:
        ExpenseInDB: The updated expense document.
    """
    if not ObjectId.is_valid(expense_id):
        raise HTTPException(status_code=400, detail="Invalid expense ID")

    update_fields = updated_data.dict(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        # Perform the update
        result = await expenses_collection.update_one(
            {"_id": ObjectId(expense_id)},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found")

        # Fetch the updated document
        updated_expense = await expenses_collection.find_one({"_id": ObjectId(expense_id)})
        return parse_expense(updated_expense)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


# pipeline = [
#     {"$group": {"_id": {"month": "$month", "year": "$year"}}},
#     {"$project": {"month": "$_id.month", "year": "$_id.year", "_id": 0}},
#     {"$sort": {"year": 1, "month": 1}}  # Optional: Sort by year and month
# ]
#
# # Execute the aggregation pipeline
# result = list(collection.aggregate(pipeline))