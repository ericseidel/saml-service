from flask import g
from app import db
import os

class Email(db.Model):
  id = db.Column(db.BigInteger, primary_key=True)
  email = db.Column(db.String(250), nullable=False)
  org_id = db.Column(db.BigInteger)
  created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
  last_modified_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

  @classmethod
  def get_all(cls):
    return cls.query.filter_by(org_id = g.org_id)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  def to_json(self):
    return {
      'id': os.environ.get('WIDGET_URL_PREFIX').strip('/').replace('/', '~') + '|user|' + str(self.id),
      'email': self.email,
      'createdAt': self.created_at,
      'lastModifiedAt': self.last_modified_at
    }
