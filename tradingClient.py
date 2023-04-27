from alpaca.trading.client import TradingClient

from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import time
import datetime
import calendar

class ClientTrading:
    def __init__(self, apiKey, secretKey, paper=True):
        self.client = TradingClient(apiKey, secretKey, paper)
        self.faild = set(['canceled','expired','stopped','rejected','suspended'])
    
    def marketBuyOrder(self, symbol, notional):
        order = MarketOrderRequest(symbol=symbol, notional=notional, side=OrderSide.BUY,
                                    time_in_force=TimeInForce.GTC)
        order_details = self.client.submit_order(order)
        return order_details
    
    def marketBuyOrderCompletion(self, symbol, notional,timeout=60):
        result = {"result":False, "message":"Order failed"}
        order_detail = self.marketBuyOrder(symbol, notional)
        id = order_detail.id
        
        order_status = True
        start = time.time()
        while order_status:
            time.sleep(5)
            order_status_by_id = self.client.get_order_by_id(id)
            status = order_status_by_id.status
            order_status = status == 'filled'
            if order_status in self.failed:
                result['message'] = f"Order failed with status {order_status}"
                return result
            
            if time.time() - start > timeout:
                result['message'] = f"Order failed with timeout and status {order_status}"
                return result

        result['result'] = True
        result['message'] = 'Order completed successfully'
        return result
    
    def buyStocks(self, cash, tickers):
        result = {"result":False, "message":"Order failed on all stocks"}
        executed = []

        cashPerStock = cash / len(tickers)
        for ticker in tickers:
            completed = self.marketBuyOrderCompletion(ticker, cashPerStock)
            if completed['result']:
                executed.append(ticker)
            else:
                result['message'] = f'Order only succeeded on {*executed,} and failed with message: {completed["message"]}'
                return result
        
        result['result'] = True
        result['message'] = 'Successfully traded all tickers'
        return result
    
    def fridayRatio(self):
        # Get the current date
        now = datetime.datetime.now()

        # Initialize a counter for the number of Fridays
        fridays_count = 0

        # current friday
        friday_current = 0

        # Loop through each day in the current month
        for day in range(1, calendar.monthrange(now.year, now.month)[1] + 1):
            # Check if the day is a Friday
            if datetime.datetime(now.year, now.month, day).strftime('%A') == 'Friday':
                fridays_count += 1
                if day <= now.day:
                    friday_current += 1
        
        return friday_current, fridays_count

    def friday_invest_ratio(self):
        current, count = self.fridayRatio()
        diff = current - 1
        return (current - diff) / (count - diff)

    def execute(self, tickers):
        result = {"result":False, "message":"Failed at the beginning"}
        account = self.client.get_account()
        cash = account.cash
        investable = cash * self.friday_invest_ratio()
        result = self.buyStocks(investable, tickers)
        return result
