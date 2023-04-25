from gui_framework.base_layouts import BaseLayout
from gui_framework.advanced_layouts import GridLayout, RowLayout, CellWrapper
from gui_framework.utils import Touch

from time import time


# BASE

"""
A Design handles / stores the information flow across its layouts. For example when a certain widget is pressed,
this then blocks every other action.

IDEA:
Use TouchWidget.onTouchDown and .onTouchUp to decide on locking any further action.
"""

class BaseDesign(BaseLayout):
	sum_dpos = (0,0)
	mode = None
	layouts = []
	locked = False
	action = ''
	touched_layout = None
	time_down = 0
	is_double_tab = False
	is_moving = False
	double_tab_duration = 0.4
	move_cursor_duration = 0.5
	touch_margin = 20

	def on_touch_down(self, touch, *args):
		self.mode = None
		for layout in self.layouts:
			if layout.collideWidget(touch.x, touch.y):
				self.touched_layout = layout
				break
		t = time()
		if t - self.time_down < self.double_tab_duration:
			self.is_double_tab = True
		else:
			self.is_double_tab = False
		self.time_down = t
		self.sum_dpos = (0,0)
		self.is_moving = False
		self.locked = False
		if self.touched_layout:
			if self.touched_layout.onTouchDown(touch):
				self.locked = True

	def on_touch_move(self, touch, *args):
		self.sum_dpos = (self.sum_dpos[0] + touch.dpos[0], self.sum_dpos[1] + touch.dpos[1])

		if not self.is_moving:
			tm = self.touch_margin
			if self.sum_dpos[0] > tm or self.sum_dpos[0] < -tm or self.sum_dpos[1] > tm or self.sum_dpos[1] < -tm:
				my_touch = Touch()
				my_touch.updatePos(touch.x, touch.y)
				my_touch.updateDpos(self.sum_dpos)
				touch = my_touch
				if not self.mode:
					self.mode = 'moving'
				self.is_moving = True

		if self.mode == 'moving':
			if self.touched_layout:
				self.touched_layout.move(touch)

	def on_touch_up(self, touch, *args):
		return_from_touch = None
		if self.mode is None:
			if self.touched_layout:
				return_from_touch = self.touched_layout.onTouchUp(touch)
				if return_from_touch:
					self.locked = True
		else:
			self.touched_layout.clearTouch(touch)
		self.touched_layout = None
		return return_from_touch

	def addLayout(self, layout_index):
		"""
		so bissl wie addWidget

		~> vl noch design layouts oder so wo noch das 'design' attribute hinzugefügt wird?
		~> und dann übergibt man das mit
		"""
		pass


class LogsDesign(BaseDesign):
	pass


# PAGES


class Page(CellWrapper):
	pass

class PageLayout(RowLayout):
	pass

class PagesDesign(BaseDesign, GridLayout):
	current_page = None
	def switch_page(self):
		"""
		There will be a certain threshold of sum_dpos beyond which switch_page will be called. This condition is not
		implemented within switch_page itself, but the move / on_touch_move method.
		"""
		grid_index = self.current_page.get_data_index()
		direction = 1
		if abs(self.sum_dpos[0]) > abs(self.sum_dpos[1]):
			direction = 0
		new_index = grid_index[direction]
		if self.sum_dpos[direction] > 0:
			"""
			in case of y movment (direction=1) we want to move the index by -1
			in case of x movment (direction=0) we want to move the index by +1
			"""
			new_index -= 2 * direction - 1
		else:
			"""
			in case of y movment (direction=1) we want to move the index by +1
			in case of x movment (direction=0) we want to move the index by -1
			"""
			new_index += 2 * direction - 1
		if new_index < 0:
			return
		elif new_index >= self.grid_size[direction]:
			return

		grid_index[direction] = new_index
		self.swith_to_page(grid_index)

	def switch_to_page(self, page_index):
		page_data = self.data[page_index[0]]['init_data'][page_index[1]]
		# TODO
		# instatiate / load page
		# transition page
		# remove current_page
		# set current_page with new page



class FutureImplementation(PagesDesign):
	def initialise(self):
		"""
		pseudo code:

		while not "all data has a widget assigned to it":
			new layout
			while layout.real_size < design.frame_size:
				layout.fillInChildren

		Strategie:
			fill in vertical / horizontal, entsprechend pages vertical / horizontal erzeugen
			alle überschießenden data in next_data speichern
			dann horizontal / vertical weitergehen

		Also zur visuellen Erläuterung wenn man sich die pages wie ein (m,n) grid vorstellt, dann wird das grid zunächst
		(1,1) bis (m,1) befüllt, dann gehts mit (1,2) weiter bis dann (m,n) erreicht ist.

		~> ist die frage wie man das machen kann
		~> fillÍnChildren, reviewChildren mit if not fully fit to frame, dann sowas wie splitUpData
		"""
		pass

	def splitUpData(self):
		pass

	def reviewPage(self, layout):
		def reviewLayout(layout, widgets):
			try:
				layout.visible
			except AttributeError:
				widgets.append(layout)
				return

			for child in layout.visible:
				reviewLayout(child, widgets)

		widgets = []
		reviewLayout(layout, widgets)

		for widget in widgets:
			remove = False
			if widget.real_pos[0] < self.real_pos[0]:
				remove = True
			elif widget.real_pos[1] < self.real_pos[1]:
				remove = True
			elif widget.real_pos[0] + widget.real_size[0] > self.real_pos[0] + self.real_size[0]:
				remove = True
			elif widget.real_pos[1] + widget.real_size[1] > self.real_pos[1] + self.real_size[1]:
				remove = True
			if remove:
				widget.parent.removeWidget(widget)



if __name__ == '__main__':
	print("Testing the syntactically correctness.")
