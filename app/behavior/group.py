from lumavate_service_util import RestBehavior
import models

class Group(RestBehavior):
  def __init__(self):
    super().__init__(models.Group)
