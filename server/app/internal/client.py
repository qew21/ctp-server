import datetime
import time
from copy import deepcopy
import logging

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from app.internal.quote import QuoteImpl
from app.internal.trade import TraderImpl


logger = logging.getLogger(__name__)
subscribe_logger = logging.getLogger('subscribe')


class Client:
    def __init__(self, md_front, td_front, broker_id, app_id, auth_code, user_id, password):
        self._md = None
        self._td = None
        self.md_front = md_front
        self.td_front = td_front
        self.broker_id = broker_id
        self.app_id = app_id
        self.auth_code = auth_code
        self.user_id = user_id
        self.password = password
        self.quotes = {}
        self.subscribe_codes = []

    def login(self):
        '''
        登录行情、交易
        '''
        self._td = None
        self._td = TraderImpl(self.td_front, self.broker_id, self.app_id, self.auth_code, self.user_id, self.password)
        self._md = None
        self._md = QuoteImpl(self.md_front)
        self.subscribe_codes = []

    def logout(self):
        '''
        登出
        '''
        self._md.shutdown()
        self._td.shutdown()
        self.subscribe_codes = []

    def parse_hq(self, x):
        subscribe_logger.info(x)
        code = x.pop('code')
        if code:
            if code not in self.subscribe_codes:
                self.subscribe_codes.append(code)
            self.quotes.update({
                code: x
            })


    def setReceiver(self):
        '''
        tick行情处理函数
        '''
        return self._md.setReceiver(self.parse_hq)

    def subscribe(self, codes):
        '''
        订阅合约代码
        '''
        if not self._td:
            return '账户未登陆！'
        for code in codes:
            if code not in self._td._instruments:
                raise ValueError("合约<%s>不存在" % code)
        self._md.subscribe(codes)

    def subscribe_quote(self, codes):
        '''
        订阅合约代码
        '''
        if not self._td:
            return '账户未登陆！'
        for code in codes:
            if code in self.subscribe_codes:
                self.subscribe_codes.remove(code)
            if code not in self._td._instruments:
                raise ValueError("合约<%s>不存在" % code)
        self._md.subscribe_quote(codes)

    def get_instruments_option(self, future=None):
        '''
        获取期权合约列表，可指定对应的期货代码
        '''
        if not self._td:
            return '账户未登陆！'
        if future is None:
            return self._td.instruments_option
        return self._td.instruments_option.get(future, None)

    def get_instruments_future(self, exchange=None):
        '''
        获取期货合约列表，可指定对应的交易所
        '''
        if not self._td:
            return '账户未登陆！'
        if exchange is None:
            return self._td.instruments_future
        return self._td.instruments_future[exchange]

    def unsubscribe(self, codes):
        '''
        取消订阅
        '''
        self._md.unsubscribe(codes)

    def getInstrument(self, code):
        '''
        获取指定合约详情
        '''
        try:
            if not self._td:
                return '账户未登陆！'
            if code not in self._td._instruments:
                raise ValueError("合约<%s>不存在" % code)
            return self._td._instruments[code].copy()
        except Exception as e:
            logger.error(e)
            return {}

    def getAccount(self):
        '''
        获取账号资金情况
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getAccount()

    def getQuote(self, code):
        '''
        获取账号资金情况
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getQuote(code)

    def getOrders(self):
        '''
        获取当天订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getOrders()

    def getTrades(self):
        '''
        获取当天订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getTrades()

    def getPositions(self):
        '''
        获取持仓
        '''
        if not self._td:
            return '账户未登陆！'
        data = self._td.getPositions()
        if data and data[0]:
            for code in set(i['code'] for i in data[0]):
                if code not in self.subscribe_codes:
                    self.subscribe([code])
            self.setReceiver()
        return data


    def orderMarket(self, code, direction, volume, target_price_type, offset_flag=None):
        '''
        市价下单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderMarket(code, direction, volume, target_price_type, offset_flag)

    def orderFAK(self, code, direction, volume, price, min_volume):
        '''
        FAK下单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderFAK(code, direction, volume, price, min_volume)

    def orderFOK(self, code, direction, volume, price):
        '''
        FOK下单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderFOK(code, direction, volume, price)

    def orderLimit(self, code, direction, volume, price, offset_flag=None):
        '''
        限价单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderLimit(code, direction, volume, price, offset_flag)

    def deleteOrder(self, order_id):
        '''
        撤销订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.deleteOrder(order_id)


    def query_points(self, code):
        # 查询合约点数的方法
        logger.debug(f"query points for {code}")
        temp = self.quotes.get(code)
        if temp and code in self.subscribe_codes:
            # 非交易时间且有上次价格，就用已有的价格；目前没有准确判断是否是交易时间的方法，只能推断
            if temp.get('trade_time', "").split(" ")[-1] in ["11:30:00", "15:00:00", "02:30:00", "06:00:00"]:
                logger.debug(f"get points for {code} done with {temp} in non-trade time")
                return temp
        self.quotes[code] = None
        data = None
        code = code.split(',')[0]
        if code not in self.subscribe_codes:
            self.subscribe([code])
            self.setReceiver()
        start = time.time()
        # 超时5秒
        try_subscribe = False
        while time.time() - start < 5:
            if self.quotes.get(code):
                data = deepcopy(self.quotes[code])
                break
            if time.time() - start > 2 and not try_subscribe:
                # 尝试重新订阅
                self.unsubscribe([code])
                self.subscribe([code])
                self.setReceiver()
                try_subscribe = True
            time.sleep(0.1)
        logger.debug(f"get points for {code} done with {data}")
        return data

    def get_custom_price(self, code, price_type, plus):
        try:
            instruments = self.getInstrument(code)
            plus = int(plus)
            if 'ask' in price_type:
                plus *= -1
            price_tick = instruments.get("price_tick", 0.02)

            data = self.query_points(code)
            if not data:
                data = self.query_points(code)
            if not data:
                return 0, "can not get price data"
            if not data[price_type][0]:
                return 0, f"can not get {price_type} price"
            if data[price_type][0]:
                return data[price_type][0] + price_tick * plus, ""
            return 0, "price data invalid"
        except Exception as e:
            logger.error(f"get_custom_price error: {e}")
            return 0, e


