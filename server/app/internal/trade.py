import datetime
import json
import re
import time
from collections import defaultdict, OrderedDict

import ctpwrapper as CTP
import ctpwrapper.ApiStructure as CTPStruct
from pytz import timezone

from app.internal.spi import SpiHelper
from app.internal.constants import DATA_DIR, FILTER
import os
import logging


logger = logging.getLogger(__name__)


class TraderImpl(SpiHelper, CTP.TraderApiPy):
    def __init__(self, front, broker_id, app_id, auth_code, user_id, password):
        SpiHelper.__init__(self)
        CTP.TraderApiPy.__init__(self)
        self._last_query_time = 0
        self._broker_id = broker_id
        self._app_id = app_id
        self._auth_code = auth_code
        self._user_id = user_id
        self._password = password
        self._front_id = None
        self._session_id = None
        self._order_action = None
        self._order_ref = 0
        flow_dir = DATA_DIR + "td_flow/"
        os.makedirs(flow_dir, exist_ok=True)
        self.Create(flow_dir)
        self.RegisterFront(front)
        self.SubscribePrivateTopic(2)  # THOST_TERT_QUICK
        self.SubscribePublicTopic(2)  # THOST_TERT_QUICK
        self.Init()
        self.waitCompletion("登录交易会话")
        # del self._app_id, self._auth_code, self._password
        self._getInstruments()
        self.instruments_option = defaultdict(list)
        self.instruments_future = defaultdict(list)
        self._buildInstrumentsDict()
        self.lastDataTime = None
        self.lastAccount = None
        self.lastPositions = []
        self.lastOrders = {}
        self.lastTrades = {}

    def _limitFrequency(self):
        delta = time.time() - self._last_query_time
        if delta < 1:
            time.sleep(1 - delta)
        self._last_query_time = time.time()

    def __del__(self):
        self.Release()
        logger.info("已登出交易服务器...")

    def shutdown(self):
        self.Release()
        logger.info("已登出交易服务器...")

    def OnFrontConnected(self):
        logger.info("已连接交易服务器...")
        field = CTPStruct.ReqAuthenticateField(BrokerID=self._broker_id,
                                               AppID=self._app_id, AuthCode=self._auth_code, UserID=self._user_id)
        logger.info(f"OnFrontConnected, {field=}")
        self.checkApiReturnInCallback(self.ReqAuthenticate(field, 0))

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        logger.info("OnRspError:")
        logger.info("requestID:", nRequestID)
        logger.info(pRspInfo)
        logger.info(bIsLast)

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告。当长时间未收到报文时，该方法被调用。
        @param nTimeLapse 距离上次接收报文的时间
        """
        logger.info("OnHeartBeatWarning time: ", nTimeLapse)

    def OnFrontDisconnected(self, nReason):
        logger.info("已断开交易服务器:{}...".format(nReason))

    def OnRspAuthenticate(self, _, info, req_id, is_last):
        assert (req_id == 0)
        assert (is_last)
        if not self.checkRspInfoInCallback(info):
            return
        logger.info("已通过交易终端认证...")
        field = CTPStruct.ReqUserLoginField(BrokerID=self._broker_id,
                                            UserID=self._user_id, Password=self._password)
        logger.info(f"OnRspAuthenticate, {field=}")
        self.checkApiReturnInCallback(self.ReqUserLogin(field, 1))

    def OnRspUserLogin(self, field, info, req_id, is_last):
        logger.info(f"OnRspUserLogin, {field=}")
        assert (req_id == 1)
        assert (is_last)
        if not self.checkRspInfoInCallback(info):
            return
        self._front_id = field.FrontID
        self._session_id = field.SessionID
        logger.info("已登录交易会话...")
        field = CTPStruct.SettlementInfoConfirmField(BrokerID=self._broker_id,
                                                     InvestorID=self._user_id)
        self.checkApiReturnInCallback(self.ReqSettlementInfoConfirm(field, 2))

    def OnRspSettlementInfoConfirm(self, _, info, req_id, is_last):
        assert (req_id == 2)
        assert (is_last)
        if not self.checkRspInfoInCallback(info):
            return
        logger.info("已确认结算单...")
        self.notifyCompletion()

    def _getInstruments(self):
        file_path = DATA_DIR + "instruments.dat"
        now_date = time.strftime("%Y-%m-%d", time.localtime())
        if os.path.exists(file_path):
            fd = open(file_path)
            cached_date = fd.readline()
            if cached_date[: -1] == now_date:
                self._instruments = json.load(fd)
                fd.close()
                logger.info("已加载全部共%d个合约..." % len(self._instruments))
                return
            fd.close()
        self._instruments = {}
        self.resetCompletion()
        self._limitFrequency()
        self.checkApiReturn(self.ReqQryInstrument(CTPStruct.QryInstrumentField(), 3))
        last_count = 0
        while True:
            try:
                self.waitCompletion("获取所有合约")
                break
            except TimeoutError as e:
                count = len(self._instruments)
                if count == last_count:
                    raise e
                logger.info("已获取%d个合约..." % count)
                last_count = count
        fd = open(file_path, "w")
        fd.write(now_date + "\n")
        json.dump(self._instruments, fd, ensure_ascii=False)
        fd.close()
        logger.info("已保存全部共%d个合约..." % len(self._instruments))

    def _buildInstrumentsDict(self):
        for symbol in self._instruments:
            instrument = self._instruments[symbol]
            instrument["symbol"] = symbol
            if re.search(r"[\d\-][CP][\d\-]", symbol):
                try:
                    self.instruments_option[re.findall(r"([A-Za-z]{2,}\d{2,})", symbol)[0]].append(instrument)
                except:
                    self.instruments_option[re.findall(r'(^[A-Za-z]\d+)', symbol)[0]].append(instrument)
            else:
                self.instruments_future[instrument['exchange']].append(instrument)

    def OnRspQryInstrument(self, field, info, req_id, is_last):
        assert (req_id == 3)
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        if field:
            # logger.info(f"OnRspQryInstrument, {field=}")
            if field.OptionsType == '1':  # THOST_FTDC_CP_CallOptions
                option_type = "call"
            elif field.OptionsType == '2':  # THOST_FTDC_CP_PutOptions
                option_type = "put"
            else:
                option_type = None
            expire_date = None if field.ExpireDate == "" else \
                time.strftime("%Y-%m-%d", time.strptime(field.ExpireDate, "%Y%m%d"))
            self._instruments[field.InstrumentID] = {"name": field.InstrumentName,
                                                     "exchange": field.ExchangeID, "multiple": field.VolumeMultiple,
                                                     "price_tick": field.PriceTick, "expire_date": expire_date,
                                                     "long_margin_ratio": FILTER(field.LongMarginRatio),
                                                     "short_margin_ratio": FILTER(field.ShortMarginRatio),
                                                     "option_type": option_type,
                                                     "strike_price": FILTER(field.StrikePrice),
                                                     "is_trading": bool(field.IsTrading)}
        if is_last:
            logger.info("已获取全部共%d个合约..." % len(self._instruments))
            self.notifyCompletion()

    def getAccount(self):
        # THOST_FTDC_BZTP_Future = 1
        try:
            field = CTPStruct.QryTradingAccountField(BrokerID=self._broker_id,
                                                     InvestorID=self._user_id, CurrencyID="CNY", BizType='1')
            logger.info(f"getAccount, {field=}")
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.ReqQryTradingAccount(field, 8))
            self.waitCompletion("获取资金账户")
        except Exception as e:
            logger.error(f"getAccount, {e=}, {self._account=}")
        return [self.lastAccount, self.lastDataTime]

    def getQuote(self, code):
        start_date = time.strftime("%H:%M:%S", time.localtime(time.time() - 1000))
        end_date = time.strftime("%H:%M:%S", time.localtime())
        logger.info(f"{start_date=}. {end_date=},{self._instruments[code]['exchange']=}")
        field = CTPStruct.QryQuoteField(BrokerID=self._broker_id, InvestUnitID='1',
                                        InvestorID=self._user_id, InstrumentID=code, InsertTimeStart=start_date,
                                        InsertTimeEnd=end_date,
                                        ExchangeID=self._instruments[code]["exchange"], QuoteSysID="123")
        logger.info(f"getQuote, {field=}")
        self.resetCompletion()
        self._limitFrequency()
        rq = self.ReqQryQuote(field, 8)
        logger.info(f"rq, {rq=}")
        self.checkApiReturn(rq)
        self.waitCompletion("获取报价")
        return self._account

    def OnRspQryTradingAccount(self, field, info, req_id, is_last):
        assert (req_id == 8)
        assert (is_last)
        logger.info(f"OnRspQryTradingAccount, {field=}")
        if not self.checkRspInfoInCallback(info):
            return
        self._account = {"balance": round(field.Balance, 2), "margin": round(field.CurrMargin, 2),
                         "available": round(field.Available, 2), "profit": round(field.PositionProfit, 2)}
        logger.info("已获取资金账户...")
        self.lastAccount = self._account
        self.notifyCompletion()

    def OnRspQryQuote(self, field, info, req_id, is_last):
        # assert(req_id == 8)
        # assert(is_last)
        logger.info(f"OnRspQryQuote, {field=}， {info=},{req_id=},{is_last=}")
        if not self.checkRspInfoInCallback(info):
            return
        # self._account = {"balance": field.Balance, "margin": field.CurrMargin,
        #         "available": field.Available}
        logger.info("已获取报价...")
        self.notifyCompletion()

    def getOrders(self):
        self._orders = {}
        try:
            field = CTPStruct.QryOrderField(BrokerID=self._broker_id,
                                            InvestorID=self._user_id)
            logger.info(f"getOrders, {field=}")
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.ReqQryOrder(field, 4))
            self.waitCompletion("获取所有报单")
            _orders = sorted(self._orders.items(), key=lambda x: x[1]['insert_time'])
            self._orders = OrderedDict(_orders)
        except Exception as e:
            logger.error(f"getOrders, {e=}, {self._orders=}")
        try:
            if self.lastOrders:
                for order_id in self.lastOrders:
                    instruments = self._instruments[self.lastOrders[order_id]['code']].copy()
                    number_str = str(instruments.get("price_tick"))
                    decimal_places = 2
                    if number_str and '.' in number_str:
                        decimal_places = len(number_str.split('.')[1])
                    self.lastOrders[order_id]['decimal_places'] = decimal_places
                    self.lastOrders[order_id]['volume'] = int(self.lastOrders[order_id]['volume'])
                self.lastOrders = {i: j for i, j in sorted(self.lastOrders.items(), key=lambda x: x[1]['insert_time'] + x[0])}
        except Exception as e:
            logger.error(f"lastOrders, {e=}, {self.lastOrders=}")
        return [self.lastOrders, self.lastDataTime]

    def getTrades(self):
        self._trades = {}
        try:
            field = CTPStruct.QryTradeField(BrokerID=self._broker_id,
                                            InvestorID=self._user_id)
            logger.info(f"getTrades, {field=}")
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.ReqQryTrade(field, 4))
            self.waitCompletion("获取所有成交")
            _trades = sorted(self._trades.items(), key=lambda x: x[1]['trade_time'])
            self._trades = OrderedDict(_trades)
        except Exception as e:
            logger.error(f"getTrades, {e=}, {self._trades=}")
        try:
            if self.lastTrades:
                for order_id in self.lastTrades:
                    instruments = self._instruments[self.lastTrades[order_id]['code']].copy()
                    number_str = str(instruments.get("price_tick"))
                    decimal_places = 2
                    if number_str and '.' in number_str:
                        decimal_places = len(number_str.split('.')[1])
                    self.lastTrades[order_id]['decimal_places'] = decimal_places
                    self.lastTrades[order_id]['volume'] = int(self.lastTrades[order_id]['volume'])
                self.lastTrades = {i: j for i, j in sorted(self.lastTrades.items(), key=lambda x: x[1]['trade_time'] + x[0])}
        except Exception as e:
            logger.error(f"lastTrades, {e=}, {self.lastTrades=}")
        return [self.lastTrades, self.lastDataTime]

    def _gotOrder(self, order):
        if len(order.OrderSysID) == 0:
            return
        oid = "%s@%s" % (order.OrderSysID, order.InstrumentID)
        (direction, volume) = (int(order.Direction), order.VolumeTotalOriginal)
        assert (direction in (0, 1))
        if order.CombOffsetFlag == '1':  # THOST_FTDC_OFEN_Close
            direction = 1 - direction
            volume = -volume
        direction = "short" if direction else "long"
        # THOST_FTDC_OST_AllTraded = 0, THOST_FTDC_OST_Canceled = 5
        is_active = order.OrderStatus not in ('0', '5')
        logger.info(f"_gotOrder = {order}")
        assert (oid not in self._orders)
        self._orders[oid] = {"code": order.InstrumentID, "direction": direction,
                             "price": order.LimitPrice, "volume": volume, "insert_time": order.InsertTime,
                             "cancel_time": order.CancelTime, "active_time": order.ActiveTime, "update_time": order.UpdateTime,
                             "comb_offset_flag": order.CombOffsetFlag,
                             "volume_traded": order.VolumeTraded, "is_active": is_active}

    def _gotTrade(self, trade):
        if len(trade.TradeID) == 0:
            return
        logger.info(f"_gotTrade = {trade}")
        oid = "%s@%s" % (trade.TradeID, trade.InstrumentID)
        (direction, volume) = (int(trade.Direction), trade.Volume)
        assert (direction in (0, 1))
        direction = "short" if direction else "long"
        self._trades[oid] = {"code": trade.InstrumentID, "direction": direction, "order_id": trade.OrderSysID,
                             "price": trade.Price, "volume": volume, "trade_date": trade.TradeDate,
                             "trade_time": trade.TradeTime}

    def OnRspQryOrder(self, field, info, req_id, is_last):
        assert (req_id == 4)
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        if field:
            self._gotOrder(field)
        if is_last:
            logger.info("已获取所有报单...")
            self.lastDataTime = datetime.datetime.now(timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
            self.lastOrders = self._orders
            self.notifyCompletion()

    def OnRspQryTrade(self, field, info, req_id, is_last):
        assert (req_id == 4)
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        if field:
            self._gotTrade(field)
        if is_last:
            logger.info("已获取所有成交...")
            self.lastDataTime = datetime.datetime.now(timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
            self.lastTrades = self._trades
            self.notifyCompletion()

    def getPositions(self):
        self._positions = []
        try:
            field = CTPStruct.QryInvestorPositionField(BrokerID=self._broker_id,
                                                       InvestorID=self._user_id)
            self.resetCompletion()
            self._limitFrequency()
            logger.info(f"getPositions, {field=}")
            self.checkApiReturn(self.ReqQryInvestorPosition(field, 5))
            self.waitCompletion("获取所有持仓")
        except Exception as e:
            logger.error(f"getPositions, {e=}, {self._positions=}")
        try:
            if self.lastPositions:
                for position in self.lastPositions:
                    instruments = self._instruments[position['code']].copy()
                    number_str = str(instruments.get("price_tick"))
                    decimal_places = 2
                    if number_str and '.' in number_str:
                        decimal_places = len(number_str.split('.')[1])
                    position['decimal_places'] = decimal_places
                self.lastPositions.sort(key=lambda x: x['code'])
        except Exception as e:
            logger.error(f"lastPositions, {e=}, {self.lastPositions=}")
        return [self.lastPositions, self.lastDataTime]

    def _gotPosition(self, position):
        code = position.InstrumentID
        if position.PosiDirection == '2':  # THOST_FTDC_PD_Long
            direction = "long"
        elif position.PosiDirection == '3':  # THOST_FTDC_PD_Short
            direction = "short"
        else:
            return
        volume = position.Position
        if volume == 0:
            return
        logger.info(f"_gotPosition, {position=}")
        open_cost = round(position.OpenCost, 2)
        position_cost = round(position.PositionCost, 2)
        position_profit = round(position.PositionProfit, 2)
        multiple = self._instruments[code]['multiple']
        self._positions.append({"code": code, "direction": direction,
                                "volume": int(volume), "margin": round(position.UseMargin, 2),
                                "cost": open_cost, "position_date": position.PositionDate,
                                "yd_position": position.YdPosition, "today_position": position.TodayPosition,
                                "long_frozen": position.LongFrozen, "short_frozen": position.ShortFrozen,
                                "open_volume": position.OpenVolume, "close_volume": position.CloseVolume,
                                "settlement_price": position.SettlementPrice,
                                "position_profit": position_profit,
                                "profit": position_profit + open_cost - position_cost,
                                "open_cost_price": round(float(position.OpenCost) / float(volume) / float(multiple), 2),
                                })

    def OnRspQryInvestorPosition(self, field, info, req_id, is_last):
        assert (req_id == 5)
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        if field:
            self._gotPosition(field)
        if is_last:
            self.lastPositions = self._positions
            self.lastDataTime = datetime.datetime.now(timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
            logger.info("已获取所有持仓...")
            self.notifyCompletion()

    def OnRtnOrder(self, order):
        if self._order_action:
            if self._order_action(order):
                self._order_action = None

    def OnRtnTrade(self, trade):
        logger.info(trade)

    def _handleNewOrder(self, order):
        order_ref = None if len(order.OrderRef) == 0 else int(order.OrderRef)
        if (order.FrontID, order.SessionID, order_ref) != \
                (self._front_id, self._session_id, self._order_ref):
            return False
        logger.info(f"_handleNewOrder, {order=}")
        if order.OrderStatus == 'a':  # THOST_FTDC_OST_Unknown
            return False
        if order.OrderSubmitStatus == '4':  # THOST_FTDC_OSS_InsertRejected
            self.notifyCompletion(order.StatusMsg)
            return True
        if order.TimeCondition == '1':  # THOST_FTDC_TC_IOC
            # THOST_FTDC_OST_AllTraded = 0, THOST_FTDC_OST_Canceled = 5
            if order.OrderStatus in ('0', '5'):
                logger.info("已执行IOC单，成交量：%d" % order.VolumeTraded)
                self._traded_volume = order.VolumeTraded
                self.notifyCompletion()
                return True
        else:
            assert (order.TimeCondition == '3')  # THOST_FTDC_TC_GFD
            if order.OrderSubmitStatus in ("3", "0"):  # THOST_FTDC_OSS_Accepted
                # THOST_FTDC_OST_AllTraded = 0, THOST_FTDC_OST_PartTradedQueueing = 1
                # THOST_FTDC_OST_PartTradedNotQueueing = 2, THOST_FTDC_OST_NoTradeQueueing = 3
                # THOST_FTDC_OST_NoTradeNotQueueing = 4, THOST_FTDC_OST_Canceled = 5
                assert (order.OrderStatus in ('0', '1', '2', '3', '4', '5'))
                assert (len(order.OrderSysID) != 0)
                self._order_id = "%s@%s" % (order.OrderSysID, order.InstrumentID)
                logger.info("已提交限价单（单号：<%s>）" % self._order_id)
                self.notifyCompletion()
                return True
        return False

    def _order(self, code, direction, volume, price, min_volume, target_price_type=None, target_offset_flag=None):
        if code not in self._instruments:
            raise ValueError("合约<%s>不存在！" % code)
        exchange = self._instruments[code]["exchange"]
        if direction == "long":
            direction = 0  # THOST_FTDC_D_Buy
        elif direction == "short":
            direction = 1  # THOST_FTDC_D_Sell
        else:
            raise ValueError("错误的买卖方向<%s>" % direction)
        if volume != int(volume) or volume == 0:
            raise ValueError("交易数量<%s>必须是非零整数" % volume)
        if volume > 0:
            offset_flag = '0'  # THOST_FTDC_OF_Open
        else:
            offset_flag = '1'  # THOST_FTDC_OF_Close
            volume = -volume
            direction = 1 - direction
        direction = str(direction)
        # Market Price Order
        if price == 0:
            if exchange == "CFFEX":
                price_type = 'G'  # THOST_FTDC_OPT_FiveLevelPrice
            else:
                price_type = '1'  # THOST_FTDC_OPT_AnyPrice
            # THOST_FTDC_TC_IOC, THOST_FTDC_VC_AV
            (time_cond, volume_cond) = ('1', '1')
        # Limit Price Order
        elif min_volume == 0:
            # THOST_FTDC_OPT_LimitPrice, THOST_FTDC_TC_GFD, THOST_FTDC_VC_AV
            (price_type, time_cond, volume_cond) = ('2', '3', '1')
        # FAK Order
        else:
            min_volume = abs(min_volume)
            if min_volume > volume:
                raise ValueError("最小成交量<%s>不能超过交易数量<%s>" % (min_volume, volume))
            # THOST_FTDC_OPT_LimitPrice, THOST_FTDC_TC_IOC, THOST_FTDC_VC_MV
            (price_type, time_cond, volume_cond) = ('2', '1', '2')
        self._order_ref += 1
        self._order_action = self._handleNewOrder
        field = CTPStruct.InputOrderField(BrokerID=self._broker_id,
                                          InvestorID=self._user_id, ExchangeID=exchange, InstrumentID=code,
                                          Direction=direction,
                                          CombOffsetFlag=offset_flag if not target_offset_flag else target_offset_flag,
                                          TimeCondition=time_cond, VolumeCondition=volume_cond,
                                          OrderPriceType=price_type if not target_price_type else target_price_type,
                                          LimitPrice=price,
                                          VolumeTotalOriginal=volume, MinVolume=min_volume,
                                          CombHedgeFlag='1',  # THOST_FTDC_HF_Speculation
                                          ContingentCondition='1',  # THOST_FTDC_CC_Immediately
                                          ForceCloseReason='0',  # THOST_FTDC_FCC_NotForceClose
                                          OrderRef="%12d" % self._order_ref)
        logger.info(f"_order, {field=}")
        self.resetCompletion()
        rq = self.ReqOrderInsert(field, 6)
        self.checkApiReturn(rq)
        self.waitCompletion("录入报单")

    def OnRspOrderInsert(self, field, info, req_id, is_last):
        assert (req_id == 6)
        assert (is_last)
        logger.info(f"OnRspOrderInsert, {field=}")
        self.OnErrRtnOrderInsert(field, info)

    def OnErrRtnOrderInsert(self, _, info):
        success = self.checkRspInfoInCallback(info)
        assert (not success)

    def orderMarket(self, code, direction, volume, target_price_type=None, offset_flag=None):
        self._order(code, direction, volume, 0, 0, target_price_type, offset_flag)
        return self._traded_volume

    def orderFAK(self, code, direction, volume, price, min_volume):
        assert (price > 0)
        self._order(code, direction, volume, price, 1 if min_volume == 0 else min_volume)
        return self._traded_volume

    def orderFOK(self, code, direction, volume, price):
        return self.orderFAK(code, direction, volume, price, volume)

    def orderLimit(self, code, direction, volume, price, target_offset_flag=None):
        assert (price > 0)
        self._order(code, direction, volume, price, 0, target_offset_flag=target_offset_flag)
        return self._order_id

    def _handleDeleteOrder(self, order):
        oid = "%s@%s" % (order.OrderSysID, order.InstrumentID)
        if oid != self._order_id:
            return False
        logger.info(f"_handleDeleteOrder, {order=}")
        if order.OrderSubmitStatus == '5':  # THOST_FTDC_OSS_CancelRejected
            self._order_delete_status = {"order_id": self._order_id, "status": order.StatusMsg}
            self.notifyCompletion(order.StatusMsg)
            return True
        # THOST_FTDC_OST_AllTraded = 0, THOST_FTDC_OST_Canceled = 5
        if order.OrderStatus in ('0', '5'):
            logger.info("已撤销限价单，单号：<%s>" % self._order_id)
            self._order_delete_status = {"order_id": self._order_id, "status": order.StatusMsg}
            # StatusMsg(已撤单) 不再抛出异常
            self.notifyCompletion()
            return True
        return False

    def deleteOrder(self, order_id):
        self._order_delete_status = {}
        items = order_id.split("@")
        if len(items) != 2:
            raise ValueError("订单号<%s>格式错误" % order_id)
        (sys_id, code) = items
        if code not in self._instruments:
            raise ValueError("订单号<%s>中的合约号<%s>不存在" % (order_id, code))
        field = CTPStruct.InputOrderActionField(BrokerID=self._broker_id,
                                                InvestorID=self._user_id, UserID=self._user_id,
                                                ActionFlag='0',  # THOST_FTDC_AF_Delete
                                                ExchangeID=self._instruments[code]["exchange"],
                                                InstrumentID=code, OrderSysID=sys_id)
        logger.info(f"deleteOrder, {field=}")
        self.resetCompletion()
        self._order_id = order_id
        self._order_action = self._handleDeleteOrder
        self.checkApiReturn(self.ReqOrderAction(field, 7))
        self.waitCompletion("撤销报单")
        return self._order_delete_status

    def OnRspOrderAction(self, field, info, req_id, is_last):
        logger.info(f"OnRspOrderAction, {field=}")
        assert (req_id == 7)
        assert (is_last)
        self.OnErrRtnOrderAction(field, info)

    def OnErrRtnOrderAction(self, _, info):
        success = self.checkRspInfoInCallback(info)
        assert (not success)
