from flask import g, make_response
from app_factory import create_app
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import os

app = create_app()
db = SQLAlchemy(app)
rest_model_mapping = {}

from routes import *
from lumavate_service_util import icon_blueprint, lumavate_blueprint, CustomEncoder
app.json_encoder = CustomEncoder
app.register_blueprint(icon_blueprint)
app.register_blueprint(lumavate_blueprint)

from behavior import Group, GroupEmail
#rest_model_mapping['groups'] = Group()
#rest_model_mapping['group-emails'] = GroupEmail()

import lumavate_service_util

print('### - Random key for use in ENCRYPTION_PRIVATE_KEY: ' + Fernet.generate_key().decode(), flush=True)

@app.before_first_request
def init():
  if os.environ.get('DEV_MODE', 'False').lower() == 'true':
    import dev_mock
    from behavior import Saml
    dm = dev_mock.DevMock(Saml().properties)

if __name__ == '__main__':
  app.run(debug=True, host="0.0.0.0")
