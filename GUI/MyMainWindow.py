from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QDesktopWidget, QMessageBox, QAction, qApp,
    QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QFileDialog,
    QGridLayout, QStackedWidget, QLineEdit, QTextEdit, QSlider, QScrollArea)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from assistant import assistant
from model import my_guitar, my_music
from model.my_guitar import *
from model import program as m_p
from . import varible
from .BarWidget import BarWidget
from .WheelWidget import WheelWidget

import sys
import time
import threading
import ctypes
import inspect
import numpy as np
from PIL import ImageGrab, Image

class MyMainWindow(QMainWindow):
    tuning = {"E A D G B E": [52, 47, 43, 38, 33, 28]}
    def __init__(self):
        super().__init__()
        self.initVariable()
        self.initUI()

        if self.editing_component == -1:
            self.new_music_project()
            # self.open_Gmusic_file()

    def initVariable(self):
        self.component = [] # 存放打开的音乐项目，最多5个
        self.editing_component = -1   # 正在编辑的项目，若没有则为-1
        self.editing_track = -1     # 正在编辑的音轨

        self.fs, self.fluid = self.load_soundfont()  # 初始化音色库
        self.varible = varible

    def initUI(self):
        self.resize(1000, 600)
        self.setWindowTitle("Guitar Music")
        self.center()

        self.set_widget()
        self.set_menu()

    # 设置菜单栏
    def set_menu(self):
        # menubar = QMenuBar(self)
        menubar = self.menuBar()
        menu = menubar.addMenu("文件(File)")
        menu.addAction("新建", lambda: self.new_music_project(), Qt.CTRL + Qt.Key_N)  # 带图标，文字
        menu.addAction("打开", lambda: self.thread_it(self.open_Gmusic_file()), Qt.CTRL + Qt.Key_O)
        menu.addSeparator()
        menu.addAction("保存", lambda: self.save_Gmusic_file(), Qt.CTRL + Qt.Key_S)
        menu.addAction("另存为", lambda: self.save_other_Gmusic_file, Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        menu.addSeparator()
        m = menu.addMenu("导入")
        m.addAction("MIDI", lambda: self.import_midi())
        m = menu.addMenu("导出")
        m.addAction("MIDI...", lambda: self.thread_it(self.leading_out_midi()))
        m.addAction("PNG...", lambda: self.save_img())
        menu.addSeparator()
        menu.addAction("退出", lambda: print("退出"), Qt.ALT + Qt.Key_F4)

        menu = menubar.addMenu("编辑(Edit)")
        menu.addAction("复制", lambda: self.copy_bar(), Qt.CTRL + Qt.Key_C)
        menu.addAction("粘贴", lambda: self.paste_bar(), Qt.CTRL + Qt.Key_V)
        menu.addSeparator()
        menu.addAction("删除本节", lambda: self.remove_bar(), Qt.CTRL + Qt.Key_D)

        menu = menubar.addMenu("音轨(Track)")
        menu.addAction("添加", lambda: print("添加音轨"))
        menu.addAction("删除", lambda: print("删除音轨"))
        menu.addSeparator()
        menu.addAction("播放", lambda: self.thread_it(self.play_music()))

        menu = menubar.addMenu("帮助(Help)")
        menu.addAction("关于Guitar Music", lambda: print("关于Guitar Music"))
        menu.addSeparator()
        menu.addAction("用户中心", lambda: print("用户中心"))

    # 设置布局
    def set_widget(self):
        left_part = self._create_wedget(self,300,600,0,0)
        right_part = self._create_wedget(self,700,600,300,0)

        music_box = self._create_wedget(left_part, 300, 400, 0, 0, "#E0EEEE")
        note_box = self._create_wedget(left_part, 300, 200, 0, 400, "#E0EEEE")

        play_box = self._create_wedget(right_part,700,100,0,0,"#FFF8DC")
        draw_box = self._create_wedget(right_part,700,500,0,100,"#FCFCFC")

        self.set_music_message_layout(music_box)
        self.set_note_message_layout(note_box)
        self.set_play_layout(play_box)
        self.set_draw_layout(draw_box)

    # 设置音乐信息布局
    def set_music_message_layout(self, box):
        def change_to_music():
            self.stackedWidget.setCurrentIndex(0)
            music_but.setStyleSheet("height:30;width:150;border:0;background:#E0EEEE")
            track_but.setStyleSheet("height:30;width:150;border:0;background:#C9C9C9")
        def change_to_track():
            self.stackedWidget.setCurrentIndex(1)
            track_but.setStyleSheet("height:30;width:150;border:0;background:#E0EEEE")
            music_but.setStyleSheet("height:30;width:150;border:0;background:#C9C9C9")
        music_but = QPushButton("音乐", box)
        music_but.setStyleSheet("height:30;width:150;border:0;background:#E0EEEE")
        music_but.clicked.connect(lambda: change_to_music())
        music_but.move(0,23)
        track_but = QPushButton("音轨", box)
        track_but.setStyleSheet("height:30;width:150;border:0;background:#C9C9C9")
        track_but.clicked.connect(lambda: change_to_track())
        track_but.move(150, 23)

        show = QWidget(box)
        show.resize(300, 347)
        show.move(0, 53)

        self.stackedWidget = QStackedWidget(show)
        self.stackedWidget.addWidget(self.__music_widget())
        self.stackedWidget.addWidget(self.__track_widget())
        self.stackedWidget.move(0,23)

        # change_to_music()

    def __music_widget(self):
        music = QWidget()

        name = QLabel('音乐名称')
        artist = QLabel('艺术家')
        meter = QLabel('节拍')
        bpm = QLabel('bpm')

        self.music_name_edit = QLineEdit()
        self.music_name_edit.textChanged.connect(lambda: self.set_component_name())
        self.music_artist_edit = QLineEdit()
        self.music_artist_edit.textChanged.connect(lambda: self.set_artist_name())
        self.music_meter_edit = QComboBox()
        self.music_meter_edit.addItem("四分音符")
        # self.music_meter_edit.addItem("八分音符")

        self.music_bpm_edit = QSlider(Qt.Horizontal)   # 速度滑块
        self.music_bpm_edit.setRange(40, 360)
        self.music_bpm_edit.setValue(120)
        self.bpm_num = QLabel(str(self.music_bpm_edit.value()))
        self.music_bpm_edit.valueChanged.connect(lambda: self.set_bpm())

        grid = QGridLayout()
        grid.setContentsMargins(30,0,0,0) # 设置边界
        grid.setSpacing(10) # 设置内部组件间距

        grid.addWidget(name, 1, 0)
        grid.addWidget(self.music_name_edit, 1, 1)
        grid.addWidget(artist, 2, 0)
        grid.addWidget(self.music_artist_edit, 2, 1)
        grid.addWidget(meter, 3, 0)
        grid.addWidget(self.music_meter_edit, 3, 1)
        grid.addWidget(bpm, 4, 0)
        grid.addWidget(self.music_bpm_edit, 4, 1)
        grid.addWidget(self.bpm_num, 4, 2)

        music.setLayout(grid)
        return music

    def __track_widget(self):
        track = QWidget()

        name = QLabel('音轨')
        change = QLabel('切换音轨')
        program = QLabel('乐器')
        tuning = QLabel('调音')

        self.track_name_edit = QLineEdit()
        self.track_name_edit.textEdited.connect(lambda: self.set_track_name())
        change_edit = QComboBox()
        change_edit.addItem("音轨1")
        # change_edit.addItem("八分音符")
        self.program_edit = QComboBox()
        self.program_edit.addItem("24 " + m_p.program_dict["24"])
        self.program_edit.addItem("25 " + m_p.program_dict["25"])
        self.program_edit.addItem("26 " + m_p.program_dict["26"])
        self.program_edit.addItem("27 " + m_p.program_dict["27"])
        self.program_edit.addItem("28 " + m_p.program_dict["28"])
        self.program_edit.currentIndexChanged.connect(lambda : self.set_track_program())

        tuning_edit = QPushButton('E A D G B E')

        playing_turning = QPushButton('▶')
        playing_turning.setMaximumWidth(35)
        playing_turning.clicked.connect(lambda: self.thread_it(self.play_tuning()))

        grid = QGridLayout()
        grid.setContentsMargins(30,0,0,0) # 设置边界
        grid.setSpacing(10) # 设置内部组件间距

        grid.addWidget(name, 1, 0)
        grid.addWidget(self.track_name_edit, 1, 1)
        grid.addWidget(change, 2, 0)
        grid.addWidget(change_edit, 2, 1)
        grid.addWidget(program, 3, 0)
        grid.addWidget(self.program_edit, 3, 1)
        grid.addWidget(tuning, 4, 0)
        grid.addWidget(tuning_edit, 4, 1)
        grid.addWidget(playing_turning, 4, 2)

        track.setLayout(grid)

        return track

    # 设置音符信息布局
    def set_note_message_layout(self, box):
        def set_note_type(type):
            self.varible.note_type = type
        def set_special_note(note):
            self.varible.special_note = note
        self.note_1_button = QPushButton("全音符")
        self.note_1_button.clicked.connect(lambda: set_note_type(1))
        self.note_2_button = QPushButton("二分音符")
        self.note_2_button.clicked.connect(lambda: set_note_type(2))
        self.note_4_button = QPushButton("四分音符")
        self.note_4_button.clicked.connect(lambda: set_note_type(4))
        self.note_8_button = QPushButton("八分音符")
        self.note_8_button.clicked.connect(lambda: set_note_type(8))
        self.note_16_button = QPushButton("十六分音符")
        self.note_16_button.clicked.connect(lambda: set_note_type(16))
        # self.note_32_button = QPushButton("三十二分音符")
        # self.note_32_button.clicked.connect(lambda: set_note_type(32))

        self.note_downDrum_button = QPushButton("底鼓")
        self.note_downDrum_button.clicked.connect(lambda: set_special_note("Down_Drum"))
        self.note_upDrum_button = QPushButton("指鼓")
        self.note_upDrum_button.clicked.connect(lambda: set_special_note("Up_Drum"))
        self.note_slide_button = QPushButton("滑音")
        self.note_slide_button.clicked.connect(lambda: set_special_note("Pitch_Note"))
        self.note_harm_button = QPushButton("泛音")
        self.note_harm_button.clicked.connect(lambda: set_special_note("Harm_Note"))
        self.note_vibrato_button = QPushButton("颤音")
        self.note_vibrato_button.clicked.connect(lambda: set_special_note("Vibrato_Note"))
        self.note_muffled_button = QPushButton("闷音")
        self.note_muffled_button.clicked.connect(lambda: set_special_note("Muffled_Sound"))
        self.note_click_button = QPushButton("点弦")
        self.note_click_button.clicked.connect(lambda: set_special_note("Click_Note"))
        self.note_cut_button = QPushButton("空拍")
        self.note_cut_button.clicked.connect(lambda: set_special_note("Cut_Sound"))

        grid = QGridLayout()
        # grid.setContentsMargins(30, 0, 0, 0)  # 设置边界
        # grid.setSpacing(10)  # 设置内部组件间距

        grid.addWidget(self.note_1_button, 1, 0)
        grid.addWidget(self.note_2_button, 1, 1)
        grid.addWidget(self.note_4_button, 1, 2)
        grid.addWidget(self.note_8_button, 1, 3)

        grid.addWidget(self.note_16_button, 2, 0)
        # grid.addWidget(self.note_32_button, 2, 1)

        grid.addWidget(self.note_downDrum_button, 3, 0)
        grid.addWidget(self.note_upDrum_button, 3, 1)
        grid.addWidget(self.note_slide_button, 3, 2)
        grid.addWidget(self.note_harm_button, 3, 3)

        grid.addWidget(self.note_vibrato_button, 4, 0)
        grid.addWidget(self.note_muffled_button, 4, 1)
        grid.addWidget(self.note_click_button, 4, 2)
        grid.addWidget(self.note_cut_button, 4, 3)

        box.setLayout(grid)


    def set_play_layout(self, box):
        # 这里设置播放停止的按钮，切换歌曲窗口的下拉条，（当前歌曲的小节数，时间，放着或者musicbox里）
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setContentsMargins(40,40,40,40)

        self.play_music_combo_box = QComboBox()
        self.play_music_combo_box.currentIndexChanged.connect(lambda : self.change_component())

        self.play = QPushButton('▶')
        self.play.setMaximumSize(30, 30)
        self.play.setMinimumSize(30, 30)
        self.play.setStyleSheet("width:30;height:30;border:1px solid #6495ED;border-radius:15px;background:#6495ED;font-size:20px")
        self.play.clicked.connect(lambda :self.play_music())

        self.stop = QPushButton('■')
        self.stop.setMaximumSize(30, 30)
        self.stop.setMinimumSize(30, 30)
        self.stop.setStyleSheet(
            "width:30;height:30;border:1px solid #6495ED;border-radius:15px;background:#6495ED;font-size:20px")
        self.stop.clicked.connect(lambda :self.stop_music())
        self.stop.hide()
        bar_count = QLabel("小节数")
        self.bar_count_edit = QLabel()

        time = QLabel("时间")

        grid.addWidget(self.play_music_combo_box, 1, 0)
        grid.addWidget(self.play, 1, 1)
        grid.addWidget(self.stop, 1, 1)
        grid.addWidget(bar_count, 1, 2)
        grid.addWidget(self.bar_count_edit, 1, 3)
        grid.addWidget(time, 1, 4)

        box.setLayout(grid)

    def set_draw_layout(self, box):
        self.wheel_draw = QWidget()
        self.wheel_draw.resize(700,10000)

        # 音乐名称
        self.component_name = QLabel(self.wheel_draw)
        self.component_name.move(0, 50)
        self.component_name.setStyleSheet("font:20pt '楷体'")

        # 艺术家
        artist_name = QLabel(self.wheel_draw)
        artist_name.setText("艺术家  ")
        artist_name.setStyleSheet("font:11pt '宋体'")
        artist_name.resize(50, 50)
        artist_name.move(50, 100)
        self.artist_name = QLabel(self.wheel_draw)
        self.artist_name.setStyleSheet("font:11pt '宋体'")
        self.artist_name.move(100, 100)
        self.artist_name.resize(200, 50)

        self.play_move = QPushButton(self.wheel_draw)
        self.play_move.setStyleSheet("border:0;height:80;width:1;background:#1C86EE;opacity:0.5")
        self.play_move.move(50, 150)
        self.play_move.hide()

        self.scrol = WheelWidget(box)
        self.scrol.right_key.connect(self.create_new_barWidget)
        self.scrol.resize(700, 500)
        self.scrol.setWidget(self.wheel_draw)
        self.scroll_bar = self.scrol.verticalScrollBar()
        # 这里主要是绘制用，首先就需要一个滚动条

    # 建立一个布局空间
    def _create_wedget(self, parent, sizeX, sizeY, moveX=0, moveY=0, bgcolor="ffffff"):
        wedget = QWidget(parent)
        wedget.resize(sizeX, sizeY)
        wedget.move(moveX, moveY)
        wedget.setStyleSheet("background-color:" + bgcolor)
        return wedget

    # 居中
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 加载音色库
    def load_soundfont(self):
        w = self._create_wedget(None,200,100)
        w.show()
        fs, fluid = assistant.load_soundfont("soundfont/Hubbe64MB.sf2")
        fs.start()
        w.close()
        return fs, fluid

    # 新建一个新的音乐项目
    def new_music_project(self):
        if self.component.__len__() <= 5:
            component = my_guitar.Component(self.fs, self.fluid)
            self.component.append({"component": component, "path": None})
            self.editing_component = self.component.__len__() - 1
            self.set_music()
        else:
            print("太多了，不能再新建了")

    # 打开一个gmusic文件
    def open_Gmusic_file(self):
        path, filetype = QFileDialog.getOpenFileName(self, "选取文件", "/Users/Kelisiya/Desktop",
                                                          "Gmusic Files (*.gmusic)")
        if path == '': return
        if self.component.__len__() <= 5:
            component = my_guitar.Component(self.fs, self.fluid)
            component.load_Gmusic(path)
            self.component.append({"component": component, "path": path})
            self.editing_component = self.component.__len__() - 1
            self.set_music()
        else:
            # print("太多了，不能再新建了")
            pass

    # 保存(已完成)
    def save_Gmusic_file(self):
        if self.editing_component == -1: return
        if not self.component[self.editing_component]["path"]:
            self.component[self.editing_component]["path"], type = \
                QFileDialog.getSaveFileName(self, 'save file', '/home/jm/study', "Gmusic Files (*.gmusic)")

        path = self.component[self.editing_component]["path"]
        if path == "": return
        print(path)
        self.component[self.editing_component]["component"].save_Gmusic(path)

    # 另存为Gmusic(已完成)
    def save_other_Gmusic_file(self):
        if self.editing_component == -1: return
        self.component[self.editing_component]["path"], type = \
            QFileDialog.getSaveFileName(self, 'save file', '/home/jm/study', "Gmusic Files (*.gmusic)")

        path = self.component[self.editing_component]["path"]
        if path == "": return
        self.component[self.editing_component]["component"].save_Gmusic(path)

    # 导出为midi文件(已完成)
    def leading_out_midi(self):
        if self.editing_component == -1: return
        path, type = \
            QFileDialog.getSaveFileName(self, 'save file', '/home/jm/study', "Gmusic Files (*.midi)")

        if path == '': return
        pattern = assistant.change_music_to_pattern(self.component[self.editing_component]["component"])
        assistant.save_midi_file(path, pattern)

    # 根据当前的正在编辑的音乐设置音乐相关信息
    def set_music(self):
        component = self.component[self.editing_component]["component"]

        self.music_name_edit.setText(component.name)
        self.music_artist_edit.setText(component.artist)
        if component.denominator == 4:
            self.music_meter_edit.setCurrentIndex(0)
        elif component.denominator == 8:
            self.music_meter_edit.setCurrentIndex(1)
        self.music_bpm_edit.setValue(component.bpm)

        self.editing_track = 0
        self.track_name_edit.setText(component.track_msg[self.editing_track].name)
        # 切换音轨 = 添加所有音轨，显示当前音轨(主音轨不添加)
        self.program_edit.setCurrentIndex(component.track_msg[self.editing_track].program - 24)
        # 调音 = 当前音轨调音

        self.play_music_combo_box.addItem(component.name)
        self.play_music_combo_box.setCurrentIndex(self.editing_component)
        self.bar_count_edit.setText(str(self.component[self.editing_component]["component"].track_msg[self.editing_track].bars.__len__()))
        # 显示时间

        self.draw_component_track()

    # 设置读取的midi音乐
    def set_my_music(self):
        component = self.component[self.editing_component]["component"]

        # self.music_name_edit.setText(component.name)
        # self.music_artist_edit.setText(component.artist)
        # if component.denominator == 4:
        #     self.music_meter_edit.setCurrentIndex(0)
        # elif component.denominator == 8:
        #     self.music_meter_edit.setCurrentIndex(1)
        # self.music_bpm_edit.setValue(component.bpm)

        # self.editing_track = 0
        self.track_name_edit.setText("midi")
        # 切换音轨 = 添加所有音轨，显示当前音轨(主音轨不添加)
        # self.program_edit.setCurrentIndex(component.track_msg[self.editing_track].program - 24)
        # 调音 = 当前音轨调音

        self.play_music_combo_box.addItem("midi")
        self.play_music_combo_box.setCurrentIndex(self.editing_component)
        # self.bar_count_edit.setText(str(self.component[self.editing_component]["component"].track_msg[self.editing_track].bars.__len__()))
        # 显示时间

        # self.draw_component_track()

    # 设置音乐名称，包括显示在画布上
    def set_component_name(self):
        self.component_name.setText(self.music_name_edit.text())
        self.component_name.adjustSize()
        self.component[self.editing_component]["component"].name = self.music_name_edit.text()
        # self.component_name.resize()
        # print(self.component_name.size().width())
        self.component_name.move(350-self.component_name.size().width()//2 ,50)

    # 设置艺术家名称，包括显示在画布上
    def set_artist_name(self):
        self.artist_name.setText(self.music_artist_edit.text())
        # self.component[self.editing_component]["component"].name = self.music_name_edit.text()

    # 绘画音轨
    def draw_component_track(self):
        if self.editing_component == -1 or self.editing_track == -1:
            return
        track = self.component[self.editing_component]["component"].track_msg[self.editing_track]
        for old_bar in self.scrol.barWidgets:
            old_bar.deleteLater()
        self.scrol.barWidgets = []
        self.scrol.editing_barWidget = 0
        for index, bar in enumerate(track.bars):
            x = (index + 2) % 2
            y = index // 2
            self.wheel_draw.repaint()
            b = BarWidget(self.wheel_draw, 50+x*300, 150+y*120, bar)
            b.clicked.connect(self.scrol.change_editing_bar_widget)  # 接受点击后传回来的哪个barWidget
            b.show()
            self.scrol.barWidgets.append(b)

    def create_new_barWidget(self, x, y ,y_index):
        # self.wheel_draw.repaint()
        # # 这里要把新的bar加入component
        bar = my_guitar.Bar()
        self.component[self.editing_component]["component"].track_msg[self.editing_track].add_bar(bar)
        b = BarWidget(self.wheel_draw, 50 + x * 300, 150 + y * 120, bar)
        b.clicked.connect(self.scrol.change_editing_bar_widget)  # 接受点击后传回来的哪个barWidget
        b.show()
        note = my_guitar.None_Note(varible.note_type)
        b.bar.add_note(note, y)
        b.repaint()

        self.scrol.barWidgets.append(b)
        self.scrol.barWidgets[self.scrol.editing_barWidget+1].move_pitch_input(x,y_index)
        self.bar_count_edit.setText(str(self.component[self.editing_component]["component"].track_msg[self.editing_track].bars.__len__()))

    # 打包进线程（耗时的操作）
    @staticmethod
    def thread_it(func, *args):
        t = threading.Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动
        # t.join()          # 阻塞--会卡死界面！

    # 设置音轨名称
    def set_track_name(self):
        self.component[self.editing_component]["component"].track_msg[self.editing_track].set_track_name(self.track_name_edit.text())

    # 更换音轨乐器
    def set_track_program(self):
        self.component[self.editing_component]["component"].track_msg[self.editing_track].program = self.program_edit.currentIndex()+24

    # 设置bpm
    def set_bpm(self):
        self.bpm_num.setText(str(self.music_bpm_edit.value()))
        self.component[self.editing_component]["component"].bpm = self.music_bpm_edit.value()
        com = self.component[self.editing_component]["component"]
        com.calculate_tick_with_bpm(com.bpm, com._resolution, com.denominator)

    # 播放调音
    def play_tuning(self):
        self.fs.program_select(0, self.fluid, 0, self.program_edit.currentIndex()+24)
        for i in reversed(varible.track_base_tuning):
            self.fs.noteon(0, i, 90)
            time.sleep(0.4)
            self.fs.noteoff(0, i)

    # 播放音乐
    def play_music(self):
        print("aaa")
        print(self.component[self.editing_component]["component"].__class__.__name__)
        if self.component[self.editing_component]["component"].__class__.__name__ == "Component":
            self.play_move.show()
            self.play.hide()
            self.stop.show()

            self.move_thread = MoveThread(self.play_move, int(self.bpm_num.text()), self.scroll_bar)
            self.move_thread.start()

            self.play_thread = PlayThread(self.component[self.editing_component]["component"], self.play, self.stop, self.move_thread)
            self.play_thread.start()
        else:
            self.play.hide()
            self.stop.show()

            self.play_midi_thread = PlayMidi(self.component[self.editing_component]["component"], self.play, self.stop,)
            self.play_midi_thread.start()

    # 停止播放
    def stop_music(self):
        if self.component[self.editing_component]["component"].__class__.__name__ == "Component":
            self.move_thread.stop()
            self._async_raise(self.play_thread.ident, SystemExit)
        else:
            self._async_raise(self.play_midi_thread.ident, SystemExit)

        self.play.show()
        self.stop.hide()

    # 抛出异常来结束线程
    @staticmethod
    def _async_raise(t, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(t)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)

    # 复制一小节的数据
    def copy_bar(self):
        self.bar_data = {}
        groups = []
        bar = self.scrol.barWidgets[self.scrol.editing_barWidget].bar.bar
        for group in bar:
            group_msg = {}
            notes = []
            group_msg.setdefault("note_type", group["note_type"])
            for note in group["group"].group:
                note_msg = {}
                if note:
                    note_msg.setdefault("class", note.__class__.__name__)
                    if note.__class__.__name__ == "Pitch_start_Note":
                        note_msg.setdefault("new_pitch", note.new_pitch)
                    note_msg.setdefault("channel", note.channel)
                    note_msg.setdefault("division", note.division)
                    note_msg.setdefault("name", note.name)
                    note_msg.setdefault("pitch", note.pitch)
                    note_msg.setdefault("velocity", note.velocity)
                    notes.append(note_msg)
                else:
                    notes.append(None)
            group_msg.setdefault("group", notes)
            groups.append(group_msg)
        self.bar_data.setdefault("bar", groups)

    # 粘贴一小节数据
    def paste_bar(self):
        bar_msg = my_guitar.Bar()
        for i, group in enumerate(self.bar_data["bar"]):
            group_msg = my_guitar.NoteGroup(type=group["note_type"])
            for index, note in enumerate(group["group"]):
                bar_msg.is_using = True
                if not note:
                    continue
                if note["class"] == "Up_Drum" or note["class"] == "Down_Drum":
                    note_msg = globals()[note["class"]](note["pitch"], note["velocity"], note["name"],
                                                        note["channel"], note["division"])
                    group_msg.set_nodes(6, note_msg)
                    continue
                if note["class"] == "Pitch_start_Note":
                    note_msg = globals()[note["class"]](note["new_pitch"], note["pitch"], note["velocity"],
                                                        note["name"], note["channel"], note["division"])
                else:
                    note_msg = globals()[note["class"]](note["pitch"], note["velocity"], note["name"], note["channel"],
                                                        note["division"])
                group_msg.set_nodes(index, note_msg)
            bar_msg.set_group(i, group_msg)

        self.scrol.barWidgets[self.scrol.editing_barWidget].bar = bar_msg
        self.scrol.barWidgets[self.scrol.editing_barWidget].parse_bar()
        self.scrol.barWidgets[self.scrol.editing_barWidget].repaint()
        self.component[self.editing_component]["component"].track_msg[self.editing_track].bars[self.scrol.editing_barWidget] = bar_msg

    # 切换音乐项目
    def change_component(self):
        if self.editing_component == self.play_music_combo_box.currentIndex():
            return
        self.editing_component = self.play_music_combo_box.currentIndex()

        component = self.component[self.editing_component]["component"]
        self.music_name_edit.setText(component.name)
        self.music_artist_edit.setText(component.artist)
        if component.denominator == 4:
            self.music_meter_edit.setCurrentIndex(0)
        elif component.denominator == 8:
            self.music_meter_edit.setCurrentIndex(1)
        self.music_bpm_edit.setValue(component.bpm)

        self.editing_track = 0
        self.track_name_edit.setText(component.track_msg[self.editing_track].name)
        # 切换音轨 = 添加所有音轨，显示当前音轨(主音轨不添加)
        self.program_edit.setCurrentIndex(component.track_msg[self.editing_track].program - 24)
        # 调音 = 当前音轨调音
        self.bar_count_edit.setText(str(self.component[self.editing_component]["component"].track_msg[self.editing_track].bars.__len__()))
        # 显示时间

        self.draw_component_track()

    # 删除小节
    def remove_bar(self):
        if self.scrol.barWidgets.__len__() == 1:
            return
        remove_index = self.scrol.editing_barWidget
        if remove_index == 0:
            self.scrol.barWidgets[1].move_pitch_input(0, 0)
            self.scrol.editing_barWidget = 0
        else:
            self.scrol.barWidgets[remove_index - 1].move_pitch_input(0, 0)
            self.scrol.editing_barWidget = remove_index - 1

        self.scrol.barWidgets.pop(remove_index).deleteLater()
        self.component[self.editing_component]["component"].track_msg[self.editing_track].bars.pop(remove_index)
        a = self.editing_component
        self.editing_component = -1
        #
        self.change_component()

    # 导出图片
    def save_img(self):
        if self.editing_component == -1: return
        path, type = \
            QFileDialog.getSaveFileName(self, 'save file', '/home/jm/study', "Gmusic Files (*.png)")

        if path == '': return
        save_thread = SaveImg(self.scroll_bar, self.x()+320, self.y()+135, self.x()+980, self.y()+601, path)
        save_thread.start()

    # 导入midi
    def import_midi(self):
        path, filetype = QFileDialog.getOpenFileName(self, "选取文件", "/Users/Kelisiya/Desktop",
                                                     "Midi Files (*.midi)")
        if path == '': return
        if self.component.__len__() <= 5:
            pattern = assistant.read_midi(path)
            component = assistant.change_pattern_to_music(pattern)
            self.component.append({"component": component, "path": path})
            self.editing_component = self.component.__len__() - 1
            self.set_my_music()
        else:
            print("太多了，不能再新建了")


class SaveImg(threading.Thread):
    def __init__(self, scroll_bar, x, y, x1, y1, path):
        threading.Thread.__init__(self)
        self.scroll_bar = scroll_bar
        self.x = x
        self.y = y
        self.x1 = x1
        self.y1 = y1
        self.box = (x, y, x1, y1)
        self.path = path

    def run(self):
        save_path = []
        imagefile = []
        for i in range(0,9):
            self.scroll_bar.setValue(i * 481)
            time.sleep(1)
            pic = ImageGrab.grab(self.box)
            pic.save('pic'+str(i)+'.png')
            save_path.append('pic'+str(i)+'.png')
        for f in save_path:
            imagefile.append(Image.open(f))
        target = Image.new('RGB', (660, 466*9))
        UNIT_SIZE = 466
        left = 0
        right = UNIT_SIZE
        for image in imagefile:
            target.paste(image, (0, left, 660, right))
            left += UNIT_SIZE  # 从上往下拼接，左上角的纵坐标递增
            right += UNIT_SIZE  # 左下角的纵坐标也递增　
            quality_value = 100
            target.save(self.path, quality=quality_value)


class PlayThread(threading.Thread):
    def __init__(self, component, play, stop, move_t):
        threading.Thread.__init__(self)
        self.component = component
        self.play = play
        self.stop = stop
        self.move_t = move_t

    def run(self):
        self.component.play_music()
        self.stop.hide()
        self.play.show()
        self.move_t.stop()


class PlayMidi(threading.Thread):
    def __init__(self, component, play, stop):
        threading.Thread.__init__(self)
        self.component = component
        self.play = play
        self.stop = stop

    def run(self):
        self.component.play_music()
        self.stop.hide()
        self.play.show()


class MoveThread(threading.Thread):
    def __init__(self, play_move, bpm, scroll_bar):
        threading.Thread.__init__(self)
        self.play_move = play_move
        self.bpm = bpm
        self.scroll_bar = scroll_bar
        self.scroll_bar.setValue(0)

        self.__is_running = threading.Event()
        self.__is_running.set()

    def run(self):
        x = 300 / 4 / 20 * (self.bpm / 60)
        while self.__is_running.is_set():
            time.sleep(0.05)
            self.play_move.move(self.play_move.x()+x, self.play_move.y())
            if self.play_move.x() > 650:
                self.play_move.move(65, self.play_move.y() + 120)
                self.scroll_bar.setValue(self.scroll_bar.value() + 120)

    def stop(self):
        self.play_move.move(50, 150)
        self.play_move.hide()
        self.__is_running.clear()

