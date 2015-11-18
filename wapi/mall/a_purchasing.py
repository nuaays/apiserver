# -*- coding: utf-8 -*-

import copy
from datetime import datetime

from core import api_resource
from wapi.decorators import param_required
from wapi.mall import models as mall_models
from wapi.mall import promotion_models
from utils import dateutil as utils_dateutil
import resource
from business.mall.purchase_info import PurchaseInfo
from business.mall.purchase_order import PurchaseOrder


class APurchasing(api_resource.ApiResource):
	"""
	购物车项目
	"""
	app = 'mall'
	resource = 'purchasing'

	def __fill_coupons_for_edit_order(webapp_owner_id, webapp_user, products):
		"""
		request_util:__fill_coupons_for_edit_order
		"""
		coupons = webapp_user.coupons 
		limit_coupons = []
		result_coupons = []
		if len(coupons) == 0:
			return result_coupons, limit_coupons

		today = datetime.today()
		product_ids = []
		total_price = 0
		# jz 2015-10-09
		# productIds2price = dict()
		productIds2original_price = dict()
		is_forbidden_coupon = True
		from resource.mall import r_product_hint
		for product in products:
			product_ids.append(product.id)
			product_total_price = product.price * product.purchase_count
			product_total_original_price = product.original_price * product.purchase_count
			# TODO: 去掉ProductHint的直接调用
			if not r_product_hint.ProductHint.is_forbidden_coupon(webapp_owner_id, product.id):
				#不是被禁用全场优惠券的商品 duhao 20150908
				total_price += product_total_price
				is_forbidden_coupon = False
			# jz 2015-10-09
			# if not productIds2price.get(product.id):
			# 	productIds2price[product.id] = 0
			# productIds2price[product.id] += product_total_price

			if not productIds2original_price.get(product.id):
				productIds2original_price[product.id] = 0
			productIds2original_price[product.id] += product_total_original_price
		for coupon in coupons:
			valid = coupon.valid_restrictions
			limit_id = coupon.limit_product_id

			if coupon.start_date > today:
				#兼容历史数据
				if coupon.status == promotion_models.COUPON_STATUS_USED:
					coupon.display_status = 'used'
				else:
					coupon.display_status = 'disable'
				limit_coupons.append(coupon)
			elif coupon.status != promotion_models.COUPON_STATUS_UNUSED:
				# 状态不是未使用
				if coupon.status == promotion_models.COUPON_STATUS_USED:
					# 状态是已使用
					coupon.display_status = 'used'
				else:
					# 过期状态
					coupon.display_status = 'overdue'
				limit_coupons.append(coupon)
			# jz 2015-10-09
			# elif coupon.limit_product_id > 0 and \
			# 	(product_ids.count(limit_id) == 0 or valid > productIds2price[limit_id]) or\
			# 	valid > total_price or\
			# 	coupon.provided_time >= today or is_forbidden_coupon:
			# 	# 1.订单没有限定商品
			# 	# 2.订单金额不足阈值
			# 	# 3.优惠券活动尚未开启
			# 	# 4.订单里面都是被禁用全场优惠券的商品 duhao
			# 	coupon.display_status = 'disable'
			# 	limit_coupons.append(coupon)

			elif coupon.limit_product_id == 0 and (valid > total_price or coupon.provided_time >= today or is_forbidden_coupon):
				#通用券
				# 1.订单金额不足阈值
				# 2.优惠券活动尚未开启
				# 3.订单里面都是被禁用全场优惠券的商品 duhao
				coupon.display_status = 'disable'
				limit_coupons.append(coupon)

			elif coupon.limit_product_id > 0 and (product_ids.count(limit_id) == 0 or valid > productIds2original_price[limit_id]or coupon.provided_time >= today):
				# 单品卷
				# 1.订单金额不足阈值
				# 2.优惠券活动尚未开启
				coupon.display_status = 'disable'
				limit_coupons.append(coupon)
			else:
				result_coupons.append(coupon)

		return result_coupons, limit_coupons

	def __format_product_group_price_factor(product_groups):
		factors = []
		for product_group in product_groups:
			product_factors = []
			for product in product_group['products']:
				product_factors.append({
					"id": product.id,
					"model": product.model_name,
					"count": product.purchase_count,
					"price": product.price,
					"original_price": product.original_price,
					"weight": product.weight,
					"active_integral_sale_rule": getattr(product, 'active_integral_sale_rule', None),
					"postageConfig": product.postage_config,
					"forbidden_coupon": (not product.can_use_coupon)
				})

			factor = {
				'id': product_group['id'],
				'uid': product_group['uid'],
				'products': product_factors,
				'promotion': product_group['promotion'],
				'promotion_type': product_group['promotion_type'],
				'promotion_result': product_group['promotion_result'],
				'integral_sale_rule': product_group['integral_sale_rule'],
				'can_use_promotion': product_group['can_use_promotion']
			}
			factors.append(factor)

		return factors

	@param_required(['woid'])
	def get(args):
		"""
		获取购物车项目

		@param id 商品ID
		"""
		webapp_user = args['webapp_user']
		webapp_owner = args['webapp_owner']
		member = args.get('member', None)

		purchase_info = PurchaseInfo.parse({
			'request_args': args
		})

		order = PurchaseOrder.create({
			"webapp_owner": webapp_owner,
			"webapp_user": webapp_user,
			"purchase_info": purchase_info,
		})

		#获得运费配置，支持前端修改数量、优惠券等后实时计算运费
		postage_factor = webapp_owner.system_postage_config['factor']

		#获取积分信息
		integral_info = webapp_user.integral_info
		integral_info['have_integral'] = (integral_info['count'] > 0)

		#获取优惠券
		#coupons, limit_coupons = Purchasing.__fill_coupons_for_edit_order(webapp_owner_id, webapp_user, products)
		coupons, limit_coupons = [], []

		#获取商城配置
		mall_config = webapp_owner.mall_config
		use_ceiling = webapp_owner.integral_strategy_settings.use_ceiling

		product_groups = APurchasing.__format_product_group_price_factor(order.product_groups)

		order_info = {
			'type': order.type,
			'ship_name': order.ship_info['name'],
			'ship_tel': order.ship_info['tel'],
			'ship_address': order.ship_info['address'],
			'ship_id': order.ship_info['id'],
			'ship_area': order.ship_info['area'],
			'pay_interfaces': order.pay_interfaces,
			'product_groups': order.product_groups
		}
		#将product_groups中的order_product转化为dict
		for product_group in order_info['product_groups']:
			new_products = []
			for product in product_group['products']:
				new_products.append(product.to_dict())
			product_group['products'] = new_products

		return {
			'order': order_info,
			'mall_config': mall_config,
			'integral_info': integral_info,
			'coupons': coupons,
			'limit_coupons': limit_coupons,
			'use_ceiling': use_ceiling,
			'postage_factor': postage_factor,
			'product_groups': product_groups
		}