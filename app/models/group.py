from lumavate_service_util import make_id
from flask import g
from app import db

class Group(db.Model):
  id = db.Column(db.BigInteger, primary_key=True)
  name = db.Column(db.String(250), nullable=False)
  org_id = db.Column(db.BigInteger)

  @classmethod
  def get_all(cls):
    return cls.query.filter_by(org_id = g.org_id)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  def to_json(self):
    return {
      'id': make_id(self.id, self.__class__),
      'name': self.name
    }
