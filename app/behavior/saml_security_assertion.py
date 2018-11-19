from flask import g
from lumavate_service_util import SecurityAssertion

class SamlSecurityAssertion(SecurityAssertion):
  def load_rolemap(self):
    self._rolemap['admin'] = g.service_data.get('adminRole', [])

  def get_all_auth_groups(self):
    try:
      from .saml import Saml
      auth_groups = Saml().auth_groups()
    except Exception as e:
      print(e, flush=True)
      auth_groups = []

    auth_groups = [{'value': x['name'], 'displayValue': x['name']} for x in auth_groups]
    auth_groups.append({'value': '__all__', 'displayValue': 'All Users'})

    return auth_groups
