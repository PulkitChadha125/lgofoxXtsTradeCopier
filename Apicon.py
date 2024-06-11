from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from Connect import XTSConnect
import pandas as pd
from datetime import datetime

app = Flask(__name__)
order_logs = []  # Variable to store the order logs
processed_orders = set()
processed_symbols = set()

id = "11013144"
API_KEY = "082144eb6500c64b37aa90"
API_SECRET = "Vnsv775#57"
source = "WEBAPI"
XTS_API_BASE_URL = "https://xts-api.trading"

xt = XTSConnect(API_KEY, API_SECRET, source)
response = xt.interactive_login()
previous_response = None


def check_trading_symbol_exists(trading_symbol):
    # Read the CSV file and check if the trading symbol exists in the 'Symbol' column
    try:
        csv_data = pd.read_csv('TradeSettings.csv')
        return trading_symbol in csv_data['Symbol'].values
    except pd.errors.EmptyDataError:
        return False


def update_order_logs(log):
    global order_logs
    order_logs.append(log)


def check_api_response():
    global previous_response
    global processed_orders
    global processed_symbols
    global order_logs  # Declare order_logs as a global variable
    processed_symbols = set()
    response = xt.get_order_book(id)  # Replace with your API call

    if response != previous_response:
        new_order_logs = []
        if 'result' in response:
            current_time = datetime.now().replace(second=0, microsecond=0)  # Get the current time without seconds and microseconds

            for order in response['result']:
                if isinstance(order, dict) and order['OrderStatus'] == 'Filled':
                    app_order_id = order['AppOrderID']
                    if app_order_id not in processed_orders:
                        trading_symbol = order['TradingSymbol']

                        # Check if the trading symbol exists in the CSV file
                        if check_trading_symbol_exists(trading_symbol):
                            order_generated_time = datetime.strptime(order['OrderGeneratedDateTime'], '%d-%m-%Y %H:%M:%S')

                            # Check if the order generated time matches the current hour and minute
                            if order_generated_time.hour == current_time.hour and order_generated_time.minute == current_time.minute:
                                order_string = f"{order_generated_time} {trading_symbol} Order For {order['OrderSide']} is {order['OrderStatus']} for {order['OrderQuantity']} and product type {order['ProductType']}, Exchange Broker Id {app_order_id}"

                                # Print the order string only once for a new app order ID
                                if app_order_id not in processed_orders:
                                    netposition_response = xt.get_position_netwise(clientID=id)
                                    found = False
                                    quantity = None

                                    for position in netposition_response['result']['positionList']:
                                        if 'childPositions' in position:
                                            for child_position in position['childPositions']:
                                                if trading_symbol == child_position['TradingSymbol']:
                                                    quantity = child_position['Quantity']
                                                    found = True
                                                    break
                                            if found:
                                                break

                                    if found:
                                        # Print the result only once
                                        if trading_symbol not in processed_symbols:
                                            print(f"Trading Symbol: {trading_symbol}, Quantity: {quantity}")
                                            processed_symbols.add(trading_symbol)

                                        # Update the log with the current time
                                        log = {
                                            'timestamp': order_generated_time,
                                            'order_string': order_string
                                        }
                                        new_order_logs.append(log)

                                        # Process the order based on conditions
                                        if order['OrderSide'] == "BUY" and int(quantity) >= 0:
                                            print(f'Place buy order {trading_symbol}')
                                        if order['OrderSide'] == "SELL" and int(quantity) <= 0:
                                            print(f'Place Short order {trading_symbol}')
                                        if order['OrderSide'] == "BUY" and int(quantity) < 0:
                                            print(f'Place Cover order {trading_symbol}')
                                        if order['OrderSide'] == "SELL" and int(quantity) > 0:
                                            print(f'Place Sell order {trading_symbol}')

                                    processed_orders.add(app_order_id)

            new_order_logs.sort(key=lambda x: x['timestamp'], reverse=True)  # Sort the order logs based on the timestamp

            if new_order_logs != order_logs:
                order_logs = new_order_logs

                with open('OrderLogs.txt', 'w') as file:
                    file.write('\n'.join(log['order_string'] for log in order_logs))


        previous_response = response


scheduler = BackgroundScheduler()
scheduler.add_job(check_api_response, 'interval', seconds=2)
scheduler.start()

def read_order_logs_from_file():
    with open('OrderLogs.txt', 'r') as file:
        return file.read().splitlines()

@app.route('/')
def index():
    order_logs = read_order_logs_from_file()
    return render_template('index.html', order_logs=order_logs)


if __name__ == '__main__':
    # Read the existing order logs from the file
    with open('OrderLogs.txt', 'r') as file:
        order_logs = file.read().splitlines()

    # Run the Flask app
    app.run(debug=True)
