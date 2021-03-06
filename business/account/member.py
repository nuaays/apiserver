# -*- coding: utf-8 -*-
"""@package business.account.member
会员
"""

import re
import json
from bs4 import BeautifulSoup
import math
from datetime import datetime

from eaglet.decorator import param_required
#from wapi import wapi_utils

from db.mall import models as mall_models
from db.mall import promotion_models
from db.member import models as member_models

#import resource
import settings
from eaglet.core import watchdog
from eaglet.core.cache import utils as cache_util
from util import emojicons_util

from business import model as business_model
from business.decorator import cached_context_property
from business.account.member_order_info import MemberOrderInfo
from business.mall.product import Product
import logging
from util.string_util import hex_to_byte, byte_to_hex

class Member(business_model.Model):
	"""
	会员
	"""
	__slots__ = (
		'id',
		'grade_id',
		'username_hexstr',
		#'webapp_user',
		'is_subscribed',
		'created',
		'token',
		'webapp_id',
		'pay_money',
		'update_time',
		'status',
		'fans_count',
		'friend_count'
	)

	@staticmethod
	def from_models(query):
		pass

	@staticmethod
	@param_required(['webapp_owner', 'model'])
	def from_model(args):
		"""
		工厂对象，根据member model获取Member业务对象

		@param[in] webapp_owner
		@param[in] model: member model

		@return Member业务对象
		"""
		webapp_owner = args['webapp_owner']
		model = args['model']

		member = Member(webapp_owner, model)
		member._init_slot_from_model(model)
		return member

	@staticmethod
	@param_required(['webapp_owner', 'member_id'])
	def from_id(args):
		"""
		工厂对象，根据member id获取Member业务对象

		@param[in] webapp_owner
		@param[in] member_id: 会员的id

		@return Member业务对象
		"""
		webapp_owner = args['webapp_owner']
		member_id = args['member_id']
		try:
			member_db_model = member_models.Member.get(id=member_id)
			return Member.from_model({
				'webapp_owner': webapp_owner,
				'model': member_db_model
			})
		except:
			return None

	@staticmethod
	@param_required(['webapp_owner', 'member_ids'])
	def from_ids(args):
		webapp_owner = args['webapp_owner']
		member_ids = args['member_ids']
		db_models = member_models.Member.select().dj_where(id__in=member_ids)
		return [Member.from_model({
			'webapp_owner': webapp_owner,
			'model': model
		}) for model in db_models]

	@staticmethod
	@param_required(['webapp_owner', 'token'])
	def from_tokens(args):
		webapp_owner = args['webapp_owner']
		token = args['token']
		member_list = []

		try:
			# 如果token为空不执行查询 直接返回[]
			if not token:
				return member_list

			member_db_models = member_models.Member.select().where(member_models.Member.token << token, member_models.Member.webapp_id==webapp_owner.webapp_id)
			for member_db_model in member_db_models:
				member = Member.from_model({
					'webapp_owner': webapp_owner,
					'model': member_db_model
				})
				member_list.append(member)
			return member_list
		except:
			return member_list

	@staticmethod
	@param_required(['webapp_owner', 'token'])
	def from_token(args):
		"""
		工厂对象，根据member id获取Member业务对象

		@param[in] webapp_owner
		@param[in] token: 会员的token

		@return Member业务对象
		"""
		webapp_owner = args['webapp_owner']
		token = args['token']
		try:
			member_db_model = member_models.Member.get(webapp_id=webapp_owner.webapp_id,token=token)
			return Member.from_model({
				'webapp_owner': webapp_owner,
				'model': member_db_model
			})
		except:
			return None

	def __init__(self, webapp_owner, model):
		business_model.Model.__init__(self)

		self.context['webapp_owner'] = webapp_owner
		self.context['db_model'] = model

	@cached_context_property
	def __grade(self):
		"""
		[property] 会员等级信息
		"""
		member_model = self.context['db_model']
		webapp_owner = self.context['webapp_owner']

		if not member_model:
			return None

		member_grade_id = member_model.grade_id
		member_grade = webapp_owner.member2grade.get(member_grade_id, '')
		return member_grade

	@property
	def discount(self):
		"""
		[property] 会员折扣

		@return 返回二元组(grade_id, 折扣百分数)
		"""
		member_model = self.context['db_model']
		if not member_model:
			return -1, 100

		member_grade = self.__grade
		if member_grade:
			return member_model.grade_id, member_grade.shop_discount
		else:
			return member_model.grade_id, 100

	@property
	def grade(self):
		"""
		[property] 会员等级
		"""
		return self.__grade

	@cached_context_property
	def __info(self):
		"""
		[property] 与会员对应的MemberInfo model对象
		"""
		member_model = self.context['db_model']
		if not member_model:
			return None

		try:
			member_info = member_models.MemberInfo.get(member=member_model)
		except:
			member_info = member_models.MemberInfo()
			member_info.member = member_model
			member_info.name = ''
			member_info.weibo_name = ''
			member_info.phone_number = ''
			member_info.sex = member_models.SEX_TYPE_UNKOWN
			member_info.is_binded = False
			member_info.weibo_nickname = ''
			member_info.phone_number = ''
			member_info.save()

		if member_info.phone_number and len(member_info.phone_number) > 10:
			member_info.phone =  '%s****%s' % (member_info.phone_number[:3], member_info.phone_number[-4:])
		else:
			member_info.phone = ''

		return member_info

	@property
	def phone(self):
		"""
		[property] 会员绑定的手机号码加密
		"""

		return self.__info.phone
	
	@cached_context_property
	def phone_number(self):
		"""
		[property] 会员绑定的手机号码
		"""

		return self.__info.phone_number


	@cached_context_property
	def captcha(self):
		"""
		[property] 手机验证码
		"""
		return self.__info.captcha

	@cached_context_property
	def captcha_session_id(self):
		"""
		[property] 手机验证码
		"""
		return self.__info.session_id

	@property
	def name(self):
		"""
		[property] 会员名
		"""

		return self.__info.name

	@property
	def is_binded(self):
		"""
		[property] 会员是否进行了绑定
		"""
		return self.__info.is_binded

	@cached_context_property
	def user_icon(self):
		"""
		[property] 会员头像
		"""
		return self.context['db_model'].user_icon

	@cached_context_property
	def integral_info(self):
		"""
		[property] 会员积分信息
		"""
		member_model = self.context['db_model']
		if member_model:
			count = member_model.integral
			grade = self.__grade
			if grade:
				usable_integral_percentage_in_order = grade.usable_integral_percentage_in_order
			else:
				usable_integral_percentage_in_order = 100
		else:
			count = 0
			usable_integral_percentage_in_order = 100

		integral_strategy_settings = self.context['webapp_owner'].integral_strategy_settings
		return {
			'count': count,
			'count_per_yuan': integral_strategy_settings.integral_each_yuan,
			'usable_integral_percentage_in_order' : usable_integral_percentage_in_order,
			'usable_integral_or_conpon' : integral_strategy_settings.usable_integral_or_conpon
		}

	@property
	def integral(self):
		"""
		[property] 会员积分数值
		"""
		member_model = self.context['db_model']

		return member_model.integral

	@cached_context_property
	def username_for_html(self):
		"""
		[property] 兼容html显示的会员名
		"""
		if (self.username_hexstr is not None) and (len(self.username_hexstr) > 0):
			username = emojicons_util.encode_emojicons_for_html(self.username_hexstr, is_hex_str=True)
		else:
			username = emojicons_util.encode_emojicons_for_html(self.username)		

		try:
			username.decode('utf-8')
		except:
			username = self.username_hexstr

		return username

	@cached_context_property
	def market_tools(self):
		"""
		[property] 会员参与的营销工具集合
		"""
		#TODO2: 实现营销工具集合
		print u'TODO2: 实现营销工具集合'
		return []

	@staticmethod
	def empty_member():
		"""工厂方法，创建空的member对象

		@return Member对象
		"""
		member = Member(None, None)
		return member


	@property
	def username(self):
		return hex_to_byte(self.username_hexstr)

	@cached_context_property
	def username_size_ten(self):
		try:
			username = unicode(self.username_for_html, 'utf8')
			_username = re.sub('<[^<]+?><[^<]+?>', ' ', username)
			if len(_username) <= 10:
				return username
			else:
				name_str = username
				span_list = re.findall(r'<[^<]+?><[^<]+?>', name_str) #保存表情符

				output_str = ""
				count = 0

				if not span_list:
					return u'%s...' % name_str[:10]

				for span in span_list:
				    length = len(span)
				    while not span == name_str[:length]:
				        output_str += name_str[0]
				        count += 1
				        name_str = name_str[1:]
				        if count == 10:
				            break
				    else:
				        output_str += span
				        count += 1
				        name_str = name_str[length:]
			 	        if count == 10:
				            break
				    if count == 10:
				        break
				return u'%s...' % output_str
		except:
			return self.username_for_html[:10]
	@staticmethod
	@param_required(['is_fans','member_id'])
	def add_friend_count(args):
		"""
		@param[in] : 

		会员建立关系后，增加member的friend_count,fans_count
		"""
		member_id = args['member_id']
		is_fans = args['is_fans']
		
		if is_fans:
			member_models.Member.update(friend_count=member_models.Member.friend_count + 1,fans_count=member_models.Member.fans_count + 1).dj_where(id=member_id).execute()
		else:
			member_models.Member.update(friend_count=member_models.Member.friend_count + 1).dj_where(id=member_id).execute()
