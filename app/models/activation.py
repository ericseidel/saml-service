from flask import g
from app import db

class Activation(db.Model):
  id = db.Column(db.BigInteger, primary_key=True)
  namespace = db.Column(db.String(250), nullable=False)
  activation_token = db.Column(db.String(2000), nullable=False)
  org_id = db.Column(db.BigInteger)
  created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
  last_modified_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
