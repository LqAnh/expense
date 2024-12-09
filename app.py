import datetime
import pandas as pd
import streamlit as st
import requests

# Backend API URL
BASE_URL = "http://127.0.0.1:8000"  # Replace with your FastAPI backend URL
st.set_page_config(
            page_title="Expenses",
            page_icon="🏠",
        )
CSS_MARKDOWN = """
    <style>
        .block-container {
            max-width: 900px;
            display: free;
            flex-direction:row;
            justify-content: flex-start;
        }
        .st-emotion-cache-z5fcl4 {
            padding: 3.5rem 1rem 10rem;
            padding-left: 4rem;
            padding-right: 4rem;
        }
        .st-emotion-cache-5rimss p {
            margin: -20px 0px 1rem;
            font-size: 1.1rem
        }
        .st-emotion-cache-1r6slb0{
            margin-top: 0rem;
        }
        img {
    -webkit-filter: brightness(100%);
    }
    .st-emotion-cache-lrlib{
        display: none;
    }
    </style>
"""
st.markdown(CSS_MARKDOWN, unsafe_allow_html=True)

# INIT
if 'update_id' not in st.session_state:
    st.session_state.update_id = ""
if 'update_get_resp' not in st.session_state:
    st.session_state.update_get_resp = ""
if 'button_status' not in st.session_state:
    st.session_state.button_status = "Summary Expenses"

# Sidebar st.session_state.button_status
with st.sidebar:
    st.markdown("""<style>.big-font {font-size:40px !important;}</style>""", unsafe_allow_html=True)
    st.markdown('<h2 class="big-font">Expense Tracker</h2>', unsafe_allow_html=True)
    st.markdown('#')

    if st.button("Create Expense", use_container_width=True):
        st.session_state.button_status = "Create Expense"
    if st.button("Summary Expenses", use_container_width=True):
        st.session_state.button_status = "Summary Expenses"
    if st.button("View All Expenses", use_container_width=True):
        st.session_state.button_status = "View All Expenses"
    if st.button("Update Expense", use_container_width=True):
        st.session_state.button_status ="Update Expense"
    if st.button("Delete Expense", use_container_width=True):
        st.session_state.button_status = "Delete Expense"


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

if st.session_state.button_status == "Create Expense":
    st.header("Create a New Expense")

    with st.form("create_expense_form"):
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date")
        month = date.month
        year = date.year
        category = st.selectbox("Categories", ("Bill", "Shopping", "Food & Drink", "Saving"), index=None)
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


elif st.session_state.button_status == "Summary Expenses":
    st.header("Expense Summary")
    month_current = datetime.datetime.now().month
    year_current = datetime.datetime.now().year
    summary_current = fetch_expense_summary(month_current, year_current)
    df = pd.DataFrame(summary_current)

    st.write(f"Total expense {month_current} - {year_current}")
    grouped_df = df.groupby(["month", "year"]).agg(
        total_amount=("total_amount", "sum"),
        category=("category", "sum")  # Concatenate categories
    ).reset_index()
    grouped_df['time'] = grouped_df['month'].astype(str) + '-' + grouped_df['year'].astype(str)
    grouped_df = grouped_df.drop(columns=['category', 'month', 'year'])
    grouped_df = grouped_df[['time', 'total_amount']]
    grouped_df["total_amount"] = grouped_df["total_amount"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(grouped_df, hide_index=True, use_container_width=True)

    st.write("Total expense by categories")
    df['time'] = df['month'].astype(str) + '-' + df['year'].astype(str)
    df = df.drop(columns=['month', 'year'])
    df["total_amount"] = df["total_amount"].apply(lambda x: f"{x:,.0f}")
    df = df[['time', 'category', 'total_amount']]
    pivot_df = df.pivot(index='time', columns='category', values='total_amount').reset_index()
    pivot_df['total'] = grouped_df["total_amount"]
    st.dataframe(pivot_df, hide_index=True, use_container_width=True)

    month = st.number_input("Month", min_value=1, max_value=12, step=1, value=None)
    year = st.number_input("Year", min_value=2000, max_value=2100, step=1, value=None)
    if st.button("Fetch Summary"):
        summary = fetch_expense_summary(month, year)
        df = pd.DataFrame(summary)

        list_month_and_year = fetch_expense_by_month_and_year(month, year)
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
        st.dataframe(grouped_df, hide_index=True, use_container_width=True)

        st.write("Total expense by categories")
        df['time'] = df['month'].astype(str) + '-' + df['year'].astype(str)
        df = df.drop(columns=['month', 'year'])
        df["total_amount"] = df["total_amount"].apply(lambda x: f"{x:,.0f}")
        df = df[['time', 'category', 'total_amount']]
        pivot_df = df.pivot(index='time', columns='category', values='total_amount').reset_index()
        pivot_df['total'] = grouped_df["total_amount"]
        st.dataframe(pivot_df, hide_index=True, use_container_width=True)

        st.write("Detail expense")
        df_detail = df_detail.drop(columns=['created_date', 'month', 'year'])
        df_detail = df_detail.sort_values(by="date", ascending=False)
        df_detail['date'] = pd.to_datetime(df_detail["date"], format='mixed').dt.strftime("%d-%m-%Y")
        df_detail["amount"] = df_detail["amount"].apply(lambda x: f"{x:,.0f}")
        df_detail = df_detail[["date", "amount", "category", "description", 'id']]
        st.dataframe(df_detail, hide_index=True, use_container_width=True)




elif st.session_state.button_status == "View All Expenses":
    st.header("All Expenses")
    expenses = fetch_expenses()
    df = pd.DataFrame(expenses)
    df = df.drop(columns=['created_date', 'month', 'year'])
    df = df.sort_values(by="date",ascending=False)
    df['date'] = pd.to_datetime(df["date"], format='mixed').dt.strftime("%d-%m-%Y")
    df["amount"] = df["amount"].apply(lambda x: f"{x:,.0f}")
    df = df[["date", "amount", "category", "description", 'id']]

    st.dataframe(df,hide_index=True,use_container_width=True)



elif st.session_state.button_status == "Update Expense":
    st.header("Update an Expense")
    expense_id = st.text_input("Expense ID to Update")
    st.session_state.update_id = expense_id

    if st.button("Fetch Expense"):
        response = requests.get(f"{BASE_URL}/expenses/{st.session_state.update_id}")
        st.session_state.update_get_resp = response
    if st.session_state.update_get_resp != "":
        if st.session_state.update_get_resp.status_code == 200:
            expense = st.session_state.update_get_resp.json()
            date = datetime.datetime.fromisoformat(expense['date'])
            month = expense['month']
            year = expense['year']
            with st.form('john'):
                amount = st.number_input("Amount", min_value=0.0, step=0.01, value=expense["amount"])
                category = st.selectbox("Categories", ("Bill", "Shopping", "Food & Drink", "Saving"), index=None)
                description = st.text_area("Description", value=expense.get("description", ""))
                date_update = st.date_input("Date", value=date)
                submitted_1 = st.form_submit_button("Submit")
                if submitted_1:
                    updated_data = {
                        "amount": amount,
                        "date": str(date) if date_update == date else str(date_update),
                        "month": month,
                        "year": year,
                        "category": category,
                        "description": description,
                    }
                    response = requests.put(f"{BASE_URL}/expenses/{st.session_state.update_id}", json=updated_data)
                    if response.status_code == 200:
                        st.success("Expense updated successfully!")
                    else:
                        st.error(response.json().get("detail", "Failed to update expense"))


elif st.session_state.button_status == "Delete Expense":
    st.header("Delete an Expense")
    expense_id = st.text_input("Expense ID to Delete")
    if st.button("Delete"):
        delete_expense(expense_id)

