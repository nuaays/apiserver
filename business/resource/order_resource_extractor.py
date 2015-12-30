#coding: utf8
"""@package business.resource.order_resource_extractor.OrderResourceExtractor
抽取Order中资源，用于取消订单过程中释放资源

释放资源步骤：

1. 从订单中识别促销信息；
2. 从订单中识别积分；
3. 从订单中识别优惠券；
4. 从订单中识别微众卡；

"""


import logging
from business import model as business_model 

from business.resource.integral_resource import IntegralResource
from business.mall.allocator.integral_resource_allocator import IntegralResourceAllocator

class OrderResourceExtractor(business_model.Model):
	"""
	Order资源抽取器
	"""
	__slots__=(

	)

	def __init__(self, webapp_owner, webapp_user):
		business_model.Model.__init__(self)

		self.context['webapp_owner'] = webapp_owner
		self.context['webapp_user'] = webapp_user
		return

	def __extract_integral(self, order):
		"""
		抽取积分资源
		"""
		logging.info(u"order.integral={}".format(order.integral))
		resources = []

		webapp_owner = self.context['webapp_owner']
		webapp_user = self.context['webapp_user']
		# TODO: allocator中的resource_type是property，目前只能用这种ugly方式获取。后续考虑将resource_type改成staticmethod。
		resource_type = IntegralResourceAllocator(webapp_owner, webapp_user).resource_type
		integral_resource = IntegralResource.get({
				'webapp_owner': webapp_owner,
				'webapp_user': webapp_user,
				'type': resource_type
			})
		integral_resource.integral = order.integral
		#integral_resource.money = order.integral_money

		resources.append(integral_resource)
		logging.info("extracted {} IntegralResources, resource_type={}".format(len(resources), resource_type))
		return resources


	def extract(self, order):
		"""
		根据Order实例抽取资源，用于释放

		@param order Order实例
		@return Resource list
		"""
		logging.info(u"trying to extract resources from order id:{}".format(order.id))

		resources = []

		# 抽取积分资源
		extracted_resources = self.__extract_integral(order)
		if extracted_resources:
			resources.extend(extracted_resources)

		logging.info(u"extracted {} resources".format(len(resources)))
		return resources