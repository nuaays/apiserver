#editor: benchi
#editor: 师帅 2015.10.20
#editor: 王丽 2015.12.25

Feature:使用微众卡购买商品
	用户能通过webapp使用微众卡购买jobs的商品
	feathure里要加一个  "weizoom_card_money":50.00,的字段

Background:
	Given 重置weapp的bdd环境
	Given jobs登录系统:weapp
	And jobs已有微众卡支付权限:weapp
	And jobs已添加支付方式:weapp
		"""
		[{
			"type":"货到付款"
		},{
			"type":"微信支付"
		},{
			"type":"支付宝"
		},{
			"type":"微众卡支付"
		}]
		"""
	And jobs已添加商品:weapp
		"""
		[{
			"name": "商品1",
			"price": 50
		}]
		"""
	And jobs已创建微众卡:weapp
		"""
		{
			"cards":[{
				"id":"0000001",
				"password":"1234567",
				"status":"未使用",
				"price":100.00
			},{
				"id":"0000002",
				"password":"1234567",
				"status":"已使用",
				"price":50.00
			},{
				"id":"0000003",
				"password":"1231231",
				"status":"未使用",
				"price":30.00
			},{
				"id":"0000004",
				"password":"1231231",
				"status":"已用完",
				"price":0.00
			},{
				"id":"0000005",
				"password":"1231231",
				"status":"未激活",
				"price":30.00
			},{
				"id":"0000006",
				"password":"1231231",
				"status":"已过期",
				"price":30.00
			},{
				"id":"0000007",
				"password":"1234567",
				"status":"未使用",
				"price":50.00
			}]
		}
		"""
	And bill关注jobs的公众号

@mall3 @mall2 @wip.bpuc1 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:1 微众卡金额大于订单金额时进行支付
	bill用微众卡购买jobs的商品时,微众卡金额大于订单金额
	1.自动扣除微众卡金额
	2.创建订单成功，订单状态为“等待发货”，支付方式为“微众卡支付”
	3.微众卡金额减少,状态为“已使用”

	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000001':weapp
		"""
		{
			"status":"未使用",
			"price":100.00
		}
		"""

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "货到付款",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000001",
				"card_pass":"1234567"
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待发货",
			"final_price": 0.0,
			"product_price": 50.0,
			"weizoom_card_money":50.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000001':weapp
		"""
		{
			"status":"已使用",
			"price":50.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:2 微众卡金额等于订单金额时进行支付
	bill用微众卡购买jobs的商品时,微众卡金额等于订单金额
	1.自动扣除微众卡金额
	2.创建订单成功，订单状态为“等待发货”，支付方式为“微众卡支付”
	3.微众卡金额减少,状态为“已用完”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "货到付款",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000007",
				"card_pass":"1234567"
			}]
		}
		"""

	Then bill成功创建订单
		"""
		{
			"status": "待发货",
			"final_price": 0.0,
			"product_price": 50.0,
			"weizoom_card_money":50.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000007':weapp
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:3 微众卡金额小于订单金额时进行支付
	bill用微众卡购买jobs的商品时,微众卡金额小于订单金额
	1.创建订单成功，订单状态为“等待支付”，待支付金额为订单金额减去微众卡金额
	2.微众卡金额为零,状态为“已使用”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000003",
				"card_pass":"1231231"
			}]
		}
		"""

	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 20.0,
			"product_price": 50.0,
			"weizoom_card_money":30.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000003':weapp
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:4 用微众卡购买商品时，输入错误的卡号密码
	bill用微众卡购买jobs的商品时,输入错误的卡号密码
	1.创建订单成功，订单状态为“等待支付”
	2.微众卡金额不变,状态为“未使用”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000001",
				"card_pass":"1231231"
			}]
		}
		"""

	Then bill获得创建订单失败的信息'卡号或密码错误'

	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}]
		}
		"""

	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 50.0,
			"product_price": 50.0,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000001':weapp
		"""
		{
			"status":"未使用",
			"price":100.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:5 用已用完的微众卡购买商品时
	bill用已用完的微众卡购买jobs的商品时
	1.创建订单成功，订单状态为“等待支付”
	2.微众卡金额不变,状态为“已用完”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000004",
				"card_pass":"1231231"
			}]
		}
		"""

	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 50.0,
			"product_price": 50.0,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000004':weapp
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:6 用未激活的微众卡购买商品时
	bill用未激活的微众卡购买jobs的商品时
	1.创建订单失败，提示"微众卡未激活"
	2.微众卡金额不变,状态为“未激活”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000005",
				"card_pass":"1231231"
			}]
		}
		"""
	Then bill获得创建订单失败的信息'微众卡未激活'

	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 50.0,
			"product_price": 50.0,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000005':weapp
		"""
		{
			"status":"未激活",
			"price":30.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:7 用已过期的微众卡购买商品时
	bill用已用过期的微众卡购买jobs的商品时
	1.提示"微众卡已过期"
	2.微众卡金额不变,状态为“已过期”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000006",
				"card_pass":"1231231"
			}]
		}
		"""

	Then bill获得创建订单失败的信息'微众卡已过期'
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 50.0,
			"product_price": 50.0,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000006':weapp
		"""
		{
			"status":"已过期",
			"price":30.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:8 用已使用过的微众卡购买商品时
	1.创建订单成功，订单状态为“待发货”
	2.扣除微众卡金额,状态为“已用完”

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000002",
				"card_pass":"1234567"
			}]
		}
		"""

	Then bill成功创建订单
		"""
		{
			"status": "待发货",
			"final_price": 0.0,
			"product_price": 50.0,
			"weizoom_card_money":50.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000002':weapp
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:9 用10张微众卡共同支付
	1.创建订单成功，订单状态为“待支付”
	2.扣除微众卡金额,状态为“已用完”
	Given jobs登录系统:weapp
	And jobs已创建微众卡:weapp
		"""
		{
			"cards":[{
				"id":"1000001",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000002",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000003",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000004",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000005",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000006",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000007",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000008",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000009",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000010",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000011",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			}]
		}
		"""

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"1000001",
				"card_pass":"1234567"
			},{
				"card_name":"1000002",
				"card_pass":"1234567"
			},{
				"card_name":"1000003",
				"card_pass":"1234567"
			},{
				"card_name":"1000004",
				"card_pass":"1234567"
			},{
				"card_name":"1000005",
				"card_pass":"1234567"
			},{
				"card_name":"1000006",
				"card_pass":"1234567"
			},{
				"card_name":"1000007",
				"card_pass":"1234567"
			},{
				"card_name":"1000008",
				"card_pass":"1234567"
			},{
				"card_name":"1000009",
				"card_pass":"1234567"
			},{
				"card_name":"1000010",
				"card_pass":"1234567"
			}]
		}
		"""

	Then bill成功创建订单
		"""
		{
			"status": "待支付",
			"final_price": 40.0,
			"product_price": 50.0,
			"weizoom_card_money":10.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡:weapp
		"""
		[{
			"id":"1000001",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000002",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000003",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000004",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000005",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000006",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000007",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000008",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000009",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000010",
			"password":"1234567",
			"status":"已用完",
			"price":0.00
		},{
			"id":"1000011",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		}]
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:10 用11张微众卡共同支付
	1.创建订单失败错误提示：只能使用10张微众卡
	2.微众卡金额,状态不变
	Given jobs登录系统:weapp
	And jobs已创建微众卡:weapp
		"""
		{
			"cards":[{
				"id":"1000001",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000002",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000003",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000004",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000005",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000006",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000007",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000008",
				"password":"1234567",
				"status":"未使用",
				"price":1.00
			},{
				"id":"1000009",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000010",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			},{
				"id":"1000011",
				"password":"1234567",
				"status":"已使用",
				"price":1.00
			}]
		}
		"""

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"1000001",
				"card_pass":"1234567"
			},{
				"card_name":"1000002",
				"card_pass":"1234567"
			},{
				"card_name":"1000003",
				"card_pass":"1234567"
			},{
				"card_name":"1000004",
				"card_pass":"1234567"
			},{
				"card_name":"1000005",
				"card_pass":"1234567"
			},{
				"card_name":"1000006",
				"card_pass":"1234567"
			},{
				"card_name":"1000007",
				"card_pass":"1234567"
			},{
				"card_name":"1000008",
				"card_pass":"1234567"
			},{
				"card_name":"1000009",
				"card_pass":"1234567"
			},{
				"card_name":"1000010",
				"card_pass":"1234567"
			},{
				"card_name":"1000011",
				"card_pass":"1234567"
			}]
		}
		"""

	Then bill获得创建订单失败的信息'微众卡只能使用十张'
	Given jobs登录系统:weapp
	Then jobs能获取微众卡:weapp
		"""
		[{
			"id":"1000001",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		},{
			"id":"1000002",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		},{
			"id":"1000003",
			"password":"1234567",
			"status":"未使用",
			"price":1.00
		},{
			"id":"1000004",
			"password":"1234567",
			"status":"未使用",
			"price":1.00
		},{
			"id":"1000005",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		},{
			"id":"1000006",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		},{
			"id":"1000007",
			"password":"1234567",
			"status":"未使用",
			"price":1.00
		},{
			"id":"1000008",
			"password":"1234567",
			"status":"未使用",
			"price":1.00
		},{
			"id":"1000009",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		},{
			"id":"1000010",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		},{
			"id":"1000011",
			"password":"1234567",
			"status":"已使用",
			"price":1.00
		}]
		"""

@mall3 @mall2 @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:11 用微众卡购买商品时，输入两张同样的卡号密码
	bill用微众卡购买jobs的商品时,输入错误的卡号密码
	1.创建订单失败，错误提示"该微众卡已经添加"
	2.微众卡金额,状态不变

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000001",
				"card_pass":"1234567"
			},{
				"card_name":"0000001",
				"card_pass":"1234567"
			}]
		}
		"""

	Then bill获得创建订单失败的信息'该微众卡已经添加'

	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000001'
		"""
		{
			"status":"未使用",
			"price":100.00
		}
		"""

@mall3 @mall2 @mall @mall.pay_weizoom_card @victor
#购买流程.编辑订单.微众卡使用
Scenario:12 用两张微众卡购买，第一张卡的金额大于商品金额
	1.使用两张微众卡进行购买，微众卡金额大于商品金额
	2.第一张微众卡还有余额
	3.第二张微众卡还有余额

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000001",
				"card_pass":"1234567"
			},{
				"card_name":"0000003",
				"card_pass":"1231231"
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"status": "待发货",
			"final_price": 0.0,
			"product_price": 50.0,
			"weizoom_card_money":50.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000001'
		"""
		{
			"status":"已使用",
			"price":50.00
		}
		"""
	Then jobs能获取微众卡'0000003'
		"""
		{
			"status":"未使用",
			"price":30.00
		}
		"""
#根据bug补充7240#新新
@mall3 @mall.pay_weizoom_card @victor @wip.bpuc13
#购买流程.编辑订单.微众卡使用
Scenario:13 用两张微众卡购买，第二张卡的金额大于商品金额
	1.使用两张微众卡进行购买，微众卡金额大于商品金额
	2.第一张微众卡余额为0
	3.第二张微众卡还有余额

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"order_id":"001",
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000003",
				"card_pass":"1231231"
			}, {
				"card_name":"0000001",
				"card_pass":"1234567"
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"order_id":"001",
			"status": "待发货",
			"final_price": 0.0,
			"product_price": 50.0,
			"weizoom_card_money":50.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000003'
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""
	Then jobs能获取微众卡'0000001'
		"""
		{
			"status":"已使用",
			"price":80.00
		}
		"""
	When jobs取消订单'001':weapp
	Then jobs能获取微众卡'0000003'
		"""
		{
			"status":"已使用",
			"price":30.00
		}
		"""
	Then jobs能获取微众卡'0000001'
		"""
		{
			"status":"已使用",
			"price":100.00
		}
		"""

#根据bug补充7240#新新
@mall3 @mall.pay_weizoom_card @victor @wip.bpuc14 
#购买流程.编辑订单.微众卡使用
Scenario:14 用两张微众卡购买，2张卡小于商品金额,购买待支付状态
	1.使用两张微众卡进行购买，bill取消订单

	Given jobs登录系统:weapp
	And jobs已创建微众卡:weapp
		"""
		{
			"cards":[{
				"id":"0000008",
				"password":"1234567",
				"status":"已使用",
				"price":10
			},{
				"id":"0000009",
				"password":"1234567",
				"status":"未使用",
				"price":30
			}]
		}
		"""

	When bill访问jobs的webapp
	When bill购买jobs的商品
		"""
		{
			"order_id":"001",
			"pay_type": "微信支付",
			"products":[{
				"name":"商品1",
				"price":50,
				"count":1
			}],
			"weizoom_card":[{
				"card_name":"0000008",
				"card_pass":"1234567"
			}, {
				"card_name":"0000009",
				"card_pass":"1234567"
			}]
		}
		"""
	Then bill成功创建订单
		"""
		{
			"order_id":"001",
			"status": "待支付",
			"final_price": 10.0,
			"product_price": 50.0,
			"weizoom_card_money":40.00,
			"products":[{
				"name":"商品1",
				"price":50.00,
				"count":1
			}]
		}
		"""
	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000008'
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""
	Then jobs能获取微众卡'0000009'
		"""
		{
			"status":"已用完",
			"price":0.00
		}
		"""
	When bill访问jobs的webapp
	Then bill'能'取消订单'001'
	When bill取消订单'001'

	Given jobs登录系统:weapp
	Then jobs能获取微众卡'0000008'
		"""
		{
			"status":"已使用",
			"price":10.00
		}
		"""
	Then jobs能获取微众卡'0000009'
		"""
		{
			"status":"已使用",
			"price":30.00
		}
		"""
