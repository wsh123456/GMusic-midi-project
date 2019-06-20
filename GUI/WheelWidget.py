from PyQt5.QtWidgets import QWidget, QLineEdit, QScrollArea
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from model import my_guitar
from . import varible
from .BarWidget import BarWidget


class WheelWidget(QScrollArea):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.barWidgets = []
        self.editing_barWidget = 0

        self.is_show = True

    right_key = pyqtSignal(int, int, int)
    def keyPressEvent(self, QKeyEvent):
        try:
            if QKeyEvent.key() == Qt.Key_Y:
                if self.is_show:
                    for bar in self.barWidgets:
                        bar.pitch_input.hide()
                    self.is_show = False
                elif not self.is_show:
                    for bar in self.barWidgets:
                        bar.pitch_input.show()
                    self.is_show = True
            if QKeyEvent.key() == Qt.Key_Escape:
                self.barWidgets[self.editing_barWidget].pitch_input.clearFocus()
                self.setFocus()
            if QKeyEvent.key() == Qt.Key_Space:
                self.barWidgets[self.editing_barWidget].pitch_input.setFocus()
            if QKeyEvent.key() == Qt.Key_Left:
                this_bar = self.barWidgets[self.editing_barWidget]
                if self.barWidgets[self.editing_barWidget].x_index == 0:
                    if self.editing_barWidget == 0:
                        return
                    else:
                        cur_bar = self.barWidgets[self.editing_barWidget-1]
                        x = cur_bar.widget_draw_bar[-1][this_bar.y_index]["x"]
                        y = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index]["y"]
                        cur_bar.move_pitch_input(x, y)
                else:
                    x = this_bar.widget_draw_bar[this_bar.x_index-1][this_bar.y_index]["x"]
                    y = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index]["y"]
                    self.barWidgets[self.editing_barWidget].move_pitch_input(x, y)
            if QKeyEvent.key() == Qt.Key_Right:
                this_bar = self.barWidgets[self.editing_barWidget]
                y = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index]["y"]
                # 1.先检测右边有没有已经存在的音符(包括空)，如果存在，直接右移
                if this_bar.x_index < len(this_bar.widget_draw_bar) -1:
                    x = this_bar.widget_draw_bar[this_bar.x_index + 1][this_bar.y_index]["x"]
                    this_bar.move_pitch_input(x, y)
                else:
                    note = my_guitar.None_Note(varible.note_type)
                    result = this_bar.bar.add_note(note, y)
                    this_bar.repaint()
                    if result:
                        this_bar.move_pitch_input(300, y)
                    else:
                        if self.editing_barWidget < len(self.barWidgets) - 1:
                            next_bar = self.barWidgets[self.editing_barWidget+1]
                            x = next_bar.widget_draw_bar[0][this_bar.y_index]["x"]
                            next_bar.move_pitch_input(x, y)
                        else:
                            x_draw = (self.editing_barWidget + 1 + 2) % 2
                            y_draw = (self.editing_barWidget + 1) // 2
                            self.right_key.emit(x_draw, y_draw, y)

            if QKeyEvent.key() == Qt.Key_Up:
                self.setFocus()
                this_bar = self.barWidgets[self.editing_barWidget]
                x = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index]["x"]
                if self.barWidgets[self.editing_barWidget].y_index == 0:
                    return
                else:
                    y = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index-1]["y"]
                    self.barWidgets[self.editing_barWidget].move_pitch_input(x, y)
            if QKeyEvent.key() == Qt.Key_Down:
                self.setFocus()
                this_bar = self.barWidgets[self.editing_barWidget]
                x = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index]["x"]
                if self.barWidgets[self.editing_barWidget].y_index == 5:
                    return
                else:
                    y = this_bar.widget_draw_bar[this_bar.x_index][this_bar.y_index + 1]["y"]
                    self.barWidgets[self.editing_barWidget].move_pitch_input(x, y)
        except Exception as e:
            print(e)

    def change_editing_bar_widget(self, index):
        self.barWidgets[self.editing_barWidget].pitch_input.hide()
        self.editing_barWidget = index
        self.barWidgets[self.editing_barWidget].pitch_input.show()


# 自定义的模拟点击类
class ClickEvent():
    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y

    def button(self):
        return self.type