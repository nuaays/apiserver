# -*- coding: utf-8 -*-
import time
import random
from db.mall import models as mall_models
from business import model as business_model
from business.resource.coupon_resource import CouponResource
from business.resource.integral_resource import IntegralResource
from business.mall import postage_calculator
#from business.mall.order import Order as BussinessOrder


class PackageOrderService(business_model.Service):
	"""
	组装资源生成订单的service
	
	内部实现以下几步：

		* 填充订单基本信息（比如与订单资源无关的无关的信息）
		#order = self._init_order(purchase_info)

		* 计算订单价格，填充订单信息
		order = self._compute_order_price(order, resources, purchase_info)

		* 申请订单价相关资源
		price_related_resources = self._allocate_price_related_resource(order, purchase_info)

		* 调整订单价格，填充订单信息
		order = self._adjust_order_price(order, price_related_resources, purchase_info)
	"""

	price_resources = [IntegralResource, CouponResource]

	def __init__(self, webapp_owner, webapp_user):
		business_model.Service.__init__(self)

		self.context['webapp_owner'] = webapp_owner
		self.context['webapp_user'] = webapp_user




	def __process_coupon(self, order, final_price):
		coupon_resource = self.type2resource.get('coupon')
		if coupon_resource:
			order.db_model.coupon_id = coupon_resource.coupon.id

			forbidden_coupon_product_price = sum([product.price * product.purchase_count for product in order.products if not product.can_use_coupon])
			final_price -= forbidden_coupon_product_price
			# 优惠券面额
			coupon_denomination = coupon_resource.money
			if final_price < coupon_denomination:
				order.db_model.coupon_money = final_price
				final_price = 0
			else:
				order.db_model.coupon_money = coupon_denomination
				final_price -= coupon_denomination
			final_price += forbidden_coupon_product_price
		return final_price


	def __process_integral(self, order, final_price):
		integral_resource = self.type2resource.get('integral')
		webapp_owner = self.context['webapp_owner']

		if integral_resource:
			order.db_model.integral = integral_resource.integral
			order.db_model.integral_money = integral_resource.money
			order.db_model.integral_each_yuan = webapp_owner.integral_strategy_settings.integral_each_yuan
			final_price -= integral_resource.money
		return final_price		

	def __process_postage(self, order, final_price, purchase_info):
		postage_config = self.context['webapp_owner'].system_postage_config
		calculator = postage_calculator.PostageCalculator(postage_config)
		postage = calculator.get_postage(order.products, purchase_info)
		order.db_model.postage = postage
		final_price += postage

	def __process_promotion(self, order):
		promotion_saved_money = 0.0
		for product_group in order.product_groups:
			promotion_result = product_group.promotion_result
			if promotion_result:
				saved_money = promotion_result.saved_money
				promotion_saved_money += saved_money
		order.db_model.promotion_saved_money = promotion_saved_money


	def __allocate_price_related_resource(self, order, purchase_info):
		return []


	def __adjust_order_price(self, order, price_related_resources, purchase_info):
		return order


	def package_order(self, order, price_free_resources, purchase_info):
		"""
		组装订单

		@param resources 表示与订单价格无关的资源

		@return order 订单对象(业务层)
		@return price_related_resources

		"""


		#webapp_owner = self.context['webapp_owner']
		#webapp_user = self.context['webapp_user']

		# 读取resources中的信息
		# TODO: 如果有多个resource有同一个type呢？
		self.type2resource = dict([(resource.type, resource) for resource in price_free_resources])

		# 处理通用券 todo 适配单品券
		final_price = sum([product.price * product.purchase_count for product in order.products])

		# 处理优惠券
		final_price = self.__process_coupon(order, final_price)

		# 处理积分
		# TODO: 确认积分应用
		final_price = self.__process_integral(order, final_price)

		# 处理邮费
		final_price = self.__process_postage(order, final_price, purchase_info)

		# 处理订单中的促销优惠金额
		self.__process_promotion(order)

		# todo 确认字段是否遗漏

		if final_price < 0:
			final_price = 0
		order.final_price = round(final_price, 2)

		# TODO: 需要实现"订单价格相关资源"分配
		price_related_resources = self.__allocate_price_related_resource(order, purchase_info)

		# 根据订单价格相关资源调整待支付价格
		# todo 处理微众卡
		order = self.__adjust_order_price(order, price_related_resources, purchase_info)

		order.final_price = round(order.final_price, 2)
		return order, price_related_resources



	# 读取resource中相关价格信息，计算并填充


	def __create_order_id(self):
		"""创建订单id

		目前采用基于时间戳＋随机数的算法生成订单id，在确定id可使用之前，通过查询mall_order表里是否有相同id来判断是否可以使用id
		这种方式比较低效，同时存在id重复的潜在隐患，后续需要改进
		"""
		# TODO2: 使用uuid替换这里的算法
		order_id = time.strftime("%Y%m%d%H%M%S", time.localtime())
		order_id = '%s%03d' % (order_id, random.randint(1, 999))
		if mall_models.Order.select().dj_where(order_id=order_id).count() > 0:
			return self.__create_order_id()
		else:
			return order_id
