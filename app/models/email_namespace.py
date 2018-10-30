from lumavate_service_util import make_id
from flask import g
from app import db

class EmailNamespace(db.Model):
  id = db.Column(db.BigInteger, primary_key=True)
  email_id = db.Column(db.BigInteger, db.ForeignKey('email.id'))
  namespace = db.Column(db.String(250), nullable=False)
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
      'id': make_id(self.id, self.__class__),
      'email': self.name,
      'createdAt': self.created_at,
      'lastModifiedAt': self.last_modified_at
    }
