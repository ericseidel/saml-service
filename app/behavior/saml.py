from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, session, url_for, Response
import requests
import json
import os
from app import db
from flask import session, abort
from lumavate_service_util import browser_response, api_response, get_lumavate_request, RestBehavior, make_id
from lumavate_properties import Properties, Components
import models
import uuid
import re
import time
from lumavate_exceptions import ValidationException, AuthorizationException, ApiException
from cryptography.fernet import Fernet
import random
import string
import csv
from io import StringIO
from .saml_security_assertion import SamlSecurityAssertion

from saml2 import (
    BINDING_HTTP_POST,
    BINDING_HTTP_REDIRECT,
    entity,
)
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
import requests

class Saml(RestBehavior):
  def __init__(self):
    super().__init__(models.Email)

  def get_encryption_private_key(self):
    return os.getenv('ENCRYPTION_PRIVATE_KEY', 'yNokwIVf-z3zaYtqg6ywM2cmKUmIleUwzxLG8qz2k7Y=').encode('utf-8')

  def get_max_session_duration(self):
    return g.service_data.get('sessionMaxDuration')

  def get_idp_name(self):
    return 'lumavate'

  def get_metadata(self):
    return g.service_data.get('samlMetadata')
    #return 'https://lumavate.okta.com/app/exk2di6ee63XMRAiv2p7/sso/saml/metadata'

  def get_entity_id(self):
    return g.service_data.get('samlEntityId')

  def get_service_provider_url(self):
    return g.service_data.get('samlServiceProviderUrl')

  def get_saml_client(self):
      acs_url = self.get_service_provider_url()
      https_acs_url = self.get_service_provider_url()

      settings = {
          "entityid" : self.get_entity_id(),
          'metadata': {
              'inline': [self.get_metadata()],
              },
          'service': {
              'sp': {
                  'endpoints': {
                      'assertion_consumer_service': [
                          (acs_url, BINDING_HTTP_REDIRECT),
                          (acs_url, BINDING_HTTP_POST),
                          (https_acs_url, BINDING_HTTP_REDIRECT),
                          (https_acs_url, BINDING_HTTP_POST)
                      ],
                  },
                  # Don't verify that the incoming requests originate from us via
                  # the built-in cache for authn request ids in pysaml2
                  'allow_unsolicited': True,
                  # Don't sign authn requests, since signed requests only make
                  # sense in a situation where you control both the SP and IdP
                  'authn_requests_signed': False,
                  'logout_requests_signed': True,
                  'want_assertions_signed': True,
                  'want_response_signed': False,
              },
          },
      }
      spConfig = Saml2Config()
      spConfig.load(settings)
      spConfig.allow_unknown_attributes = True
      saml_client = Saml2Client(config=spConfig)
      return saml_client

  def is_email_in_group(self, email, group):
    group_def = next((x for x in g.service_data.get('authGroups', []) if x['componentData']['title'] == group), None)
    if group_def and 'emails' in group_def['componentData']:
      pattern = group_def['componentData']['emails']
      if pattern is not None:
        for e in pattern.split(','):
          if re.match('^' + e.replace('.', '\.').replace('*', '.*').replace('-', '\-') + '$', email):
            return True

      return False
    if group_def and 'list' in group_def['componentData']:
      group_def = models.Group.get_all().filter_by(name=group_def['componentData']['list']).first()
      email_def = models.Email.get_all().filter_by(email=email).first()

      if group_def and email_def:
        if models.GroupEmail.get_all().filter_by(email_id=email_def.id, group_id=group_def.id).first() is not None:
          return True

    return False

  def login(self):
    saml_client = self.get_saml_client()
    reqid, info = saml_client.prepare_for_authenticate()

    redirect_url = None
    for key, value in info['headers']:
        if key is 'Location':
            redirect_url = value
    response = redirect(redirect_url, code=302)
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response

  def sso(self):
    saml_client = self.get_saml_client()
    authn_response = saml_client.parse_authn_request_response(
        request.form['SAMLResponse'],
        entity.BINDING_HTTP_POST)
    authn_response.get_identity()
    user_info = authn_response.get_subject()

    email = user_info.text
    userdata= {
      'subject': email,
      'ava': {}
    }

    for k in authn_response.ava:
      userdata['ava'][k] = authn_response.ava[k]
      if k.lower == 'email':
        email = authn_response.ava[k]

    ens = self.create_email_in_namespace(email)
    db.session.commit()

    userinfo = {
      'email': email,
      'session': g.token_data['session'],
      'emailNamespaceId': ens.id,
      'sessionStart': time.time(),
      'userdata': userdata
    }

    get_lumavate_request().put('/pwa/v1/session', self.encrypt_user_info(userinfo))

    if g.service_data.get('loginPageLink') is not None:
      return redirect(g.service_data.get('loginPageLink', {}).get('url'), 302)
    else:
      return redirect('https://' + request.host, 302)

  def create_email_in_namespace(self, email_address):
    email = models.Email.query \
        .filter_by(org_id=g.org_id) \
        .filter_by(email=email_address).first()
    if email is None:
      email = self.create_record(models.Email)
      email.email = email_address

    ens = models.EmailNamespace.query \
        .filter_by(org_id=g.org_id) \
        .filter_by(namespace=g.token_data.get('namespace')) \
        .filter_by(email_id=email.id).first()
    if ens is None:
      ens = self.create_record(models.EmailNamespace)
      ens.email_id = email.id
      ens.namespace = g.token_data.get('namespace')

    db.session.flush()
    return ens

  def encrypt_user_info(self, userinfo):
    cipher_suite = Fernet(self.get_encryption_private_key())
    return {
      os.environ.get('SERVICE_NAME'): cipher_suite.encrypt(json.dumps(userinfo).encode('utf-8')).decode()
    }

  def status_data(self):
    if os.environ.get('DEV_MODE', 'False').lower() == 'true':
      import dev_mock
      from behavior import Saml
      return jsonify(dev_mock.DevMock(self.properties).get_auth_data())

    data = g.session.get(os.environ.get('SERVICE_NAME'))
    if data is None:
      raise AuthorizationException('No Session')

    data = data.encode('utf-8')
    cipher_suite = Fernet(self.get_encryption_private_key())
    userinfo = json.loads(cipher_suite.decrypt(data).decode())

    ens = models.EmailNamespace.get(userinfo.get('emailNamespaceId'))
    if ens is None:
      raise AuthorizationException('No User')

    if time.time() - userinfo.get('sessionStart', 0) > self.get_max_session_duration():
      raise AuthorizationException('Old Session')

    roles = []
    for group in self.auth_groups():
      if self.is_email_in_group(userinfo['email'], group['name']):
        roles.append(group['name'])

    return {
        'user': make_id(ens.email_id, 'user'),
        'roles': roles,
        'status': 'active',
        'additionalData': userinfo.get('userdata')
    }

  def status(self):
    return self.status_data()

  def show_status(self):
    return jsonify(self.status_data())

  def logout(self):
    sess_data = {
      os.environ.get('SERVICE_NAME'): None
    }

    get_lumavate_request().put('/pwa/v1/session', sess_data)
    return {'status': 'Ok'}

  def batch_get(self):
    f = StringIO()
    writer = csv.writer(f)
    fields = ['email','id']

    writer.writerow(fields)
    rows = []
    for email in models.Email.get_all().all():
      rows.append([email.email, make_id(email.id, 'user')])

    writer.writerows(rows)
    response = Response(f.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = u'attachment; filename=example.csv'
    return response

  def batch_post(self):
    input = self.get_batch_import_content()

    group_mapping = {x.name : x.id for x in models.Group.get_all().all()}
    email_mapping = {}

    row_data = []
    values = {'org_id': g.org_id}
    param_ct = 1

    for row in input:
      if row['group'] not in group_mapping:
        group = models.Group()
        group.name = row['group']
        group.org_id = 1
        db.session.add(group)
        db.session.flush()
        group_mapping[group.name] = group.id

      if row['email'] not in email_mapping:
        email = models.Email.get_all().filter_by(email=row['email']).first()
        if email is None:
          email = models.Email()
          email.org_id = g.token_data.get('orgId')
          email.email = row['email']
          db.session.add(email)
          db.session.flush()

        email_mapping[email.email] = email.id

      email_parm = 'value{}'.format(param_ct)
      param_ct = param_ct + 1
      group_parm = 'value{}'.format(param_ct)
      param_ct = param_ct + 1
      values[email_parm] = email_mapping[row['email']]
      values[group_parm] = group_mapping[row['group']]
      row_data.append('select :{} as e, :{} as g\n'.format(email_parm, group_parm))

    s = ' union '.join(row_data)
    s = '''with insert_data as ({})
insert into group_email (email_id, group_id, org_id)
select e, g, :org_id from insert_data
  where not exists(select 1 from group_email as ge
    where ge.email_id = insert_data.e and ge.group_id = insert_data.g and ge.org_id = :org_id)'''.format(s)
    r = db.session.connection().execute(text(s).bindparams(**values))
    return {'recordsInserted': r.rowcount}

  def batch_delete(self):
    input = self.get_batch_import_content()

    group_mapping = {x.name : x.id for x in models.Group.get_all().all()}
    email_mapping = {}
    statements = []

    for row in input:
      if row['email'] not in email_mapping:
        email = models.Email.get_all().filter_by(email=row['email']).first()
        if email is None:
          email = models.Email()
          email.org_id = g.token_data.get('orgId')
          email.email = row['email']
          db.session.add(email)
          db.session.flush()

        email_mapping[email.email] = email.id

      if row['group'] not in group_mapping:
        pass
        #continue

      values = {
        'org':g.org_id,
        'email':email_mapping[row['email']],
        'group':group_mapping[row['group']]}

      statements.append(text('delete from group_email where org_id=:org and email_id=:email and group_id=:group').bindparams(**values))

    affected = 0
    for s in statements:
      affected += db.session.connection().execute(s).rowcount

    return {'recordsDeleted': affected}

  def auth_groups(self):
    groups = []
    for group in g.service_data.get('authGroups', []):
      groups.append({'name': group['componentData']['title']})

    return groups

  def __get_email_pattern_component(self):
    # Define a component for auth groups defined by a wildcard email pattern
    section = 'Email Pattern Settings'
    ht = '''
Defines what emails fall into this group.  Blank entry will match on no emails.  A wildcard '*'
can be used to match on a group of emails, and multiple patterns can be combined by
separating with a comma.

### Examples
```
*@domain.com = all addresses at domain.com

john@domain.com,bob@domain.com = only john@domain.com and bob@domain.com

*@domain.com,*@other-domain.com = everyone at either domain.com or other-domain.com

* = everybody
```
    '''
    pattern_props = [
      Properties.Property(None, section, 'title', 'Security Group Name', 'text'),
      Properties.Property(None, section, 'emails', 'Allowed Emails', 'text', help_text=ht)
    ]

    icon = 'https://{}{}discover/icons/email.svg'
    icon = icon.format(request.host, os.environ.get('WIDGET_URL_PREFIX'))
    c = Components.BaseComponent(
        'samlPatternGroup', # the unique component id
        'authenticationGroup',      # the class of components
        None,                       # section
        'Email Pattern',            # label
        None,                       # display name
        icon,                       # icon url
        pattern_props)              # properties

    c.icon_url = icon
    return c

  def __get_email_list_component(self):
    # Define a component for auth groups defined by a list of emails in the db

    groups = {x.name: x.name for x in models.Group.get_all().all()}

    section = 'Email List Settings'
    list_props = [
      Properties.Property(None, section, 'title', 'Security Group Name', 'text'),
      Properties.Property(None, section, 'list', 'List', 'dropdown', options=groups),
    ]

    icon = 'https://{}{}discover/icons/list.svg'
    icon = icon.format(request.host, os.environ.get('WIDGET_URL_PREFIX'))
    c = Components.BaseComponent(
        'samlListGroup', # the unique component id
        'authenticationGroup',   # the class of components
        None,                    # section
        'Email List',            # label
        None,                    # display name
        'icon-url',              # icon url
        list_props)              # properties

    c.icon_url = icon
    return c

  def __get_auth_groups(self):
    groups = []
    if g.token_data.get('authUrl') is not None:
      try:
        slug = '/'.join(g.token_data.get('authUrl').strip('/').split('/')[:2])
        auth_group_url = 'https://{}/{}/discover/auth-groups'
        groups = get_lumavate_request().get(auth_group_url.format(request.host, slug))
      except ApiException:
        pass

    return [{'value': x['name'], 'displayValue': x['name']} for x in groups]

  def properties(self, integration_cloud='ic', url_ref='email-auth'):
    c = Properties.ComponentPropertyType
    widget_props = []

    ################################
    # Authentication
    ################################
    widget_props.append(Properties.Property(
      'Authentication',
      'Authentication Settings',
      'authGroups',
      'Groups',
      'components',
      c.options([self.__get_email_pattern_component(), self.__get_email_list_component()]), []))

    ################################
    # Authentication
    ################################

    widget_props.append(Properties.Property(
      'Authorization',
      'Authorization Settings',
      'adminRole',
      'Email / Group Administration',
      'multiselect',
      options = SamlSecurityAssertion().get_all_auth_groups(),
      default=[]))

    ################################
    # SAML
    ################################
    widget_props.append(Properties.Property(
      'Advanced',
      'SAML Settings',
      'samlServiceProviderUrl',
      'Service Provider URL',
      'text',
      default='https://{}.{}{}sso'.format(g.token_data.get('namespace'), '.'.join(request.host.split('.')[1:]), os.environ.get('WIDGET_URL_PREFIX')),
      options={}))

    widget_props.append(Properties.Property(
      'Advanced',
      'SAML Settings',
      'samlEntityId',
      'Entity ID',
      'text',
      default='http://saml.example.com:saml/idp.xml',
      options={}))

    widget_props.append(Properties.Property(
      'Advanced',
      'SAML Settings',
      'samlMetadata',
      'Metadata',
      'text',
      default='',
      options={'rows': 5}))

    ################################
    # Session
    ################################
    ht = '''
The amount of time in seconds that a user can remain logged in to the experience
    '''
    widget_props.append(Properties.Property(
      'Advanced',
      'Session Settings',
      'sessionMaxDuration',
      'Session Max Duration (Seconds)',
      'numeric',
      default = 60 * 60 * 24 * 30,
      help_text=ht,
      options={'min': 0}))

    ht = '''
After successfully logging in, this setting will be direct the user to the appropriate
page.  If unset the user will be sent to teh home page.
    '''
    widget_props.append(Properties.Property(
      'Advanced',
      'Session Settings',
      'loginPageLink',
      'Login Page Link',
      'page-link',
      help_text=ht))

    ################################
    # Microservice Dependencies
    ################################
    ht = '''
If a profile service is present, it will be notified that a user logged in, and
the email address will be set automatically.
    '''

    widget_props.append(Properties.Property(
      'Advanced',
      'Microservice Dependencies',
      'profileServiceUri',
      'Profile Service Uri',
      'text',
      help_text=ht,
      default=''))

    return [x.to_json() for x in widget_props]
