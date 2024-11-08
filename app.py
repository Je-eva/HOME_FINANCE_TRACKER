from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pymysql as mysql
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)
CORS(app)

# Connect to the database
connection = mysql.connect(host="localhost", user="root", password="123456", database="jeeva")

# Function to create the table if it doesn't exist
def create_table():
    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_records (
                Date DATE,
                Name VARCHAR(100),
                COST int,
                Expenses_Income VARCHAR(20),
                Description VARCHAR(10000)
            )
        ''')
    connection.commit()
    print("Table created successfully")

# Function to insert a new record
def insert(date, name, cost, expenses_income, description):
    date_d = datetime.strptime(date, "%Y-%m-%d").date()
    cost = int(cost)
    
    with connection.cursor() as cursor:
        cursor.execute('''
            INSERT INTO financial_records VALUES (%s, %s, %s, %s, %s) 
        ''', (date_d, name, cost, expenses_income, description))
    connection.commit()
    print("Record inserted successfully.")

# Function to fetch records from the database
def fetch_records():
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM financial_records')
        records = cursor.fetchall()
    return [dict(zip(['Date', 'Name', 'COST', 'Expenses_Income', 'Description'], record)) for record in records]

# Function to fetch and display expenses for a particular name
def get_expenses_name(name):
    with connection.cursor() as cursor:
        query = "SELECT * FROM financial_records WHERE Name = %s"
        cursor.execute(query, (name,))
        records = cursor.fetchall()
    return [dict(zip(['Date', 'Name', 'COST', 'Expenses_Income', 'Description'], record)) for record in records]

# Function to fetch and display expenses between two dates
def get_expenses_date(start_date, end_date):
    with connection.cursor() as cursor:
        query = "SELECT * FROM financial_records WHERE Date BETWEEN %s AND %s"
        cursor.execute(query, (start_date, end_date))
        records = cursor.fetchall()
    return [dict(zip(['Date', 'Name', 'COST', 'Expenses_Income', 'Description'], record)) for record in records]

# Function to plot expenditure
def plot_expenditure(start_date, end_date, plot_type):
    if plot_type in ['income', 'expense']:
        query = f"SELECT Date, COST FROM financial_records WHERE Date BETWEEN %s AND %s AND Expenses_Income = '{plot_type}'"
        with connection.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            records = cursor.fetchall()

        if records:
            df = pd.DataFrame(records, columns=['Date', 'Cost'])
            df['Date'] = pd.to_datetime(df['Date'])

            plt.figure(figsize=(10, 6))
            sns.lineplot(x='Date', y='Cost', data=df, marker='o')
            plt.title(f'{plot_type.capitalize()} Over Time')
            plt.xlabel('Date')
            plt.ylabel('Cost')
            plt.xticks(rotation=45)
            plt.tight_layout()

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plt.close()
            return plot_url
        else:
            return None

    elif plot_type == 'both':
        query_income = "SELECT Date, COST FROM financial_records WHERE Date BETWEEN %s AND %s AND Expenses_Income = 'income'"
        query_expense = "SELECT Date, COST FROM financial_records WHERE Date BETWEEN %s AND %s AND Expenses_Income = 'expense'"
        
        with connection.cursor() as cursor:
            cursor.execute(query_income, (start_date, end_date))
            income_records = cursor.fetchall()
            cursor.execute(query_expense, (start_date, end_date))
            expense_records = cursor.fetchall()

        if income_records and expense_records:
            df_income = pd.DataFrame(income_records, columns=['Date', 'Cost'])
            df_income['Date'] = pd.to_datetime(df_income['Date'])
            df_expense = pd.DataFrame(expense_records, columns=['Date', 'Cost'])
            df_expense['Date'] = pd.to_datetime(df_expense['Date'])

            fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 12))

            sns.lineplot(x='Date', y='Cost', data=df_income, marker='o', ax=axes[0])
            axes[0].set_title('Income Over Time')
            axes[0].set_xlabel('Date')
            axes[0].set_ylabel('Cost')
            axes[0].tick_params(axis='x', rotation=45)

            sns.lineplot(x='Date', y='Cost', data=df_expense, marker='o', ax=axes[1])
            axes[1].set_title('Expense Over Time')
            axes[1].set_xlabel('Date')
            axes[1].set_ylabel('Cost')
            axes[1].tick_params(axis='x', rotation=45)

            plt.tight_layout()

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plt.close()
            return plot_url
        else:
            return None
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/records', methods=['GET', 'POST'])
def handle_records():
    if request.method == 'GET':
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        if start_date and end_date:
            records = get_expenses_date(start_date, end_date)
        else:
            records = fetch_records()
        return jsonify(records)
    elif request.method == 'POST':
        record = request.json
        insert(record['date'], record['name'], record['cost'], record['type'], record['description'])
        return jsonify({"message": "Record inserted successfully"}), 201

@app.route('/api/records/<username>', methods=['GET'])
def handle_user_records(username):
    return jsonify(get_expenses_name(username))

@app.route('/api/plot', methods=['GET'])
def handle_plot():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    plot_type = request.args.get('type', 'both')
    if start_date and end_date:
        plot_url = plot_expenditure(start_date, end_date, plot_type)
        if plot_url:
            return jsonify({"plot": plot_url})
        else:
            return jsonify({"message": "No data available for the specified date range"}), 404
    else:
        return jsonify({"message": "Start date and end date are required"}), 400

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pymysql as mysql
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)
CORS(app)

# ... (keep all the existing code)

# New function to get user-specific data
def get_user_data(username, start_date=None, end_date=None):
    with connection.cursor() as cursor:
        if start_date and end_date:
            query = """
            SELECT Date, COST, Expenses_Income
            FROM financial_records
            WHERE Name = %s AND Date BETWEEN %s AND %s
            ORDER BY Date
            """
            cursor.execute(query, (username, start_date, end_date))
        else:
            query = """
            SELECT Date, COST, Expenses_Income
            FROM financial_records
            WHERE Name = %s
            ORDER BY Date
            """
            cursor.execute(query, (username,))
        records = cursor.fetchall()
    return [dict(zip(['Date', 'COST', 'Expenses_Income'], record)) for record in records]

# New function to get monthly expense trends for all users
def get_monthly_expense_trends():
    with connection.cursor() as cursor:
        query = """
        SELECT Name, DATE_FORMAT(Date, '%Y-%m') as Month, SUM(CASE WHEN Expenses_Income = 'expense' THEN COST ELSE 0 END) as Expense
        FROM financial_records
        GROUP BY Name, DATE_FORMAT(Date, '%Y-%m')
        ORDER BY Name, Month
        """
        cursor.execute(query)
        records = cursor.fetchall()
    return [dict(zip(['Name', 'Month', 'Expense'], record)) for record in records]

# New API endpoint for user-specific data
@app.route('/api/user-data/<username>', methods=['GET'])
def handle_user_data(username):
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    data = get_user_data(username, start_date, end_date)
    return jsonify(data)

# New API endpoint for monthly expense trends
@app.route('/api/monthly-expense-trends', methods=['GET'])
def handle_monthly_expense_trends():
    data = get_monthly_expense_trends()
    return jsonify(data)

# New API endpoint to get all usernames
@app.route('/api/usernames', methods=['GET'])
def handle_usernames():
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT Name FROM financial_records")
        usernames = [row[0] for row in cursor.fetchall()]
    return jsonify(usernames)

# ... (keep the rest of the existing code)
def get_user_income_expense(start_date, end_date):
    with connection.cursor() as cursor:
        query = """
        SELECT Name, 
               SUM(CASE WHEN Expenses_Income = 'income' THEN COST ELSE 0 END) as Income,
               SUM(CASE WHEN Expenses_Income = 'expense' THEN COST ELSE 0 END) as Expense
        FROM financial_records
        WHERE Date BETWEEN %s AND %s
        GROUP BY Name
        """
        cursor.execute(query, (start_date, end_date))
        records = cursor.fetchall()
    return [dict(zip(['Name', 'Income', 'Expense'], record)) for record in records]

# New function to get user contribution data
def get_user_contribution():
    with connection.cursor() as cursor:
        query = """
        SELECT Name, 
               SUM(CASE WHEN Expenses_Income = 'income' THEN COST ELSE 0 END) as Income,
               SUM(CASE WHEN Expenses_Income = 'expense' THEN COST ELSE 0 END) as Expense
        FROM financial_records
        GROUP BY Name
        """
        cursor.execute(query)
        records = cursor.fetchall()
    return [dict(zip(['Name', 'Income', 'Expense'], record)) for record in records]

# New API endpoint for user-specific income and expense comparison
@app.route('/api/user-income-expense', methods=['GET'])
def handle_user_income_expense():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    if start_date and end_date:
        data = get_user_income_expense(start_date, end_date)
        return jsonify(data)
    else:
        return jsonify({"message": "Start date and end date are required"}), 400

# New API endpoint for user contribution
@app.route('/api/user-contribution', methods=['GET'])
def handle_user_contribution():
    data = get_user_contribution()
    return jsonify(data)

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
