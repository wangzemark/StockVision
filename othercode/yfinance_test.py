import yfinance as yf

# Define the ticker symbol
ticker_symbol = "HK1810"

# Create a Ticker object
ticker = yf.Ticker(ticker_symbol)

# Fetch historical market data
historical_data = ticker.history(period="1y")  # data for the last year
print("Historical Data:")
print(historical_data.loc["2025-01-08 00:00:00-05:00"])
print("\nData Type:",type(historical_data))