from flask_login import UserMixin


class User(UserMixin):
  def __init__(self, email, first_name, last_name, password, role):
    self.id = email
    self.email = email
    self.first_name = first_name
    self.last_name = last_name
    self.password = password
    self.role = role