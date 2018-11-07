from flask import g
from lumavate_service_util import SecurityAssertion

class SamlSecurityAssertion(SecurityAssertion):
  def load_rolemap(self):
    self._rolemap['admin'] = g.service_data.get('adminRole', [])
