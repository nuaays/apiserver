# -*- coding: utf-8 -*-
"""@package wapi.mall.a_review
评论API

"""

#import copy
#from datetime import datetime

from core import api_resource
from wapi.decorators import param_required
#from db.mall import models as mall_models
#from db.mall import promotion_models
#from utils import dateutil as utils_dateutil
#import resource
#from wapi.mall.a_purchasing import APurchasing as PurchasingApiResource
#from core.cache import utils as cache_utils
#from business.mall.order_factory import OrderFactory
#from business.mall.purchase_info import PurchaseInfo
#from business.mall.pay_interface import PayInterface
from business.mall.order_review import OrderReview
from business.mall.product_review import ProductReview
import logging
from core.watchdog.utils import watchdog_info

class AReview(api_resource.ApiResource):
	"""
	评论

	@see 原始源码在`webapp/modules/mall/request_api_util.py`中的`create_product_review()`。
	"""
	app = 'mall'
	resource = 'review'


	@staticmethod
	def _get_order_review_list(request,need_product_detail=False):
		'''
			得到会员已完成订单中所有未评价的商品列表的订单，
			或者已评价未晒图的订单

			PreCondition: webapp_user_id, member_id,
			PostCondition: orders

		@see 原始代码位置 `webapp/modules/mall/request_util.py`
		'''

		webapp_user_id = request.webapp_user.id  # 游客身份
		member_id = request.member.id            # 会员身份

		# 得到会员的所有已完成的订单
		orders = Order.by_webapp_user_id(webapp_user_id).filter(status=5)
		orderIds = [order.id for order in orders]
		orderHasProducts = OrderHasProduct.objects.filter(order_id__in=orderIds)
		totalProductIds = [orderHasProduct.product_id for orderHasProduct in orderHasProducts]

		orderId2orderHasProducts = dict()
		for orderHasProduct in orderHasProducts:
			if not orderId2orderHasProducts.get(orderHasProduct.order_id):
				orderId2orderHasProducts[orderHasProduct.order_id] = []
			orderId2orderHasProducts.get(orderHasProduct.order_id).append(orderHasProduct)

		orderHasProductIds = [orderHasProduct.id for orderHasProduct in orderHasProducts]
		ProductReviews = mall_models.ProductReview.objects.filter(order_has_product_id__in=orderHasProductIds)
		orderHasProductId2ProductReviews = dict()
		for ProductReview in ProductReviews:
			orderHasProductId2ProductReviews[ProductReview.order_has_product_id] = ProductReview

		allProductReviewPicture = mall_models.ProductReviewPicture.objects.filter(order_has_product_id__in= orderHasProductIds)
		ProductReviewPictureIds = [ProductReviewPicture.product_review_id for ProductReviewPicture in allProductReviewPicture]
		def _product_review_has_picture(product_review):
			'''
			评价是否有晒图
			'''


			if product_review.id in ProductReviewPictureIds:
				return True
			else:
				return False

		if need_product_detail:
			cache_products = webapp_cache.get_webapp_products_detail(request.webapp_owner_id, totalProductIds)
			cache_productId2cache_products = dict([(product.id, product) for product in cache_products])

			# 对于每个订单
			for order in orders:
				products = []             # 订单的所有未评价商品, 或者有评价未晒图
				order_is_reviewed = True  # 订单是否评价完成
				# 对于订单的每件商品
				for orderHasProduct in orderId2orderHasProducts[order.id]:
					# 如果商品有评价
					product_review = orderHasProductId2ProductReviews.get(orderHasProduct.id,False)
					product = copy.copy(cache_productId2cache_products[orderHasProduct.product_id]) #此处需要复制
					if product_review:
						product.has_review = True
						product_review_picture =  _product_review_has_picture(product_review)
						# 如果评价有晒图
						if product_review_picture:
							order_is_reviewed = order_is_reviewed & True
						# 评价无晒图
						else:
							order_is_reviewed = order_is_reviewed & False
							product.order_has_product_id = orderHasProduct.id
							product.has_picture = False
							product.fill_specific_model(
								orderHasProduct.product_model_name, cache_productId2cache_products[product.id].models)
							product.product_model_name = product.custom_model_properties
							products.append(product)
					# 商品无评价
					else:
						order_is_reviewed = order_is_reviewed & False
						product.order_has_product_id = orderHasProduct.id
						product.has_review = False
						product.fill_specific_model(
							orderHasProduct.product_model_name, cache_productId2cache_products[product.id].models)
						product.product_model_name = product.custom_model_properties

						products.append(product)

					product.order_product_model_name = orderHasProduct.product_model_name

				order.products = products
				order.order_is_reviewed = order_is_reviewed
		else:
			##############################################################################
			for order in orders:

				order_is_reviewed = True  # 订单是否评价完成
				# 对于订单的每件商品
				for orderHasProduct in orderId2orderHasProducts[order.id]:
					# 如果商品有评价
					product_review = orderHasProductId2ProductReviews.get(orderHasProduct.id,False)
					# product = dict() #此处需要复制
					if product_review:

						product_review_picture =  _product_review_has_picture(product_review)
						# 如果评价有晒图
						if product_review_picture:
							order_is_reviewed = order_is_reviewed & True
						# 评价无晒图
						else:
							order_is_reviewed = order_is_reviewed & False

					# 商品无评价
					else:
						order_is_reviewed = order_is_reviewed & False
				order.order_is_reviewed = order_is_reviewed

		return orders



	@staticmethod
	def get_review_status(request):
		"""
		得到个人中心待评价列表的状态，
		如果所有订单已完成晒图， 返回True
		否则返回 False
		"""
		# 得到个人中心的所用订单
		#orders = request_util._get_order_review_list(request)
		orders = AReview._get_order_review_list(request)
		# 如果订单都已经完成晒图
		result = True
		for order in orders:
			result = result & order.order_is_reviewed
		return result


	@param_required(['woid', 'order_id', 'product_id', 'order_has_product_id'])
	def put(args):
		"""
		创建评论

		@param order_id
		@param product_id
		@param order_has_product_id
		@param [IN] send_time
		@param [IN] detail_time
		"""
		picture_list = args.get('picture_list')

		# 从`webapp/modules/mall/request_api_utils.py:create_product_review()`中迁移
		# 规格化所需数据
		#owner_id = int(request.webapp_owner_id)
		webapp_owner = args['webapp_owner']
		webapp_user = args['webapp_user']
		owner_id = webapp_user.id
		order_id = args['order_id']
		#member_id = int(request.member.id)
		member = webapp_user.member
		member_id = member.id
		product_id = int(args['product_id'])
		order_has_product_id = int(args['order_has_product_id'])

		send_time = args.get('send_time', None)
		# 原来是`detal_time`(by Victor)
		detail_time = args.get('detail_time', None)

		#request_length = request.META['CONTENT_LENGTH']

		if send_time and detail_time:
			send_time = float(send_time)
			detail_time = float(detail_time)
			send_time = send_time + detail_time
			total_seconds =  time.time() - send_time
			logging.info(u"order_has_product_id: %d, request time: %d, response time: %d, total_seconds: %d, total_size: %dkb" %
							(order_has_product_id, float(send_time), time.time(), total_seconds, int(request_length)//1024),
					  type="mall",
					  user_id=int(webapp_owner.id))

		data_dict = args
		product_score = data_dict.get('product_score', None)
		review_detail = data_dict.get('review_detail', None)
		serve_score = data_dict.get('serve_score', None)
		deliver_score = data_dict.get('deliver_score', None)
		process_score = data_dict.get('process_score', None)
		picture_list = data_dict.get('picture_list', None)
		#创建订单评论
		"""
		order_review, created = mall_models.OrderReview.objects.get_or_create(
			order_id=order_id,
			owner_id=owner_id,
			member_id=member_id,
			serve_score=serve_score,
			deliver_score=deliver_score,
			process_score=process_score)
		"""
		# 由业务模型创建review
		order_review = OrderReview.create(order_id, owner_id, member_id, serve_score, deliver_score, process_score)	

		# 创建商品评论
		product_view = ProductReview.create(order_id, owner_id, product_id, order_review, review_detail, product_score, member_id, order_has_product_id, picture_list)

		#response = create_response(200)
		#response.data = get_review_status(request)
		data = AReview.get_review_status(args)
		"""
		if picture_list:
			for picture in list(eval(picture_list)):
				mall_models.ProductReviewPicture(
					product_review=product_review,
					order_has_product_id=order_has_product_id,
					att_url=picture
				).save()
				watchdog_info(u"create_product_review after save img  %s" %\
					(picture), type="mall", user_id=request.webapp_owner_id)

			watchdog_info(u"create_product_review end, order_has_product_id is %s" %\
				(order_has_product_id), type="mall", user_id=owner_id)
		"""
		#return response.get_response()
		return data

	@param_required([])
	def get(args):
		"""
		获得评论信息
		"""
		return {
		}