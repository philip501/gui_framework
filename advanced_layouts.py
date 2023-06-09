from kivy.properties import ListProperty, ObjectProperty, NumericProperty, BooleanProperty, StringProperty

from gui_framework.base_layouts import (
	BaseLayout,
	MoveLayout,
	VerticalLayout,
	HorizontalLayout,
	ScrollLayout,
	SlideLayout,
	ZoomLayout,
	FontLayout,
	MarginLayout,
	MoveMarginLayout,
	VerticalMarginLayout,
	HorizontalMarginLayout,
	ScrollMarginLayout,
	SlideMarginLayout,
	ZoomMarginLayout,
	FontMarginLayout,
	BaseChild,
	ChildWidget,
	ZoomChild,
	BaseText
)
from gui_framework.utils import RealWidget

from typing import List
from copy import deepcopy


"""
ATTENTION !!!

Base Layouts cannot be used be used as children for nested layouts because they dont inherit from base child and
therefore cannot be assigned a data_index to. Hence, we need a wrapper for (actual) children that stops the propagation.
"""


# NESTED

"""
This is an extension to all existing layout. Its children are (nested!) layouts themselves, hence all methods need to be
propagated to them.
"""

"""
Changelog:

0.10.0 check if children are nested layouts themselves
"""

"""
NOTES:

0.9.0 additionalKwargs* methods of base layouts now use real_size from 'init_data', therefore we can call the super
method now for the nested methods.

0.10.0 so far, check_nested_layout is only necessary when adding the anchor to the additional_kwargs

0.11.0 moved fillInFromScratch to base layouts
"""

"""
TODOs:

The current implementation stores all the children data in the sense that for n nested layouts the leaf children data
gets stored at every parent data, hence n times.

~> There needs to be some sort of mix between storing all the data and keeping a reference.
"""

"""
THOUGHTS I HAD ON:

- nested move
Some logic is needed to forward the move to nested layouts beyond updatePos. Simply calling reviewChildren will
definitely do, but that might be a little bit expensive for every move.

Instead we do these forwards within the inspect methods.
"""


class NestedLayout(BaseLayout, BaseChild):
	def __init__(self, *args, anchor=None, **kwargs):
		super(NestedLayout, self).__init__(**kwargs)
		BaseChild.__init__(self, *args)
		self.anchor = anchor

	def is_anchor(self):
		return self.anchor is None

	def get_anchor(self):
		if self.is_anchor():
			return self
		return self.anchor

	def updateDataFromVisible(self):
		for child in self.visible:
			child.updateDataFromVisible()
			self.updateDataFromChild(child)

	def is_fully_visible(self, child_widget):
		anchor = self.get_anchor()
		anchor_pos = anchor.real_pos
		anchor_size = anchor.real_size

		child_pos = child_widget.real_pos
		child_size = child_widget.real_size

		return anchor_pos[0] <= child_pos[0] and \
			anchor_pos[1] <= child_pos[1] and \
			child_pos[0] + child_size[0] <= anchor_pos[0] + anchor_size[0] and \
			child_pos[1] + child_size[1] <= anchor_pos[1] + anchor_size[1]


class NestedMoveLayout(NestedLayout, MoveLayout):
	def additionalKwargs(self, data_index):
		"""
		We needed to implement adding the anchor to the additional kwargs this way so that we dont get problems with the
		hierarchy of the classes
		"""
		return {'anchor': self.get_anchor()}

	def additionalKwargsInsert(self, data_index):
		additional_data = super(NestedMoveLayout, self).additionalKwargsInsert(data_index)
		additional_data.update(self.additionalKwargs(data_index))
		return additional_data

	def create_child(self, child_type, data_index, init_data):
		#print(data_index)
		new_child = child_type(data_index, **init_data)
		new_child.fillInFromScratch()
		return new_child

	def reviewChildren(self):
		for child in self.visible:
			child.reviewChildren()

	def fillInChildren(self):
		super(NestedMoveLayout, self).fillInChildren()
		"""
		After filling in the nested layouts, not all of their children might be visible. Hence we review the filled-in
		layouts.

		This seems to be a little bit too expensive; need to think of a different logic.

		Probably some sort of propagation of fill-in, but how do we decide where to start the filling?
		~> Maybe looking at first_child and last_child and if one of them does not fullfil the *_condition, then start
		from the other side. Yeah, i think that will do.

		=> implemented in fillInFromScratch, used in create_child, used in addWidget
		"""
		#self.reviewChildren()

	def removeWidget(self, child_widget):
		for child in child_widget.visible:
			child_widget.removeWidget(child)
		"""
		The super.removeWidget method will implicitely call the nested deleteWidget method. Since child_widget.visible
		will already be empty by that point, this will then result in simply executing the super.deleteWidget method.
		"""
		super(NestedMoveLayout, self).removeWidget(child_widget)

	def deleteWidget(self, child_widget):
		"""
		MoveLayout.deleteWidget will remove the widget from visible. Hence, we need to shallow copy visible and iterate
		over that.
		"""
		remove_widgets = child_widget.visible.copy()
		for child in remove_widgets:
			child_widget.deleteWidget(child)
		super(NestedMoveLayout, self).deleteWidget(child_widget)

	def additionalKwargsFillFirst(self, data_index, reference_child):
		additional_data = super(NestedMoveLayout, self).additionalKwargsFillFirst(data_index, reference_child)
		additional_data.update(self.additionalKwargs(data_index))
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		additional_data = super(NestedMoveLayout, self).additionalKwargsFillLast(data_index, reference_child)
		additional_data.update(self.additionalKwargs(data_index))
		return additional_data

	def propagate_inspect(self, delta_x, delta_y):
		# propagate inspect to visible excluding those that are fully within the anchor's frame
		for child in self.visible:
			if not self.is_fully_visible(child):
				child.inspect(delta_x, delta_y)


class NestedVerticalLayout(NestedMoveLayout, VerticalLayout):
	def delta_first(self, first_child):
		anchor = self.get_anchor()
		return (anchor.real_pos[1] + anchor.real_size[1]) - (first_child.real_pos[1] - first_child.real_size[1])

	def delta_last(self, last_child):
		anchor = self.get_anchor()
		return anchor.real_pos[1] - (last_child.real_pos[1] + 2 * last_child.real_size[1])

	def delta_second(self, second_child):
		anchor = self.get_anchor()
		return (anchor.real_pos[1] + anchor.real_size[1]) - second_child.real_pos[1]

	def delta_penultimate(self, penultimate_child):
		anchor = self.get_anchor()
		return anchor.real_pos[1] - (penultimate_child.real_pos[1] + penultimate_child.real_size[1])

	def checkDelta(self, delta_x, delta_y):
		"""
		We only need to check the delta at the anchor level.
		"""
		if self.is_anchor():
			return super(NestedVerticalLayout, self).checkDelta(delta_x, delta_y)
		return delta_x, delta_y

	def inspect(self, delta_x, delta_y):
		super(NestedVerticalLayout, self).inspect(delta_x, delta_y)
		self.propagate_inspect(delta_x, delta_y)


class NestedHorizontalLayout(NestedMoveLayout, HorizontalLayout):
	def delta_first(self, first_child):
		anchor = self.get_anchor()
		return anchor.real_pos[0] - (first_child.real_pos[0] + 2 * first_child.real_size[0])

	def delta_last(self, last_child):
		anchor = self.get_anchor()
		return (anchor.real_pos[0] + anchor.real_size[0]) - (last_child.real_pos[0] - last_child.real_size[0])

	def delta_second(self, second_child):
		anchor = self.get_anchor()
		return anchor.real_pos[0] - (second_child.real_pos[0] + second_child.real_size[0])

	def delta_penultimate(self, penultimate_child):
		anchor = self.get_anchor()
		return (anchor.real_pos[0] + anchor.real_size[0]) - penultimate_child.real_pos[0]

	def checkDelta(self, delta_x, delta_y):
		if self.is_anchor():
			return super(NestedHorizontalLayout, self).checkDelta(delta_x, delta_y)
		return delta_x, delta_y

	def inspect(self, delta_x, delta_y):
		super(NestedHorizontalLayout, self).inspect(delta_x, delta_y)
		self.propagate_inspect(delta_x, delta_y)


class NestedScrollLayout(NestedVerticalLayout, ScrollLayout):
	pass


class NestedSlideLayout(NestedHorizontalLayout, SlideLayout):
	pass


class NestedZoomLayout(NestedVerticalLayout, ZoomLayout):
	pass


class FontLayout(NestedZoomLayout, FontLayout):
	pass


class NestedMarginLayout(NestedLayout, MarginLayout):
	pass

class NestedMoveMarginLayout(NestedMarginLayout, MoveMarginLayout):
	pass

class NestedVerticalMarginLayout(NestedMoveMarginLayout, VerticalMarginLayout):
	pass

class NestedHorizontalMarginLayout(NestedMoveMarginLayout, HorizontalMarginLayout):
	pass

class NestedScrollMarginLayout(NestedVerticalMarginLayout, ScrollMarginLayout):
	pass

class NestedSlideMarginLayout(NestedHorizontalMarginLayout, SlideMarginLayout):
	pass

class NestedZoomMarginLayout(NestedVerticalMarginLayout, ZoomMarginLayout):
	pass

class NestedFontMarginLayout(NestedZoomMarginLayout, FontMarginLayout):
	pass


# WRAPPER

class ChildWrapper(NestedMoveLayout):
	"""
	For GridLayout we need Cell to be a child and a layout. Since this causes inheritance problems (eg for which
	__init__ gets called), we need a wrapper layout class that acts just like a child.
	"""
	def __init__(self, *args, child_type: ChildWidget = ChildWidget, wrapped_data={}, **kwargs):
		super(ChildWrapper, self).__init__(*args, **kwargs)
		self.child_type = child_type
		self.formatDataFromWrapped(wrapped_data)

	def updateSize(self, real_size):
		super(ChildWrapper, self).updateSize(real_size)
		for child in self.visible:
			child.updateSize(real_size)

	def formatDataFromWrapped(self, wrapped_data):
		if wrapped_data:
			self.data = [
				{
					'child_type': self.child_type,
					'init_data': wrapped_data
				}
			]

	def create_child(self, child_type: ChildWidget, data_index, init_data):
		return super(NestedMoveLayout, self).create_child(child_type, data_index, init_data)

	def createFirstHelperWidget(self):
		return RealWidget(self.real_pos, self.real_size)

	def additionalKwargs(self, data_index):
		return {}

	def additionalKwargsInsert(self, data_index):
		additional_data = super(ChildWrapper, self).additionalKwargsInsert(data_index)
		additional_data['real_pos'] = self.real_pos
		additional_data['real_size'] = self.real_size
		return additional_data

	def additionalKwargsFillFirst(self, data_index, reference_child):
		additional_data = super(ChildWrapper, self).additionalKwargsFillFirst(data_index, reference_child)
		additional_data['real_pos'] = self.real_pos
		additional_data['real_size'] = self.real_size
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		additional_data = super(ChildWrapper, self).additionalKwargsFillLast(data_index)
		additional_data['real_pos'] = self.real_pos
		additional_data['real_size'] = self.real_size
		return additional_data

	def reviewChildren(self):
		super(NestedMoveLayout, self).reviewChildren()

	def removeWidget(self, child_widget):
		super(NestedMoveLayout, self).removeWidget(child_widget)

	def deleteWidget(self, child_widget):
		super(NestedMoveLayout, self).deleteWidget(child_widget)

	def fillInDelta(self, delta, helper_child):
		return self.real_pos, 0

	def propagate_inspect(self, delta_x, delta_y):
		pass

	def delta_first(self, first_child):
		return 0

	def delta_last(self, last_child):
		return 0

	def delta_second(self, second_child):
		return 0

	def delta_penultimate(self, penultimate_child):
		return 0

	def updateDataFromVisible(self):
		super(NestedLayout, self).updateDataFromVisible()

	def onTouchDownAnimation(self, touch):
		if self.visible:
			self.visible[0].onTouchDownAnimation(touch)

	def onTouchUpAnimation(self, touch):
		if self.visible:
			self.visible[0].onTouchUpAnimation(touch)


"""
TODO: da muss ich mir noch überlegen, wie ich resize_factor, this_font_size, this_text usw propagaten will, falls
notwendig. Wenn ich das zb immer bei additionalKwargs* übergeben und bei to_data speichern möchte, dann muss ich mir
noch was bei wrapped data überlegen. oder einfach dann td noch data anlegen?
"""

class ZoomChildWrapper(ChildWrapper):
	def __init__(self, *args, child_type: ZoomChild = ZoomChild, resize_factor=1, **kwargs):
		super(ZoomChildWrapper, self).__init__(*args, child_type=child_type, **kwargs)
		self.resize_factor = resize_factor

	def create_child(self, child_type: ZoomChild, data_index, init_data):
		return super(ZoomChildWrapper, self).create_child(child_type, data_index, init_data)

	def additionalKwargsInsert(self, data_index):
		additional_data = super(ZoomChildWrapper, self).additionalKwargsInsert(data_index)
		additional_data['resize_factor'] = self.resize_factor
		return additional_data

	def additionalKwargsFillFirst(self, data_index, reference_child):
		additional_data = super(ZoomChildWrapper, self).additionalKwargsFillFirst(data_index, reference_child)
		additional_data['resize_factor'] = self.resize_factor
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		additional_data = super(ZoomChildWrapper, self).additionalKwargsFillLast(data_index, reference_child)
		additional_data['resize_factor'] = self.resize_factor
		return additional_data

	def to_data(self) -> dict:
		data = super(ZoomChildWrapper, self).to_data()
		#data['init_data']['resize_factor'] = self.resize_factor
		return data

	def updateResize(self, resize_factor):
		if self.visible:
			self.visible[0].resize_factor = resize_factor

class BaseTextWrapper(ZoomChildWrapper):
	def __init__(self, *args, child_type: BaseText = BaseText, this_text='', this_font_size=11, **kwargs):
		super(BaseTextWrapper, self).__init__(*args, child_type=child_type, **kwargs)
		self.this_text = this_text
		self.this_font_size = this_font_size

	def create_child(self, child_type: BaseText, data_index, init_data):
		return super(BaseTextWrapper, self).create_child(child_type, data_index, init_data)

	def additionalKwargsInsert(self, data_index):
		additional_data = super(BaseTextWrapper, self).additionalKwargsInsert(data_index)
		#additional_data['this_text'] = self.this_text
		additional_data['this_font_size'] = self.this_font_size
		return additional_data

	def additionalKwargsFillFirst(self, data_index, reference_child):
		additional_data = super(BaseTextWrapper, self).additionalKwargsFillFirst(data_index, reference_child)
		#additional_data['this_text'] = self.this_text
		additional_data['this_font_size'] = self.this_font_size
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		additional_data = super(BaseTextWrapper, self).additionalKwargsFillLast(data_index, reference_child)
		#additional_data['this_text'] = self.this_text
		additional_data['this_font_size'] = self.this_font_size
		return additional_data

	def to_data(self) -> dict:
		data = super(BaseTextWrapper, self).to_data()
		#data['init_data']['this_text'] = self.this_text
		#data['init_data']['this_font_size'] = self.this_font_size
		return data

	def updateText(self, text):
		if self.visible:
			self.visible[0].this_text = text

	def updateFontSize(self, font_size):
		if self.visible:
			self.visible[0].this_font_size = font_size


# GRID

"""
For GridLayout we need a modification to the 'data' attribute. We dont intend to create RowWidgets within which we then
add the column elements, we desire to add each cell of a grid as such to the GridLayout. For that reason we need to
modify the existing data definition of BaseLayout.

For this we need additional positional information for our grid_data.

For this purpose GridLayout also needs to store the information about the height of the rows and the width of the
columns.

Since grid_data is a List, we effectively store the cells like a matrix as a vector. This requires modification of the
BaseChild and BaseLayout methods. We also want to enable to only fill certain cells.


CHANGE OF MIND

Using rows simplifies the logic and is the better solution to stay consistent with the original architecture of nesting
widgets.
"""

"""
Changelog:

0.0 some sort of get_index_by_position is needed, some sort of insert_cell and insert_cells (maybe insert_row as a
convenient method, and even insert_col)
~> like if row / col index does not exist yet (this can be checked by len(row_heights) / len(col_widths)) we need to
insert / add this row / col as a whole to our grid_data vector (List).

we also need to change the BaseChild methods for this purpose (see NOTES).

0.0.1 change of mind, rows will be organized as rows, this makes everything easier.

0.1.0 introducing content_size for BaseCell

0.2.0 Cell is now a BaseText to avoid / resolve any inheritance problems when implementing a cell with text.
"""

"""
NOTES:

0.0 a data_index in BaseLayout is an integer, here we need it to be a list.

0.1.0 Since we pass the col_width and row_height to all cells, we needed a new attribute that stores the cells
"original" size. This is needed when we want to recalculate those sizes in case a cell gets deleted or altered in size.
"""

"""
TODO:
I am unsure how I want to implement this. By default, the row is created empty if no data is provided. Even if data is
provided, we still want to keep the possibility of cells being empty.

~> How should I interpret the insertion logic here? 
=> Keep it as it is, we need it that way for moving and stuff, fillInFromScratch also relies on that logic.
=> We need an updateCell method, the "insertion" point of view regarding filling in an empty cell will have to use that
one.
"""

"""
IDEAS:

'real_size' needs to be present from the start (of initialization). Since this can depend on the layout itself, maybe we
want to add it on additionalKwargs*? From grid to row, from row to cell - via col_widhts and row_heights.
(note: this is already implemented for row to cell)
"""


class Cell(BaseText):
	"""
	Within RowLayout we want to propagate any changes of its real_size to its children. When deleting a child (and its
	data) we want possibly adjust all cells heights to the new max height. Since real_size is not suitable for this
	purpose due to the propagation, we need a new attribute for that - content_size.

	NOTE: (Usually) Do NOT update the cells real_pos at any point from within any cells method. This will be done on row
	level.
	"""
	def get_data_index(self):
		return [self.parent.data_index, self.data_index]

	def updateData(self, data):
		"""
		This method is used to update the cells attributes and content from data.

		NOTE: You will probably want to update content_size when implementing this method. Its usage is inherent to
		recalculate the rows height when deleting a cell or updating a cells data.

		NOTE: You will probably not need to handle the case where content_size exceeds real_size, simply call the super
		method at the end of your implementation.

		TODO:
		This should be handled in the wrapper.
		"""
		if self.content_size[0] > self.real_size[0]:
			self.real_size[0] = self.content_size[0]
		if self.content_size[1] > self.real_size[1]:
			self.real_size[1] = self.content_size[1]

class CellWrapper(BaseTextWrapper):
	"""
	Since RowLayout is a nested layout, its children (cells that is) need to be a layout themselves.

	NOTE: Empty cells are allowed. Handling their onTouch* needs to be managed on implementation.

	This needed wrapping logic already fulfills a nested version of cell. Hence we can do alignment and alike here.

	valign: vertical alignment of the content; possible values:
		TOP
		CENTER
		BOTTOM
	halign: horizontal alignemt of the content; possible values:
		LEFT
		CENTER
		RIGHT

	By default the content alignment will be TOP-LEFT.
	"""
	content_size = (0,0)
	valign = 'LEFT'
	halign = 'TOP'
	def __init__(self, *args, child_type: Cell = Cell, content_size=None, valign='LEFT', halign='TOP', **kwargs):
		super(CellWrapper, self).__init__(*args, child_type=child_type, **kwargs)
		self.valign = valign
		self.halign = halign
		if content_size is None:
			self.content_size = self.real_size
		else:
			self.content_size = content_size
		self.align_content()
		self.override_content_size = False

	def updateSize(self, real_size):
		super(ChildWrapper, self).updateSize(real_size)

		if self.override_content_size:
			self.content_size = self.real_size
		else:
			self.content_size = [
				min(self.real_size[0], self.content_size[0]),
				min(self.real_size[1], self.content_size[1])
			]
		self.override_content_size = False
		for child in self.visible:
			child.updateSize(self.content_size)

	def align_content(self):
		if not self.visible:
			return

		delta_width = self.real_size[0] - self.content_size[0]
		delta_height = self.real_size[1] - self.content_size[1]
		real_pos = [self.real_pos[0], self.real_pos[1]]

		if self.valign == 'TOP':
			real_pos[1] += delta_height
		elif self.halign == 'CENTER':
			real_pos[1] += delta_height / 2

		if self.halign == 'RIGHT':
			real_pos[0] += delta_width
		elif self.halign == 'CENTER':
			real_pos[0] += delta_width / 2

		self.visible[0].setPos(real_pos)

	def addWidget(self, data_index, additional_data):
		super(CellWrapper, self).addWidget(data_index, additional_data)
		self.align_content()

	def updateData(self, data):
		if self.visible:
			self.visible[0].updateData()
			self.align_content()

	def to_data(self) -> dict:
		data = super(CellWrapper, self).to_data()
		data['init_data']['content_size'] = self.content_size
		data['init_data']['valign'] = self.valign
		data['init_data']['halign'] = self.halign
		return data

	def additionalKwargsInsert(self, data_index):
		additional_data = super(CellWrapper, self).additionalKwargsInsert(data_index)
		additional_data['real_size'] = self.content_size
		return additional_data

	def additionalKwargsFillFirst(self, data_index, reference_child):
		additional_data = super(CellWrapper, self).additionalKwargsFillFirst(data_index, reference_child)
		additional_data['real_size'] = self.content_size
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		additional_data = super(CellWrapper, self).additionalKwargsFillLast(data_index, reference_child)
		additional_data['real_size'] = self.content_size
		return additional_data


class RowLayout(NestedHorizontalLayout):
	"""
	NOTE: Empty cells are allowed. Handling their onTouch* needs to be managed on implementation.
	"""
	col_widths: List = []
	def __init__(self, *args, col_widths=[], **kwargs):
		super(RowLayout, self).__init__(*args, **kwargs)
		self.col_widths = deepcopy(col_widths)
		if not self.data:
			self.data = [{} for i in range(len(self.col_widths))]

	def is_empty(self):
		if [True for d in self.data if d]:
			return False
		return True

	def deleteWidget(self, data_index):
		super(RowLayout, self).deleteWidget(data_index)
		self.recalculate_max_child_height()

	def recalculate_max_child_height(self):
		"""
		NOTE: Regarding its usage, This method has nothing to do with BaseLayout.calculate_max_child_height albeit their
		name similarities.
		"""
		self.updateDataFromVisible()
		max_child_height = 0
		for child in self.data:
			content_size = child['init_data']['content_size']
			if content_size[0] > max_child_height:
				max_child_height = content_size[0]
		self.updateHeight(max_child_height)

	def createFirstHelperWidget(self):
		real_pos = self.real_pos
		real_size = [self.col_widths[0], self.real_size[1]]
		helper_widget = RealWidget(real_pos, real_size)
		return helper_widget

	def _add_real_size_for_kwargs(self, data_index):
		"""
		NOTE: This method is ONLY for internal purpose. Do NOT use this method at any time!

		Due to the internal logic that 'real_size' needs to be set from the very start for all additionalKwargs* methods
		and the implementation choice to set the real size on instantiation level from grid to row and from row to cell,
		we need to do so before calling the additionalKwargs* super methods. Since this is the same for all of them, we
		extracted this logic to this separate method.
		"""
		real_size = [self.col_widths[data_index], self.real_size[1]]

		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		raw_data['init_data']['real_size'] = real_size

		return real_size

	def additionalKwargsInsert(self, data_index):
		real_size = self._add_real_size_for_kwargs(data_index)

		additional_data = super(RowLayout, self).additionalKwargsInsert(data_index)

		data_index = self.get_data_index(data_index)
		additional_data['real_size'] = real_size
		return additional_data

	def additionalKwargsFillFirst(self, data_index, reference_child):
		real_size = self._add_real_size_for_kwargs(data_index)

		additional_data = super(RowLayout, self).additionalKwargsFillFirst(data_index, reference_child)

		data_index = self.get_data_index(data_index)
		additional_data['real_size'] = real_size
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		real_size = self._add_real_size_for_kwargs(data_index)

		additional_data = super(RowLayout, self).additionalKwargsFillLast(data_index, reference_child)

		data_index = self.get_data_index(data_index)
		additional_data['real_size'] = real_size
		return additional_data

	def insertNewAndReposition(self, data_index, new_data, child_type: ChildWidget):
		# NOTE: real_size has to be set in init_data
		real_size = new_data['real_size']
		self.col_widths.insert(self.get_data_index(data_index), real_size[0])

		if real_size[1] > self.real_size[1]:
			self.updateHeight(real_size[1])

		# insert data, create child and reposition due to inserted widget
		super(RowLayout, self).insertNewAndReposition(data_index, new_data, child_type)

	def fillInDelta(self, delta, helper_child):
		if delta < 0:
			real_pos = self.real_pos
			data_index = 0
		else:
			real_pos = [self.real_pos[0] + self.real_size[0] - self.col_widths[-1], self.real_pos[1]]
			data_index = -1
		return real_pos, data_index

	def updateCell(self, data_index, update_data):
		visible_index = self.get_visible_index(data_index)
		cell = self.visible[visible_index]

		# I need to tmp store the cells content height in case it is the same as the rows height and reduces along the
		# process.
		tmp_height = cell.content_size[1]

		cell.updateData(update_data)

		# check for size changes
		if cell.real_size[1] > self.real_size[1]:
			self.updateHeight(cell.real_size[1])
		elif cell.content_size[1] < tmp_height:
			if tmp_height == self.real_size[1]:
				self.recalculate_max_child_height()

	def updateColWidth(self, col_index, col_width, override_content_size=False):
		col_index = self.get_data_index(col_index)
		delta = col_width - self.col_widths[col_index]
		self.col_widths[col_index] = col_width
		cell = self.visible[self.get_visible_index(col_index)]
		cell.override_content_size = override_content_size
		cell.updateSize([col_width, self.real_size[1]])
		self.repositionChildren(cell, delta=[delta, 0])

	def updateHeight(self, height, override_content_size=False):
		delta = self.real_size[1] - height
		for child in self.visible:
			child.override_content_size = override_content_size
			child.updateSize([child.real_size[0], height])
		self.updateSize([self.real_size[0], height])
		self.updatePos([0, delta])

	def updateColWidths(self, col_widths, override_content_size=False):
		for i in range(len(self.visible)):
			cell = self.visible[i]
			data_index = self.get_visible_index(cell.data_index)
			self.updateColWidth(data_index, col_widths[data_index], override_content_size=override_content_size)
		self.col_widths = deepcopy(col_widths)
		self.updateSize([sum(self.col_widths), self.real_size[1]])


class GridLayout(NestedVerticalLayout):
	"""
	In data we store 
	"""
	grid_size = (0,0)
	col_widths: List = []
	row_heights: List = []
	def __init__(self, *args, col_widths=[], row_heights=[], **kwargs):
		super(GridLayout, self).__init__(*args, **kwargs)
		self.col_widths = deepcopy(col_widths)
		self.row_heights = deepcopy(row_heights)
		if not self.data:
			self.data = [{} for i in range(len(self.row_heights))]

	def get_cell_index(self, data_index):
		"""
		Here, we can only get the cell index for the rows.
		"""
		row_index, col_index = data_index
		row_index = super(GridLayout, self).get_data_index(row_index)
		return [row_index, col_index]

	def get_visible_cell_index(self, data_index):
		"""
		Here, we can only get the visible index for the rows.
		"""
		row_index, col_index = data_index
		row_visible_index = super(GridLayout, self).get_visible_index(row_index)
		return [row_visible_index, col_index]

	def addData(self, data_index, data):
		super(GridLayout, self).addData(data_index, data)

	def removeData(self, data_index):
		super(GridLayout, self).removeData(data_index)

	def insertCell(self, data_index, new_data, child_type: CellWrapper):
		"""
		NOTE: reposition of children has to be done "manually" by calling the corresponding method after insertCell
		"""
		visible_index = self.get_visible_cell_index(data_index)
		row_index, col_index = visible_index
		row = self.visible[row_index]
		row.insertWidgetAndData(data_index, new_data, child_type)

	def deleteCell(self, data_index):
		visible_index = self.get_visible_cell_index(data_index)
		row_index, col_index = visible_index
		row = self.visible[row_index]
		row.deleteWidget(col_index)

		# if row is empty, delete it; if row height has changed, reposition rows below
		data_row_index = self.get_data_index(data_index[0])
		if row.is_empty():
			self.deleteWidget(row_index)
		elif row.real_size[1] < self.row_heights[data_row_index]:
			delta = row.real_size[1] - self.row_heights[data_row_index]
			self.repositionChildren(row, delta=delta)
			self.row_heights[data_row_index] = row.real_size[1]

	def _add_real_size_for_kwargs(self, data_index):
		"""
		NOTE: This method is ONLY for internal purpose. Do NOT use this method at any time!

		Due to the internal logic that 'real_size' needs to be set from the very start for all additionalKwargs* methods
		and the implementation choice to set the real size on instantiation level from grid to row and from row to cell,
		we need to do so before calling the additionalKwargs* super methods. Since this is the same for all of them, we
		extracted this logic to this separate method.
		"""
		real_size = [sum(self.col_widths), self.row_heights[data_index]]

		data_index = self.get_data_index(data_index)
		raw_data = self.data[data_index]
		raw_data['init_data']['real_size'] = real_size

		return real_size

	def additionalKwargsInsert(self, data_index):
		real_size = self._add_real_size_for_kwargs(data_index)

		additional_data = super(GridLayout, self).additionalKwargsInsert(data_index)
		additional_data['col_widths'] = self.col_widths

		data_index = self.get_data_index(data_index)
		additional_data['real_size'] = real_size
		return additional_data

	def addWidget(self, data_index, additional_data):
		super(GridLayout, self).addWidget(data_index, additional_data)

	def additionalKwargsFillFirst(self, data_index, reference_child):
		real_size = self._add_real_size_for_kwargs(data_index)

		additional_data = super(GridLayout, self).additionalKwargsFillFirst(data_index, reference_child)
		additional_data['col_widths'] = self.col_widths

		data_index = self.get_data_index(data_index)
		additional_data['real_size'] = real_size
		return additional_data

	def additionalKwargsFillLast(self, data_index, reference_child):
		real_size = self._add_real_size_for_kwargs(data_index)

		additional_data = super(GridLayout, self).additionalKwargsFillLast(data_index, reference_child)
		additional_data['col_widths'] = self.col_widths

		data_index = self.get_data_index(data_index)
		additional_data['real_size'] = real_size
		return additional_data

	def insertCellAndReposition(self, data_index, new_data, child_type: CellWrapper):
		"""
		This method inserts a cell into an existing row. All other rows will be inserted an empty cell at the same
		position.
		"""
		visible_index = self.get_visible_cell_index(data_index)
		row_index, col_index = visible_index
		row = self.visible[row_index]

		# insert the widget
		row.insertNewAndReposition(col_index, new_data, child_type)

		# if inserted widget has a greater height (in this case the row will have already adjusted its height during the
		# insertion process), move rows below accordingly
		data_row_index = self.get_data_index(data_index[0])
		if row.real_size[1] > self.row_heights[data_row_index]:
			delta = self.row_heights[data_row_index] - row.real_size[1]
			self.repositionChildren(row, delta=[0, delta])
			self.row_heights[data_row_index] = row.real_size[1]

		# get col_index and col_width
		col_index = row.get_data_index(col_index)
		col_width = row.col_widths[col_index]

		# first insert empty, then updateColWidth
		for i in range(len(self.visible)):
			if i == row_index:
				continue
			child = self.visible[i]

			# TODO: reposition will get called twice by that. If there is performance issues, this needs to be changed.
			child.insertNewAndReposition(col_index, {}, child_type)
			child.updateColWidth(col_index, col_width)

	def updateCell(self, data_index, update_data):
		visible_index = self.get_visible_cell_index(data_index)
		row_index, col_index = visible_index
		row = self.visible[row_index]
		row.updateCell(data_index, update_data)

	def updateColWidths(self, col_widths, override_content_size=False):
		"""
		We dont want to update real_size, since this serves as the frame of the grid and should not get fit to its
		visible content.
		"""
		for row in self.visible:
			row.updateColWidths(col_widths, override_content_size=override_content_size)
		self.col_widths = deepcopy(col_widths)
		self.calculate_max_child_width()

	def updateRowHeights(self, row_heights, override_content_size=False):
		"""
		We dont want to update real_size, since this serves as the frame of the grid and should not get fit to its
		visible content.
		"""
		for i in range(len(self.visible)):
			row = self.visible[i]
			data_index = self.get_data_index(row.data_index)
			delta = self.row_heights[data_index] - row_heights[data_index]
			row.updateHeight(row_heights[data_index], override_content_size=override_content_size)
			self.repositionChildren(row, delta=[0, delta])
		self.row_heights = deepcopy(row_heights)



if __name__ == '__main__':
	print("Testing the syntactically correctness.")
