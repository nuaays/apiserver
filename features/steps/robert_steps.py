# -*- coding: utf-8 -*-
import json
import urllib
from datetime import datetime

from behave import *

from features.steps import steps_db_util
from features.util import bdd_util
from features.util.helper import WAIT_SHORT_TIME
from db.mall import models as mall_models
from db.mall import promotion_models
from db.member import models as member_models
from .steps_db_util import (
	get_custom_model_id_from_name, get_product_model_keys, get_area_ids
)
import logging

def _get_product_model_ids_from_name(webapp_owner_id, model_name):
	"""
	获取规格ids, 根据名称
	"""
	if model_name is None or model_name == "standard":
		return "standard"
	return get_custom_model_id_from_name(webapp_owner_id ,model_name)

# 获取规格名称, 根据ids
def _get_product_model_name_from_ids(webapp_owner_id, ids):
	if ids is None or ids == "standard":
		return "standard"
	return get_custom_model_id_from_name(webapp_owner_id ,ids)

PAYNAME2ID = {
	u'全部': -1,
	u'微信支付': 2,
	u'货到付款': 9,
	u'支付宝': 0,
	u'优惠抵扣': 10
}

@When(u"{webapp_user_name}购买{webapp_owner_name}的商品")
def step_impl(context, webapp_user_name, webapp_owner_name):
	"""
	举例:
	```
		{
			"order_id": "" # 订单号
			"ship_area": "",
			"ship_name": "bill",
			"ship_address": "",
			"ship_tel": "",
			"customer_message": "",
			"integral": "10",
			"integral_money": "10",
			"weizoom_card": [{"card_name":"", "card_pass": ""}],
			"coupon": "coupon_1",
			"date": "" # 下单时间
			"products": [
				{
					"count": "",
					"name": "",
					"promotion": {"name": ""},
					integral: ""
				},...
			],
			"weizoom_card":[{
				"card_name":"0000001",
				"card_pass":"1234567"
			}]
		}
	```
	"""
	if hasattr(context, 'caller_step_purchase_info') and context.caller_step_purchase_info:
		args = context.caller_step_purchase_info
	else:
		args = json.loads(context.text)

	def __get_current_promotion_id_for_product(product, member_grade_id):
		promotion_ids = [r.promotion_id for r in promotion_models.ProductHasPromotion.select().dj_where(product_id=product.id)]
		promotions = list(promotion_models.Promotion.select().dj_where(id__in=promotion_ids, status=promotion_models.PROMOTION_STATUS_STARTED).where(promotion_models.Promotion.type>4))
		if len(promotions) > 0 and (promotions[0].member_grade_id <= 0 or \
				promotions[0].member_grade_id == member_grade_id):
			# 存在促销信息，且促销设置等级对该会员开放
			if promotions[0].type != promotion_models.PROMOTION_TYPE_INTEGRAL_SALE:
				return promotions[0].id
		return 0

	settings = member_models.IntegralStrategySttings.select().dj_where(webapp_id=context.webapp_id)
	integral_each_yuan = settings[0].integral_each_yuan

	member = bdd_util.get_member_for(webapp_user_name, context.webapp_id)
	group2integralinfo = dict()

	if webapp_owner_name == u'订单中':
		is_order_from_shopping_cart = "true"
		webapp_owner_id = context.webapp_owner_id
		product_ids = []
		product_counts = []
		promotion_ids = []
		product_model_names = []

		products = context.response.context['order'].products
		integral = 0
		integral_group_items = []
		for product in products:
			product_counts.append(str(product.purchase_count))
			product_ids.append(str(product.id))

			if hasattr(product, 'promotion'):
				promotion = Promotion.objects.get(name=product.promotion.name)
				promotion_ids.append(str(promotion.id))
			else:
				promotion_ids.append(str(__get_current_promotion_id_for_product(product_obj, member.grade_id)))
			product_model_names.append(_get_product_model_ids_from_name(webapp_owner_id, product.model_name))

			if hasattr(product, 'integral') and product.integral > 0:
				integral += product.integral
				integral_group_items.append('%s_%s' % (product.id, product.model['name']))
		if integral:
			group2integralinfo['-'.join(integral_group_items)] = {
				"integral": integral,
				"money": round(integral / integral_each_yuan, 2)
			}
	else:
		is_order_from_shopping_cart = "false"
		webapp_owner_id = bdd_util.get_user_id_for(webapp_owner_name)
		product_ids = []
		product_counts = []
		product_model_names = []
		promotion_ids = []
		products = args['products']
		# integral = 0
		# integral_group_items = []
		for product in products:
			product_counts.append(str(product['count']))
			product_name = product['name']
			product_obj = mall_models.Product.get(owner=webapp_owner_id, name=product_name)
			product_ids.append(str(product_obj.id))
			if product.has_key('promotion'):
				promotion = promotion_models.Promotion.get(name=product['promotion']['name'])
				promotion_ids.append(str(promotion.id))
			else:
				promotion_ids.append(str(__get_current_promotion_id_for_product(product_obj, member.grade_id)))
			_product_model_name = _get_product_model_ids_from_name(webapp_owner_id, product.get('model', None))
			product_model_names.append(_product_model_name)
			if 'integral' in product and product['integral'] > 0:
				# integral += product['integral']
				# integral_group_items.append('%s_%s' % (product_obj.id, _product_model_name))
				group2integralinfo['%s_%s' % (product_obj.id, _product_model_name)] = {
					"integral": product['integral'],
					"money": round(product['integral'] / integral_each_yuan, 2)
				}
		# if integral:
		# 	group2integralinfo['-'.join(integral_group_items)] = {
		# 		"integral": integral,
		# 		"money": round(integral / integral_each_yuan, 2)
		# 	}

	order_type = args.get('type', 'normal')

	# 处理中文地区转化为id，如果数据库不存在的地区则自动添加该地区
	ship_area = get_area_ids(args.get('ship_area'))

	data = {
		"woid": webapp_owner_id,
		"module": 'mall',
		"is_order_from_shopping_cart": is_order_from_shopping_cart,
		"target_api": "order/save",
		"product_ids": '_'.join(product_ids),
		"promotion_ids": '_'.join(promotion_ids),
		"product_counts": '_'.join(product_counts),
		"product_model_names": '$'.join(product_model_names),
		"ship_name": args.get('ship_name', "未知姓名"),
		"area": ship_area,
		"ship_id": 0,
		"ship_address": args.get('ship_address', "长安大街"),
		"ship_tel": args.get('ship_tel', "11111111111"),
		"is_use_coupon": "false",
		"coupon_id": 0,
		# "coupon_coupon_id": "",
		"message": args.get('customer_message', ''),
		"group2integralinfo": json.JSONEncoder().encode(group2integralinfo),
		"card_name": '',
		"card_pass": '',
		"xa-choseInterfaces": PAYNAME2ID.get(args.get("pay_type", u"微信支付"),-1)
	}
	if 'integral' in args and args['integral'] > 0:
		# 整单积分抵扣
		# orderIntegralInfo:{"integral":20,"money":"10.00"}"
		orderIntegralInfo = dict()
		orderIntegralInfo['integral'] = args['integral']
		if 'integral_money' in args:
			orderIntegralInfo['money'] = args['integral_money']
		else:
			orderIntegralInfo['money'] = round(int(args['integral'])/integral_each_yuan, 2)
		data["orderIntegralInfo"] = json.JSONEncoder().encode(orderIntegralInfo)
	if order_type == u'测试购买':
		data['order_type'] = mall_models.PRODUCT_TEST_TYPE
	else:
		data['order_type'] = order_type
	if u'weizoom_card' in args:
		for card in args[u'weizoom_card']:
			data['card_name'] += card[u'card_name'] + ','
			data['card_pass'] += card[u'card_pass'] + ','

	#填充商品积分
	# for product_model_id, integral in product_integrals:
	# 	data['is_use_integral_%s' % product_model_id] = 'on'
	# 	data['integral_%s' % product_model_id] = integral

	#填充优惠券信息
	# 根据优惠券规则名称填充优惠券ID
	coupon = args.get('coupon', None)
	if coupon:
		data['is_use_coupon'] = 'true'
		data['coupon_id'] = coupon

	url = '/wapi/mall/order/?_method=put'
	data['woid'] = context.webapp_owner_id
	response = context.client.post(url, data)
	# bdd_util.assert_api_call_success(response)
	context.response = response


	#response结果为: {"errMsg": "", "code": 200, "data": {"msg": null, "order_id": "20140620180559"}}

	if response.body['code'] == 200:
		# context.created_order_id为订单ID
		context.created_order_id = response.data['order_id']


		#访问支付结果链接
		pay_url_info = response.data['pay_url_info']
		pay_type = pay_url_info['type']
		del pay_url_info['type']
		if pay_type == 'cod':
			pay_url = '/wapi/pay/pay_result/?_method=put'
			data = {
				'pay_interface_type': pay_url_info['pay_interface_type'],
				'order_id': pay_url_info['order_id']
			}
			context.client.post(pay_url, data)
	else:
		context.created_order_id = -1

	if context.created_order_id != -1:
		if 'date' in args:
			mall_models.Order.update(created_at=bdd_util.get_datetime_str(args['date'])).dj_where(order_id=context.created_order_id).execute()
		if 'order_id' in args:
			db_order = mall_models.Order.get(order_id=context.created_order_id)
			db_order.order_id=args['order_id']
			db_order.save()
			if db_order.origin_order_id <0:
				for order in Order.select().dj_where(origin_order_id=db_order.id):
					order.order_id = '%s^%s' % (args['order_id'], order.supplier)
					order.save()
			context.created_order_id = args['order_id']

	logging.info("[Order Created] webapp_owner_id: {}, created_order_id: {}".format(webapp_owner_id, context.created_order_id))
	
	context.product_ids = product_ids
	context.product_counts = product_counts
	context.product_model_names = product_model_names
	context.webapp_owner_name = webapp_owner_name


@then(u"{webapp_user_name}成功创建订单")
def step_impl(context, webapp_user_name):
	__check_order(context, webapp_user_name)


def __check_order(context, webapp_user_name):
	order_id = context.created_order_id
	if order_id == -1:
		print 'Server Error: ', json.dumps(json.loads(context.response.content), indent=True)
		assert False, "order_id must NOT be -1"
		return

	url = '/wapi/mall/order/?woid=%s&order_id=%s' % (context.webapp_owner_id, order_id)
	response = context.client.get(bdd_util.nginx(url), follow=True)

	actual_order = response.data['order']
	actual_order['order_no'] = actual_order['order_id']
	actual_order['status'] = actual_order['status_text']
	# 获取coupon规则名
	if (actual_order['coupon_id'] != 0) and (actual_order['coupon_id'] != -1):
		# coupon = Coupon.objects.get(id=actual_order.coupon_id)
		coupon = steps_db_util.get_coupon_by_id(actual_order['coupon_id'])
		actual_order['coupon_id'] = coupon.coupon_rule.name

	for product in actual_order['products']:
		product['count'] = product['purchase_count']
		product['grade_discounted_money'] = product['discount_money']
		if product['promotion']:
			promotion = product['promotion']
			promotion['type'] = promotion['type_name']

		if product['model']:
			model = product['model']
			if model['property_values']:
				product['model'] = ' '.join(property_value['name'] for property_value in model['property_values'])

	# 需要订单中给出微众卡支付金额
	#actual_order['weizoom_card_money'] = 0.0

	expected = json.loads(context.text)
	if expected.get('actions', None):
		# TODO 验证订单页面操作
		del expected['actions']
	bdd_util.assert_dict(expected, actual_order)


#bill支付订单成功的校验其实跟成功创建订单的校验是一样的
@then(u"{webapp_user_name}支付订单成功")
def step_impl(context, webapp_user_name):
	__check_order(context, webapp_user_name)


@then(u"{webapp_usr_name}手机端获取订单'{order_id}'")
def step_impl(context, webapp_usr_name, order_id):
	# 为获取完可顺利支付
	context.created_order_id = order_id

	url = '/wapi/mall/order/?woid=%s&order_id=%s' % (context.webapp_owner_id, order_id)
	response = context.client.get(bdd_util.nginx(url), follow=True)

	actual = response.data['order']

	has_sub_order = actual['has_sub_order']
	actual['order_no'] = actual['order_id']
	actual['order_time'] = (str(actual['created_at']))
	actual['methods_of_payment'] = actual['pay_interface_name']
	#actual.member = actual.buyer_name
	actual['status'] = actual['status_text']
	actual['ship_area'] = actual['ship_area']

	if has_sub_order:
		products = []
		orders = actual['sub_orders']
		for i, order in enumerate(orders):
			sub_order_products = __fix_field_for(order['products'])
			product_dict = {
				u"包裹" + str(i + 1): sub_order_products,
				'status': mall_models.ORDERSTATUS2MOBILETEXT[order['status']]
			}
			products.append(product_dict)

		actual['products'] = products
	else:
		products = __fix_field_for(actual['products'])

	expected = json.loads(context.text)
	bdd_util.assert_dict(expected, actual)


def __fix_field_for(products):
	for product in products:
		product['count'] = product['purchase_count']
		product['grade_discounted_money'] = product['discount_money']
		if product['promotion']:
			promotion = product['promotion']
			promotion['type'] = promotion['type_name']

		if product['model']:
			model = product['model']
			if model['property_values']:
				product['model'] = ''.join(property_value['name'] for property_value in model['property_values'])

	return products









@when(u"{webapp_user_name}加入{webapp_owner_name}的商品到购物车")
def step_impl(context, webapp_user_name, webapp_owner_name):
	webapp_owner_id = context.webapp_owner_id

	products_info = json.loads(context.text)
	url = '/wapi/mall/shopping_cart_item/?_method=put'
	for product_info in products_info:
		product_name = product_info['name']
		product_count = product_info.get('count', 1)
		product = mall_models.Product.get(owner=webapp_owner_id, name=product_name)

		if 'model' in product_info:
			for key, value in product_info['model']['models'].items():
				product_model_name = _get_product_model_ids_from_name(webapp_owner_id, key)
				data = {
					"woid": webapp_owner_id,
					"product_id": product.id,
					"count": value['count'],
					"product_model_name": product_model_name,
					"woid": webapp_owner_id
				}

				response = context.client.post(url, data)
				bdd_util.assert_api_call_success(response)
		else:
			data = {
				"woid": webapp_owner_id,
				"product_id": product.id,
				"count": product_count,
				"webapp_owner_id": webapp_owner_id,
				"product_model_name": 'standard',
			}

			response = context.client.post(url, data)
			bdd_util.assert_api_call_success(response)


@then(u"{webapp_user_name}能获得购物车")
def step_impl(context, webapp_user_name):
	"""
	e.g.:1
		{
			"product_groups": [{
				"promotion": {
					"type": "premium_sale",
					"result": {
						"premium_products": [{
							"name": "商品4",
							"premium_count": 3
						}]
					}
				},
				"can_use_promotion": true,
				"products": [{
					"name": "商品5",
					"model": "M",
					"price": 7.0,
					"count": 1
				}, {
					"name": "商品5",
					"model": "S",
					"price": 8.0,
					"count": 2
				}]
			}],
			"invalid_products": []
		}
	e.g.:2
		{
			"product_groups": [{
				"promotion": null,
				"can_use_promotion": false,
				"products": [{
					"name": "商品1",
					"count": 1
				}]
			}, {
				"promotion": null,
				"can_use_promotion": false,
				"products": [{
					"name": "商品2",
					"count": 2
				}]
			}],
			"invalid_products": []
		}
	"""
	url = '/wapi/mall/shopping_cart/?woid=%d' % context.webapp_owner_id
	response = context.client.get(bdd_util.nginx(url), follow=True)
	bdd_util.assert_api_call_success(response)
	product_groups = response.data['product_groups']
	invalid_products = response.data['invalid_products']

	def fill_products_model(products):
		for product in products:
			model = []
			original_model = product['model']
			if original_model and ('property_values' in original_model) and original_model['property_values']:
				for property_value in original_model['property_values']:
					model.append('%s' % (property_value['name']))
			product['model'] = ' '.join(model)
			product['count'] = product['purchase_count']

	fill_products_model(invalid_products)
	for product_group in product_groups:
		from copy import deepcopy
		promotion = None
		promotion = product_group['promotion']
		products = product_group['products']

		if not promotion:
			product_group['promotion'] = None
		elif not product_group['can_use_promotion']:
			product_group['promotion'] = None
		else:
			#由于相同promotion产生的不同product group携带着同一个promotion对象，所以这里要通过copy来进行写时复制
			new_promotion = deepcopy(promotion)
			product_group['promotion'] = new_promotion
			new_promotion['type'] = product_group['promotion_type']
			new_promotion['result'] = product_group['promotion_result']
			if new_promotion['type'] == 'flash_sale':
				products[0]['price'] = new_promotion['detail']['promotion_price']
			if new_promotion['type'] == 'premium_sale':
				new_promotion['result'] = product_group['promotion']['detail']

		fill_products_model(product_group['products'])

	actual = {
		'product_groups': product_groups,
		'invalid_products': invalid_products
	}

	expected = json.loads(context.text)
	bdd_util.assert_dict(expected, actual)


@when(u"{webapp_user_name}从购物车中删除商品")
def step_impl(context, webapp_user_name):
	product_names = json.loads(context.text)
	product_ids = []
	for product_name in product_names:
		product = mall_models.Product.get(owner=context.webapp_owner_id, name=product_name)
		product_ids.append(product.id)

	#忽略model的处理，所以feature中要保证购物车中不包含同一个商品的不同规格
	shopping_cart_item_ids = [str(item.id) for item in mall_models.ShoppingCart.select().dj_where(webapp_user_id=context.webapp_user.id, product_id__in=product_ids)]
	for shopping_cart_item_id in shopping_cart_item_ids:
		data = {
			"id": shopping_cart_item_id,
			"woid": context.webapp_owner_id
		}

		response = context.client.post('/wapi/mall/shopping_cart_item/?_method=delete', data)
		bdd_util.assert_api_call_success(response)


@when(u"{webapp_user_name}从购物车发起购买操作")
def step_impl(context, webapp_user_name):
	"""
	action = "click" or "pay"

	e.g.:
		{
			"action": "click"
			"context": [
				{'name': 'basketball', 'model': "standard"},
				{...}
			]
		}
	"""
	# 设置默认收货地址
	if member_models.ShipInfo.select().count() == 0:
		context.execute_steps(u"When %s设置%s的webapp的默认收货地址:weapp" % (webapp_user_name, 'jobs'))
	__i = json.loads(context.text)
	if __i.get("action") == u"pay":
		argument = __i.get('context')
		# 获取购物车参数
		product_ids, product_counts, product_model_names = _get_shopping_cart_parameters(context.webapp_user.id, argument)
		url = '/wapi/mall/purchasing/?woid=%s&product_ids=%s&product_counts=%s&product_model_names=%s' % (context.webapp_owner_id, product_ids, product_counts, product_model_names)
		print '==========================================***************************************'
		print url
		print '==========================================***************************************'
		product_infos = {
			'product_ids': product_ids,
			'product_counts': product_counts,
			'product_model_names': product_model_names
		}
		if __i.get('coupon'):
			product_infos['coupon_id'] = __i['coupon']
	elif __i.get("action") == u"click":
		argument = __i.get('context')
		# 获取购物车参数
		product_ids, product_counts, product_model_names = _get_shopping_cart_parameters(context.webapp_user.id, argument)
		url = '/wapi/mall/purchasing/?woid=%s&product_ids=%s&product_counts=%s&product_model_names=%s' % (context.webapp_owner_id, product_ids, product_counts, product_model_names)
		print '==========================================***************************************'
		print url
		print '==========================================***************************************'
		product_infos = {
			'product_ids': product_ids,
			'product_counts': product_counts,
			'product_model_names': product_model_names
		}
		if __i.get('coupon'):
			product_infos['coupon_id'] = __i['coupon']

	response = context.client.get(bdd_util.nginx(url), follow=True)
	context.product_infos = product_infos
	context.response = response

@then(u"{webapp_user_name}获得待编辑订单")
def step_impl(context, webapp_user_name):
	"""
		e.g.:
		[{'name': "asdfasdfa",
		  'count': "111"
		},{...}]
	"""
	context_text = json.loads(context.text)
	if context_text == []:
		actual = []
		expected_products = []
	else:
		actual = []
		expected_products = context_text['products']
		product_groups = context.response.data['order']['product_groups']
		for i in product_groups:
			for product in i['products']:
				_a = {}
				_a['name'] = product['name']
				_a['count'] = product['purchase_count']
				actual.append(_a)

	bdd_util.assert_list(expected_products, actual)

def _get_shopping_cart_parameters(webapp_user_id, context):
	"""
	webapp_user_id-> int
	context -> list
		e.g.:
			[
				{'name': "",
				 'model': },
				{...},
			]
	"""

	shopping_cart_items = mall_models.ShoppingCart.select().dj_where(webapp_user_id=webapp_user_id)
	if context is not None:
		product_infos = context
		product_ids = []
		product_counts = []
		product_model_names = []
		for product_info in product_infos:
			product_name = product_info['name']
			product_model_name = product_info.get('model', 'standard')
			product_model_name = get_product_model_keys(product_model_name)

			product = mall_models.Product.get(name=product_info['name'])
			cart = mall_models.ShoppingCart.get(webapp_user_id=webapp_user_id, product=product.id, product_model_name=product_model_name)
			product_ids.append(str(product.id))
			product_counts.append(str(cart.count))
			product_model_names.append(product_model_name)
	else:
		shopping_cart_items = list(mall_models.ShoppingCart.select().dj_where(webapp_user_id=webapp_user_id))
		product_ids = [str(item.product_id) for item in shopping_cart_items]
		product_counts = [str(item.count) for item in shopping_cart_items]
		product_model_names = [item.product_model_name for item in shopping_cart_items]

	product_ids = '_'.join(product_ids)
	product_counts = '_'.join(product_counts)
	product_model_names = '$'.join(product_model_names)
	return product_ids, product_counts, product_model_names

def _get_prodcut_info(order):
	product_ids = []
	product_counts = []
	product_model_names = []
	promotion_ids = []

	for product_group in order['product_groups']:
		for product in product_group['products']:
			product_ids.append(str(product['id']))
			product_counts.append(str(product['purchase_count']))
			product_model_names.append(str(product['model_name']))
			if product_group['can_use_promotion']:
				promotion_ids.append(str(product_group['promotion']['id']))
			else:
				promotion_ids.append('0')
	return {'product_ids': '_'.join(product_ids),
			'product_counts': '_'.join(product_counts),
			'product_model_names': '$'.join(product_model_names),
			'promotion_ids': '_'.join(promotion_ids)
			}

@then(u"{webapp_user_name}'{pay_type}'使用支付方式'{pay_interface}'进行支付")
def step_impl(context, webapp_user_name, pay_type, pay_interface):
	response = context.response

	pay_interface_names = [mall_models.PAYTYPE2NAME.get(interface['type']) for interface in response.data['order']['pay_interfaces']]

	if pay_type == u'能':
		if pay_interface == u"微众卡支付":
			from db.account.models import AccountHasWeizoomCardPermissions
			is_can_use_weizoom_card = (AccountHasWeizoomCardPermissions.select().dj_where(owner_id=context.webapp_owner_id).count() > 0)
			context.tc.assertTrue(is_can_use_weizoom_card)
			context.tc.assertTrue(pay_interface in pay_interface_names)
		else:
			context.tc.assertTrue(pay_interface in pay_interface_names)
	else:
		context.tc.assertTrue(pay_interface not in pay_interface_names)

@when(u"{webapp_user_name}在购物车订单编辑中点击提交订单")
def step_click_check_out(context, webapp_user_name):
	"""
	{
		"pay_type":  "货到付款",
	}
	"""
	argument = json.loads(context.text)
	pay_type = argument['pay_type']

	order = context.response.data['order']
	product_info = _get_prodcut_info(order)
	url = '/wapi/mall/order/?_method=put'
	data = {
		'order_type': 'normal',
		'is_order_from_shopping_cart': 'true',
		'woid': context.webapp_owner_id,
		'xa-choseInterfaces': mall_models.PAYNAME2TYPE.get(pay_type, -1),
		'group2integralinfo': {},

		"ship_name": argument.get('ship_name', "未知姓名"),
		"area": get_area_ids(argument.get('ship_area')),
		"ship_address": argument.get('ship_address', "长安大街"),
		"ship_tel": argument.get('ship_tel', "11111111111"),
	}

	data.update(product_info)
	coupon_id = context.product_infos.get('coupon_id', None)
	if coupon_id:
		data['is_use_coupon'] = 'true'
		data['coupon_id'] = coupon_id
	if argument.get('integral', None):
		data['orderIntegralInfo'] = json.dumps({
			'integral': argument['integral'],
			'money': argument['integral_money']
		})

	response = context.client.post(url, data)

	#bdd_util.assert_api_call_success(response)
	context.response = response

	#访问支付结果链接
	if response.body['code'] == 200:
		pay_url_info = response.data['pay_url_info']
		context.pay_url_info = pay_url_info
		pay_type = pay_url_info['type']
		del pay_url_info['type']
		if pay_type == 'cod':
			pay_url = '/wapi/pay/pay_result/?_method=put'
			data = {
				'pay_interface_type': pay_url_info['pay_interface_type'],
				'order_id': pay_url_info['order_id']
			}
			context.client.post(pay_url, data)
		
		context.created_order_id = response.data['order_id']
	else:
		context.created_order_id = -1
		context.server_error_msg = response.data['detail'][0]['msg']
		print "buy_error----------------------------",context.server_error_msg,response

	if context.created_order_id != -1:
		if 'date' in argument:
			mall_models.Order.update(created_at=bdd_util.get_datetime_str(argument['date'])).dj_where(order_id=context.created_order_id)
		if 'order_id' in argument:
			db_order = mall_models.Order.get(order_id=context.created_order_id)
			db_order.order_id=argument['order_id']
			db_order.save()
			if db_order.origin_order_id <0:
				for order in mall_models.Order.select().dj_where(origin_order_id=db_order.id):
					order.order_id = '%s^%s' % (argument['order_id'], order.supplier)
					order.save()
			context.created_order_id = argument['order_id']

	logging.info("[Order Created] webapp_owner_id: {}, created_order_id: {}".format(context.webapp_owner_id, context.created_order_id))


@then(u"{webapp_user_name}查看个人中心全部订单")
def step_visit_personal_orders(context, webapp_user_name):
    expected = json.loads(context.text)
    actual = []

    url = '/wapi/mall/order_list/?woid=%d&type=-1' % (context.webapp_owner_id)
    response = context.client.get(bdd_util.nginx(url), follow=True)
    orders = response.data['orders']
    import datetime
    for actual_order in orders:
        order = {}
        order['final_price'] = actual_order['final_price']
        order['products'] = []
        order['counts'] = actual_order['product_count']
        order['status'] = mall_models.ORDERSTATUS2MOBILETEXT[actual_order['status']]
        order['pay_interface'] = mall_models.PAYTYPE2NAME[actual_order['pay_interface_type']]
        order['created_at'] = actual_order['created_at']
        # BBD中购买的时间再未指定购买时间的情况下只能为今天
        created_at = datetime.datetime.strptime(actual_order['created_at'], '%Y.%m.%d %H:%M')
        if created_at.date() == datetime.date.today():
            order['created_at'] = u'今天'

        for i, product in enumerate(actual_order['products']):
            # 列表页面最多显示3个商品
            a_product = {}
            a_product['name'] = product['name']
            # a_product['price'] = product.total_price
            order['products'].append(a_product)
        actual.append(order)
    bdd_util.assert_list(expected, actual)


@when(u"{webapp_user_name}使用支付方式'{pay_interface_name}'进行支付")
def step_impl(context, webapp_user_name, pay_interface_name):
	pay_interfaces = mall_models.PayInterface.select()
	for pay_interface in pay_interfaces:
		if mall_models.PAYTYPE2NAME[pay_interface.type] != pay_interface_name:
			continue
		break

	pay_url = '/wapi/pay/pay_result/?_method=put'
	data = {
		'pay_interface_type': pay_interface.type,
		'order_id': context.created_order_id
	}
	context.client.post(pay_url, data)