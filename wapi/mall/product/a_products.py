# -*- coding: utf-8 -*-

from core import api_resource
from wapi.decorators import param_required
import resource
from business.mall.simple_products import SimpleProducts

class AProducts(api_resource.ApiResource):
	"""
	商品
	"""
	app = 'mall'
	resource = 'products'

	@param_required(['woid', 'category_id'])
	def get(args):
		"""
		获取商品详情

		@param category_id 商品分类ID
		"""
		category_id = args['category_id']
		webapp_owner = args['webapp_owner']

		products = SimpleProducts.get({
			"webapp_owner": webapp_owner,
			"category_id": category_id,
			"is_access_weizoom_mall": False
		})
		result = [product.format_to_dict() for product in products]
		return result