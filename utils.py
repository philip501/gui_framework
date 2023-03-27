from typing import List


class Touch(object):
	def __init__(self):
		self.x = 0
		self.y = 0
		self.dpos = (0, 0)

	def updateDpos(self, dpos: List):
		self.dpos = dpos

	def updatePos(self, x, y):
		self.x = x
		self.y = y


class Delta(object):
	def __init__(self):
		self.x = 0
		self.y = 0

	def updateValues(self, x, y):
		self.x = x
		self.y = y


class RealWidget(object):
	"""
	This is a helper widget for storing real_pos and real_size when i dont want to create the whole widget. See
	base_layout.BaseWidget for more details on these two attributes.
	"""
	def __init__(self, real_pos: List, real_size: List):
		self.real_pos = real_pos
		self.real_size = real_size
