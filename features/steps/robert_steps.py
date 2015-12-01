# -*- coding: utf-8 -*-
import json

from behave import *

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

@when(u"{webapp_user_name}购买{webapp_owner_name}的商品")
def step_impl(context, webapp_user_name, webapp_owner_name):
	"""最近修改: yanzhao
	e.g.:
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
			]
		}
	"""
	if hasattr(context, 'caller_step_purchase_info') and context.caller_step_purchase_info:
		args = context.caller_step_purchase_info
	else:
		args = json.loads(context.text)

	def __get_current_promotion_id_for_product(product, member_grade_id):
		promotion_ids = [r.promotion_id for r in promotion_models.ProductHasPromotion.select().dj_where(product_id=product.id)]
		promotions = list(promotion_models.Promotion.select().dj_where(id__in=promotion_ids, status=promotion_models.PROMOTION_STATUS_STARTED).where(promotion_models.Promotion.type>3))
		if len(promotions) > 0 and (promotions[0].member_grade_id <= 0 or \
				promotions[0].member_grade_id == member_grade_id):
			# 存在促销信息，且促销设置等级对该会员开放
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
		"xa-choseInterfaces": PAYNAME2ID.get(args.get("pay_type",""),-1)
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
	bdd_util.assert_api_call_success(response)
	context.response = response
	#response结果为: {"errMsg": "", "code": 200, "data": {"msg": null, "order_id": "20140620180559"}}

	if response.body['code'] == 200:
		# context.created_order_id为订单ID
		context.created_order_id = response.data['order_id']
	else:
		context.created_order_id = -1
		context.server_error_msg = response.data['msg']
		print "buy_error----------------------------",context.server_error_msg,response

	if context.created_order_id != -1:
		if 'date' in args:
			mall_models.Order.update(created_at=bdd_util.get_datetime_str(args['date'])).dj_where(order_id=context.created_order_id)
		if 'order_id' in args:
			db_order = Order.get(order_id=context.created_order_id)
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
    order_id = context.created_order_id
    if order_id == -1:
        print 'Server Error: ', json.dumps(json.loads(context.response.content), indent=True)
        assert False, "order_id must NOT be -1"
        return

    # order = Order.objects.get(order_id=order_id)

    url = '/wapi/mall/order/?woid=%s&order_id=%s' % (context.webapp_owner_id, order_id)
    logging.info('URL: {}'.format(url))
    response = context.client.get(bdd_util.nginx(url), follow=True)

    actual_order = response.data['order']
    actual_order['order_no'] = actual_order['order_id']
    actual_order['status'] = actual_order['status_text']
    # 获取coupon规则名
    if (actual_order['coupon_id'] != 0) and (actual_order['coupon_id'] != -1):
        # coupon = Coupon.objects.get(id=actual_order.coupon_id)
        coupon = steps_db_util.get_coupon_by_id(actual_order.coupon_id)
        actual_order.coupon_id = coupon.coupon_rule.name

    for product in actual_order['products']:
    	product['count'] = product['purchase_count']
        if 'custom_model_properties' in product and product['custom_model_properties']:
            product['model'] = ' '.join([property['property_value'] for property in product['custom_model_properties']])


    expected = json.loads(context.text)
    if expected.get('actions', None):
        # TODO 验证订单页面操作
        del expected['actions']
    bdd_util.assert_dict(expected, actual_order)









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
	product_groups = response.data['product_groups']
	invalid_products = response.data['invalid_products']

	def fill_products_model(products):
		for product in products:
			model = []
			original_model = product['model']
			if original_model and 'property_values' in original_model:
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
				products[0].price = new_promotion['detail']['promotion_price']
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
	data = {
		"shopping_cart_item_ids": ','.join(shopping_cart_item_ids),
		"woid": context.webapp_owner_id
	}

	response = context.client.post('/wapi/mall/shopping_cart_item/?_method=delete', data)
	bdd_util.assert_api_call_success(response)