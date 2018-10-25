from flask import g
from sqlalchemy.orm import backref
from app import db
import os

class GroupEmail(db.Model):
  id = db.Column(db.BigInteger, primary_key=True)
  email_id = db.Column(db.BigInteger, db.ForeignKey('email.id'))
  group_id = db.Column(db.BigInteger, db.ForeignKey('group.id'))
  org_id = db.Column(db.BigInteger)
  created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
  last_modified_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

  _email = db.relationship('Email', backref=backref('group_email', cascade='all, delete-orphan'))
  _group = db.relationship('Group', backref=backref('group_email', cascade='all, delete-orphan'))

  @classmethod
  def get_all(cls):
    return cls.query.filter_by(org_id = g.org_id)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  def to_json(self):
    return {
      'id': self.id,
      'email': self._email.email if self._email else None,
      'userId': os.environ.get('WIDGET_URL_PREFIX').strip('/').replace('/', '~') + '|user|' + str(self.email_id),
      'group': self._group.name if self._group else None,
      'createdAt': self.created_at,
      'lastModifiedAt': self.last_modified_at
    }
