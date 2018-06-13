import csv
from dotenv import load_dotenv
import json
import os
import pdb
import requests
from datetime import datetime, timedelta

def parse_response(response_text):

    # response_text can be either a raw JSON string or an already-converted dictionary
    if isinstance(response_text, str): # if not yet converted, then:
        response_text = json.loads(response_text) # convert string to dictionary

    results = []
    time_series_daily = response_text["Time Series (Daily)"] #> a nested dictionary
    for trading_date in time_series_daily: # FYI: can loop through a dictionary's top-level keys/attributes

        prices = time_series_daily[trading_date] #> {'1. open': '101.0924', '2. high': '101.9500', '3. low': '100.5400', '4. close': '101.6300', '5. volume': '22165128'}
        result = {
            "date": trading_date,
            "open": prices["1. open"],
            "high": prices["2. high"],
            "low": prices["3. low"],
            "close": prices["4. close"],
            "volume": prices["5. volume"]
        }
        results.append(result)
    return results

def parse_header(response_text):

    # response_text can be either a raw JSON string or an already-converted dictionary
    if isinstance(response_text, str): # if not yet converted, then:
        response_text = json.loads(response_text) # convert string to dictionary

    response_header = response_text["Meta Data"] #> a nested dictionary
    return response_header

def write_prices_to_file(prices=[], filename="db/prices.csv"):
    csv_filepath = os.path.join(os.path.dirname(__file__), "..", filename)
    with open(csv_filepath, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for d in prices:
            row = {
                "timestamp": d["date"], # change attribute name to match project requirements
                "open": d["open"],
                "high": d["high"],
                "low": d["low"],
                "close": d["close"],
                "volume": d["volume"]
            }
            writer.writerow(row)

def format_usd(price_to_format):
    price_to_format = "${0:,.2f}".format(price_to_format)
    return price_to_format


if __name__ == '__main__': # only execute if file invoked from the command-line, not when imported into other files, like tests

    # load_dotenv() # loads environment variables set in a ".env" file, including the value of the ALPHAVANTAGE_API_KEY variable

    #api_key = #"6UC0D1KZNMLWEHU4"  # os.environ.get("ALPHAVANTAGE_API_KEY") or "OOPS. Please set an environment variable named 'ALPHAVANTAGE_API_KEY'."
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY") or "OOPS. Please set an environment variable named 'ALPHAVANTAGE_API_KEY'."
    # CAPTURE USER INPUTS (SYMBOL)

    symbol =  input("Please input a stock symbol (e.g. 'NFLX'): ")

    # VALIDATE SYMBOL AND PREVENT UNECESSARY REQUESTS
    if len(symbol) < 1:
        quit("CHECK YOUR SYMBOL. EXPECTING A MINIMUM OF ONE CHARACTER.")

    try:
        float(symbol)
        quit("CHECK YOUR SYMBOL. EXPECTING A NON-NUMERIC SYMBOL.")
    except ValueError as e:
        pass

    # ASSEMBLE REQUEST URL
    # ... see: https://www.alphavantage.co/support/#api-key

    request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&&apikey={api_key}"

    # ISSUE "GET" REQUEST
    print("ISSUING A REQUEST")
    response = requests.get(request_url)

    # VALIDATE RESPONSE AND HANDLE ERRORS
    if "Error Message" in response.text:
        quit("REQUEST ERROR, PLEASE TRY AGAIN. CHECK YOUR STOCK SYMBOL")

    # PARSE RESPONSE (AS LONG AS THERE ARE NO ERRORS)

    daily_prices = parse_response(response.text)

    header_details = parse_header(response.text)
    last_refresh_date = header_details["3. Last Refreshed"]

    # WRITE TO CSV

    write_prices_to_file(prices=daily_prices, filename="db/prices.csv")

    # PERFORM CALCULATIONS

    # GET THE CLOSING PRICE
    latest_closing_price = daily_prices[0]["close"]
    latest_closing_price = float(latest_closing_price)
    latest_closing_price_usd = format_usd(latest_closing_price)

    # CALCULATE AVERAGE HIGHS AND LOWS
    daily_highs = []
    daily_lows = []
    daily_dates = []
    for p in daily_prices:
        daily_dates.append(p["date"])
        #daily_highs.append(float(p["high"])) # for 100 day average
        #daily_lows.append(float(p["low"])) # for 100 day average

    max_date = max(daily_dates)
    date_upper_range = datetime.strptime(max_date, "%Y-%m-%d")
    date_lower_range = date_upper_range - timedelta(weeks=52)

    fifty_two_week_highs = []
    fifty_two_week_lows = []
    for p in daily_prices:
        if datetime.strptime(p["date"], "%Y-%m-%d") >= date_lower_range and datetime.strptime(p["date"], "%Y-%m-%d") <= date_upper_range:
            fifty_two_week_highs.append(float(p["high"]))
            fifty_two_week_lows.append(float(p["low"]))

    fifty_two_week_high = sum(fifty_two_week_highs)/len(fifty_two_week_highs)
    fifty_two_week_high_usd = format_usd(fifty_two_week_high)
    fifty_two_week_low = sum(fifty_two_week_lows)/len(fifty_two_week_lows)
    fifty_two_week_low_usd = format_usd(fifty_two_week_low)

    #daily_high = sum(daily_highs)/len(daily_highs) # for 100 day average
    #daily_high_usd = format_usd(daily_high) # for 100 day average
    #daily_low = sum(daily_lows)/len(daily_lows) # for 100 day average
    #daily_low_usd = format_usd(daily_low) # for 100 day average

    print("------------------------------------------")
    print(f"Displaying results for {symbol}")
    print(f"Current from {last_refresh_date}")
    print("Report run time " + str(datetime.now()))
    print("------------------------------------------")
    print(f"Lastest closing price...... {latest_closing_price_usd}")
    print(f"52 week average high....... {fifty_two_week_high_usd}")
    print(f"52 week average low........ {fifty_two_week_low_usd}")
    print("------------------------------------------")
    # PRODUCE FINAL RECOMMENDATION

    eight_week_closes = []
    sixteen_week_closes = []
    thirty_two_week_closes = []
    sixty_four_week_closes = []

    eight_week_lower_range = date_upper_range - timedelta(weeks=8)
    for p in daily_prices:
        if datetime.strptime(p["date"], "%Y-%m-%d") >= eight_week_lower_range and datetime.strptime(p["date"], "%Y-%m-%d") <= date_upper_range:
            eight_week_closes.append(float(p["close"]))

    sixteen_week_lower_range = date_upper_range - timedelta(weeks=16)
    for p in daily_prices:
        if datetime.strptime(p["date"], "%Y-%m-%d") >= sixteen_week_lower_range and datetime.strptime(p["date"], "%Y-%m-%d") <= eight_week_lower_range:
            sixteen_week_closes.append(float(p["close"]))

    thirty_two_week_lower_range = date_upper_range - timedelta(weeks=32)
    for p in daily_prices:
        if datetime.strptime(p["date"], "%Y-%m-%d") >= thirty_two_week_lower_range and datetime.strptime(p["date"], "%Y-%m-%d") <= sixteen_week_lower_range:
            thirty_two_week_closes.append(float(p["close"]))

    sixty_four_week_lower_range = date_upper_range - timedelta(weeks=64)
    for p in daily_prices:
        if datetime.strptime(p["date"], "%Y-%m-%d") >= sixty_four_week_lower_range and datetime.strptime(p["date"], "%Y-%m-%d") <= thirty_two_week_lower_range:
            sixty_four_week_closes.append(float(p["close"]))

    eight_week_close = sum(eight_week_closes)/len(eight_week_closes)
    sixteen_week_close = sum(sixteen_week_closes)/len(sixteen_week_closes)
    thirty_two_week_close = sum(thirty_two_week_closes)/len(thirty_two_week_closes)
    sixty_four_week_close = sum(sixty_four_week_closes)/len(sixty_four_week_closes)

    if eight_week_close - sixteen_week_close > 0 and sixteen_week_close - thirty_two_week_close > 0 and thirty_two_week_close - sixty_four_week_close > 0:
        recommendation = f"{symbol} IS ON A STEADY RISE. DO NOT BUY!"
    elif eight_week_close - sixteen_week_close < 0 and sixteen_week_close - thirty_two_week_close < 0 and thirty_two_week_close - sixty_four_week_close < 0:
        if latest_closing_price < 1.2 * fifty_two_week_low:
            recommendation = f"{symbol} IS ON A STEADY DECLINE, BUT THIS CAN TURN. BUY!"
        else:
            recommendation = f"{symbol} IS ON A STEADY DECLINE. DO NOT BUY!"
    elif latest_closing_price < 1.2 * fifty_two_week_low:
        recommendation = "BUY!"
    else:
        recommendation = "DON'T BUY!"
    print(f"Recommendation............. {recommendation}")
