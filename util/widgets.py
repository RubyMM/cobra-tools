import os
import webbrowser
from PyQt5 import QtGui, QtCore, QtWidgets

from util import config, qt_theme

MAX_UINT = 4294967295
myFont=QtGui.QFont()
myFont.setBold(True)

def startup(cls):
	appQt = QtWidgets.QApplication([])
	
	#style
	appQt.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
	appQt.setPalette(qt_theme.dark_palette)
	appQt.setStyleSheet("QToolTip { color: #ffffff; background-color: #353535; border: 1px solid white; }")
	
	win = cls()
	win.show()
	appQt.exec_()
	config.write_config("config.ini", win.cfg)

def abort_open_new_file(parent, newfile, oldfile):
	# only return True if we should abort
	if newfile == oldfile:
		return True
	if oldfile:
		qm = QtWidgets.QMessageBox
		return qm.No == qm.question(parent.parent,'', "Do you really want to load "+os.path.basename(newfile)+"? You will lose unsaved work on "+os.path.basename(oldfile)+"!", qm.Yes | qm.No)

def showdialog(str):
	msg = QtWidgets.QMessageBox()
	msg.setIcon(QtWidgets.QMessageBox.Information)
	msg.setText(str)
	#msg.setInformativeText("This is additional information")
	msg.setWindowTitle("Error")
	#msg.setDetailedText("The details are as follows:")
	msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
	retval = msg.exec_()

def vbox(parent, grid):
	"""Adds a grid layout"""
	# vbox = QtWidgets.QVBoxLayout()
	# vbox.addLayout(grid)
	# vbox.addStretch(1.0)
	# vbox.setSpacing(0)
	# vbox.setContentsMargins(0,0,0,0)
	parent.setLayout(grid)

class LabelEdit(QtWidgets.QWidget):
	def __init__(self, name, ):
		QtWidgets.QWidget.__init__(self,)
		self.shader_container = QtWidgets.QWidget()
		self.label = QtWidgets.QLabel(name)
		self.entry = QtWidgets.QLineEdit()
		vbox = QtWidgets.QHBoxLayout()
		vbox.addWidget(self.label)
		vbox.addWidget(self.entry)
		# vbox.addStretch(1)
		self.setLayout(vbox)

class LabelCombo(QtWidgets.QWidget):
	def __init__(self, name, options):
		QtWidgets.QWidget.__init__(self,)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		self.shader_container = QtWidgets.QWidget()
		self.label = QtWidgets.QLabel(name)
		self.entry = QtWidgets.QComboBox()
		self.entry.addItems(options)
		sizePolicy.setHeightForWidth(self.entry.sizePolicy().hasHeightForWidth())
		self.entry.setSizePolicy(sizePolicy)
		# self.entry.setMaxVisibleItems(10)
		self.entry.setEditable(True)
		vbox = QtWidgets.QHBoxLayout()
		vbox.addWidget(self.label)
		vbox.addWidget(self.entry)
		self.setLayout(vbox)

	def setText(self, txt):
		indx = self.entry.findText(txt)
		# add new item if not found
		if indx == -1:
			self.entry.addItem(txt)
			indx = self.entry.findText(txt)
		self.entry.setCurrentIndex(indx)

class MySwitch(QtWidgets.QPushButton):
	PRIMARY =   QtGui.QColor(53, 53, 53)
	SECONDARY = QtGui.QColor(35, 35, 35)
	OUTLINE = QtGui.QColor(122, 122, 122)
	TERTIARY =  QtGui.QColor(42, 130, 218)
	BLACK =  QtGui.QColor(0, 0, 0)
	WHITE =     QtGui.QColor(255, 255, 255)
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setCheckable(True)
		self.setMinimumWidth(66)
		self.setMinimumHeight(22)

	def setValue(self, v):
		self.setChecked(v)

	def paintEvent(self, event):
		label = "ON" if self.isChecked() else "OFF"
		bg_color = self.TERTIARY if self.isChecked() else self.PRIMARY

		radius = 10
		width = 32
		center = self.rect().center()

		painter = QtGui.QPainter(self)
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		painter.translate(center)
		painter.setBrush(self.SECONDARY)

		pen = QtGui.QPen(self.WHITE)
		pen.setWidth(0)
		painter.setPen(pen)

		painter.drawRoundedRect(QtCore.QRect(-width, -radius, 2*width, 2*radius), radius, radius)
		painter.setBrush(QtGui.QBrush(bg_color))
		sw_rect = QtCore.QRect(-radius, -radius, width + radius, 2*radius)
		if not self.isChecked():
			sw_rect.moveLeft(-width)
		painter.drawRoundedRect(sw_rect, radius, radius)
		painter.drawText(sw_rect, QtCore.Qt.AlignCenter, label)
class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(100)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(100)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

class MatcolInfo():
	def __init__(self, attrib, tooltips={}):
		"""attrib must be pyffi matcol InfoWrapper object"""
		# QtWidgets.QWidget.__init__(self,)
		self.attrib = attrib
		self.label = QtWidgets.QLabel(attrib.name)
		
		self.data = QtWidgets.QWidget()
		layout = QtWidgets.QHBoxLayout()
		layout.setSpacing(0)
		# layout.setMargin(0)
		layout.setContentsMargins(0,0,0,0)
		buttons = [self.create_field(i) for i in attrib.info.flags if i]
		for button in buttons:
			layout.addWidget(button)
		self.data.setLayout(layout)
		# get tooltip
		tooltip = tooltips.get(self.attrib.name, "Undocumented attribute.")
		self.data.setToolTip(tooltip)
		self.label.setToolTip(tooltip)

	def create_field(self, ind):
		default = self.attrib.info.value[ind]

		def update_ind( v):
			# use a closure to remember index
			# print(self.attrib, ind, v)
			self.attrib.info.value[ind] = v

		def update_ind_int( v):
			# use a closure to remember index
			# print(self.attrib, ind, v)
			self.attrib.info.value[ind] = int(v)

		t = str(type(default))
		if "float" in t:
			field = QtWidgets.QDoubleSpinBox()
			field.setDecimals(3)
			field.setRange(-10000, 10000)
			field.setSingleStep(.05)
			field.valueChanged.connect(update_ind)
		elif "bool" in t:
			# field = QtWidgets.QSpinBox()
			field = MySwitch()
			field.clicked.connect(update_ind)
		elif "int" in t:
			default = int(default)
			# field = QtWidgets.QSpinBox()
			field = QtWidgets.QDoubleSpinBox()
			field.setDecimals(0)
			field.setRange(-MAX_UINT, MAX_UINT)
			field.valueChanged.connect(update_ind_int)
		field.setValue(default)
		field.setMinimumWidth(50)
		field.setAlignment(QtCore.Qt.AlignCenter)
		field.setContentsMargins(0,0,0,0)
		return field

class VectorEntry():
	def __init__(self, attrib, tooltips={}):
		"""attrib must be pyffi attrib object"""
		# QtWidgets.QWidget.__init__(self,)
		self.attrib = attrib
		self.label = QtWidgets.QLabel(attrib.name)
		
		self.data = QtWidgets.QWidget()
		layout = QtWidgets.QHBoxLayout()
		buttons = [self.create_field(i) for i in range(len(attrib.value))]
		for button in buttons:
			layout.addWidget(button)
		self.data.setLayout(layout)

		# get tooltip
		tooltip = tooltips.get(self.attrib.name, "Undocumented attribute.")
		self.data.setToolTip(tooltip)
		self.label.setToolTip(tooltip)

	
	def create_field(self, ind):
		default = self.attrib.value[ind]

		def update_ind( v):
			# use a closure to remember index
			# print(self.attrib, ind, v)
			self.attrib.value[ind] = v

		def update_ind_int( v):
			# use a closure to remember index
			# print(self.attrib, ind, v)
			self.attrib.value[ind] = int(v)

		t = str(type(default))
		if "float" in t:
			field = QtWidgets.QDoubleSpinBox()
			field.setDecimals(3)
			field.setRange(-10000, 10000)
			field.setSingleStep(.05)
			field.valueChanged.connect(update_ind)
		elif "bool" in t:
			# field = QtWidgets.QSpinBox()
			field = MySwitch()
			field.clicked.connect(update_ind)
		elif "int" in t:
			default = int(default)
			# field = QtWidgets.QSpinBox()
			field = QtWidgets.QDoubleSpinBox()
			field.setDecimals(0)
			field.setRange(-MAX_UINT, MAX_UINT)
			field.valueChanged.connect(update_ind_int)
		field.setValue(default)
		field.setMinimumWidth(50)
		return field

class FileWidget(QtWidgets.QLineEdit):
	"""An entry widget that starts a file selector when clicked and also accepts drag & drop.
	Displays the current file's basename.
	"""

	def __init__(self, parent, cfg, description="", ask_user=True):
		super(FileWidget, self).__init__(parent)
		self.parent = parent
		self.cfg = cfg
		if not self.cfg:
			self.cfg["dir_in"]  = "C://"
		self.setDragEnabled(True)
		self.setReadOnly(True)
		self.filepath = ""
		self.description = description
		self.setToolTip(self.description)
		self.ask_user = ask_user
			
	def abort_open_new_file(self, new_filepath):
		# only return True if we should abort
		if not self.ask_user:
			return False
		if new_filepath == self.filepath:
			return True
		if self.filepath:
			qm = QtWidgets.QMessageBox
			return qm.No == qm.question(self,'', "Do you really want to load "+os.path.basename(new_filepath)+"? You will lose unsaved work on "+os.path.basename(self.filepath)+"!", qm.Yes | qm.No)
			
	def accept_file(self, filepath):
		if os.path.isfile(filepath):
			if os.path.splitext(filepath)[1].lower() in (".flac", ".wav"):
				if not self.abort_open_new_file(filepath):
					self.filepath = filepath
					self.cfg["dir_in"], filename = os.path.split(filepath)
					self.setText(filename)
					self.parent.poll()
			else:
				showdialog("Unsupported File Format")
				
	def get_files(self, event):
		data = event.mimeData()
		urls = data.urls()
		if urls and urls[0].scheme() == 'file':
			return urls
		
	def dragEnterEvent(self, event):
		if self.get_files(event):
			event.acceptProposedAction()
			self.setFocus(True)

	def dragMoveEvent(self, event):
		if self.get_files(event):
			event.acceptProposedAction()
			self.setFocus(True)

	def dropEvent(self, event):
		urls = self.get_files(event)
		if urls:
			filepath = str(urls[0].path())[1:]
			self.accept_file(filepath)
			
	def ask_open(self):
		filepath = QtWidgets.QFileDialog.getOpenFileName(self, 'Open '+self.description, self.cfg["dir_in"], "Audio files (*.flac *.wav)")[0]
		self.accept_file(filepath)
		
	def mousePressEvent(self, event):
		self.ask_open()

class MainWindow(QtWidgets.QMainWindow):

	def __init__(self, name, ):
		QtWidgets.QMainWindow.__init__(self)		
		
		self.central_widget = QtWidgets.QWidget(self)
		self.setCentralWidget(self.central_widget)
		
		self.name = name
		# self.resize(720, 400)
		self.setWindowTitle(name)
		try:
			base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
			self.setWindowIcon(QtGui.QIcon(os.path.join(base_dir,'icons/frontier.png')))
		except: pass
		
		self.cfg = config.read_config("config.ini")
		

	def report_bug(self):
		webbrowser.open("https://github.com/OpenNaja/cobra-tools/issues/new", new=2)
		
	def online_support(self):
		webbrowser.open("https://github.com/OpenNaja/cobra-tools/wiki", new=2)

	def update_file(self, filepath):
		self.cfg["dir_in"], file_name = os.path.split(filepath)
		self.setWindowTitle(self.name+" "+ file_name)
		
	def add_to_menu(self, button_data):
		for submenu, name, func, shortcut in button_data:
			button = QtWidgets.QAction(name, self)
			button.triggered.connect(func)
			if shortcut: button.setShortcut(shortcut)
			submenu.addAction(button)
			