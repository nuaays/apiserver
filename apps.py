# -*- coding: utf-8 -*-

import json
import decimal
from datetime import datetime, date

import falcon
from eaglet.core import api_resource
from core.exceptionutil import unicode_full_stack
from eaglet.core import watchdog
import settings
import wapi.resources
import wapi as wapi_resource
from eaglet.core.db import models

from business.model import Model as business_model

class ThingsResource:
	def on_get(self, req, resp):
		"""Handles GET requests"""
		resp.status = falcon.HTTP_200  # This is the default status
		resp.body = ('\nTwo things awe me most, the starry sky '
					 'above me and the moral law within me.\n'
					 '\n'
					 '    ~ Immanuel Kant Robert lalala\n\n')

class ApiListerResource:
	def on_get(self, req, resp):
		"""
		列出API
		"""
		api_list = []
		for (app_resource, resource_cls) in api_resource.APPRESOURCE2CLASS.items():
			app, resource = app_resource.split('-')
			api_cls = resource_cls['cls']
			api_info = {
				'app': app,
				'resource': resource,
				'class_name': str(api_cls),
				'explain': api_cls.__doc__.strip(),
				'methods': filter(lambda method: hasattr(api_cls, method), ['get', 'post', 'put', 'delete']),
			}
			api_list.append(api_info)
		resp.status = falcon.HTTP_200
		resp.body = json.dumps(api_list)
		return

def _default(obj):
	if isinstance(obj, datetime): 
		return obj.strftime('%Y-%m-%d %H:%M:%S') 
	elif isinstance(obj, date): 
		return obj.strftime('%Y-%m-%d') 
	elif isinstance(obj, decimal.Decimal):
		return str(obj)
	# elif settings.DEBUG and isinstance(obj, models.Model):
	# 	return obj.to_dict()
	# todo 删除
	elif isinstance(obj, business_model):
		return obj.to_dict()
	else: 
		raise TypeError('%r is not JSON serializable (type %s)' % (obj, type(obj)))

class FalconResource:
	def __init__(self):
		#self.app = app
		#self.resource = resource
		pass

	def call_wapi(self, method, app, resource, req, resp):		
		response = {
			"code": 200,
			"errMsg": "",
			"innerErrMsg": "",
		}
		resp.status = falcon.HTTP_200
		
		args = {}
		args.update(req.params)
		args.update(req.context)
		args['wapi_id'] = req.path + '_' + req.method

		try:
			raw_response = wapi_resource.wapi_call(method, app, resource, args, req)
			if type(raw_response) == tuple:
				response['code'] = raw_response[0]
				response['data'] = raw_response[1]
				if response['code'] != 200:
					response['errMsg'] = response['data']
					response['innerErrMsg'] = response['data']
			else:
				response['code'] = 200
				response['data'] = raw_response
		except wapi_resource.ApiNotExistError as e:
			response['code'] = 404
			response['errMsg'] = str(e).strip()
			response['innerErrMsg'] = unicode_full_stack()
			message = u"req:{}, error:{}".format(req.params, unicode_full_stack())
			watchdog.error(message)
			print '>>>>>>>>>>>>>error_message',message
		except Exception as e:
			response['code'] = 531 #不要改动这个code，531是表明apiserver内部发生异常的返回码
			response['errMsg'] = str(e).strip()
			response['innerErrMsg'] = unicode_full_stack()
			message = u"req:{}, error:{}".format(req.params, unicode_full_stack())
			watchdog.error(message)
			print '>>>>>>>>>>>>>error_message',message

		resp.body = json.dumps(response, default=_default)

	def on_get(self, req, resp, app, resource):
		self.call_wapi('get', app, resource, req, resp)

	def on_post(self, req, resp, app, resource):
		_method = req.params.get('_method', 'post')
		self.call_wapi(_method, app, resource, req, resp)


def create_app():
	#添加middleware
	middlewares = []
	for middleware in settings.MIDDLEWARES:
		items = middleware.split('.')
		module_path = '.'.join(items[:-1])
		module_name = items[-1]
		module = __import__(module_path, {}, {}, ['*',])
		klass = getattr(module, module_name, None)
		if klass:
			print 'load middleware %s' % middleware
			middlewares.append(klass())
		else:
			print '[ERROR]: invalid middleware %s' % middleware

	falcon_app = falcon.API(middleware=middlewares)

	#for (app_resource, resource_cls) in api_resource.APPRESOURCE2CLASS.items():
	#	app, resource = app_resource.split('-')
	#	print("registered API: /wapi/%s/%s/" % (app, resource))

	#handle_cls = 
	# 注册到Falcon
	falcon_app.add_route('/wapi/{app}/{resource}/', FalconResource())

	if settings.DEBUG:
		from core.dev_resource import api_console_resource
		falcon_app.add_route('/console/', api_console_resource.ApiConsoleResource())

		from core.dev_resource import static_resource
		falcon_app.add_sink(static_resource.serve_static_resource, '/static/')

	# things will handle all requests to the '/things' URL path
	# Resources are represented by long-lived class instances
	falcon_app.add_route('/things', ThingsResource())

	# WAPI内部指令
	falcon_app.add_route('/__cmd/apilist/', ApiListerResource())

	return falcon_app

