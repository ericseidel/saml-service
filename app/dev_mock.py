from flask import g
from lumavate_properties import Properties, Components
from lumavate_service_util import LumavateMockRequest, set_lumavate_request_factory, DevMock
from lumavate_token import AuthToken
from behavior import Saml
from app import db
import json
import time
import os

class DevMock(DevMock):
  def get_auth_token(self):
    t = super().get_auth_token()
    t.auth_url = 'http://{}:5005/ic/saml/'.format(os.environ.get('DOCKER_IP'))
    t.session = 'abc123'
    t.company_id = 1
    return t

  def get_session_data(self):
    email = 'j.lawrence@lumavate.com'
    ens = Saml().create_email_in_namespace(email)
    db.session.commit()
    userinfo = {
      'email': email,
      'session': 'abc123',
      'emailNamespaceId': ens.id,
      'sessionStart': time.time(),
    }
    sess_data = Saml().encrypt_user_info(userinfo)
    sess_data.update(super().get_session_data())
    return sess_data

  def bootstrap_context(self):
    super().bootstrap_context()
    g.service_data = {'adminRole': ['Super Admins']}

  def get_property_data(self):
    sd = super().get_property_data()
    sd = sd.set_property('loginPageLink', {'url': 'https://google.com'})
    sd = sd.set_property('adminRole', ['Super Admins'])
    sd = sd.append_component(
      'authGroups', 'samlPatternGroup',
      {
        'title': 'Super Admins',
        'emails': 'j.lawrence@lumavate.com'
      }
    )
    return sd

  def get_auth_data(self):
    return {
      'roles': [
        'Super Admins'
      ],
      'status': 'active',
      'user': 'ic~saml!user!1'
    }

  def get_mock_func(self):
    return self.make_request

  def make_request(
      self,
      method,
      path,
      headers=None,
      payload=None,
      files=None,
      raw=False,
      timeout=None):
    if path.startswith('/pwa/v1/session'):
      return payload

    return None
