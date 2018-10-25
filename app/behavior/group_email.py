from flask import request, g
from lumavate_exceptions import ValidationException
from lumavate_service_util import RestBehavior
import models
from app import db

class GroupEmail(RestBehavior):
  def __init__(self):
    super().__init__(models.GroupEmail)

  def get_group_emails(self, group_name):
    group = models.Group.get_all().filter_by(name=group_name).first()
    if group is None:
      return None

    return models.GroupEmail.get_all().filter_by(group_id=group.id)

  def add_to_group(self, group_name, email_address):
    group = models.Group.get_all().filter_by(name=group_name).first()
    if group is None:
      group = models.Group()
      group.name = group_name
      group.org_id = 1
      db.session.add(group)

    email = models.Email.get_all().filter_by(email=email_address).first()
    if email is None:
      email = models.Email()
      email.org_id = g.token_data.get('orgId')
      email.email = email_address
      db.session.add(email)

    rec = models.GroupEmail.get_all().filter_by(email_id=email.id, group_id=group.id).first()
    if rec is None:
      rec = self.create_record(models.GroupEmail)
      rec.email_id = email.id
      rec.group_id = group.id
      db.session.flush()

    return rec

  def remove_from_group(self, group_name, email_address):
    group = models.Group.get_all().filter_by(name=group_name).first()
    if group is None:
      return None

    email = models.Email.get_all().filter_by(email=email_address).first()
    if email is None:
      return None

    rec = models.GroupEmail.get_all().filter_by(email_id=email.id, group_id=group.id).first()
    if rec is not None:
      r = rec.to_json()
      db.session.delete(rec)
      db.session.flush()
      return rec

    return None
