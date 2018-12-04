
# encoding: UTF-8

from __future__ import print_function

import json
import sys
import traceback
import zlib
from collections import defaultdict

from enum import Enum
from typing import Dict, List

from vnpy.trader.vtGateway import *
#
#
# class TestGateway(VtGateway):
#
#     def __init__(self, eventEngine, gatewayName):
#         self._lastOrderId = 0
#         super(TestGateway, self).__init__(eventEngine, gatewayName)
#
#     def sendOrder(self, orderReq): # type: (VtOrderReq)->str
#         symbol = orderReq.symbol
#         orderId = str(self._lastOrderId)
#         orderData = VtOrderData.createFromGateway(
#             gateway=self,
#             orderId=orderId,
#             symbol=symbol,
#             exchange='TESTExchange',
#             price=orderReq.price,
#             volume=orderReq.volume,
#             direction=orderReq.direction,
#             offset=
#         )
#
#         self.onOrder(orderData)
#         return orderData.vtOrderID
#
