# -*- coding: utf-8 -*-
import json

from core import api_resource
from wapi.decorators import param_required
from wapi.mall import models as mall_models
from utils import dateutil as utils_dateutil
import resource
from business.mall.product import Product


class AProduct(api_resource.ApiResource):
	"""
	商品
	"""
	app = 'mall'
	resource = 'product'


	@param_required(['woid', 'product_id'])
	def get(args):
		"""
		获取商品详情

		@param id 商品ID

		@note 从Weapp中迁移过来
		@see  mall_api.get_product_detail(webapp_owner_id, product_id, webapp_user, member_grade_id)
		"""

		"""
		显示“商品详情”页面

		"""
		product_id = args['product_id']
		webapp_owner_id = args['woid']
		webapp_user = args['webapp_user']

		member = args.get('member', None)
		member_grade_id = member.grade_id if member else None
		
		# 检查置顶评论是否过期
		# TODO: 是否每次都需要去进行检查？还是交给service每天凌晨进行更新
		# resource.post('mall', 'top_product_review', {
		# 	"product_id": product_id
		# })

		product = Product.from_id({
			'woid': args['woid'],
			'member': args['member'],
			'product_id': args['product_id']
		})

		return product.to_dict(extras=['hint'])