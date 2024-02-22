################################################################################
# Filename          : app.py
# 
# Description       : This file is responsible for running the Flask framework .
#
################################################################################


################################################################################
# IMPORTS
################################################################################

# ------------------------------------------------------------------------------
# Standard Python Libraries
# ------------------------------------------------------------------------------

import sys
import json
import finnhub 
import mysql.connector
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

from plotly.subplots            import make_subplots
from datetime                   import date
from datetime                   import datetime
from datetime                   import timedelta

from flask                      import Flask, render_template, jsonify
from flask                      import request, session, flash
from flask                      import redirect, url_for
from waitress                   import serve

from sklearn.preprocessing      import MinMaxScaler 
from sklearn.model_selection    import TimeSeriesSplit
from sklearn.metrics            import mean_squared_error, r2_score, mean_absolute_error
from keras.models               import load_model


# Database
__flask_app_connection             = None
__flask_app_cursor                 = None

# Temporary watchlist 
watchlist                          = set()


# try:
#     # Database Settings
#     # change according to your database settings 
#     config = {
#         'host':  'stocksage1.c3ukkiiyeiiz.us-east-1.rds.amazonaws.com',
#         'port': 3306,
#         'user': 'admin',
#         'password': 'Stocksage123',
#         'database': 'stocksage'
#     }


#     __flask_app_connection = mariadb.connect(**config)

# except mariadb.Error as e:
#     print(f"Error connecting to MariaDB Platform: {e}")
#     sys.exit(1)


try:
    # Database Settings
    # Change according to your database settings 
    # config = {
    #     'host': 'localhost',
    #     'port': 3306,
    #     'user': 'root',
    #     'password': '1234',
    #     'database': 'db_am_manager'
    # }

    config = {
        'host':  'stocksage1.c3ukkiiyeiiz.us-east-1.rds.amazonaws.com',
        'port': 3306,
        'user': 'admin',
        'password': 'Stocksage123',
        'database': 'stocksage'
    }

    __flask_app_connection = mysql.connector.connect(**config)

except mysql.connector.Error as e:
    print(f"Error connecting to MySQL: {e}")
    sys.exit(1)

__flask_app_cursor = __flask_app_connection.cursor(dictionary = True)

app = Flask(__name__)
app.secret_key = "1234"

# ----------------------------------------------------------------------
# Flask Route (START)
# ----------------------------------------------------------------------

# landing page
@app.route("/", methods=["POST", "GET"])
def landingPage():
    return __landing_page()
        
# about page
@app.route("/about", methods=["POST", "GET"])
def aboutPage():
    return __about_page()
        
# work page
@app.route("/work", methods=["POST", "GET"])
def workPage():
    return __work_page()
        
# team page
@app.route("/team", methods=["POST", "GET"])
def teamPage():
    return __team_page()
        
# contact page
@app.route("/contact", methods=["POST", "GET"])
def contactPage():
    return __contact_page()
        
# login page
@app.route("/login", methods=["POST", "GET"])
def login():
    return __page_login()
            
# register page
@app.route("/register", methods=["POST", "GET"])
def registerUser():
    return __page_register()
        
# create admin page
@app.route("/createAdmin", methods=["POST", "GET"])
def createAdmin():
    return __page_createAdmin()
        
# home page    
@app.route("/home", methods=["POST", "GET"])
def home():
    return __page_home()
        
# Route to search stock    
@app.route("/search", methods=["POST", "GET"])
def search_stock():
    return __search_stock()
        
# Route to add a symbol to the watchlist
@app.route('/add_to_watchlist/<symbol>')
def add_to_watchlist(symbol):
    watchlist.add(symbol)
    db_watchlist = ', '.join(watchlist)
    username = session.get("name")

    __flask_app_cursor.execute(
            "UPDATE user SET watchlist = %s WHERE username = %s",
                (db_watchlist, username)
        )
    __flask_app_connection.commit()
            
    return redirect(url_for('watchList'))
  
# Route to remove a symbol from the watchlist
@app.route('/remove_from_watchlist/<symbol>')
def remove_from_watchlist(symbol):
    watchlist.remove(symbol)
    db_watchlist = ', '.join(watchlist)
    username = session.get("name")

    __flask_app_cursor.execute(
            "UPDATE user SET watchlist = %s WHERE username = %s",
                (db_watchlist, username)
        )
    __flask_app_connection.commit()
    return redirect(url_for('watchList'))
        
# watch list page
@app.route("/watchList", methods=["POST", "GET"])
def watchList():
    return __page_watchList()
            
# profile page
@app.route("/profile", methods=["POST", "GET"])
def profile():
    return __page_profile()
        
# stock details page
@app.route('/stock_detail/<symbol>')
def stock_detail(symbol):
    return __page_stock_details(symbol)
        
# prediction page
@app.route('/prediction')
def prediction():
    return __page_prediction()
        
# Route for prediction
@app.route('/predict', methods=['POST'])
def predict():
    return __predict()
        
# update profile page
@app.route("/update_profile", methods=["POST"])
def update_profile():
    return __page_update_profile()

# route for getting stock symbol   
@app.route("/quote")
def display_quote():
    # get a stock ticker symbol from the query string
    # default to AAPL
    symbol = request.args.get('symbol', default="AAPL")

    # pull the stock quote
    quote = yf.Ticker(symbol)

    #return the object via the HTTP Response
    return jsonify(quote.info)

# route for pulling the stock history
@app.route("/history")
def display_history():
    #get the query string parameters
    symbol = request.args.get('symbol', default="AAPL")
    period = request.args.get('period', default="1y")
    interval = request.args.get('interval', default="1mo")

    #pull the quote
    quote = yf.Ticker(symbol)	
    #use the quote to pull the historical data from Yahoo finance
    hist = quote.history(period=period, interval=interval)
    #convert the historical data to JSON
    data = hist.to_json()
    #return the JSON in the HTTP response
    return data

# manage users page
@app.route("/manageUsers", methods=["POST", "GET"])
def manageUsers():
    return __page_manageUsers()
        
# View enquiries page
@app.route("/viewEnquiries", methods=["POST", "GET"])
def viewEnquiries():
    return __page_viewEnquiries()
        
# edit page
@app.route("/edit", methods=["POST", "GET"])
def edit():
    return __page_edit()
        
# route for searching user
@app.route("/searchUser", methods=["POST", "GET"])
def search():
    return __search_user()

# route to logout        
@app.route("/logout")
def logout():
    return __page_logout()
        
# ----------------------------------------------------------------------
# Flask Route (END)
# ----------------------------------------------------------------------

# ==========================================================================
# Private Methods
# ==========================================================================
    
# --------------------------------------------------------------------------
# Flask Route Contents (START)
# --------------------------------------------------------------------------

# method to get related news 
def news_sentiment(date, company_code):

        api_key = "cn0ah7pr01qkcvkfucv0cn0ah7pr01qkcvkfucvg"; 
        finnhub_client = finnhub.Client(api_key=api_key)

        start_date = (date - timedelta(days=1)).strftime('%Y-%m-%d')
        date = date.strftime('%Y-%m-%d')

        # Get all the news of that day for the company
        data = finnhub_client.company_news(company_code, _from = start_date, to=date)
        return data


def __landing_page():
    """ This method renders the landing page.
    """

    return render_template("landingPage.html")
    
def __about_page():
    """ This method renders the about page. 
    """

    return render_template("about.html")
    
def __work_page():
    """ This method renders the work page.
     """

    return render_template("work.html")
    
def __team_page():
    """ This method renders the team page.
    """

    return render_template("team.html")
    
def __contact_page():
    """ This method renders the contact page 
        and saves enquiries into the database.
    """

    if request.method == "POST":

        input_name = request.form["name"]
        input_email = request.form["email"]
        input_message = request.form["message"]

        __flask_app_cursor.execute(
            "INSERT INTO enquiries (name,email,message) VALUES (%s, %s, %s)",
                (input_name, input_email, input_message),
        )

        __flask_app_connection.commit()

        flash("Enquiry Sent Successfully!")
        return redirect(url_for("contactPage"))
                
    else:
        return render_template("contact.html")

    
def __page_login():
    """ This method reads user input for login details
        and allows user to log in after checking credentials.
    """

    if request.method == "POST":
      
        session["name"] = request.form.get("name")
        session["password"] = request.form.get("Password")
                
        user = request.form["name"]
        input_password = request.form["Password"]
                
        valid_user = False

        if user == "" or input_password == "":
            flash("User Name or Password cannot be empty!", "info")
            return redirect(url_for("login"))

        __flask_app_cursor.execute(
            "SELECT username FROM user"
        )

        for name in __flask_app_cursor.fetchall():
            if name["username"] == user :                   
                valid_user = True

        if valid_user == True:
            __flask_app_cursor.execute(
                "SELECT password FROM user WHERE username = %s",
                (user,)
            )

            for password in __flask_app_cursor.fetchall():
                if input_password == password["password"]:

                    #//this code block is used to distinguish users with diffeent permissions
                    __flask_app_cursor.execute(
                        "SELECT permission FROM user WHERE username = %s",
                        (user,)
                    )
                    for permission in __flask_app_cursor.fetchall():
                        session["permission"] = permission["permission"]
                                
                    # List of 10 popular stock symbols
                    stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'DIS', 'NVDA', 'BA', 'NFLX', 'INTC']

                    # Create an empty DataFrame to store the data
                    all_data = pd.DataFrame()

                    today = date.today()
                    yesterday = today - timedelta(days = 1)
                    yesterday2 = today - timedelta(days = 3)

                    # Fetch historical data for each stock and concatenate it to the DataFrame
                    for symbol in stock_symbols:
                        stock_data = yf.download(symbol, start=yesterday, end=today, progress=False)
                        stock_data['Symbol'] = symbol  # Add a column for the stock symbol
                        all_data = pd.concat([all_data, stock_data])

                    # Reset index to make 'Date' a regular column
                    all_data.reset_index(inplace=True)

                    # Drop the 'Date' column
                    all_data.drop(columns='Date', inplace=True)

                    # Reorder columns with "Symbol" as the first column
                    columns_order = ['Symbol'] + [col for col in all_data.columns if col != 'Symbol']
                            
                    # Reset the index to start from 1
                    all_data.index = all_data.index + 1
                    all_data = all_data[columns_order]

                    # Convert the DataFrame to HTML
                    table_html = all_data.to_html(classes='table table-striped')
                    return render_template("home.html", data=all_data.to_dict('records'))
                        
                else:
                    flash(
                        "User Name or Password incorrect! Login Unsuccesful!"
                        , "info"
                    )
                    return redirect(url_for("login"))
            else:
                flash("User Name does not exist!", "info")
                return redirect(url_for("login"))
        else:
            return render_template("login.html")
    else:
            return render_template("login.html")


def __page_register():
    """ This method reads user input for account details
        and allows user to create a new account.
    """

    if request.method == "POST":

        input_fullname = request.form["name"]
        input_username = request.form["username"]
        input_email = request.form["email"]
        input_password = request.form["Password"]
        confirm_password = request.form["ConfirmPassword"]
        risk_status = request.form["Risk-Status"]
        age_range = request.form["Age"]
        user_exists = False

        __flask_app_cursor.execute("SELECT username FROM user")

        for username in __flask_app_cursor:

            if username['username']  == input_username:
                user_exists = True
                   

        if user_exists == False:

            if input_password == confirm_password:
                __flask_app_cursor.execute(
                    "INSERT INTO user (username,password,email,fullname,permission,riskstatus,agerange) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (input_username, input_password, input_email, input_fullname, "Member", risk_status, age_range),
                )

                __flask_app_connection.commit()

                flash("Registered Successfully!")
                return redirect(url_for("login"))

            else:
                flash("Password and Confirm password does not match!")
                return redirect(url_for("registerUser"))
        else:
            flash("User already Exists!")
            return redirect(url_for("registerUser"))
                
    else:
        return render_template("register.html")

def __page_createAdmin():
    """ This method reads user input for admin account details
        and allows user to create a new admin account.
    """

    if not session.get("name"):
        return redirect("/")
    elif(session["permission"] != "Admin"):
        return redirect("/home")

    if request.method == "POST":

        input_fullname = request.form["name"]
        input_username = request.form["username"]
        input_email = request.form["email"]
        input_password = request.form["Password"]
        confirm_password = request.form["ConfirmPassword"]
        risk_status = request.form["Risk-Status"]
        age_range = request.form["Age"]
        user_exists = False

        __flask_app_cursor.execute("SELECT username FROM user")

        for username in __flask_app_cursor:

            if username['username']  == input_username:
                user_exists = True
                   

        if user_exists == False:

            if input_password == confirm_password:
                __flask_app_cursor.execute(
                    "INSERT INTO user (username,password,email,fullname,permission,riskstatus,agerange) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (input_username, input_password, input_email, input_fullname, "Admin", risk_status, age_range),
                )

                __flask_app_connection.commit()

                flash("Admin Created Successfully!")
                return redirect(url_for("createAdmin"))

            else:
                flash("Password and Confirm password does not match!")
                return redirect(url_for("createAdmin"))
        else:
            flash("User already Exists!")
            return redirect(url_for("createAdmin"))
                
    else:
        return render_template("createAdmin.html")
        
def __page_profile():
        """ This method renders the profile page.
        """

        username = session.get("name")
        __flask_app_cursor.execute(
                "SELECT * FROM user WHERE username = %s", (username,)
            )
        
        user = __flask_app_cursor.fetchone()
        if not session.get("name"):

            return redirect("/")

        else:
            
            return render_template("profile.html", user = user)

        
def __page_home():

        """ This method renders the home page
        """
        if not session.get("name"):
            return redirect("/")
            
        else:
            # List of 10 popular stock symbols
            stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'DIS', 'NVDA', 'BA', 'NFLX', 'INTC']

            # Create an empty DataFrame to store the data
            all_data = pd.DataFrame()

            today = date.today()
            yesterday = today - timedelta(days = 1)
            yesterday2 = today - timedelta(days = 3)

            # Fetch historical data for each stock and concatenate it to the DataFrame
            for symbol in stock_symbols:
                stock_data = yf.download(symbol, start=yesterday, end=today, progress=False)

                stock_data['Symbol'] = symbol  # Add a column for the stock symbol
                all_data = pd.concat([all_data, stock_data])

            # Reset index to make 'Date' a regular column
            all_data.reset_index(inplace=True)

            # Drop the 'Date' column
            all_data.drop(columns='Date', inplace=True)

            # Reorder columns with "Symbol" as the first column
            columns_order = ['Symbol'] + [col for col in all_data.columns if col != 'Symbol']
            
            # Reset the index to start from 1
            all_data.index = all_data.index + 1
            all_data = all_data[columns_order]

            return render_template("home.html", data=all_data.to_dict('records'))
        
def __search_stock():
        """ This method allows users to search 
            for specific stock and renders the home page.
        """
        if not session.get("name"):
            return redirect("/")
            
        else:
            # List of 10 popular stock symbols
            stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'DIS', 'NVDA', 'BA', 'NFLX', 'INTC']

            # Create an empty DataFrame to store the data
            all_data = pd.DataFrame()

            today = date.today()
            yesterday = today - timedelta(days = 1)
            yesterday2 = today - timedelta(days = 3)

            # Fetch historical data for each stock and concatenate it to the DataFrame
            for symbol in stock_symbols:
                stock_data = yf.download(symbol, start=yesterday, end=today, progress=False)

                stock_data['Symbol'] = symbol  # Add a column for the stock symbol
                all_data = pd.concat([all_data, stock_data])

            # Reset index to make 'Date' a regular column
            all_data.reset_index(inplace=True)

            # Drop the 'Date' column
            all_data.drop(columns='Date', inplace=True)

            # Reorder columns with "Symbol" as the first column
            columns_order = ['Symbol'] + [col for col in all_data.columns if col != 'Symbol']
            
            # Reset the index to start from 1
            all_data.index = all_data.index + 1
            all_data = all_data[columns_order]


            # Create an empty DataFrame to store the data
            search_details = pd.DataFrame()
            search_symbol = request.form['search_symbol']

            search_data = yf.download(search_symbol, start=yesterday, end=today, progress=False)
            search_data['Symbol'] = search_symbol  # Add a column for the stock symbol
            search_details = pd.concat([search_details, search_data])

            return render_template("home.html", data=all_data.to_dict('records'), searchDetails=search_details.to_dict('records'))

def __page_watchList():
    """ This method renders the watch list page.
    """
    if not session.get("name"):
        return redirect("/")
            
    else:
         # Create an empty DataFrame to store the data
        all_data = pd.DataFrame()

        today = date.today()
        yesterday = today - timedelta(days = 1)
        yesterday2 = today - timedelta(days = 3)

        username = session.get("name")

        __flask_app_cursor.execute(
                "SELECT watchlist FROM user WHERE username = %s ",
                (username,)
            )
     
        db_watchlist = (__flask_app_cursor.fetchall()[0])['watchlist']   
                   
        if(db_watchlist != ''):
            watchlist = set(str(db_watchlist).split(", "))
        else:
            watchlist = set()
            

        if(len(watchlist) != 0):
        # Fetch historical data for each stock and concatenate it to the DataFrame
            for symbol in watchlist:
                stock_data = yf.download(symbol, start=yesterday, end=today, progress=False)

                stock_data['Symbol'] = symbol  # Add a column for the stock symbol
                all_data = pd.concat([all_data, stock_data])

            # Reset index to make 'Date' a regular column
            all_data.reset_index(inplace=True)

            # Drop the 'Date' column
            all_data.drop(columns='Date', inplace=True)

            # Reorder columns with "Symbol" as the first column
            columns_order = ['Symbol'] + [col for col in all_data.columns if col != 'Symbol']
                
            # Reset the index to start from 1
            all_data.index = all_data.index + 1
            all_data = all_data[columns_order]

            return render_template("watchlist.html", watchlist = watchlist, data=all_data.to_dict('records'))
        else:
            return render_template("watchlist.html", watchlist = watchlist, data={})

def __page_stock_details(symbol):
        """ This method renders the stock details page.
        """
        if not session.get("name"):
            return redirect("/")
            
        else:    
            # Fetch basic information for the specified symbol
            stock_info = yf.Ticker(symbol).info

            # Fetch news for the specified symbol
            stock_news = yf.Ticker(symbol).news

             # Fetch historical stock prices for the symbol
            historical_data = yf.Ticker(symbol).history(period='1y')

            # Create an interactive candlestick chart using Plotly
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.7, 0.3])

            # Candlestick chart
            candlestick = go.Candlestick(x=historical_data.index,
                                        open=historical_data['Open'],
                                        high=historical_data['High'],
                                        low=historical_data['Low'],
                                        close=historical_data['Close'],
                                        name='Candlesticks')

            fig.add_trace(candlestick, row=1, col=1)

            # Volume chart
            volume = go.Bar(x=historical_data.index, y=historical_data['Volume'], name='Volume', marker=dict(color='blue'))

            fig.add_trace(volume, row=2, col=1)

            # Set layout
            fig.update_layout(
                            xaxis_rangeslider_visible=False,
                            height=600)

            # Convert the plot to HTML
            candlestick_chart = fig.to_html(full_html=False)

            

            # Render the symbol detail page with information and news
            return render_template('stock_detail.html', symbol=symbol, stock_info=stock_info, stock_news=stock_news, candlestick_chart=candlestick_chart)

def __page_prediction():
        """ This renders the prediction page.
        """
        if not session.get("name"):
            return redirect("/")
            
        else:
            # Render the symbol detail page with information and news
            return render_template('prediction.html')

def __predict():
        """ This method reads user input for prediction 
            and renders the prediction page with    
            the relevant predicted information and news.
        """
        if not session.get("name"):
            return redirect("/")
            
        else:
            # Load the pre-trained LSTM model
            model = load_model('final_model.h5')

            # Load the MinMaxScaler
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaler.fit_transform(yf.download('AAPL', start='2010-01-01', end='2022-01-01')[['Open', 'High', 'Low', 'Volume', 'Close']].values)

            # Get form data
            ticker_symbol = request.form['ticker_symbol']
            end_date = request.form['end_date']

            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_predict = end_date - timedelta(days=1)

            # Get historical data
            data = yf.download(ticker_symbol, start='2010-01-01', end=end_date_predict)
            scaled_data = scaler.transform(data[['Open', 'High', 'Low', 'Volume', 'Close']].values)
            
            # Prepare input for prediction
            prediction_days = 70
            x_input = scaled_data[-prediction_days:].reshape(1, prediction_days, 5)
            
            # Make prediction
            prediction = model.predict(x_input)
            
            # Inverse transform the prediction
            predicted_price = scaler.inverse_transform(np.concatenate((scaled_data[-1,:-1], prediction), axis=None).reshape(1, 5))[-1,-1]
            formatted_predicted_price = "${:,.2f}".format(predicted_price)

            # ================================================ #
            # Evaluate the model
            # ================================================ # 

            # Display the model version from json file 
            # Evaluate the model
            actual_price = data.iloc[-1]['Close']
            mae = mean_absolute_error([actual_price], [predicted_price])
            mse = mean_squared_error([actual_price], [predicted_price])
            rmse = np.sqrt(mse)

            # ================================================ #
            # Add the plot 
            # ================================================ #

            fig = make_subplots(rows=1, cols=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Past Stock Prices'))
            fig.add_trace(go.Scatter(x=[end_date], y=[predicted_price], mode='markers', marker=dict(color='red', size=8), name='Predicted Price'))
            fig.update_layout(title='Past Stock Prices and Predicted Price', xaxis_title='Date', yaxis_title='Stock Price', showlegend=True)

           
            plot_html = fig.to_html(full_html=False)

            # Retrive the model metadata 
            with open('model_metadata.json', 'r') as f:
                metadata = json.load(f)

            #display news
            news_data = news_sentiment(end_date, ticker_symbol)

            news_info = []
            for news_item in news_data:

                timestamp = news_item['datetime']
                news_date = datetime.utcfromtimestamp(timestamp)

                news_info.append({
                    'datetime': news_date.strftime('%Y-%m-%d %H:%M:%S'),  
                    'headline': news_item['headline'],
                    'image': news_item['image'],
                    'url': news_item['url']
                })

            # Render the template 
            return render_template('prediction.html',
                                prediction=f'Predicted price for {ticker_symbol} on {end_date}: {formatted_predicted_price}',
                                mse = mse,
                                mae = mae,
                                r2mse = rmse, 
                                plot_html = plot_html,
                                meta_data = metadata,
                                news_info = news_info
                                )


def __page_update_profile():
        """ This method reads user input for account details
            and allows user to update an existing account.
        """
        if not session.get("name"):
            return redirect("/")
            
        else: 
            if request.method == "POST":
                    userid = request.form.get("userid")
                    username = request.form.get("username")
                    password = request.form.get("Password")
                    email = request.form.get("email")
                    fullname = request.form.get("fullname")
                    risk_status = request.form["Risk-Status"]
                    age_range = request.form["Age"]

                    if request.form['action'] == "update":
                        __flask_app_cursor.execute(
                            "UPDATE user SET username = %s, password = %s, email = %s, fullname = %s, riskstatus = %s, agerange = %s WHERE userid = %s",
                            (username, password, email, fullname, risk_status, age_range, userid)
                        )
                        __flask_app_connection.commit()
                    
                        return redirect("/login")
                    
                    elif request.form['action'] == "delete":
                        __flask_app_cursor.execute(
                            "DELETE FROM user WHERE userid = %s", (userid,)
                        )
                        __flask_app_connection.commit()

                        return redirect("/login")   


def __page_manageUsers():
        """ This method renders the manage user page 
            and allows user to edit or delete existing users.
        """
        username = session.get("name")

        if(session["permission"] == "Admin"):
            __flask_app_cursor.execute(
                    "SELECT * FROM user "
                )
        else:
            __flask_app_cursor.execute(
                    "SELECT * FROM user WHERE permission = 'Member'"
                )
        users = __flask_app_cursor.fetchall()

        if not session.get("name"):
            return redirect("/")
        elif(session["permission"] != "Admin"):
            return redirect("/home")    
        else:
            
            return render_template("manageUsers.html", users=users)
        
def __page_viewEnquiries():
        """ This method renders the view enquiries page
        """
        username = session.get("name")
        __flask_app_cursor.execute(
                "SELECT * FROM enquiries"
            )
        
        enquiries = __flask_app_cursor.fetchall()

        if not session.get("name"):
            return redirect("/")
        elif(session["permission"] != "Admin"):
            return redirect("/home")    
        else:
            
            return render_template("enquiries.html", enquiries = enquiries)

def __page_edit():
        """ This method renders the edit page
        """

        userid = request.args.get("userid")
        __flask_app_cursor.execute(
                "SELECT * FROM user WHERE userid = %s", (userid,)
            )
        
        user = __flask_app_cursor.fetchone()

        if not session.get("name"):
            return redirect("/") 
        else:
            
            return render_template("profile.html", user=user)

def __search_user():
        """ This method allows user to search for specific user
        """

        search_term = request.form.get("searchbar")
        search_pattern = "%"+ search_term +"%"
        __flask_app_cursor.execute(
                "SELECT * FROM user WHERE username LIKE %s AND permission = 'Member'", (search_pattern,)
            )
        
        users = __flask_app_cursor.fetchall()
        if not users:
            __flask_app_cursor.execute(
                "SELECT * FROM user WHERE permission = 'Member'"
            )
        
            users = __flask_app_cursor.fetchall()
        

        if not session.get("name"):
            return redirect("/")
            
        else:
            print(search_term)
            return render_template("manageUsers.html", users=users)    

def __page_logout():
        """ This method logs the user out and redirects to the landing page
        """
        session["name"] = None
        return redirect("/")

    # --------------------------------------------------------------------------
    # Flask Route Contents (END)
    # --------------------------------------------------------------------------

# ==============================================================================
# FlaskApp Class (End) 
# ==============================================================================


# ==============================================================================
# Program Entry Point (Start) 
# ==============================================================================

if __name__ == "__main__":

    app.run()

# ==============================================================================
# Program Entry Point (End) 
# ==============================================================================



################################################################################
# END OF FILE
################################################################################