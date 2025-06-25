# SOL-USD Trading Strategy Backtest (SMA Crossover + RSI + TP/SL)

import yfinance as yf
import pandas as pd

# === Parameters and Setup ===

symbol = "SOL-USD"                  # Trading symbol (Solana vs USD)
initial_balance = 10000            # Starting capital in USD
short_window = 10                  # Short-term moving average window
long_window = 40                   # Long-term moving average window
stop_loss_pct = 0.01               # 1% stop loss
take_profit_pct = 0.05             # 5% take profit
rsi_threshold = 67                 # Minimum RSI to confirm buy signal

# === Download Historical Price Data ===

# Gets hourly price data from the past 6 months
data = yf.download(symbol, period="6mo", interval="1h")[["Close"]]

# === Indicator Calculations ===

# Simple Moving Averages
data["SMA_short"] = data["Close"].rolling(window=short_window).mean()
data["SMA_long"] = data["Close"].rolling(window=long_window).mean()

# RSI Calculation (14-period)
delta = data["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

# === Generate Signals Based on Indicators ===

# Buy signal when short SMA crosses above long SMA
data["Signal"] = 0
data.loc[data["SMA_short"] > data["SMA_long"], "Signal"] = 1
data["MA_Crossover"] = data["Signal"].diff()   # 1 = bullish crossover

# === Simulate Trades ===

balance = initial_balance     # Current cash balance
crypto_position = 0.0         # Amount of SOL held
entry_price = 0.0             # Price at which SOL was bought
trades = []                   # Log of executed trades

# Loop through each bar in the dataset
for i in range(1, len(data)):
    price = data["Close"].iloc[i].item()
    rsi = data["RSI"].iloc[i]
    signal_raw = data["MA_Crossover"].iloc[i]

    # Buy condition: crossover + no open position + RSI filter
    if pd.notna(signal_raw):
        signal = float(signal_raw)
        if signal == 1.0 and crypto_position == 0.0 and rsi > rsi_threshold:
            entry_price = price
            crypto_position = balance / price
            balance = 0
            trades.append({"type": "buy", "price": price, "time": data.index[i]})

    # Exit trade if stop loss or take profit is hit
    if crypto_position > 0.0:
        current_return = (price - entry_price) / entry_price
        if current_return <= -stop_loss_pct or current_return >= take_profit_pct:
            balance = crypto_position * price
            crypto_position = 0.0
            trades.append({"type": "sell", "price": price, "time": data.index[i]})

# === Final Portfolio Valuation ===

final_price = data["Close"].iloc[-1].item()
final_value = balance + (crypto_position * final_price)
profit = final_value - initial_balance
return_pct = (profit / initial_balance) * 100

# === Performance Metrics: Win Rate ===

wins, losses = 0, 0
for i in range(0, len(trades) - 1, 2):   # Each buy/sell pair
    buy = trades[i]["price"]
    sell = trades[i + 1]["price"]
    if sell > buy:
        wins += 1
    else:
        losses += 1
accuracy = (wins / (wins + losses)) * 100 if wins + losses > 0 else 0

# === Print Final Summary ===

print("\n📊 SOL Strategy Performance:")
print(f"Final Value: ${final_value:.2f}")
print(f"Profit: ${profit:.2f}")
print(f"Return: {return_pct:.2f}%")
print(f"Win Rate: {accuracy:.2f}% ({wins} wins / {wins + losses} trades)")
