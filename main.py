from flask import Flask, render_template, redirect, url_for, flash, session,request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import pandas as pd
from datetime import datetime
from Algofox import *
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired
import secrets
from threading import Thread

from Connect import XTSConnect
from Exception import XTSInputException


def get_zerodha_credentials():
    # delete_file_contents("OrderLog.txt")
    # delete_file_contents("C:\\Users\\Administrator\\OneDrive\\Desktop\\RaviSptrendRsiVwap-master\\RaviSptrendRsiVwap-master\\OrderLog.txt")
    credentials = {}
    try:
        df = pd.read_csv('MainSettings.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return credentials
credentials_dict = get_zerodha_credentials()
StrategyMode=credentials_dict.get('StrategyMode')

class AuthenticationForm(FlaskForm):
    # XTS Detail
    userId = StringField('UserId', validators=[DataRequired()])
    apiKey = StringField('API KEY', validators=[DataRequired()])
    apiSecret = StringField('API SECRET', validators=[DataRequired()])

    # Algofox details
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')], validators=[DataRequired()])

old_net_pos=None
authenticated=False
id = "11013144"
# API_KEY = "082144eb6500c64b37aa90"
# API_SECRET = "Vnsv775#57"
source = "WEBAPI"
XTS_API_BASE_URL = "https://xts-api.trading"


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
order_logs = []  # Variable to store the order logs


processed_logs = set()  # Set to keep track of processed logs
processed_orders = set()  # Set to keep track of processed orders

def login (username,password,role):
    mainurl=f'https://{url}'
    placeorder=f'http://api.{url}/api/Trade/v1/placeorder'
    authenticate=f'https://api.{url}/api/Trade/v1/authenticate'
    req = requests.post(url=authenticate,
                        json={"username": username, "password": password,
                              "role": role})


    print(req["code"])

    return req["code"]
userId=None
apiKey=None
apiSecret=None
us=None
ps=None
rl=None
xt=None
# xt = XTSConnect(API_KEY, API_SECRET, source)
# response = xt.interactive_login()

url = input("Enter your Admin URL = https//")

createurl(url)


def delete_file_contents(file_path):
    try:
        with open(file_path, 'w') as file:
            file.truncate(0)
        print(f"Successfully deleted all contents of {file_path}.")
    except IOError:
        print(f"Error: Failed to delete contents of {file_path}.")


@app.route('/', methods=['GET', 'POST'])
def authentication():
    delete_file_contents("OrderLogs.txt")
    global authenticated,xt,us,ps,rl
    form = AuthenticationForm()

    if form.validate_on_submit():
        # Access form data
        userId = form.userId.data
        apiKey = form.apiKey.data
        apiSecret = form.apiSecret.data

        username = form.username.data
        password = form.password.data
        role = form.role.data

        loginresult=login_algpfox(username=username, password=password, role=role)
        try:
            # Create XTSConnect instance
            xt = XTSConnect(apiKey, apiSecret, source)
            # Perform authentication
            response = xt.interactive_login()
            if response['type'] == 'success' and loginresult==200:
                # Authentication successful
                authenticated=True
                print("Authentication successful")

                # Store the form data in session
                session['form_data'] = {
                    'userId': userId,
                    'apiKey': apiKey,
                    'apiSecret': apiSecret,
                    'username': username,
                    'password': password,
                    'role': role
                }

                # Redirect to index.html
                return redirect(url_for('index', username=username, password=password, role=role))
            else:
                # Authentication failed
                print("Authentication failed")
                flash("Authentication failed. Please check your XTS details.")

        except XTSInputException as e:
            # XTS input exception raised
            print("XTS input exception:", str("Wrong Credential XTS"))
            flash("XTS details are incorrect. Please check your XTS details.")

        except Exception as e:
            # Other exception occurred
            print("An error occurred:", str("Wrong Credential XTS"))
            flash("Authentication failed. Please check your XTS Credentiales.")

    return render_template('authentication.html', form=form)


def read_symbols_from_csv():
    symbols = []

    try:
        df = pd.read_csv('TradeSettings.csv', usecols=['Symbol'])
        symbols = df['Symbol'].tolist()
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return symbols

def get_all_detail_csv():
    symbols = []

    try:
        df = pd.read_csv('TradeSettings.csv')
        symbols = df.to_dict(orient='records')
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return symbols



printed_orders = []

def check_api_response():
    global authenticated,xt,us,ps,rl,old_net_pos,StrategyMode

    if authenticated:
        with open('OrderLogs.txt', 'r') as f:
            existing_logs = set(f.read().splitlines())

        orderbook = xt.get_order_book()

        try:
            results = orderbook.get('result', [])



            with open('OrderLogs.txt', 'a+') as f:
                for order in results:
                    AppOrderID = order.get('AppOrderID')
                    if AppOrderID not in processed_orders and AppOrderID not in processed_logs:
                        OrderGeneratedDateTime = order.get('OrderGeneratedDateTime')
                        TradingSymbol = order.get('TradingSymbol')
                        OrderQuantity = order.get('OrderQuantity')
                        OrderStatus = order.get('OrderStatus')
                        OrderSide = order.get('OrderSide')
                        ProductType = order.get('ProductType')

                        output = f"{OrderGeneratedDateTime} Order for {OrderSide} {TradingSymbol} {ProductType} for {OrderQuantity} Quantity is {OrderStatus}, Exchange order Id {AppOrderID}"
                        print(output)
                        if output not in existing_logs:
                            f.write(output + '\n')  # Append the output to the OrderLogs.txt file
                            processed_orders.add(AppOrderID)  # Add the AppOrderID to the set of processed orders
                            processed_logs.add(AppOrderID)  # Add the AppOrderID to the set of processed logs

            current_time = datetime.now().strftime("%H:%M")
            symbols = read_symbols_from_csv()  # Read symbols from the CSV file

            for order in results:
                OrderStatus = order.get('OrderStatus')
                OrderGeneratedDateTime = order.get('OrderGeneratedDateTime')
                TradingSymbol = order.get('TradingSymbol')
                OrderQuantity = order.get('OrderQuantity')
                AppOrderID = order.get('AppOrderID')
                OrderSide = order.get('OrderSide')
                ProductType = order.get('ProductType')
                OrderType=order.get('OrderType')
                OrderPrice=order.get('OrderPrice')

                order_time = datetime.strptime(OrderGeneratedDateTime, "%d-%m-%Y %H:%M:%S").strftime("%H:%M")
                ssymbols=get_all_detail_csv()
                if OrderStatus == 'Filled' and StrategyMode=="COMPLETED" and order_time == current_time and AppOrderID not in printed_orders:

                    for symbol in ssymbols:
                        if symbol['Symbol'] == TradingSymbol:
                            ExchangeSymbol = symbol['ExchangeSymbol']
                            StrategyTag = symbol['StrategyTag']
                            Segment = symbol['Segment']
                            product = symbol['ProductType']
                            strike=symbol['STRIKE']
                            contract=symbol['CONTRAC TYPE']
                            expiery=symbol['EXPIERY']


                    if TradingSymbol in symbols:  # Check if the trading symbol is in the symbol list
                        output = f"{OrderGeneratedDateTime} Order for {OrderSide} {TradingSymbol} {ProductType} for {OrderQuantity} Quantity is {OrderStatus}, Exchange order Id {AppOrderID}"
                        print(output)
                        printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list
                        netpositionresponce = xt.get_position_netwise()
                        print("netpositionresponce",netpositionresponce)


                        if Segment == "EQ":
                            for position in netpositionresponce['result']['positionList']:
                                if position['TradingSymbol'] == TradingSymbol:
                                    # for child_position in position['childPositions']:
                                    #     if child_position['TradingSymbol'] == TradingSymbol:
                                    symbol_net_pos = position['Quantity']
                                    print(symbol_net_pos)
                                    if OrderSide == "BUY":
                                        old_net_pos = int(symbol_net_pos) - int(OrderQuantity)
                                    if OrderSide == "SELL":
                                        old_net_pos = int(symbol_net_pos) + int(OrderQuantity)
                                print(old_net_pos)

                        if Segment == "OPTIDX":
                            for position in netpositionresponce['result']['positionList']:
                                if position['TradingSymbol'] == TradingSymbol:
                                    symbol_net_pos = position['Quantity']
                                    print(symbol_net_pos)
                                    if OrderSide == "BUY":
                                        old_net_pos = int(symbol_net_pos) - int(OrderQuantity)
                                    if OrderSide == "SELL":
                                        old_net_pos = int(symbol_net_pos) + int(OrderQuantity)

                                    print(old_net_pos)

                                    printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list

                        if Segment == "FUTIDX":

                            for position in netpositionresponce['result']['positionList']:
                                if position['TradingSymbol'] == TradingSymbol:
                                    symbol_net_pos = position['Quantity']
                                    print(symbol_net_pos)

                                    if OrderSide == "BUY":
                                        old_net_pos = int(symbol_net_pos) - int(OrderQuantity)
                                    elif OrderSide == "SELL":
                                        old_net_pos = int(symbol_net_pos) + int(OrderQuantity)

                                    print(old_net_pos)



                                    printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list


                        if Segment == "FUTSTK":
                            for position in netpositionresponce['result']['positionList']:
                                if position['TradingSymbol'] == TradingSymbol:
                                    symbol_net_pos = position['Quantity']
                                    print(symbol_net_pos)

                                    if OrderSide == "BUY":
                                        old_net_pos = int(symbol_net_pos) - int(OrderQuantity)
                                    elif OrderSide == "SELL":
                                        old_net_pos = int(symbol_net_pos) + int(OrderQuantity)

                                    print(old_net_pos)

                                    printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list


                        if Segment == "OPTSTK":
                            for position in netpositionresponce['result']['positionList']:
                                if position['TradingSymbol'] == TradingSymbol:
                                    symbol_net_pos = position['Quantity']
                                    print(symbol_net_pos)

                                    if OrderSide == "BUY":
                                        old_net_pos = int(symbol_net_pos) - int(OrderQuantity)
                                    elif OrderSide == "SELL":
                                        old_net_pos = int(symbol_net_pos) + int(OrderQuantity)

                                    print(old_net_pos)

                                    printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list


                        if Segment == "FUTSTK":
                            for position in netpositionresponce['result']['positionList']:
                                if position['TradingSymbol'] == TradingSymbol:
                                    symbol_net_pos = position['Quantity']
                                    print(symbol_net_pos)

                                    if OrderSide == "BUY":
                                        old_net_pos = int(symbol_net_pos) - int(OrderQuantity)
                                    elif OrderSide == "SELL":
                                        old_net_pos = int(symbol_net_pos) + int(OrderQuantity)

                                    print(old_net_pos)

                                    printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list


                        order_executed = False
                        if not order_executed and OrderSide == "BUY" and int(old_net_pos) >= 0:
                            print(f"Sending Buy Order @ {TradingSymbol} ")
                            order_executed=True
                            if Segment == "EQ":
                                Buy_order_algofox(symbol=ExchangeSymbol,quantity=OrderQuantity,instrumentType=Segment,direction=OrderSide,price=OrderPrice,product=product,order_typ=OrderType,strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "OPTIDX":
                                sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                Buy_order_algofox(symbol=sname,quantity=OrderQuantity,instrumentType=Segment,direction=OrderSide,price=OrderPrice,product=product,order_typ=OrderType,strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTIDX":
                                sname = f"{ExchangeSymbol}|{str(expiery)}"
                                Buy_order_algofox(symbol=sname, quantity=OrderQuantity, instrumentType=Segment,
                                                  direction=OrderSide, price=OrderPrice, product=product,
                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTSTK":
                                sname = f"{ExchangeSymbol}|{str(expiery)}"
                                Buy_order_algofox(symbol=sname, quantity=OrderQuantity, instrumentType=Segment,
                                                  direction=OrderSide, price=OrderPrice, product=product,
                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "OPTSTK":
                                sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                Buy_order_algofox(symbol=sname,quantity=OrderQuantity,instrumentType=Segment,direction=OrderSide,price=OrderPrice,product=product,order_typ=OrderType,strategy=StrategyTag,username=us,password=ps,role=rl)

                        if not order_executed and OrderSide == "SELL" and int(old_net_pos) <= 0:
                            print(f"Sending Short Order @ {TradingSymbol}")
                            order_executed = True
                            if Segment == "EQ":
                                    Short_order_algofox(symbol=ExchangeSymbol, quantity=OrderQuantity,
                                                                  instrumentType=Segment, direction="SHORT",price=OrderPrice, product=product,
                                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "OPTIDX":
                                    sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "FUTIDX":
                                    sname = f"{ExchangeSymbol}|{str(expiery)}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTSTK":
                                    sname = f"{ExchangeSymbol}|{str(expiery)}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "OPTSTK":
                                    sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                        if not order_executed and OrderSide == "BUY" and int(old_net_pos)< 0:
                            print(f"Sending Cover Order @ {TradingSymbol}")
                            order_executed = True
                            if Segment == "EQ":
                                    Cover_order_algofox(symbol=ExchangeSymbol, quantity=OrderQuantity,
                                                                  instrumentType=Segment, direction="COVER",price=OrderPrice, product=product,
                                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "OPTIDX":
                                                    sname = f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                                    Cover_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="COVER",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTIDX":
                                                    sname = f"{ExchangeSymbol}|{str(expiery)}"
                                                    Cover_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="COVER",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTSTK":
                                                    sname = f"{ExchangeSymbol}|{str(expiery)}"
                                                    Cover_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="COVER",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "OPTSTK":
                                                    sname = f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                                    Cover_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="COVER",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                        if not order_executed and OrderSide == "SELL" and int(old_net_pos) > 0:
                            print(f"Sending Sell Order @ {TradingSymbol}")
                            order_executed = True
                            if Segment == "EQ":
                                Sell_order_algofox(symbol=ExchangeSymbol, quantity=OrderQuantity,
                                                                  instrumentType=Segment, direction="SELL",price=OrderPrice, product=product,
                                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "OPTIDX":
                                sname = f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                Sell_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                       instrumentType=Segment, direction="SELL",
                                                                       price=OrderPrice, product=product,
                                                                       order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTIDX":
                                sname = f"{ExchangeSymbol}|{str(expiery)}"
                                Sell_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                       instrumentType=Segment, direction="SELL",
                                                                       price=OrderPrice, product=product,
                                                                       order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTSTK":
                                sname = f"{ExchangeSymbol}|{str(expiery)}"
                                Sell_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                       instrumentType=Segment, direction="SELL",
                                                                       price=OrderPrice, product=product,
                                                                       order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "OPTSTK":
                                sname = f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                Sell_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                       instrumentType=Segment, direction="SELL",
                                                                       price=OrderPrice, product=product,
                                                                       order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                if OrderStatus == 'Rejected' and (StrategyMode=="REJECTED") and order_time == current_time and AppOrderID not in printed_orders:

                    for symbol in ssymbols:
                        if symbol['Symbol'] == TradingSymbol:
                            ExchangeSymbol = symbol['ExchangeSymbol']
                            StrategyTag = symbol['StrategyTag']
                            Segment = symbol['Segment']
                            product = symbol['ProductType']
                            strike=symbol['STRIKE']
                            contract=symbol['CONTRAC TYPE']
                            expiery=symbol['EXPIERY']


                    if TradingSymbol in symbols:  # Check if the trading symbol is in the symbol list

                        output = f"{OrderGeneratedDateTime} Order for {OrderSide} {TradingSymbol} {ProductType} for {OrderQuantity} Quantity is {OrderStatus}, Exchange order Id {AppOrderID}"
                        print(output)
                        printed_orders.append(AppOrderID)  # Add the AppOrderID to the printed orders list

                        order_executed = False
                        if not order_executed and OrderSide == "BUY" :
                            print(f"Sending Buy Order @ {TradingSymbol} ")
                            order_executed=True
                            if Segment == "EQ":
                                Buy_order_algofox(symbol=ExchangeSymbol,quantity=OrderQuantity,instrumentType=Segment,direction=OrderSide,price=OrderPrice,product=product,order_typ=OrderType,strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "OPTIDX":
                                sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                Buy_order_algofox(symbol=sname,quantity=OrderQuantity,instrumentType=Segment,direction=OrderSide,price=OrderPrice,product=product,order_typ=OrderType,strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTIDX":
                                sname = f"{ExchangeSymbol}|{str(expiery)}"
                                Buy_order_algofox(symbol=sname, quantity=OrderQuantity, instrumentType=Segment,
                                                  direction=OrderSide, price=OrderPrice, product=product,
                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTSTK":
                                sname = f"{ExchangeSymbol}|{str(expiery)}"
                                Buy_order_algofox(symbol=sname, quantity=OrderQuantity, instrumentType=Segment,
                                                  direction=OrderSide, price=OrderPrice, product=product,
                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "OPTSTK":
                                sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                Buy_order_algofox(symbol=sname,quantity=OrderQuantity,instrumentType=Segment,direction=OrderSide,price=OrderPrice,product=product,order_typ=OrderType,strategy=StrategyTag,username=us,password=ps,role=rl)

                        if not order_executed and OrderSide == "SELL" :
                            print(f"Sending Short Order @ {TradingSymbol}")
                            order_executed = True
                            if Segment == "EQ":
                                    Short_order_algofox(symbol=ExchangeSymbol, quantity=OrderQuantity,
                                                                  instrumentType=Segment, direction="SHORT",price=OrderPrice, product=product,
                                                                  order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "OPTIDX":
                                    sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)
                            if Segment == "FUTIDX":
                                    sname = f"{ExchangeSymbol}|{str(expiery)}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "FUTSTK":
                                    sname = f"{ExchangeSymbol}|{str(expiery)}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)

                            if Segment == "OPTSTK":
                                    sname=f"{ExchangeSymbol}|{str(expiery)}|{str(strike)}|{contract}"
                                    Short_order_algofox(symbol=sname, quantity=OrderQuantity,
                                                                        instrumentType=Segment, direction="SHORT",
                                                                        price=OrderPrice, product=product,
                                                                        order_typ=OrderType, strategy=StrategyTag,username=us,password=ps,role=rl)


        except KeyError:
            pass
        except Exception as e:
            print("An error occurred while processing the order book:")
            print(str(e))
            print(orderbook)  # Print the orderbook response for inspection


def run_check_api_response():
    xt = XTSConnect(apiKey, apiSecret, source)
    response = xt.interactive_login()

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_api_response, args=(xt,), trigger=IntervalTrigger(seconds=1))
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


@app.route('/index')
def index():
    global us,ps,rl
    logs = read_order_logs()
    logs.reverse()  # Reverse the order of logs to display the latest log first

    us = request.args.get('username')
    ps = request.args.get('password')
    rl = request.args.get('role')

    return render_template('index.html', logs=logs)



def read_order_logs():
    with open('OrderLogs.txt', 'r') as f:
        logs = f.read().splitlines()
    return logs


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=check_api_response,
        trigger=IntervalTrigger(seconds=1),
        id='check_api_response_job',
        name='Check API Response',
        replace_existing=True
    )
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=True)