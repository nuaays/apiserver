# watcher: wangxinrui@weizoom.com,benchi@weizoom.com
#editor 新新 2015.11.26
@func:webapp.modules.mall.views.list_products
Feature: 在webapp中支付订单
	bill能在webapp中支付订单


Background:
	Given 重置'weapp'的bdd环境
	Given jobs登录系统::weapp
	And jobs已添加支付方式::weapp
		"""
		[{
			"type": "微信支付",
			"version": 2,
			"description": "我的微信支付V2",
			"is_active": "启用"
		},{
			"type": "货到付款",
			"is_active": "启用"
		}]
		"""
	And jobs已添加商品::weapp
		"""
		[{
			"name": "商品1",
			"price": 9.90
		}, {
			"name": "商品2",
			"price": 8.80
		}]	
		"""
	And bill关注jobs的公众号

@mall3 @mall @mall.webapp @mall.pay_order @duhao
Scenario:1 使用货到付款支付
	bill在下单购买jobs的商品后，能使用货到付款进行支付，支付后
	1. bill的订单中变为"待发货"
	2. jobs在后台看到订单变为"待发货"
	
	When bill访问jobs的webapp
	And bill购买jobs的商品
		"""
		{
			"pay_type": "货到付款",
			"products": [{
				"name": "商品1",
				"count": 1
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待发货",
			"final_price": 9.90,
			"products": [{
				"name": "商品1",
				"price": 9.90,
				"count": 1
			}]
		}
		"""
	
@mall2 @mall @mall.webapp @mall.pay_order @mall3 @duhao
Scenario:2 使用V2版微信支付进行同步支付
	bill在下单购买jobs的商品后，能使用微信支付进行支付，支付后
	1. bill的订单中变为"待发货"
	2. jobs在后台看到订单变为"待发货"
	
	When bill访问jobs的webapp
	And bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products": [{
				"name": "商品1",
				"count": 1
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 9.90,
			"products": [{
				"name": "商品1",
				"price": 9.90,
				"count": 1
			}]
		}
		"""
	When bill使用支付方式'微信支付'进行支付
		"""
		{
			"is_sync": true
		}
		"""
	Then bill支付订单成功
		"""
		{
			"status": "待发货",
			"final_price": 9.90,
			"products": [{
				"name": "商品1",
				"price": 9.90,
				"count": 1
			}]
		}
		"""

@mall2 @mall @mall.webapp @mall.pay_order @mall3 @duhao
Scenario:3 使用V2版微信支付进行异步支付
	bill在下单购买jobs的商品后，能使用微信支付进行支付，支付后
	1. bill的订单中变为"待发货"
	2. jobs在后台看到订单变为"待发货"
	
	When bill访问jobs的webapp
	And bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products": [{
				"name": "商品1",
				"count": 1
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 9.90,
			"products": [{
				"name": "商品1",
				"price": 9.90,
				"count": 1
			}]
		}
		"""
	When bill使用支付方式'微信支付'进行支付
		"""
		{
			"is_sync": false
		}
		"""
	Then bill支付订单成功
		"""
		{
			"status": "待发货",
			"final_price": 9.90,
			"products": [{
				"name": "商品1",
				"price": 9.90,
				"count": 1
			}]
		}
		"""

@mall2 @mall @mall.webapp @mall.pay_order @mall3 @duhao
Scenario:4 使用微信支付,没有支付
	
	When bill访问jobs的webapp
	And bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products": [{
				"name": "商品1",
				"count": 1
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 9.90,
			"products": [{
				"name": "商品1",
				"price": 9.90,
				"count": 1
			}]
		}
		"""
