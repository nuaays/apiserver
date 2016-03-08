# -*- coding: utf-8 -*-
"""@package business.coupon_allocator.CouponResourceAllocator
请求积分资源

"""

from business import model as business_model
from wapi.decorators import param_required


class GroupBuyResource(business_model.Resource):
	"""积分资源
	"""
	__slots__ = (
		'type',
		'pid',
		'group_buy_price'
	)

	@staticmethod
	@param_required(['type'])
	def get(args):
		"""工厂方法，创建CouponResource对象

		@return CouponResource对象
		"""
		pass

		# a = GroupBuyResource(args['type'])
		#
		# return coupon_resource

	def __init__(self, type):
		business_model.Resource.__init__(self)
		self.type = type
		self.pid = 0
		self.group_buy_price = 0

	def get_type(self):
		return self.type
