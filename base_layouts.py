from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty, ObjectProperty, NumericProperty, BooleanProperty, StringProperty

from gui_framework.utils import Touch

import inspect


"""
NOTE: Base layouts cannot be used as children for nested layouts. For further information as to why, see comment in
advanced_layouts.
"""

DEFAULT_SIZE = 10

class BaseAttributes(object):
	padding: tuple = (0,0,0,0)


class BaseWidget(Widget, BaseAttributes):
	"""
	NOTE: is_bottom_widget is needed since kivy children will be defined in .kv file and dont have an updatePos method
	~> this implicates that every child is either a BaseWidget or a kivy widget
	"""
	real_pos: ListProperty = ListProperty((0,0))
	real_size: ListProperty = ListProperty((DEFAULT_SIZE,DEFAULT_SIZE))
	is_bottom_widget = False
	def updatePos(self, delta):
		self.real_pos = [self.real_pos[0] + delta[0], self.real_pos[1] + delta[1]]
		if not self.is_bottom_widget:
			for child in self.children:
				child.updatePos(delta)

	def updateSize(self, real_size):
		"""
		This method is needed for nested layouts, when you want to propagate the new size to its children. This needs to
		be done by the user though, there is no common logic for that.
		"""
		self.real_size = real_size

	def setPos(self, real_pos):
		delta = [real_pos[0] - self.real_pos[0], real_pos[1] - self.real_pos[1]]
		self.updatePos(delta)

	def to_data(self) -> dict:
		"""
		We HAVE to pass real_size to data. Apperently ListProperty is not subscriptable like that (on class level) but
		somehow gets "resolved" when instantiated.
		"""
		return {'child_type': type(self), 'init_data': {'real_size': self.real_size}}


class AnchorWidget(BaseWidget):
	"""
	NOTE: the purpose of this class is if a non bottom widget wants to add kivy widget to it
	"""
	def __init__(self, **kwargs):
		super(AnchorWidget, self).__init__(**kwargs)
		self.is_bottom_widget = True


class TouchWidget(BaseWidget):
	"""
	NOTE: In the current implementation all touches gets orchestrated by a Design. The touches will then be propagated
	further down the hierarchy and the information on locking further actions (return True) will be returned further up
	the hierarchy. We therefore do not implement onTouchDown and onTouchUp beyond returning False.
	"""
	def collideWidget(self, x, y):
		if self.x < x < self.x + self.real_size[0] and self.y < y < self.y + self.real_size[1]:
			return True
		return False

	def onTouchDown(self, touch):
		return False

	def onTouchUp(self, touch):
		"""
		NOTE: When implementing this method, you might want to check collideWidget before any further actions. A Design
		remembers the touched widget and calls .onTouchUp for this widget.
		"""
		return False

# BASE

"""
Changelog:

0.1 The following BASE layouts used to only work (properly) if their children are all of the same type. The code was
refactored for a more general purpose.

All the layouts were only suitable when widgets with the same height are added to them (in a vertical order). For this
purpose we refactored BaseLayout.data such that its elements follow the type hint
{'child_type': BaseChild, 'kwargs': dict} (used to be only a dictionary containing the kwargs).

0.2 For ZoomLayout we needed the possibility to include resize_factor in the conditions for removing / adding widgets
when moving. For this purpose we added the methods data_first, condition_second, condition_penultimate.

0.3 With the possibility of having children of different type and the desire to support nested layouts (grid, ...),
there arises the "problem" of keeping widgets that are far off the current screen due to the second / penultimate child
being of large size. For this purpose (the desire is to remove first / last children in such a case) we introduce a
margin attribute - ScrollLayout.visibility_margin.

0.3.1 This new attribute visibility_margin is now optional (default 'None').

0.3.2 Introducing visibility_margin_min (and renaming the other to visibility_margin_max) for the case if there are
small filler / separatopm widgets between large ones that need some time to load, potentially taking so much time that
they pop up on screen when they should have already been there.

0.3.3 Removing those margin stuffs from BASE layouts, wasnt quite sure about them. Moving them to MARGIN layouts.

0.4 Refactoring code for margins, added / renamed methods such condition_first_second, ...

0.4.1 Refactored ScrollLayout.move, no need for second_child and penultimate child any more. All done with first_child
and last_child respectively.
0.4.2 In accordance, no more need for visibility_margin_max. Renaming visibility_margin_min to visibility_margin. It is
now optional with default 'None'.
~> compare 0.3.1

0.5 Refactor for GridLayout, move visible from ScrollLayout to BaseLayout, made naming in data more suitable for nested
layouts

0.6 Refactoring. Make MoveLayout the base one and ScollLayout the special one.

0.7 Refactoring for nested layouts

0.7.1 MoveLayout contains the basic logic, vertical specific moved to VerticalLayout, horizontal equivalent is
implemented in HorizontalLayout; lots of refactoring for this purpose.

0.8.0 Nested layouts can also be children. This means on initialising we need to implicitly call BaseLayout.__init__ and
BaseChild.__init__. Since i don't know what happens on calling Widget.__init__ twice, I decided to move BaseChild to an
object class and put a ChildWidget class on top of it, taking its original place.

0.9.0 "ListProperty not subscriptable": for this reason we cannot use child_type.real_size and therefore store this
value in 'init_data'.

0.11.0 moved fillInFromScratch to base layouts
"""

"""
NOTES:

0.4 ScollLayout.condition_second and .condition_penultimate where originally used for second_child and penultimate_child
in .move method. Now only used for first_child and last_child respectively. The naming might be a bit confusing now but
you can think of it as the first becoming the second child if the condition is met, and the last becoming the
penultimate, respectively.

0.6 MoveLayout is the new base class on top of BaseLayout. It contains most of the needed logic for moving, adding,
removing, filling in, reviewing children. The specific criteria (delta_first, ...) and additionalKwargs* need to be
implemented in the classes that inherit from MoveLayout, MoveLayout only has dummy versions of those.

0.11.0 MoveLayout.fillInFromScratch is not used in other base methods as of yet, but is applicable to base layouts.


NOTES for TESTING:

Probably all conditions need to be tested, if they work as intended (and not the other way round).
"""

"""
Base classes should not be used directly.
"""

class BaseChild(object):
	def __init__(self, data_index=0):
		self.data_index = data_index

	def updateIndex(self, data_index):
		self.data_index = data_index

	def incrementIndex(self):
		self.data_index += 1

	def decrementIndex(self):
		self.data_index -= 1

class ChildWidget(BaseWidget, BaseChild):
	def __init__(self, data_index, **kwargs):
		BaseWidget.__init__(self, **kwargs)
		BaseChild.__init__(self, data_index)
		self.is_bottom_widget = True

"""
BaseLayout should not even be inherited from directly
"""

class BaseLayout(TouchWidget):
	"""
	An element of data looks like this:
		{'child_type': ChildWidget, 'init_data', dict}
	"""
	data: list[dict] = []
	visible: list = []
	mode: str = ''
	disable_touch: bool = False
	def __init__(self, data=[], **kwargs):
		super(BaseLayout, self).__init__(**kwargs)
		self.data = data

		# setting visible to empty list is apparently necessary; otherwise it gets treated as a class variable and is
		# shared across all instances, insertions will then affect all instances - very bad for nested layouts.
		self.visible = []

	def updateDataFromChild(self, child_widget):
		data_index = child_widget.data_index
		raw_data = child_widget.to_data()
		self.data[data_index] = raw_data

	def formatData(self, init_data, child_type):
		raw_data = {'child_type': child_type, 'init_data': init_data}
		return raw_data

	def addData(self, data_index, data):
		self.data.insert(self.get_data_index(data_index), data)

	def removeData(self, data_index):
		self.data.pop(self.get_data_index(data_index))

	def get_data_index(self, data_index):
		if data_index < 0:
			d_index = data_index + len(self.data)
			if d_index < 0:
				data_index = 0
		elif data_index > len(self.data):
			data_index = len(self.data)
		return data_index

	def get_visible_index(self, data_index):
		if not self.visible:
			return 0

		first_index = self.visible[0].data_index
		last_index = self.visible[-1].data_index
		data_index = self.get_data_index(data_index)
		if data_index < first_index:
			visible_index = 0
		elif data_index > last_index:
			visible_index = len(self.visible)
		else:
			visible_index = data_index - first_index
		return visible_index

	def updateDataFromVisible(self):
		for child in self.visible:
			self.updateDataFromChild(child)

	def to_data(self):
		"""
		For layouts, their sizes are not fixed in general and can change over time. Hence, we safe real_size.
		"""
		self.updateDataFromVisible()
		raw_data = super(BaseLayout, self).to_data()
		raw_data['init_data']['data'] = self.data
		return raw_data


## MOVE

"""
NOTE FOR THE FUTURE:
Split up MoveLayout methods into data related and move related. Since these two areas kind of overlap and there is no
necessity to do so, they stay in the same class.
"""

class MoveLayout(BaseLayout):
	# TODO
	# visible leistet dasselbe wie children ??
	sum_dpos = (0,0)
	max_child_width = DEFAULT_SIZE
	max_child_height = DEFAULT_SIZE
	orientation = 'vertical'
	def create_child(self, child_type, data_index, init_data):
		"""
		There is customization needed for nested layouts, hence we encapsuled this one liner in a method.
		"""
		return child_type(data_index, **init_data)

	def additionalKwargsInsert(self, data_index):
		"""
		For layouts that inherit from this class, one will probably want to implement it with some 'real_pos' logic.

		return {'real_pos': ...}
		"""
		return {}

	def insertWidget(self, data_index):
		"""
		NOTE: reposition of children has to be done "manually" by calling the corresponding method after insertWidget
		"""
		# calculate real_pos for inserted widget
		additional_data = self.additionalKwargsInsert(data_index)

		# add widget
		self.addWidget(data_index, additional_data)

	def insertWidgetAndData(self, data_index, new_data, child_type: ChildWidget):
		insert_index = self.get_visible_index(data_index)
		for i in range(len(self.visible) - insert_index):
			self.visible[insert_index + i].incrementIndex()
		self.addData(data_index, self.formatData(new_data, child_type))
		self.insertWidget(data_index)

	def addWidget(self, data_index, additional_data):
		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		init_data = raw_data['init_data']
		child_type = raw_data['child_type']
		visible_index = self.get_visible_index(data_index)

		# add real_pos to raw_data
		init_data.update(additional_data)

		# create instance of added widget
		new_child = self.create_child(child_type, data_index, init_data)

		# add widget
		self.visible.insert(visible_index, new_child)
		self.add_widget(new_child, index=visible_index)

	def calculate_max_child_width(self):
		"""
		This method follows the idea that a layout is at a fixed position with a fixed size on the screen and that its
		children move within this frame. Due to the implementation of move the max width is not to be smaller than
		real_size[0].
		"""
		max_child_width = self.real_size[0]
		for child in self.visible:
			if child.real_size[0] > max_child_width:
				max_child_width = child.real_size[0]
		self.max_child_width = max_child_width

	def calculate_max_child_height(self):
		"""
		This method follows the idea that a layout is at a fixed position with a fixed size on the screen and that its
		children move within this frame. Due to the implementation of move the max height is not to be smaller than
		real_size[1].
		"""
		max_child_height = self.real_size[1]
		for child in self.visible:
			if child.real_size[1] > max_child_height:
				max_child_height = child.real_size[1]
		self.max_child_height = max_child_height

	def removeWidget(self, child_widget):
		self.updateDataFromChild(child_widget)
		self.deleteWidget(child_widget)

	def deleteWidget(self, child_widget):
		self.visible.remove(child_widget)
		self.remove_widget(child_widget)

	def removeWidgetAndData(self, child_widget):
		data_index = child_widget.data_index
		remove_index = self.get_visible_index(data_index)
		for i in range(len(self.visible) - remove_index):
			self.visible[remove_index + i].decrementIndex()
		self.deleteWidget(child_widget)
		self.removeData(data_index)

	def reviewChildren(self):
		remove_widgets = []
		real_pos = self.real_pos
		real_size = self.real_size
		for child in self.visible:
			if self.delta_first_condition(child):
				remove_widgets.append(child)
			elif self.delta_last_condition(child):
				remove_widgets.append(child)
		for child in remove_widgets:
			self.removeWidget(child)

	def createFirstHelperWidget(self):
		# TODO: raise NeedImplementationError ?
		return None

	def fillInDelta(self, delta, helper_child):
		# TODO: raise NeedImplementationError ?
		return None, None

	def fillInFromScratch(self):
		if not self.data:
			return

		"""
		Note that for nested layouts (we want the widgets to be created and fit with respect to the anchor frame) the
		anchor comes into play in the conditions and deltas. Therefore we dont need any anchor logic in here.
		"""

		helper_child = self.createFirstHelperWidget()
		delta = self.delta_first(helper_child)

		real_pos, data_index = self.fillInDelta(delta, helper_child)

		additional_data = self.additionalKwargsInsert(data_index)
		additional_data['real_pos'] = real_pos

		self.addWidget(data_index, additional_data)
		self.fillInChildren()

	def additionalKwargsFillFirst(self, data_index, reference_child):
		"""
		For layouts that inherit from this class, one will probably want to implement it with some 'real_pos' logic.

		return {'real_pos': ...}
		"""
		return {}

	def additionalKwargsFillLast(self, data_index, reference_child):
		"""
		For layouts that inherit from this class, one will probably want to implement it with some 'real_pos' logic.

		return {'real_pos': ...}
		"""
		return {}

	def fillInChildren(self):
		"""
		NOTE: after filling there is the posibility that the first child is still too low. the repositioning of all
		widgets needs to be called manually.

		NOTE: this method assumes that there are already children visible.

		NOTE: This method works for both vertical and horizontal layouts.
		"""
		real_pos = self.real_pos
		real_size = self.real_size

		# insert widget from first data entry if none are visible
		if not self.visible:
			if not self.data:
				return
			raw_data = self.data[0]
			self.insertWidget(0)

		# fill widgets from top
		first_child = self.visible[0]
		while self.delta_first_condition(first_child):
			data_index = first_child.data_index - 1
			if data_index < 0:
				break
			additional_data = self.additionalKwargsFillFirst(data_index, first_child)
			self.addWidget(data_index, additional_data)
			first_child = self.visible[0]

		# fill widgets from bottom
		last_child = self.visible[-1]
		print(last_child)
		print([data['child_type'] for data in self.data])
		while self.delta_last_condition(last_child):
			data_index = last_child.data_index + 1
			if data_index >= len(self.data):
				break
			additional_data = self.additionalKwargsFillLast(data_index, last_child)
			self.addWidget(data_index, additional_data)
			last_child = self.visible[-1]

	def repositionChildren(self, reference_widget, direction=1, delta=None):
		if not self.visible:
			return
		if not delta:
			# TODO: raise some error?
			return
		reposition_index = self.get_visible_index(reference_widget.data_index) + 1
		for i in range(len(self.visible) - reposition_index):
			self.visible[reposition_index + i].updatePos(delta)

	def insertAndReposition(self, data_index):
		"""
		NOTE: convenience method for insertWidget and subsequent repositionChildren
		"""
		self.insertWidget(data_index)
		child_index = self.get_visible_index(data_index)
		child_widget = self.visible[child_index]
		self.repositionForInsert(child_widget)

	def insertNewAndReposition(self, data_index, new_data, child_type: ChildWidget):
		"""
		NOTE: convenience method for insertWidgetAndData and subsequent repositionChildren
		"""
		self.insertWidgetAndData(data_index, new_data, child_type)
		child_index = self.get_visible_index(data_index)
		child_widget = self.visible[child_index]
		self.repositionForInsert(child_widget)

	def repositionForInsert(self, child_widget):
		pass

	def removeAndReposition(self, data_index):
		"""
		NOTE: convenience method for removeWidget and subsequent repositionChildren
		"""
		child_index = self.get_visible_index(data_index)
		child_widget = self.visible[child_index]
		self.repositionForRemove(child_widget)
		self.removeWidget(data_index)

	def repositionForRemove(self, child_widget):
		pass

	def fillAndReposition(self):
		# TODO: raise NeedImplementationError ?
		pass

	def delta_first(self, first_child):
		# TODO: raise NeedImplementationError ?
		return None

	def delta_first_condition(self, first_child):
		"""
		This condition indicates that the first child is far out of sight and needs to be removed.
		"""
		return self.delta_first(first_child) > 0

	def condition_first(self, first_child, delta):
		"""
		This condition indicates that the first child is about to be far out of sight due to movement and needs to be
		removed.
		"""
		return delta > self.delta_first(first_child)

	def delta_last(self, last_child):
		# TODO: raise NeedImplementationError ?
		return None

	def delta_last_condition(self, last_child):
		"""
		This condition indicates that the last child is far out of sight and needs to be removed.
		"""
		return self.delta_last(last_child) < 0

	def condition_last(self, last_child, delta):
		"""
		This condition indicates that the first child is about to be far out of sight due to movement and needs to be
		removed.
		"""
		return delta < self.delta_last(last_child)

	def delta_second(self, second_child):
		# TODO: raise NeedImplementationError ?
		return None

	def condition_second(self, second_child, delta):
		"""
		This condition indicates that the first child is still not in sight, therefore no widget needs to be added on
		top.

		The naming of that method might be confusing, but you can think of it as such: If the condition is not met, then
		the first child will become the second.
		"""
		return delta > self.delta_second(second_child)

	def delta_penultimate(self, penultimate_child):
		# TODO: raise NeedImplementationError ?
		return None

	def condition_penultimate(self, penultimate_child, delta):
		"""
		This condition indicates that the last child is still not in sight, therefore no widget needs to be added below.

		The naming of that method might be confusing, but you can think of it as such: If the condition is not met, then
		the last child will become the penultimate.
		"""
		return delta < self.delta_penultimate(penultimate_child)

	def inspectLast(self, delta):
		"""
		If last_child is out of sight, then remove it.
		"""
		last_child = self.visible[-1]
		if self.condition_last(last_child, delta):
			self.removeWidget(last_child)

	def inspectSecond(self, delta):
		"""
		If first_child is in sight, add the previous from data
		"""
		first_child = self.visible[0]
		if not self.condition_second(first_child, delta):
			if first_child.data_index > 0:
				first_index = first_child.data_index - 1
				additional_data = self.additionalKwargsFillFirst(first_index, first_child)
				self.addWidget(first_index, additional_data)

	def inspectLastSecond(self, delta):
		"""
		NOTE: convenience method for inspectLast and inspectSecond
		"""
		self.inspectSecond(delta)
		self.inspectLast(delta)

	def inspectFirst(self, delta):
		"""
		if first_child is out of sight, then remove it
		"""
		first_child = self.visible[0]
		if self.condition_first(first_child, delta):
			self.removeWidget(first_child)

	def inspectPenultimate(self, delta):
		"""
		if last_child is in sight, add the next from data
		"""
		last_child = self.visible[-1]
		if not self.condition_penultimate(last_child, delta):
			if last_child.data_index + 1 < len(self.data):
				last_index = last_child.data_index + 1
				additional_data = self.additionalKwargsFillLast(last_index, last_child)
				self.addWidget(last_index, additional_data)

	def inspectFirstPenultimate(self, delta):
		"""
		NOTE: convenience method for inspectFirst and inspectPenultimate
		"""
		self.inspectPenultimate(delta)
		self.inspectFirst(delta)

	def check_delta_top(self, first_child):
		return (self.real_pos[1] + self.real_size[1]) - (first_child.real_pos[1] + first_child.real_size[1])

	def check_delta_bottom(self, last_child):
		return self.real_pos[1] - last_child.real_pos[1]

	def check_delta_left(self, first_child):
		return self.real_pos[0] - first_child.real_pos[0]

	def check_delta_right(self, last_child):
		return (self.real_pos[0] + self.real_size[0]) - (last_child.real_pos[0] + last_child.real_size[0])

	def checkDelta(self, delta_x, delta_y):
		return delta_x, delta_y

	def inspect(self, delta_x, delta_y):
		# TODO: raise NeedImplementationError ?
		pass

	def move(self, touch):
		# TODO
		"""
		The logic does not seem to be right at the moment. I think we need to introduce an option in condition_second
		and condition_penultimate to differentiate between '>' and '<' and use those for deciding whether to add a
		widget or not. The current way of doing that (those 'else' clauses) needs to be restructured.

		=> no need for such an option, simple use 'not' condition.

		~> definitely needs to be tested!!!
		"""
		if not self.visible:
			return

		delta_x, delta_y = touch.dpos

		delta_x, delta_y = self.checkDelta(delta_x, delta_y)
		self.inspect(delta_x, delta_y)

		for child in self.visible:
			child.updatePos([delta_x, delta_y])

		# we need to return delta_x, delta_y for nested layouts
		return delta_x, delta_y


## ORIENTATION

"""
The 'orientation' is only referring to the children alignment within the layout, and not to the moving direction. For
vertical movement only, you wanna take a look at ScrollLayout.
"""


class VerticalLayout(MoveLayout):
	def additionalKwargsInsert(self, data_index):
		"""
		Since children are not of the same type necessarily, the ypos of the inserted widget is the reference_pos[1] of
		the current widget at that position minus their difference of real_size[1]. We store real_size in data, hence we
		get it from there.
		"""
		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		child_type = raw_data['child_type']

		# NOTE: real_size has to be set in init_data
		real_size = raw_data['init_data']['real_size']

		visible_index = self.get_visible_index(data_index)
		if not self.visible:
			real_pos = [self.real_pos[0], self.real_pos[1] + self.real_size[1] - real_size[1]]
		elif visible_index < len(self.visible):
			reference_pos = self.visible[visible_index].real_pos
			reference_size = self.visible[visible_index].real_size
			real_pos = [reference_pos[0], reference_pos[1] - (real_size[1] - reference_size[1])]
		else:
			reference_pos = self.visible[visible_index - 1].real_pos
			real_pos = [reference_pos[0], reference_pos[1] - real_size[1]]
		return {'real_pos': real_pos}

	def addWidget(self, data_index, additional_data):
		super(VerticalLayout, self).addWidget(data_index, additional_data)
		new_child = self.visible[self.get_visible_index(data_index)]
		if new_child.real_size[0] > self.max_child_width:
			self.max_child_width = new_child.real_size[0]

	def removeWidget(self, child_widget):
		super(VerticalLayout, self).removeWidget(child_widget)
		if self.max_child_width > self.real_size[0]:
			if child_widget.real_size[0] == self.max_child_width:
				self.calculate_max_child_width()

	def createFirstHelperWidget(self):
		first_child_raw = self.data[0]
		real_size = first_child_raw['init_data']['real_size']
		real_pos = (self.real_pos[0], self.real_pos[1] + self.real_size[1] - real_size[1])

		helper_widget = RealWidget(real_pos, real_size)
		return helper_widget

	def fillInDelta(self, delta, helper_child):
		if delta > 0:
			real_pos = helper_child.real_pos
			data_index = 0
		else:
			real_pos = self.real_pos
			data_index = -1
		return real_pos, data_index

	def additionalKwargsFillFirst(self, data_index, reference_child):
		reference_pos = reference_child.real_pos
		reference_size = reference_child.real_size
		real_pos = [reference_pos[0], reference_pos[1] + reference_size[1]]
		return {'real_pos': real_pos}

	def additionalKwargsFillLast(self, data_index, reference_child):
		"""
		Since children are not of the same type necessarily, the ypos of the filled-in widget is the reference_pos[1] of
		the last widget minus the filled-in real_size[1]. We store real_size in data, hence we get it from there.
		"""
		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		child_type = raw_data['child_type']

		# NOTE: real_size has to be set in init_data
		real_size = raw_data['init_data']['real_size']

		reference_pos = reference_child.real_pos
		real_pos = [reference_pos[0], reference_pos[1] - real_size[1]]
		return {'real_pos': real_pos}

	def repositionChildren(self, reference_widget, direction=1, delta=None):
		if not delta:
			delta = [0, reference_widget.real_size[1] * direction]
		super(VerticalLayout, self).repositionChildren(reference_widget, direction=direction, delta=delta)

	def repositionForInsert(self, child_widget):
		self.repositionChildren(child_widget, direction=-1)

	def repositionForRemove(self, child_widget):
		self.repositionChildren(child_widget)

	def fillAndReposition(self):
		"""
		NOTE: convenience method for fillInChildren and subsequent repositionChildren if first child is below upper
		bound (which is necessarily followed by fillInChildren again since last child is moved upwards, potentially
		leaving a gap to the lower bound).
		"""
		self.fillInChildren()
		first_child = self.visible[0]
		delta = self.delta_first(first_child)
		if delta > 0:
			first_child.updatePos([0, delta])
			self.repositionChildren(first_child, delta=[0, delta])
			self.fillInChildren()

	def delta_first(self, first_child):
		return (self.real_pos[1] + self.real_size[1]) - (first_child.real_pos[1] - first_child.real_size[1])

	def delta_last(self, last_child):
		return self.real_pos[1] - (last_child.real_pos[1] + 2 * last_child.real_size[1])

	def delta_second(self, second_child):
		return (self.real_pos[1] + self.real_size[1]) - second_child.real_pos[1]

	def delta_penultimate(self, penultimate_child):
		return self.real_pos[1] - (penultimate_child.real_pos[1] + penultimate_child.real_size[1])

	def check_delta_right(self, first_child):
		return (self.real_pos[0] + self.real_size[0]) - (first_child.real_pos[0] + self.max_child_width)

	def checkDelta(self, delta_x, delta_y):
		first_child = self.visible[0]
		last_child = self.visible[-1]

		# check delta_y
		if delta_y > 0:
			delta = self.check_delta_bottom(last_child)
			if delta_y > delta:
				if last_child.data_index + 1 == len(self.data):
					delta_y = delta
		if delta_y < 0:
			delta = self.check_delta_top(first_child)
			if delta_y < delta:
				if first_child.data_index == 0:
					delta_y = delta

		# check delta_x
		if delta_x < 0:
			delta = self.check_delta_right(first_child)
			if delta_x < delta:
				delta_x = delta
		if delta_x > 0:
			delta = self.check_delta_left(first_child)
			if delta_x > delta:
				delta_x = delta

		return delta_x, delta_y

	def inspect(self, delta_x, delta_y):
		if delta_y < 0:
			self.inspectLastSecond(delta_y)
		elif delta_y > 0:
			self.inspectFirstPenultimate(delta_y)


"""
Because I initially implemented HorizontalLayout wrong (from right to left, simply copying the methods from
VerticalLayout - which is from top to bottom - and adapting from ypos to xpos), this definitely needs to be TESTED.
"""

class HorizontalLayout(MoveLayout):
	def additionalKwargsInsert(self, data_index):
		"""
		HorizontalLayout algins the widgets from left to right, hence the inserted widget takes the place of the current
		widget. Therefore, we simply need to take the reference_pos.
		"""
		visible_index = self.get_visible_index(data_index)
		if not self.visible:
			real_pos = self.real_pos
		elif visible_index < len(self.visible):
			reference_pos = self.visible[visible_index].real_pos
			real_pos = reference_pos
		else:
			reference_pos = self.visible[visible_index - 1].real_pos
			reference_size = self.visible[visible_index - 1].real_size
			real_pos = [reference_pos[0] + reference_size[0], reference_pos[1]]
		return {'real_pos': real_pos}

	def addWidget(self, data_index, additional_data):
		super(HorizontalLayout, self).addWidget(data_index, additional_data)
		new_child = self.visible[self.get_visible_index(data_index)]
		if new_child.real_size[1] > self.max_child_height:
			self.max_child_height = new_child.real_size[1]

	def removeWidget(self, child_widget):
		super(HorizontalLayout, self).removeWidget(child_widget)
		if self.max_child_height > self.real_size[1]:
			if child_widget.real_size[1] == self.max_child_height:
				self.calculate_max_child_height()

	def createFirstHelperWidget(self):
		first_child_raw = self.data[0]
		real_size = first_child_raw['init_data']['real_size']
		real_pos = self.real_pos

		helper_widget = RealWidget(real_pos, real_size)
		return helper_widget

	def fillInDelta(self, delta, helper_child):
		if delta < 0:
			real_pos = self.real_pos
			data_index = 0
		else:
			last_child_raw = self.data[0]
			real_size = last_child_raw['init_data']['real_size']
			real_pos = [self.real_pos[0] + self.real_size[0] - real_size[0], self.real_pos[1]]
			data_index = -1
		return real_pos, data_index

	def additionalKwargsFillFirst(self, data_index, reference_child):
		"""
		Since children are not of the same type necessarily, the xpos of the filled-in widget is the reference_pos[0] of
		the first widget minus the filled-in real_size[0]. We store real_size in data, hence we get it from there.
		"""
		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		child_type = raw_data['child_type']

		# NOTE: real_size has to be set in init_data
		real_size = raw_data['init_data']['real_size']

		reference_pos = reference_child.real_pos
		real_pos = [reference_pos[0] - real_size[0], reference_pos[1]]
		return {'real_pos': real_pos}

	def additionalKwargsFillLast(self, data_index, reference_child):
		reference_pos = reference_child.real_pos
		reference_size = reference_child.real_size
		real_pos = [reference_pos[0] + reference_size[0], reference_pos[1]]
		return {'real_pos': real_pos}

	def repositionChildren(self, reference_widget, direction=1, delta=None):
		if not delta:
			delta = [reference_widget.real_size[0] * direction, 0]
		super(HorizontalLayout, self).repositionChildren(reference_widget, direction=direction, delta=delta)

	def repositionForInsert(self, child_widget):
		self.repositionChildren(child_widget)

	def repositionForRemove(self, child_widget):
		self.repositionChildren(child_widget, direction=-1)

	def fillAndReposition(self):
		"""
		NOTE: convenience method for fillInChildren and subsequent repositionChildren if first child is right from left
		bound (which is necessarily followed by fillInChildren again since last child is moved upwards, potentially
		leaving a gap to the lower bound).
		"""
		self.fillInChildren()
		first_child = self.visible[0]
		delta = self.delta_first(first_child)
		if delta < 0:
			first_child.updatePos([delta, 0])
			self.repositionChildren(first_child, delta=[delta, 0])
			self.fillInChildren()

	def delta_first(self, first_child):
		return self.real_pos[0] - (first_child.real_pos[0] + 2 * first_child.real_size[0])

	def delta_first_condition(self, first_child):
		return self.delta_first(first_child) < 0

	def condition_first(self, first_child, delta):
		return delta < self.delta_first(first_child)

	def delta_last(self, last_child):
		return (self.real_pos[0] + self.real_size[0]) - (last_child.real_pos[0] - last_child.real_size[0])

	def delta_last_condition(self, last_child):
		return self.delta_last(last_child) > 0

	def condition_last(self, last_child, delta):
		return delta > self.delta_last(last_child)

	def delta_second(self, second_child):
		return self.real_pos[0] - (second_child.real_pos[0] + second_child.real_size[0])

	def condition_second(self, second_child, delta):
		return delta < self.delta_second(second_child)

	def delta_penultimate(self, penultimate_child):
		return (self.real_pos[0] + self.real_size[0]) - penultimate_child.real_pos[0]

	def condition_penultimate(self, penultimate_child, delta):
		return delta > self.delta_penultimate(penultimate_child)

	def check_delta_top(self, first_child):
		return (self.real_pos[1] + self.real_size[1]) - (first_child.real_pos[1] + self.max_child_height)

	def checkDelta(self, delta_x, delta_y):
		first_child = self.visible[0]
		last_child = self.visible[-1]

		# check delta_y
		if delta_y > 0:
			delta = self.check_delta_bottom(first_child)
			if delta_y > delta:
				delta_y = delta
		if delta_y < 0:
			delta = self.check_delta_top(first_child)
			if delta_y < delta:
				delta_y = delta

		# check delta_x
		if delta_x < 0:
			delta = self.check_delta_right(last_child)
			if delta_x < delta:
				if last_child.data_index == 0:
					delta_x = delta
		if delta_x > 0:
			delta = self.check_delta_left(first_child)
			if delta_x > delta:
				if first_child.data_index + 1 == len(self.data):
					delta_x = delta

		return delta_x, delta_y

	def inspect(self, delta_x, delta_y):
		if delta_x > 0:
			self.inspectLastSecond(delta_x)
		elif delta_x < 0:
			self.inspectFirstPenultimate(delta_x)


class MixedLayout(MoveLayout):
	def inspect(self, delta_x, delta_y):
		pass


## Scroll


class ScrollLayout(VerticalLayout):
	def move(self, touch):
		delta_x, delta_y = touch.dpos
		scroll_touch = Touch()
		delta = (0, delta_y)
		pos = (touch.x - delta_x, touch.y)
		scroll_touch.updateDpos(delta)
		scroll_touch.updatePos(*pos)

		# move y-axis
		delta_x, delta_y = super(ScrollLayout, self).move(scroll_touch)

		# we need to return delta_x, delta_y for nested layouts
		return delta_x, delta_y

	def fitChildrenToFrame(self):
		# TODO: do i want to implement sth like this?
		pass

class SlideLayout(HorizontalLayout):
	def move(self, touch):
		delta_x, delta_y = touch.dpos
		scroll_touch = Touch()
		delta = (delta_x, 0)
		pos = (touch.x, touch.y - delta_y)
		scroll_touch.updateDpos(delta)
		scroll_touch.updatePos(*pos)

		# move y-axis
		delta_x, delta_y = super(SlideLayout, self).move(scroll_touch)

		# we need to return delta_x, delta_y for nested layouts
		return delta_x, delta_y

	def fitChildrenToFrame(self):
		# TODO: do i want to implement sth like this?
		pass


## ZOOM


class ZoomChild(ChildWidget):
	"""
	NOTE: the size of kv children has to be defined like real_size * resize_factor
	"""
	resize_factor = NumericProperty(1)
	def resize(self, resize_factor):
		self.resize_factor = resize_factor
		for child in self.children:
			child.resize(resize_factor)

	def to_data(self) -> dict:
		raw_data = super(ZoomChild, self).to_data()
		raw_data['init_data']['resize_factor'] = self.resize_factor
		return raw_data


class ZoomLayout(VerticalLayout):
	max_zoom = 1
	min_zoom = 1
	current_zoom = 1
	def additionalKwargsInsert(self, data_index):
		additional_data = super(ZoomLayout, self).additionalKwargsInsert(data_index)

		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		child_type = raw_data['child_type']

		# NOTE: resize_factor has to be set in init_data
		resize_factor = raw_data['init_data']['resize_factor']

		visible_index = self.get_visible_index(data_index)
		if self.visible:
			resize_factor = self.visible[visible_index].resize_factor

		additional_data['resize_factor'] = resize_factor
		return additional_data

	def addWidget(self, data_index, additional_data):
		# add widget
		super(ZoomLayout, self).addWidget(data_index, additional_data)

		# update max_child_width
		visible_index = self.get_visible_index(data_index)
		new_child = self.visible[visible_index]
		max_width = new_child.real_size[1] * new_child.resize_factor
		if max_width > self.max_child_width:
			self.max_child_width = max_width

	def additionalKwargsFillFirst(self, data_index, reference_child):
		additional_data = super(ZoomLayout, self).additionalKwargsFillFirst(data_index, reference_child)
		additional_data['resize_factor'] = reference_child.resize_factor
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		additional_data = super(ZoomLayout, self).additionalKwargsFillLast(data_index, reference_child)
		additional_data['resize_factor'] = reference_child.resize_factor
		return additional_data

	def resizeWidgets(self, reference_widget, resize_factor):
		self.max_child_width *= resize_factor
		reference_index = reference_widget.data_index
		for child in self.visible:
			child_index = child.data_index
			child.updatePos([0, (child_index - reference_index) * child.real_size[1] * (child.resize_factor - resize_factor)])
			child.resize(resize_factor)

	def resizeFillAndReposition(self, reference_widget, resize_factor):
		"""
		NOTE: convenience method for resizeWidgets and subsequent fillAndReposition
		"""
		self.resizeWidgets(reference_widget, resize_factor)
		self.fillAndReposition()

	def delta_first(self, first_child):
		return (self.real_pos[1] + self.real_size[1]) - (first_child.real_pos[1] + first_child.real_size[1] * first_child.resize_factor)

	def delta_last(self, last_child):
		return self.real_pos[1] - (last_child.real_pos[1] + 2 * last_child.real_size[1] * last_child.resize_factor)

	def condition_penultimate(self, penultimate_child, delta_y):
		return penultimate_child.real_pos[1] + penultimate_child.real_size[1] * penultimate_child.resize_factor + delta_y < self.real_pos[1] - self.visibility_margin_min


## WITH FONTS


class BaseText(ZoomChild):
	"""
	NOTE: the font_size of kv children has to be defined like int(this_font_size * resize_factor)
	"""
	this_text = StringProperty('')
	this_font_size = NumericProperty(11)


class FontLayout(ZoomLayout):
	def additionalKwargsInsert(self, data_index):
		additional_data = super(FontLayout, self).additionalKwargsInsert(data_index)

		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		child_type = raw_data['child_type']

		# NOTE: this_font_size has to be set in init_data
		font_size = raw_data['init_data']['this_font_size']

		visible_index = self.get_visible_index(data_index)
		if self.visible:
			font_size = self.visible[visible_index].this_font_size

		additional_data['this_font_size'] = font_size
		return additional_data

	def addWidget(self, data_index, additional_data):
		super(FontLayout, self).addWidget(data_index, additional_data)

	def additionalKwargsFillFirst(self, reference_child):
		additional_data = super(FontLayout, self).additionalKwargsFillFirst(reference_child)
		additional_data['this_font_size'] = reference_child.this_font_size
		return additional_data

	def additionalKwargsFillLast(self, reference_child):
		additional_data = super(FontLayout, self).additionalKwargsFillLast(reference_child)
		additional_data['this_font_size'] = reference_child.this_font_size
		return additional_data

	def updateFontSize(self, reference_widget, font_size):
		# TODO
		# propagate font_size to children
		# resize all children
		# remove / add widgets from visible / data
		for child in self.visible:
			child.this_font_size = font_size
		self.resizeWidgetsToFont(reference_widget, font_size)

	def resizeWidgetsToFont(self, reference_widget, font_size):
		"""
		NOTE: Treating a change in font_size the same way as resizing widgets is on purpose! since all related widgets
		need to be resized in an according manner such that the new layout with the changed font_size stays
		proportionally the same.
		"""
		helper_widget = type(reference_widget)(-1)  # BaseChild needs an index, chose -1 to fulifll that.
		helper_widget.this_font_size = font_size
		helper_widget.this_text = 'H'
		refactor_size = helper_widget.real_size[1] / reference_widget.real_size[1]
		self.resizeFillAndReposition(reference_widget, resize_factor)


# MARGIN

"""
NOTE: Don't confuse margin with PADDING !!!

~> at least thats how its meant in the context of these layouts, as a visibility margin.

Usecase: When widgets are so small in size, that delta_y is greater than its real_size[1]. Since only one widget will be
added in each iteration, this would instantly leave a gap between the visible widgets and the screens border. In order
to prevent this, we give ourselves a little bit of (visibilitiy) margin.
"""

"""
TEST all those conditions
"""

class MarginLayout(BaseLayout):
	visibility_margin = None


class MoveMarginLayout(MarginLayout, MoveLayout):
	def get_visibility_margin_value(self):
		if self.visibility_margin is None:
			return 0
		return self.visibility_margin


class VerticalMarginLayout(MoveMarginLayout, VerticalLayout):
	def delta_first_condition(self, first_child):
		return self.delta_first(first_child) - self.get_visibility_margin_value() > 0

	def delta_last_condition(self, last_child):
		return self.delta_last(last_child) + self.get_visibility_margin_value() < 0

	def condition_first(self, first_child, delta):
		return delta > self.delta_first(first_child) + self.get_visibility_margin_value()

	def condition_last(self, last_child, delta):
		return delta < self.delta_last(last_child) - self.get_visibility_margin_value()


class HorizontalMarginLayout(MoveMarginLayout, HorizontalLayout):
	def delta_first_condition(self, first_child):
		return self.delta_first(first_child) + self.get_visibility_margin_value() < 0

	def delta_last_condition(self, last_child):
		return self.delta_last(last_child) - self.get_visibility_margin_value() > 0

	def condition_first(self, first_child, delta):
		return delta < self.delta_first(first_child) - self.get_visibility_margin_value()

	def condition_last(self, last_child, delta):
		return delta > self.delta_last(last_child) + self.get_visibility_margin_value()


class ScrollMarginLayout(VerticalMarginLayout, ScrollLayout):
	pass


class SlideMarginLayout(HorizontalMarginLayout, SlideLayout):
	pass


class ZoomMarginLayout(VerticalMarginLayout, ZoomLayout):
	pass


class FontMarginLayout(ZoomMarginLayout, FontLayout):
	pass



if __name__ == '__main__':
	print("Testing the syntactically correctness.")
