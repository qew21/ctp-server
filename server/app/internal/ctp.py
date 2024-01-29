from app.config import account
from app.internal.client import Client


user_id = account.investor_id
broker_id = account.broker_id
password = account.password
td_front = account.trader_server
md_front = account.md_server
app_id = account.app_id
auth_code = account.auth_code

ctp_client = Client(md_front, td_front, broker_id, app_id, auth_code, user_id, password)