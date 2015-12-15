# -*- coding: utf-8 -*-
"""@package business.mall.allocator.order_integral_resource_allocator.OrderIntegralResourceAllocator
请求积分资源

"""
import logging
import json
from bs4 import BeautifulSoup
import math
import itertools
from datetime import datetime

from wapi.decorators import param_required
from wapi import wapi_utils
from core.cache import utils as cache_util
from db.mall import models as mall_models
import resource
from core.watchdog.utils import watchdog_alert
from business import model as business_model 
from business.mall.product import Product
from business.mall.allocator.integral_resource_allocator import IntegralResourceAllocator
import settings
from business.decorator import cached_context_property


class OrderIntegralResourceAllocator(business_model.Service):
	"""订单积分分配器
	"""
	__slots__ = ()

	def __init__(self, webapp_owner, webapp_user):
		business_model.Service.__init__(self)

		self.context['webapp_owner'] = webapp_owner
		self.context['webapp_user'] = webapp_user
		self.context['resource2allocator'] = {}

	def release(self, resources):
		release_resources = []
		for resource in resources:
			if resource.get_type() == business_model.RESOURCE_TYPE_INTEGRAL:
				release_resources.append(resource)

		for release_resource in release_resources:
			allocator = self.context['resource2allocator'].get(release_resource, None)
			#TODO-bert 异常处理
			if allocator:
				allocator.release()

	def __allocate_order_integral_setting(self, webapp_owner, order, purchase_info):
		"""
		申请积分抵扣规则

		Returns:
			is_success: 如果成功，返回True；否则，返回False
			reason: 如果成功，返回None；否则，返回失败原因
		"""
		use_ceiling = webapp_owner.integral_strategy_settings.use_ceiling
		if use_ceiling < 0:
			reason = {
				'type': 'integral:order_integral:not_enabled',
				'msg': u'积分抵扣尚未开启',
				'short_msg': u'积分抵扣尚未开启'
			}
			return False, reason

		count_per_yuan = webapp_owner.integral_strategy_settings.integral_each_yuan
		total_integral = purchase_info.order_integral_info['integral']
		integral_money = round(float(purchase_info.order_integral_info['money']), 2)

		product_price = sum([product.price * product.purchase_count for product in order.products])
		if (integral_money - 1) > round(product_price * use_ceiling / 100, 2)\
			or (total_integral + 1) < (integral_money * count_per_yuan):
			reason = {
				'type': 'integral:order_integral:exceed_limit',
				'msg': u'积分使用超限',
				'short_msg': u'积分使用超限'
			}
			return False, reason

		return True, None

	def __supply_product_info_into_fail_reason(self, product, result):
		result['id'] = product.id
		result['name'] = product.name
		result['stocks'] = product.stocks
		result['model_name'] = product.model_name
		result['pic_url'] = product.thumbnails_url

	def __allocate_integral_sale(self, webapp_owner, order, purchase_info):
		"""
		申请积分应用活动

		Returns:
			is_success: 如果成功，返回True；否则，返回False
			reason: 如果成功，返回None；否则，返回失败原因
		"""
		count_per_yuan = webapp_owner.integral_strategy_settings.integral_each_yuan

		group2integralinfo =  purchase_info.group2integralinfo
		uid2group = dict((group.uid, group) for group in order.product_groups)
		for group_uid, integral_info in group2integralinfo.items():
			promotion_product_group = uid2group[group_uid]

			if not promotion_product_group.active_integral_sale_rule:
				#当purchase_info提交的信息中存在group的积分信息
				#但是该group当前没有了active_integral_sale_rule
				#意味着商品的积分应用已经过期
				reason = {
					'type': 'integral:integral_sale:expired',
					'msg': u'积分折扣已经过期',
					'short_msg': u'已经过期'
				}
				self.__supply_product_info_into_fail_reason(promotion_product_group.products[0], reason)
				return False, reason


			use_integral = int(integral_info['integral'])
			integral_money = round(float(integral_info['money']), 2)
			
			# 校验前台输入：积分金额不能大于使用上限、积分值不能小于积分金额对应积分值
			# 根据用户会员与否返回对应的商品价格
			product_price = sum([product.price * product.purchase_count for product in promotion_product_group.products])
			integral_sale_rule = promotion_product_group.active_integral_sale_rule
			max_integral_price = round(product_price * integral_sale_rule['discount'] / 100, 2)
			if max_integral_price < (integral_money - 0.01) \
				or (integral_money * count_per_yuan) > (use_integral + 1):
				reason = {
					'type': 'integral:integral_sale:exceed_max_integral_limit',
					'msg': u'使用积分不能大于促销限额',
					'short_msg': u'使用积分不能大于促销限额'
				}
				self.__supply_product_info_into_fail_reason(promotion_product_group.products[0], reason)
				return False, reason

		return True, None

	def allocate_resource(self, order, purchase_info):
		webapp_owner = self.context['webapp_owner']
		webapp_user = self.context['webapp_user']

		count_per_yuan = webapp_owner.integral_strategy_settings.integral_each_yuan
		total_integral = 0
		integral_money = 0
		if purchase_info.order_integral_info:
			#使用积分抵扣
			is_success, reason = self.__allocate_order_integral_setting(webapp_owner, order, purchase_info)
			if not is_success:
				return False, reason, None

			total_integral = purchase_info.order_integral_info['integral']
		elif purchase_info.group2integralinfo:
			#使用积分应用
			is_success, reason = self.__allocate_integral_sale(webapp_owner, order, purchase_info)
			if not is_success:
				return False, reason, None

			for group_uid, integral_info in purchase_info.group2integralinfo.items():
				total_integral += int(integral_info['integral'])

		integral_resource_allocator = IntegralResourceAllocator(webapp_owner, webapp_user)
		is_success, reason, resource = integral_resource_allocator.allocate_resource(total_integral)

		if is_success:
			self.context['resource2allocator'][resource] = integral_resource_allocator
			return True, '', resource
		else:
			return False, reason, None