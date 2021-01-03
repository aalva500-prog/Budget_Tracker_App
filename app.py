from flask import Flask, render_template, request, url_for
import requests
from flask_pymongo import PyMongo
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, DecimalField

import main_functions

app = Flask(__name__)

app.config["SECRET_KEY"] = "your-secret-key-goes-here"

app.config["MONGO_URI"] = "mongodb+srv://username:password@cluster0.u0hsx.mongodb.net/" \
                          "db?retryWrites=true&w=majority"

mongo = PyMongo(app)


class Expenses(FlaskForm):
    description = StringField('Description')
    category = SelectField('Category', choices=[('groceries', 'Groceries'), ('health insurance', 'Health Insurance'),
                                                ('electricity', 'Electricity'), ('car insurance', 'Car Insurance'),
                                                ('rent', 'Rent'), ('telephone', 'Telephone'),
                                                ('clothing', 'Clothing'), ('tolls', 'Tolls'),
                                                ('maintenance', 'Car Maintenance'), ('gas', 'Gasoline')])
    cost = DecimalField('Cost')
    currency = SelectField('Currency', choices=[('USD', 'US Dollars'), ('USDBRL', 'Brazilian Real'),
                                                ('USDBTC', 'Bitcoin'), ('USDCAD', 'Canadian Dollar'),
                                                ('USDCOP', 'Colombian Peso'), ('USDEUR', 'Euro'),
                                                ('USDGBP', 'British Pound Sterling')])
    date = DateField('Date')


def get_expenses_by_category(category):
    # Access the database adding the cost of all documents
    # of the category passed as input parameter
    # write the appropriate query to retrieve the cost
    expense_category = 0
    query = {"category": category}
    records = mongo.db.expenses.find(query)

    for i in records:
        expense_category += float(i["cost"])
    return round(expense_category, 2)


def currency_converter(cost, currency):
    # Extract information from API using the topic selected and the API_key
    url = "http://api.currencylayer.com/live?access_key=your-api-key-goes-here" \
          "&currencies=BTC,BRL,CAD,COP,EUR,GBP"
    # Make the request
    response = requests.get(url).json()
    # Convert the selected currency to USD
    converted_cost = cost / response["quotes"][currency]
    return round(converted_cost, 2)


@app.route('/')
def index():
    # Find all documents in the database
    my_expenses = mongo.db.expenses.find()
    # Get only the list of categories from the database
    categories = mongo.db.expenses.find({}, {"category": 1})
    total_expenses = 0

    # Calculate the total of expenses
    for i in my_expenses:
        total_expenses += float(i["cost"])

    # Create an empty dictionary
    expensesByCategory = {}
    # Calculate expenses by Category
    for x in categories:
        # Create an expenses by category element in the dictionary
        expensesByCategory[x["category"]] = get_expenses_by_category(x["category"])

    return render_template("index.html", expenses=round(total_expenses, 2), expensesByCategory=expensesByCategory)


@app.route('/addExpenses', methods=['GET', 'POST'])
def addExpenses():
    expensesForm = Expenses(request.form)  # Include the form based on class Expenses
    if request.method == 'POST':
        # Get info from the form
        description = request.form['description']
        category = request.form['category']
        cost = request.form['cost']
        date = request.form['date']
        currency = request.form['currency']
        # Verify if the selected currency is different than USD
        if currency != "USD":
            # Convert currency to USD
            cost = currency_converter(float(request.form['cost']), currency)
        # Create dictionary to be inserted in the database
        record = {'description': description, 'category': category, 'cost': float(cost), 'date': date}
        # Insert the new document in the database
        mongo.db.expenses.insert_one(record)
        return render_template("expenseAdded.html")
    return render_template("addExpenses.html", form=expensesForm)


app.run()
