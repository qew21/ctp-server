import threading
from app.internal.constants import MAX_TIMEOUT


class SpiHelper:
    def __init__(self):
        self._event = threading.Event()
        self._error = None

    def resetCompletion(self):
        self._event.clear()
        self._error = None

    def waitCompletion(self, operation_name=""):
        if not self._event.wait(MAX_TIMEOUT):
            raise TimeoutError("%s超时" % operation_name)
        if self._error:
            raise RuntimeError(self._error)

    def notifyCompletion(self, error=None):
        self._error = error
        self._event.set()

    def _cvtApiRetToError(self, ret):
        assert (-3 <= ret <= -1)
        return ("网络连接失败", "未处理请求超过许可数", "每秒发送请求数超过许可数")[-ret - 1]

    def checkApiReturn(self, ret):
        if ret != 0:
            raise RuntimeError(self._cvtApiRetToError(ret))

    def checkApiReturnInCallback(self, ret):
        if ret != 0:
            self.notifyCompletion(self._cvtApiRetToError(ret))

    def checkRspInfoInCallback(self, info):
        if not info or info.ErrorID == 0:
            return True
        self.notifyCompletion(info.ErrorMsg)
        return False
