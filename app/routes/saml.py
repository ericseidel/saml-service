from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, send_from_directory
import requests
import json
import os
from app import db
from flask import session, abort, request
from lumavate_service_util import browser_response, api_response, SecurityType
from lumavate_properties import Properties, Components
import models
import uuid
import re
from behavior import Saml, GroupEmail, Group

saml_blueprint = Blueprint('saml_blueprint', __name__)

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/', methods=['GET'])
@browser_response
def root(integration_cloud, widget_type):
  return render_template('home.html', logo='/{}/{}/discover/icons/microservice.png'.format(integration_cloud, widget_type))

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/renew', methods=['GET'])
@browser_response
def renew(integration_cloud, widget_type):
  return Saml().renew_token()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/login', methods=['GET'])
@browser_response
def login(integration_cloud, widget_type):
  return Saml().login()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/sso', methods=['POST', 'GET'])
@browser_response
def sso(integration_cloud, widget_type):
  if request.method == 'GET':
    return Saml().login()
  else:
    return Saml().sso()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/batch', methods=['POST', 'GET'])
@api_response(SecurityType.browser_origin)
def batch(integration_cloud, widget_type):
  if request.method == 'POST':
    return Saml().batch_post()
  else:
    return Saml().batch_get()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/batch-delete', methods=['POST'])
@api_response(SecurityType.browser_origin)
def batch_delete(integration_cloud, widget_type):
  return Saml().batch_delete()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/status', methods=['GET'])
@api_response(SecurityType.browser_origin)
def status(integration_cloud, widget_type):
  return Saml().status()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/showstatus', methods=['GET'])
@browser_response
def show_status(integration_cloud, widget_type):
  return Saml().show_status()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/logout', methods=['POST'])
@api_response(SecurityType.api_origin)
def logout(integration_cloud, widget_type):
  return Saml().logout()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/discover/auth-groups', methods=['GET'])
@api_response(SecurityType.system_origin)
def auth_groups(integration_cloud, widget_type):
  return Saml().auth_groups()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/discover/properties', methods=['GET'])
@api_response(SecurityType.system_origin)
def properties(integration_cloud, widget_type):
  return Saml().properties(integration_cloud=integration_cloud, url_ref=widget_type)

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/groups', methods=['GET'])
@api_response(SecurityType.api_origin)
def get_groups(integration_cloud, widget_type):
  return Group().get_collection()

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/emails/<string:email>', methods=['GET'])
@api_response(SecurityType.api_origin)
def get_email(integration_cloud, widget_type, email):
  return

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/groups/<string:group>', methods=['GET'])
@api_response(SecurityType.api_origin)
def get_group_emails(integration_cloud, widget_type, group):
  return GroupEmail().get_group_emails(group)

@saml_blueprint.route('/<string:integration_cloud>/<string:widget_type>/groups/<string:group>/<string:email>', methods=['POST', 'DELETE'])
@api_response(SecurityType.api_origin)
def manage_group(integration_cloud, widget_type, group, email):
  if request.method.lower() == 'post':
    return GroupEmail().add_to_group(group, email)
  else:
    return GroupEmail().remove_from_group(group, email)
