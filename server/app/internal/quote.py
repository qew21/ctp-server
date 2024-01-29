import ctpwrapper as CTP
import ctpwrapper.ApiStructure as CTPStruct
from app.internal.spi import SpiHelper
from app.internal.constants import DATA_DIR, FILTER
import os
import logging


logger = logging.getLogger("subscribe")


class QuoteImpl(SpiHelper, CTP.MdApiPy):
    def __init__(self, front):
        SpiHelper.__init__(self)
        CTP.MdApiPy.__init__(self)
        self._receiver = None
        flow_dir = DATA_DIR + "md_flow/"
        os.makedirs(flow_dir, exist_ok=True)
        self.Create(flow_dir)
        self.RegisterFront(front)
        self.Init()
        self.waitCompletion("登录行情会话")

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        logger.info("OnRspError:")
        logger.info("requestID:", nRequestID)
        logger.info(pRspInfo)
        logger.info(bIsLast)

    def __del__(self):
        self.Release()
        logger.info("已登出行情服务器...")

    def shutdown(self):
        self.Release()
        logger.info("已登出行情服务器...")

    def OnFrontConnected(self):
        logger.info("已连接行情服务器...")
        field = CTPStruct.ReqUserLoginField()
        logger.info(f"OnFrontConnected, {field=}")
        self.checkApiReturnInCallback(self.ReqUserLogin(field, 0))
        self.status = 0

    def OnFrontDisconnected(self, nReason):
        logger.info("已断开行情服务器:{}...".format(nReason))

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告。当长时间未收到报文时，该方法被调用。
        @param nTimeLapse 距离上次接收报文的时间
        """
        logger.info('Md OnHeartBeatWarning, time = {0}'.format(nTimeLapse))

    def OnRspUserLogin(self, _, info, req_id, is_last):
        assert (req_id == 0)
        assert (is_last)
        if not self.checkRspInfoInCallback(info):
            return
        logger.info("已登录行情会话...")
        self.status = 1
        self.notifyCompletion()

    def setReceiver(self, func):
        old_func = self._receiver
        self._receiver = func
        return old_func

    def subscribe(self, codes):
        self.resetCompletion()
        self.checkApiReturn(self.SubscribeMarketData(codes))
        self.waitCompletion("订阅行情")

    def subscribe_quote(self, codes):
        self.resetCompletion()
        self.checkApiReturn(self.SubscribeForQuoteRsp(codes))
        self.waitCompletion("订阅询价")

    def OnRspSubMarketData(self, field, info, _, is_last):
        logger.info(f"OnRspSubMarketData, {field=}")
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        logger.info("已订阅<%s>的行情..." % field.InstrumentID)
        if is_last:
            self.notifyCompletion()

    def OnRspSubForQuoteRsp(self, field, info, _, is_last):
        logger.info(f"OnRspSubForQuoteRsp, {field=}, {info=}")
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        logger.info("已订阅<%s>的询价..." % field.InstrumentID)
        if is_last:
            self.notifyCompletion()

    def OnRtnDepthMarketData(self, field):
        if not self._receiver:
            return
        logger.info(f"OnRtnDepthMarketData, {field=}")
        self._receiver({"trade_time": field.TradingDay[:4] + '-' + field.TradingDay[4:6] + '-' + field.TradingDay[
                                                                                                 6:] + " " + field.UpdateTime,
                        "update_sec": int(field.UpdateMillisec),
                        "code": field.InstrumentID, "price": FILTER(field.LastPrice),
                        "open": FILTER(field.OpenPrice), "close": FILTER(field.ClosePrice),
                        "highest": FILTER(field.HighestPrice), "lowest": FILTER(field.LowestPrice),
                        "upper_limit": FILTER(field.UpperLimitPrice),
                        "lower_limit": FILTER(field.LowerLimitPrice),
                        "settlement": FILTER(field.SettlementPrice), "volume": field.Volume,
                        "turnover": field.Turnover, "open_interest": int(field.OpenInterest),
                        "pre_close": FILTER(field.PreClosePrice),
                        "pre_settlement": FILTER(field.PreSettlementPrice),
                        "pre_open_interest": int(field.PreOpenInterest),
                        "ask1": (FILTER(field.AskPrice1), field.AskVolume1),
                        "bid1": (FILTER(field.BidPrice1), field.BidVolume1),
                        "ask2": (FILTER(field.AskPrice2), field.AskVolume2),
                        "bid2": (FILTER(field.BidPrice2), field.BidVolume2),
                        "ask3": (FILTER(field.AskPrice3), field.AskVolume3),
                        "bid3": (FILTER(field.BidPrice3), field.BidVolume3),
                        "ask4": (FILTER(field.AskPrice4), field.AskVolume4),
                        "bid4": (FILTER(field.BidPrice4), field.BidVolume4),
                        "ask5": (FILTER(field.AskPrice5), field.AskVolume5),
                        "bid5": (FILTER(field.BidPrice5), field.BidVolume5)})

    def OnRtnForQuoteRsp(self, field):
        logger.info(f"OnRtnForQuoteRsp, {field=}")
        if not self._receiver:
            return
        self._receiver({"trade_time": field.TradingDay[:4] + '-' + field.TradingDay[4:6] + '-' + field.TradingDay[
                                                                                                 6:] + " " + field.UpdateTime,
                        "update_sec": int(field.UpdateMillisec),
                        "code": field.InstrumentID, "price": FILTER(field.LastPrice),
                        "open": FILTER(field.OpenPrice), "close": FILTER(field.ClosePrice),
                        "highest": FILTER(field.HighestPrice), "lowest": FILTER(field.LowestPrice),
                        "upper_limit": FILTER(field.UpperLimitPrice),
                        "lower_limit": FILTER(field.LowerLimitPrice),
                        "settlement": FILTER(field.SettlementPrice), "volume": field.Volume,
                        "turnover": field.Turnover, "open_interest": int(field.OpenInterest),
                        "pre_close": FILTER(field.PreClosePrice),
                        "pre_settlement": FILTER(field.PreSettlementPrice),
                        "pre_open_interest": int(field.PreOpenInterest),
                        "ask1": (FILTER(field.AskPrice1), field.AskVolume1),
                        "bid1": (FILTER(field.BidPrice1), field.BidVolume1),
                        "ask2": (FILTER(field.AskPrice2), field.AskVolume2),
                        "bid2": (FILTER(field.BidPrice2), field.BidVolume2),
                        "ask3": (FILTER(field.AskPrice3), field.AskVolume3),
                        "bid3": (FILTER(field.BidPrice3), field.BidVolume3),
                        "ask4": (FILTER(field.AskPrice4), field.AskVolume4),
                        "bid4": (FILTER(field.BidPrice4), field.BidVolume4),
                        "ask5": (FILTER(field.AskPrice5), field.AskVolume5),
                        "bid5": (FILTER(field.BidPrice5), field.BidVolume5)})

    def unsubscribe(self, codes):
        self.resetCompletion()
        self.checkApiReturn(self.UnSubscribeMarketData(codes))
        self.waitCompletion("取消订阅行情")

    def OnRspUnSubMarketData(self, field, info, _, is_last):
        logger.info(f"OnRspUnSubMarketData, {field=}")
        if not self.checkRspInfoInCallback(info):
            assert (is_last)
            return
        logger.info("已取消订阅<%s>的行情..." % field.InstrumentID)
        if is_last:
            self.notifyCompletion()
