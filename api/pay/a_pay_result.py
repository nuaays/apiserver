# -*- coding: utf-8 -*-

from eaglet.core import api_resource
from eaglet.core import watchdog
from eaglet.decorator import param_required

from business.mall.order import Order
from business.mall.order_config import OrderConfig
from business.mall.red_envelope import RedEnvelope
from business.member_card.member_card_pay_order import MemberCardPayOrder
from core.exceptionutil import unicode_full_stack


class APayResult(api_resource.ApiResource):
	"""
	订单
	"""
	app = 'pay'
	resource = 'pay_result'

	@param_required(['order_id'])
	def get(args):
		"""
		获取支付结果页面

		@param id 订单order_id
		"""
		webapp_user = args['webapp_user']
		webapp_owner = args['webapp_owner']

		order_id = args['order_id'].split('-')[0]

		order = Order.from_id({
			'webapp_owner': webapp_owner,
			'webapp_user': webapp_user,
			'order_id': order_id
		})

		if not order.is_valid():
			msg = u'订单({})不存在'.format(order_id)
			error_msg = u'weixin pay, stage:[get_pay_result], result:{}, exception:\n{}'.format(msg, msg)
			watchdog.alert(error_msg)
			return 500, {'msg': error_msg}

		is_show_red_envelope = False
		red_envelope_rule_id = 0
		red_envelope = webapp_owner.red_envelope
		if RedEnvelope.can_show_red_envelope(order, red_envelope):
			# 是可以显示分享红包按钮
			is_show_red_envelope = True
			red_envelope_rule_id = red_envelope['id']

		order_config = OrderConfig.get_order_config({'webapp_owner': webapp_owner})

		qrcode_img = webapp_owner.qrcode_img
		activity_url = ''
		if order.is_group_buy:
			activity_url = order.order_group_info['activity_url'] + '&from=pay_result'

		return {
			'is_trade_success': True,
			'order': order.to_dict('is_group_buy'),
			'is_show_red_envelope': is_show_red_envelope,
			'red_envelope_rule_id': red_envelope_rule_id,
			'qrcode_img': qrcode_img,
			'activity_url': activity_url,
			'order_config': order_config
		}

	@param_required(['order_id', 'pay_interface_type'])
	def put(args):
		"""
		微信支付、支付宝回调接口
		@return:
		"""

		webapp_user = args['webapp_user']
		webapp_owner = args['webapp_owner']

		order_id = args['order_id'].split('-')[0]
		if order_id.startswith('vip_'):  #如果是会员卡的订单，则特殊处理
			order = MemberCardPayOrder.from_order_id({
				'webapp_owner': args['webapp_owner'],
				'webapp_user': args['webapp_user'],
				'order_id': order_id
			})
			order.pay()
			is_success = True
			msg = ''
		else:  #普通商城订单
			pay_interface_type = int(args['pay_interface_type'])
			order = Order.from_id({
				'webapp_owner': webapp_owner,
				'webapp_user': webapp_user,
				'order_id': order_id
			})

			try:
				is_success, msg = order.pay(pay_interface_type=pay_interface_type)
			except:
				is_success = False
				msg = unicode_full_stack()
				watchdog.alert(msg)

		return {
			'order_id': args['order_id'],
			'is_success': is_success,
			'msg': msg
		}


	# @param_required(['order_id', 'pay_interface_type'])
	# def put(args):
	# 	"""
	# 	获取支付结果
	#
	# 	@param id 商品ID
	# 	"""
	# 	webapp_user = args['webapp_user']
	# 	webapp_owner = args['webapp_owner']
	#
	# 	pay_interface_type = args['pay_interface_type']
	#
	# 	# 同步支付结果开始时间
	# 	get_pay_result_start_time = int(time.time() * 1000)
	#
	# 	pay_result = {
	# 		'order_id': args['order_id'],
	#
	# 		'out_trade_no': args.get('out_trade_no', ''), #alipay, tenpay
	# 		'result': args.get('result', ''), #alipay
	#
	# 		'trade_status': args.get('trade_status', ''), #tenpay
	# 		'pay_info': args.get('pay_info', ''), #tenpay
	# 	}
	# 	pay_interface = PayInterface.from_type({
	# 		'webapp_owner': webapp_owner,
	# 		'pay_interface_type': pay_interface_type
	# 	})
	# 	pay_result = pay_interface.parse_pay_result(pay_result)
	# 	is_trade_success = pay_result['is_success']
	# 	order_id = pay_result['order_id']
	#
	# 	try:
	# 		watchdog.info(u'weixin pay, stage:[get_pay_result], result:支付同步通知{}'.format(pay_result))
	# 	except:
	# 		pass
	#
	# 	order = None
	# 	if order_id and is_trade_success:
	# 		order = Order.from_id({
	# 			'webapp_owner': webapp_owner,
	# 			'webapp_user': webapp_user,
	# 			'order_id': order_id
	# 		})
	#
	# 		if not order.is_valid():
	# 			msg = u'订单({})不存在'.format(order_id)
	# 			error_msg = u'weixin pay, stage:[get_pay_result], result:{}, exception:\n{}'.format(msg, msg)
	# 			watchdog.error(error_msg)
	# 			return 500, msg
	# 		is_pay_success = order.pay(pay_interface.type)
	# 		if is_pay_success:
	# 			# webapp_user.set_purchased()  #这个不应该在这处理 duhao
	# 			pass
	#
	# 		#TODO2: 进行支付后处理
	# 		#mall_signals.post_pay_order.send(sender=Order, order=order, request=request)
	#
	# 	#TODO2 : 处理优惠券
	# 	# if order.coupon_id:
	# 	# 	try:
	# 	# 		coupons = coupon_model.Coupon.objects.filter(id=order.coupon_id)
	# 	# 		if coupons.count() > 0:
	# 	# 			coupon = coupons[0]
	# 	# 			order.coupon_id = coupon.coupon_rule.name
	# 	# 	except:
	# 	# 		error_msg = u'weixin pay, stage:[get_pay_result], result:获取优惠券异常, exception:\n{}'.format(unicode_full_stack())
	# 	# 		watchdog.error(error_msg)
	# 	# 		pass
	#
	# 	#TODO2: 是否提示用户领红包
	# 	is_show_red_envelope = False
	# 	red_envelope_rule_id = 0
	# 	red_envelope = webapp_owner.red_envelope
	# 	if RedEnvelope.can_show_red_envelope(order, red_envelope):
	# 		# 是可以显示分享红包按钮
	# 		is_show_red_envelope = True
	# 		red_envelope_rule_id = red_envelope['id']
	#
	# 	# 同步支付结果结束时间
	# 	get_pay_result_end_time = int(time.time() * 1000)
	# 	msg = u'weixin pay, stage:[get pay result], order_id:{}, consumed:{}ms'.format(order_id, (get_pay_result_end_time - get_pay_result_start_time))
	# 	watchdog.info(msg)
	#
	# 	# 记录支付结束时间
	# 	pay_end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
	# 	msg = u'weixin pay, stage:[end], order_id:{}, time:{}'.format(order_id, pay_end_time)
	# 	watchdog.info(msg)
	#
	# 	return {
	# 		'is_trade_success': is_trade_success,
	# 		'order': order.to_dict(),
	# 		'is_show_red_envelope': is_show_red_envelope,
	# 		'red_envelope_rule_id': red_envelope_rule_id
	# 	}
