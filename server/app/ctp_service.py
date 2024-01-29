import logging

from app.routes.api import api
from app.internal.ctp import ctp_client

from sanic import Sanic, response, HTTPResponse

logger = logging.getLogger(__name__)
logger.info('start')

app = Sanic(name=__name__, configure_logging=False)
app.config.RESPONSE_TIMEOUT = 6000000
app.config.REQUEST_TIMEOUT = 6000000
app.config.KEEP_ALIVE_TIMEOUT = 600000
app.blueprint(api)


@app.middleware("request")
def cors_middle_req(request):
    """路由需要启用OPTIONS方法"""
    if request.method.lower() == 'options':
        allow_headers = [
            'Authorization',
            'content-type'
        ]
        headers = {
            'Access-Control-Allow-Methods':
                ', '.join(request.app.router.get_supported_methods(request.path)),
            'Access-Control-Max-Age': '86400',
            'Access-Control-Allow-Headers': ', '.join(allow_headers),
        }
        return HTTPResponse('', headers=headers)


@app.middleware("response")
def cors_middle_res(request, response):
    """跨域处理"""
    allow_origin = '*'
    response.headers.update(
        {
            'Access-Control-Allow-Origin': allow_origin,
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, workers=1, debug=False, auto_reload=False, access_log=True)
