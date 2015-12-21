# __author__ : "王丽" 2015-12-21

Feature: 会员绑定手机号
"""
	1 会员个人中心：点击"绑定手机"
	2 进入"绑定会员"界面，输入手机号，点击"获取验证码"，获得手机验证码
	3 输入正确的验证码，点击"确认提交"，给出"绑定成功"的提示
	4 输入错误的杨正吗，点击"确认提交"，给出"手机验证码错误，请重新输入"的提示
	5 绑定手机成功之后，访问"绑定会员"页，获得绑定手机号，中间隐藏
"""

@person @bindingPhone
Scenario:1 手机绑定-输入正确的验证码
	When bill关注jobs的公众账号
	When bill访问jobs的Webapp

	When bill获得手机绑定验证码
		"""
		{
			"phone": 15194857825,
			"verification_code": 1234
		}
		"""
	When bill绑定手机
		"""
		{
			"phone": 15194857825,
			"verification_code": 1234
		}
		"""
	Then bill获得提示信息"绑定成功"

@person @bindingPhone
Scenario:2 手机绑定-输入错误的验证码
	When bill关注jobs的公众账号
	When bill访问jobs的Webapp

	When bill获得手机绑定验证码
		"""
		{
			"phone": 15194857825,
			"verification_code": 1234
		}
		"""
	When bill绑定手机
		"""
		{
			"phone": 15194857825,
			"verification_code": 6789
		}
		"""
	Then bill获得提示信息"手机验证码错误，请重新输入"

@person @bindingPhone
Scenario:3 手机绑定-绑定成功访问绑定页
	When bill关注jobs的公众账号
	When bill访问jobs的Webapp

	When bill获得手机绑定验证码
		"""
		{
			"phone": 15194857825,
			"verification_code": 1234
		}
		"""
	When bill绑定手机
		"""
		{
			"phone": 15194857825,
			"verification_code": 1234
		}
		"""
	Then bill获得提示信息"绑定成功"

	When bill访问"绑定会员"页
	Then bill获得绑定信息
		"""
		{
			"绑定手机": 151****7825,
		}
		"""