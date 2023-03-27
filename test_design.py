from gui_framework.base_designs import BaseDesign
from gui_framework.base_layouts import VerticalLayout, ChildWidget
from gui_framework.advanced_layouts import GridLayout, RowLayout, Cell

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import ListProperty, ObjectProperty, NumericProperty, BooleanProperty, StringProperty


# testing base stuff

class TestWidget(ChildWidget):
	this_text = StringProperty('')
	real_size = ListProperty((Window.width, Window.height / 3))
	def __init__(self, *args, **kwargs):
		print("args: ", args)
		print("kwargs: ", kwargs)
		super(TestWidget, self).__init__(*args, **kwargs)
		self.is_bottom_widget = True

	def updatePos(self, delta):
		super(TestWidget, self).updatePos(delta)
		#print(delta)

	def to_data(self) -> dict:
		data = super(TestWidget, self).to_data()
		data['init_data']['this_text'] = self.this_text
		return data


class TestLayout(VerticalLayout):
	def __init__(self, **kwargs):
		super(TestLayout, self).__init__(**kwargs)


class TestDesign(BaseDesign):
	def __init__(self, **kwargs):
		super(TestDesign, self).__init__(**kwargs)

		# create layout
		layout = TestLayout(real_pos=(0,0), real_size=(Window.width, Window.height / 4))
		self.layouts.append(layout)
		self.add_widget(layout)

		# add data and widgets to layout
		data = [
			{
				'child_type': TestWidget,
				'init_data': {
					'this_text': 'This is a test.',
					'real_size': (Window.width * 2, Window.height / 3)
				}
			},
			{
				'child_type': TestWidget,
				'init_data': {
					'this_text': '1. This is a test.',
					'real_size': (Window.width, Window.height / 3)
				}
			},
			{
				'child_type': TestWidget,
				'init_data': {
					'this_text': '2. This is a test.',
					'real_size': (Window.width, Window.height / 3)
				}
			},
		]

		layout.data = data
		layout.fillInChildren()

		"""
		for raw_data in data:
			layout.insertWidgetAndData(0, raw_data['init_data'], raw_data['child_type'])
			new_child = layout.visible[-1]
			print(new_child.real_pos)
			print(new_child.data_index)
		print(layout.data)
		"""


# testing grid

class TestCell(TestWidget, Cell):
	pass

class TestRow(RowLayout):
	pass

class TestGrid(GridLayout):
	pass


class GridDesign(BaseDesign):
	def __init__(self, **kwargs):
		super(GridDesign, self).__init__(**kwargs)

		# create layout
		layout = TestGrid(
			col_widths=[Window.width * 2, Window.width, Window.width],
			row_heights=[Window.height / 3],
			real_pos=(0,0),
			real_size=(Window.width, Window.height / 2)
		)
		self.layouts.append(layout)
		self.add_widget(layout)

		# add data and widgets to layout
		row_data = [
			{
				'child_type': TestCell,
				'init_data': {
					'this_text': 'This is a test.',
					'real_size': (Window.width * 2, Window.height / 3)
				}
			},
			{
				'child_type': TestCell,
				'init_data': {
					'this_text': '1. This is a test.',
					'real_size': (Window.width, Window.height / 3)
				}
			},
			{
				'child_type': TestCell,
				'init_data': {
					'this_text': '2. This is a test.',
					'real_size': (Window.width, Window.height / 3)
				}
			},
		]
		data = [
			{
				'child_type': TestRow,
				'init_data': {
					'real_size': (Window.width, Window.height / 3),
					'data': row_data
				}
			},
			{
				'child_type': TestRow,
				'init_data': {
					'real_size': (Window.width, Window.height / 3),
					'data': row_data
				}
			},
		]

		layout.data = data
		layout.fillInChildren()

		print(layout.visible)
		print(layout.visible[0].visible)



class TestApp(App):
	def build(self):
		return GridDesign()


if __name__ == '__main__':
	print("Testing the syntactically correctness.")
	TestApp().run()
