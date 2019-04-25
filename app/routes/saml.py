from lumavate_service_util import lumavate_route, SecurityType, RequestType
from flask import request, render_template, g
from behavior import Saml, GroupEmail, Group, SamlSecurityAssertion

@lumavate_route('/discover/auth-groups', ['GET'], RequestType.system, [SecurityType.jwt])
def auth_groups():
  return Saml().auth_groups()

@lumavate_route('/discover/properties', ['GET'], RequestType.system, [SecurityType.jwt])
def properties():
  return Saml().properties(integration_cloud=g.integration_cloud, url_ref=g.widget_type)

@lumavate_route('/', ['GET'], RequestType.page, [SecurityType.jwt])
def root():
  return render_template('home.html', logo='/{}/{}/discover/icons/microservice.png'.format(g.integration_cloud, g.widget_type))

@lumavate_route('/login', ['GET'], RequestType.page, [SecurityType.jwt])
def login():
  return Saml().login()

@lumavate_route('/sso', ['GET', 'POST'], RequestType.page, [SecurityType.jwt, SecurityType.none])
def sso():
  if request.method == 'GET':
    return Saml().login()
  else:
    return Saml().sso()

@lumavate_route('/batch', ['GET', 'POST'], RequestType.api, [SecurityType.sut, SecurityType.signed])
def batch():
  SamlSecurityAssertion().assert_has_role('admin')
  if request.method == 'POST':
    return Saml().batch_post()
  else:
    return Saml().batch_get()

@lumavate_route('/batch-delete', ['POST'], RequestType.api, [SecurityType.sut, SecurityType.signed])
def batch_delete():
  SamlSecurityAssertion().assert_has_role('admin')
  return Saml().batch_delete()

@lumavate_route('/status', ['POST', 'GET'], RequestType.api, [SecurityType.jwt])
def status():
  return Saml().status()

@lumavate_route('/showstatus', ['GET'], RequestType.page, [SecurityType.jwt])
def show_status():
  return Saml().show_status()

@lumavate_route('/logout', ['GET'], RequestType.api, [SecurityType.sut, SecurityType.signed])
def logout():
  return Saml().logout()

@lumavate_route('/groups', ['GET'], RequestType.api, [SecurityType.signed])
def get_groups():
  return Group().get_collection()

@lumavate_route('/groups/<int:group>', ['GET'], RequestType.api, [SecurityType.signed])
def get_group_emails(group):
  return GroupEmail().get_group_emails(group)

@lumavate_route('/groups/<string:group>/<string:email>', ['POST', 'DELETE'], RequestType.api, [SecurityType.signed])
def manage_group(group, email):
  SamlSecurityAssertion().assert_has_role('admin')
  if request.method == 'POST':
    return GroupEmail().add_to_group(group, email)
  else:
    return GroupEmail().remove_from_group(group, email)
