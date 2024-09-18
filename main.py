import MetaTrader5 as mt5
import telepot
import time
from datetime import datetime

# MT5ga kirish uchun hisob ma'lumotlari
login = 191053119  # Hisob raqamingiz
password = "Ak714bjfk"  # Parolingiz
server = "Exness-MT5Trial"  # Broker serveringiz

# Telegram bot konfiguratsiyasi
telegram_token = '7308122911:AAFe91LhORsqSkGgz7EAWxyHCSwJt-xPLZQ'
chat_id = '7212724653'

# MetaTrader5ni boshlash
if not mt5.initialize(login=login, password=password, server=server):
    print(f"MT5 initializatsiyasi muvaffaqiyatsiz: {mt5.last_error()}")
    quit()

# Telegram orqali xabar yuborish funksiyasi
def send_telegram_message(message):
    bot = telepot.Bot(telegram_token)
    bot.sendMessage(chat_id, message)

# Savdo ochish funksiyasi
def open_trade(symbol, lot, order_type, sl_points, tp_points):
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": price - sl_points * mt5.symbol_info(symbol).point if order_type == mt5.ORDER_TYPE_BUY else price + sl_points * mt5.symbol_info(symbol).point,
        "tp": price + tp_points * mt5.symbol_info(symbol).point if order_type == mt5.ORDER_TYPE_BUY else price - tp_points * mt5.symbol_info(symbol).point,
        "deviation": 20,
        "magic": 234000,
        "comment": "Python bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Buyurtma amalga oshmadi, xato: {result.retcode}")
        return False
    return True

# Savdo yopish funksiyasi
def close_trade(order_ticket):
    positions = mt5.positions_get(ticket=order_ticket)
    if len(positions) > 0:
        position = positions[0]
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(position.symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Closing position",
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Savdo yopishda xato: {result.retcode}")
            return False
        return True
    return False

# Savdo strategiyasi (Buy/Sell asosida)
def trade_strategy():
    symbol = "XAUUSD"  # Savdo qilinadigan aktiv
    lot = 0.01
    sl_points = 50  # Stop Loss punktlar
    tp_points = 100  # Take Profit punktlar
    
    # Buy/Sell signal (strategiya)
    moving_average = mt5.iMA(symbol, mt5.TIMEFRAME_M1, 200, 0, mt5.MODE_SMA, mt5.PRICE_CLOSE, 0)
    previous_moving_average = mt5.iMA(symbol, mt5.TIMEFRAME_M1, 200, 0, mt5.MODE_SMA, mt5.PRICE_CLOSE, 1)
    
    # Agar narx yuqorida bo'lsa - Buy
    if mt5.symbol_info_tick(symbol).ask > moving_average and mt5.symbol_info_tick(symbol).ask <= previous_moving_average:
        if open_trade(symbol, lot, mt5.ORDER_TYPE_BUY, sl_points, tp_points):
            send_telegram_message(f"Buy order ochildi: {lot} lot, {sl_points} SL, {tp_points} TP")
    
    # Agar narx pastda bo'lsa - Sell
    elif mt5.symbol_info_tick(symbol).bid < moving_average and mt5.symbol_info_tick(symbol).bid >= previous_moving_average:
        if open_trade(symbol, lot, mt5.ORDER_TYPE_SELL, sl_points, tp_points):
            send_telegram_message(f"Sell order ochildi: {lot} lot, {sl_points} SL, {tp_points} TP")

# Savdo monitoring qilish
while True:
    trade_strategy()
    time.sleep(60)  # Har 1 daqiqada savdo qilishni tekshirib boradi

# MetaTraderni tozalash
mt5.shutdown()
  
