import asyncio
import hashlib

import aiohttp
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from pytz import timezone


logger = logging.getLogger(__name__)
from sanic import Blueprint, response

from app.internal.ctp import ctp_client

api = Blueprint('ctp_trade')


async def get_json(url, headers=None):
    '''
    get请求json方法
    '''
    if headers is None:
        headers = {}
    try:
        async with session.get(url, headers=headers) as resp:
            resp_json = await resp.json()
            return resp_json
    except Exception as e:
        logger.error(f"get_json error: {e}")
        return {}


async def login_request():
    base_url = 'http://127.0.0.1:7000'
    res = await get_json(base_url + '/login')
    logger.info(res)
    if 'time' not in res:
        for i in range(10):
            await asyncio.sleep(6)
            res = await get_json(base_url + '/login')
            logger.info(f"login retry {i}, res: {res}")
            if 'time' in res:
                break
    return res




async def logout_request():
    base_url = 'http://127.0.0.1:7000'
    res = await get_json(base_url + '/logout')
    logger.info(res)
    return res


@api.listener('before_server_start')
async def before_server_start(app, loop):
    '''全局共享session'''
    logger.info("before_server_start")
    global session, scheduler, ctp_client
    jar = aiohttp.CookieJar(unsafe=True)
    timeout = aiohttp.ClientTimeout(total=15)
    session = aiohttp.ClientSession(cookie_jar=jar, connector=aiohttp.TCPConnector(ssl=False), timeout=timeout)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(login_request, 'cron', id='job_login', day_of_week='mon,tue,wed,thu,fri', hour='8,20', minute=40,
                      second=0)
    scheduler.add_job(login_request, trigger='date',
                      next_run_time=datetime.datetime.now(timezone('Asia/Shanghai')) + datetime.timedelta(seconds=10), id="pad_task")
    scheduler.start()


@api.listener('after_server_stop')
async def after_server_stop(app, loop):
    '''关闭session'''
    logger.info("after_server_stop")
    ctp_client.logout()
    await session.close()
    scheduler.shutdown()


@api.route('/', methods=['GET'])
async def html(request):
    return await response.file('app/static/index.html')


@api.route('/login', methods=['GET'])
async def login(request):
    try:
        ctp_client.login()
        return response.json({"time": datetime.datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/logout', methods=['GET'])
async def logout(request):
    try:
        ctp_client.logout()
        return response.json({"time": datetime.datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/get_account', methods=['GET'])
async def get_account(request):
    try:
        data = ctp_client.getAccount()
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/get_position', methods=['GET'])
async def get_postion(request):
    try:
        data = ctp_client.getPositions()
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/order_limit', methods=['GET'])
async def order_limit(request):
    '''
    code为合约代码，direction为字符串"long"或者"short"之一，表示多头或空头。
    volume为整数，表示交易数量，正数表示该方向加仓，负数表示该方向减仓。
    price为float类型的价格。提交成功返回“订单号@合约号”。
    '''
    code = request.args.get("code")
    direction = request.args.get("direction", "long")
    volume = int(request.args.get("volume", 1))
    price = float(request.args.get("price", "0"))
    offset_flag = request.args.get("offset_flag")

    try:
        data = ctp_client.orderLimit(code, direction, volume, price, offset_flag)
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/order_market', methods=['GET'])
async def order_market(request):
    '''
    市价单不指定价格，而是以当前市场价格成交，能成交多少就成交多少，剩余未成交的撤单。返回成交数量，介于[0, volume]之间。
    '''
    code = request.args.get("code")
    direction = request.args.get("direction", "long")
    volume = int(request.args.get("volume", 1))
    price_type = request.args.get("price_type")
    offset_flag = request.args.get("offset_flag")

    try:
        data = ctp_client.orderMarket(code, direction, volume, price_type, offset_flag)
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/order_custom', methods=['GET'])
async def order_market(request):
    '''
    按指定的价格类型下限价单。
    '''
    code = request.args.get("code")
    direction = request.args.get("direction", "long")
    volume = int(request.args.get("volume", 1))
    price_type = request.args.get("price_type", "bid1")
    plus = request.args.get("plus", 0)
    offset_flag = request.args.get("offset_flag")
    price, e = ctp_client.get_custom_price(code, price_type, plus)
    try:
        data = ctp_client.orderLimit(code, direction, volume, price, offset_flag)
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/order_delete', methods=['GET'])
async def order_delete(request):
    '''
    已提交未完全成交的限价单可以撤单。order_id为orderLimit()的返回值。
    '''
    order_id = request.args.get("order_id")
    try:
        data = ctp_client.deleteOrder(order_id)
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"status": str(e)}, ensure_ascii=False)


@api.route('/get_orders', methods=['GET'])
async def get_orders(request):
    try:
        data = ctp_client.getOrders()
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/get_trades', methods=['GET'])
async def get_trades(request):
    try:
        data = ctp_client.getTrades()
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/get_instruments_future', methods=['GET'])
async def get_instruments_future(request):
    exchange = request.args.get("exchange", "")
    try:
        if exchange == "":
            data = ctp_client.get_instruments_future()
        else:
            data = ctp_client.get_instruments_future(exchange)
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/get_instruments', methods=['GET'])
async def get_instruments(request):
    try:
        data = ctp_client.get_instruments_future()
        instruments = []
        for j in data.values():
            instruments.extend([k['symbol'] for k in j if 'symbol' in k])
        return response.json(instruments, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)

@api.route('/get_instruments_detail', methods=['GET'])
async def get_instruments_detail(request):
    code = request.args.get("code", "")
    try:
        if code != "":
            data = ctp_client.getInstrument(code)
        else:
            data = {}
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/subscribe', methods=['GET'])
async def subscribe(request):
    codes = request.args.get("codes")
    try:
        if codes != "":
            ctp_client.subscribe(codes.split(','))
            ctp_client.setReceiver()
            data = "已订阅{}合约".format(codes)
        else:
            data = {}
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/unsubscribe', methods=['GET'])
async def unsubscribe(request):
    codes = request.args.get("codes")
    try:
        if codes != "":
            ctp_client.unsubscribe(codes.split(','))
            data = "已取消订阅{0}".format(codes)
        else:
            data = {}
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)


@api.route('/query_points', methods=['GET'])
async def query_points(request):
    '''
    行情数据：实时
    '''
    code = request.args.get('code')
    try:
        data = ctp_client.query_points(code)
        if not data:
            data = ctp_client.query_points(code)
            if not data:
                data = "订阅失败，超时10秒没有返回"
        return response.json(data, ensure_ascii=False)
    except Exception as e:
        return response.json({"error": str(e)}, ensure_ascii=False)

