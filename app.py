import datetime
import pandas as pd
import streamlit as st
import requests

# Backend API URL
BASE_URL = "http://127.0.0.1:8000"  # Replace with your FastAPI backend URL


# Sidebar Menu
with st.sidebar:
    st.markdown("""<style>.big-font {font-size:40px !important;}</style>""", unsafe_allow_html=True)
    st.markdown('<h2 class="big-font">Expense Tracker</h2>', unsafe_allow_html=True)
    st.markdown('#')
    menu = st.selectbox("Menu", ["Create Expense","Summary Expenses", "View All Expenses", "Update Expense", "Delete Expense"])


# Helper Functions
def fetch_expenses():
    response = requests.get(f"{BASE_URL}/expenses/")
    if response.status_code == 200:
        return response.json()
    st.error("Failed to fetch expenses.")
    return []

def delete_expense(expense_id):
    response = requests.delete(f"{BASE_URL}/expenses/{expense_id}")
    if response.status_code == 200:
        st.success(response.json()["message"])
    else:
        st.error(response.json()["detail"])

def fetch_expense_summary(month=None, year=None):
    params = {}
    if month:
        params["month"] = month
    if year:
        params["year"] = year
    response = requests.get(f"{BASE_URL}/expenses/summary/", params=params)
    if response.status_code == 200:
        return response.json()
    st.error("Failed to fetch summary.")
    return []

def fetch_expense_by_month_and_year(month=None, year=None):
    params = {}
    if month:
        params["month"] = month
    if year:
        params["year"] = year
    response = requests.get(f"{BASE_URL}/expenses/ls_month_year/", params=params)
    if response.status_code == 200:
        return response.json()
    st.error("Failed to fetch summary.")
    return []

# Menu Options
if menu == "Create Expense":
    st.header("Create a New Expense")

    with st.form("create_expense_form"):
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date")
        month = date.month
        year = date.year
        category = st.selectbox("Categories", ("Bill", "Shopping", "Saving"))
        description = st.text_area("Description", "")
        submitted = st.form_submit_button("Submit")

        if submitted:
            expense_data = {
                "amount": amount,
                "date": str(date),
                "month": month,
                "year": year,
                "category": category,
                "description": description,
            }
            response = requests.post(f"{BASE_URL}/expenses/", json=expense_data)
            if response.status_code == 200:
                st.success("Expense created successfully!")
            else:
                st.error(response.json().get("detail", "Failed to create expense"))


elif menu == "Summary Expenses":
    st.header("Expense Summary")
    month = st.number_input("Month", min_value=1, max_value=12, step=1, value=None)
    year = st.number_input("Year", min_value=2000, max_value=2100, step=1, value=None)
    if st.button("Fetch Summary"):
        summary = fetch_expense_summary(month, year)
        df = pd.DataFrame(summary)

        list_month_and_year = fetch_expense_by_month_and_year(month, year)
        print(list_month_and_year)
        df_detail = pd.DataFrame(list_month_and_year)

        st.write("Total expense")
        grouped_df = df.groupby(["month", "year"]).agg(
            total_amount=("total_amount", "sum"),
            category=("category", "sum")  # Concatenate categories
        ).reset_index()
        grouped_df['time'] = grouped_df['month'].astype(str) + '-' + grouped_df['year'].astype(str)
        grouped_df = grouped_df.drop(columns=['category', 'month', 'year'])
        grouped_df = grouped_df[['time','total_amount']]
        grouped_df["total_amount"] = grouped_df["total_amount"].apply(lambda x: f"{x:,.0f}")
        st.table(grouped_df.assign(hack='').set_index('hack'))

        st.write("Total expense by categories")
        df['time'] = df['month'].astype(str) + '-' + df['year'].astype(str)
        df = df.drop(columns=['month','year'])
        df["total_amount"] = df["total_amount"].apply(lambda x: f"{x:,.0f}")
        df = df[['time', 'category', 'total_amount']]
        st.table(df.assign(hack='').set_index('hack'))

        st.write("Detail expense")
        df_detail = df_detail.drop(columns=['created_date', 'month', 'year'])
        df_detail = df_detail.sort_values(by="date", ascending=False)
        df_detail['date'] = pd.to_datetime(df_detail["date"], format='mixed').dt.strftime("%d-%m-%Y")
        df_detail["amount"] = df_detail["amount"].apply(lambda x: f"{x:,.0f}")
        df_detail = df_detail[["date", "amount", "category", "description", 'id']]
        st.table(df_detail.assign(hack='').set_index('hack'))




elif menu == "View All Expenses":
    st.header("All Expenses")
    expenses = fetch_expenses()
    df = pd.DataFrame(expenses)
    df = df.drop(columns=['created_date', 'month', 'year'])
    df = df.sort_values(by="date",ascending=False)
    df['date'] = pd.to_datetime(df["date"], format='mixed').dt.strftime("%d-%m-%Y")
    df["amount"] = df["amount"].apply(lambda x: f"{x:,.0f}")
    df = df[["date", "amount", "category", "description", 'id']]
    st.table(df.assign(hack='').set_index('hack'))


elif menu == "Update Expense":
    st.header("Update an Expense")
    expense_id = st.text_input("Expense ID to Update")
    if st.button("Fetch Expense"):
        response = requests.get(f"{BASE_URL}/expenses/{expense_id}")
        if response.status_code == 200:
            expense = response.json()
            date = datetime.datetime.fromisoformat(expense['date'])
            month = expense['month']
            year = expense['year']
            with st.form("update_expense_form"):
                amount = st.number_input("Amount", min_value=0.0, step=0.01, value=expense["amount"])
                category = st.selectbox("Categories", ("Bill", "Shopping", "Saving"))
                description = st.text_area("Description", value=expense.get("description", ""))
                date_update = st.date_input("Date", value=date)
                submitted = st.form_submit_button("Submit")
                print("BBBBB")
                if submitted:
                    print("AAAAA")
                    updated_data = {
                        "amount": amount,
                        "date": date if date_update == date else date_update,
                        "month": month,
                        "year": year,
                        "category": category,
                        "description": description,

                    }
                    print(updated_data)
                    response = requests.put(f"{BASE_URL}/expenses/{expense_id}", json=updated_data)
                    if response.status_code == 200:
                        st.success("Expense updated successfully!")
                    else:
                        st.error(response.json().get("detail", "Failed to update expense"))
        else:
            st.error(response.json().get("detail", "Expense not found"))

elif menu == "Delete Expense":
    st.header("Delete an Expense")
    expense_id = st.text_input("Expense ID to Delete")
    if st.button("Delete"):
        delete_expense(expense_id)

