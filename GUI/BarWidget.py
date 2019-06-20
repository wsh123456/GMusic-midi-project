from PyQt5.QtWidgets import QWidget, QLineEdit
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from model import my_guitar
from . import varible

class BarWidget(QWidget):
    def __init__(self, parent, x, y, bar):
        super().__init__(parent=parent)

        self.resize(301, 85)
        self.move(x, y)
        self.bar = bar
        self.varible = varible
        self.parse_bar()

        self.x_index, self.y_index = 0, 0
        self.pitch_input = QLineEdit(self)  # 用来输入音符的
        self.pitch_input.textEdited.connect(lambda: self.set_note())
        self.pitch_input.setFont(QFont('楷体', 7))
        self.pitch_input.resize(14, 14)
        self.pitch_input.move(15, 10)
        self.pitch_input.setText(self.change_pitch(self.widget_draw_bar[self.x_index][self.y_index]))
        self.pitch_input.hide()

    # 绘制基础六线谱 高85，上下各17的空余量；宽201，多1的竖线宽度
    def draw_base(self, qp):
        pen = QPen(Qt.gray, 0.5, Qt.SolidLine)
        qp.setPen(pen)

        qp.drawLine(0, 17, 300, 17)
        qp.drawLine(0, 27, 300, 27)
        qp.drawLine(0, 37, 300, 37)
        qp.drawLine(0, 47, 300, 47)
        qp.drawLine(0, 57, 300, 57)
        qp.drawLine(0, 67, 300, 67)

        pen = QPen(Qt.black, 1, Qt.SolidLine)
        qp.setPen(pen)
        qp.drawLine(0, 17, 0, 67)
        qp.drawLine(300, 17, 300, 67)

    # 设置点击事件
    clicked = pyqtSignal(int)
    def mouseReleaseEvent(self, QMouseEvent):
        def __do_click(x, y):
            self.move_pitch_input(x, y)
            # 纵坐标计算
            # x, self.x_index = self.__count_x_position(x)
            # y, self.y_index = self.__count_y_position(y)
            # self.pitch_input.setText(self.change_pitch(self.widget_draw_bar[self.x_index][self.y_index]))
            # self.pitch_input.move(x - 7, y - 7)
            # # 根据widget_draw_bar的权重来得出鼠标点击的是哪一列
            # # 再获取哪一行，找到对应的音符
            # # 进行修改或者添加，记住对应的xy，到bar中进行setnode操作
            # self.clicked.emit((self.x() - 50) // 300 + (self.y() - 150) // 120 * 2)
            # self.varible.special_note = "Note"

        if QMouseEvent.button() == Qt.LeftButton:
            x = QMouseEvent.x()
            y = QMouseEvent.y()
            __do_click(x, y)


    def move_pitch_input(self, x, y):
        # 纵坐标计算
        x, self.x_index = self.__count_x_position(x)
        y, self.y_index = self.__count_y_position(y)
        self.pitch_input.setText(self.change_pitch(self.widget_draw_bar[self.x_index][self.y_index]))
        self.pitch_input.move(x - 7, y - 7)

        self.clicked.emit((self.x() - 50) // 300 + (self.y() - 150) // 120 * 2)
        self.varible.special_note = "Note"

    # 计算x轴上的音符显示位置,传入一个点击的x，返回计算好的应显示位置的x
    def __count_x_position(self, x):
        if x <= 24: return 24, 0
        count = 24
        for index, group in enumerate(self.bar.bar):
            cur_count = count
            count = 24 + 64 / group["note_type"] * 4 * index
            if count > x:
                if x - cur_count < count - x:
                    return cur_count, index - 1
                return count, index
        return 24 + 64 / self.bar.bar[-1]["note_type"] * 4 * (len(self.bar.bar)-1), len(self.bar.bar)-1

    def __count_y_position(self, y):
        if y < 22: return 17, 0
        if 22 <= y < 32: return 27, 1
        if 32 <= y < 42: return 37, 2
        if 42 <= y < 52: return 47, 3
        if 52 <= y < 62: return 57, 4
        if 62 <= y: return 67, 5

    # def set_event(self):
    #     print("aa")

    def paintEvent(self, QPaintEvent):
        qp = QPainter()
        qp.begin(self)
        self.parse_bar()
        self.draw_base(qp)
        self.draw_bar()
        qp.end()

    # 解析小节，存储为可绘制信息
    def parse_bar(self):
        result = []
        for index, group in enumerate(self.bar.bar) :
            group_result = []
            if group["group"]:
                x = 17 + 64 / group["note_type"] * 4 * index
                for i, note in enumerate(group["group"].group):
                    y = i * 10 + 20
                    if note.__class__.__name__ == "Up_Drum":
                        y = 0
                    if not note:
                        group_result.append({"x": x, "y": y, "note_class": note.__class__.__name__, "note": ""})
                        continue
                    group_result.append({"x": x, "y":y, "index":i, "note_class":note.__class__.__name__, "note":note.pitch})
            result.append(group_result)
        self.widget_draw_bar = result

    # 绘制小节的音符信息
    def draw_bar(self):
        qp = QPainter()
        qp.begin(self)

        pen = QPen(Qt.black, 0.8, Qt.SolidLine)
        qp.setPen(pen)

        for group in self.widget_draw_bar:
            for i, note in enumerate(group):
                if note["note"]:
                    if note["note_class"] == "Down_Drum":
                        qp.drawText(note["x"]+3, 80, "*")
                    elif note["note_class"] == "Up_Drum":
                        qp.drawText(note["x"]+3, 7, "*")
                    elif note["note_class"] == "Cut_Sound":
                        break
                    elif note["note_class"] == "Pitch_start_Note":
                        if len(str(note["note"])) == 1:
                            qp.drawText(note["x"] + 2, note["y"], self.change_pitch(note))
                            qp.drawText(note["x"] + 2+7, note["y"] - 5, "︵")
                            qp.drawText(note["x"] + 2+9, note["y"] - 11, "s")
                        else:
                            qp.drawText(note["x"], note["y"], self.change_pitch(note))
                            qp.drawText(note["x"]+7, note["y"] - 5, "︵")
                            qp.drawText(note["x"]+9, note["y"] - 11, "s")
                    elif note["note_class"] == "Vibrato_Note":
                        if len(str(note["note"])) == 1:
                            qp.drawText(note["x"] + 2, note["y"], self.change_pitch(note))
                            qp.drawText(note["x"] + 2, note["y"] - 1, "﹋")
                        else:
                            qp.drawText(note["x"], note["y"], self.change_pitch(note))
                            qp.drawText(note["x"], note["y"] - 1, "﹋")
                    elif note["note_class"] == "Muffled_Sound":
                        if len(str(note["note"])) == 1:
                            qp.drawText(note["x"], note["y"], "("+self.change_pitch(note)+")")
                        else:
                            qp.drawText(note["x"]-4, note["y"], "("+self.change_pitch(note)+")")
                    elif note["note_class"] == "Harm_Note":
                        if len(str(note["note"])) == 1:
                            qp.drawText(note["x"], note["y"], "<"+self.change_pitch(note)+">")
                        else:
                            qp.drawText(note["x"]-4, note["y"], "<"+self.change_pitch(note)+">")
                    elif note["note_class"] == "Click_Note":
                        if len(str(note["note"])) == 1:
                            qp.drawText(note["x"]+2, note["y"], self.change_pitch(note))
                            qp.drawText(note["x"]+2-7, note["y"]-7, "︵")
                        else:
                            qp.drawText(note["x"], note["y"], self.change_pitch(note))
                            qp.drawText(note["x"]-7, note["y"]-7, "︵")
                    else:
                        if len(str(note["note"])) == 1:
                            qp.drawText(note["x"]+2, note["y"], self.change_pitch(note))
                        else:
                            qp.drawText(note["x"], note["y"], self.change_pitch(note))
        qp.end()

    def set_note(self):
        if self.bar.bar[self.x_index]["group"].min_note_type > self.varible.note_type:
            self.varible.note_type = self.bar.bar[self.x_index]["group"].min_note_type
        pitch = self.pitch_input.text()
        if pitch == "":
            # 空的话将原来位置上的音符移除
            self.bar.bar[self.x_index]["group"].remove_node(self.y_index)
        # elif pitch == "x":
        #     # 输入x表示添加切弦
        #     note = my_guitar.Cut_Sound(name=self.varible.note_type)
        #     self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
        elif pitch in self.varible.pin_scope:
            # 0-20表示添加音符范围，还要再看添加的是否为音符
            # 分三种:打板，滑弦，其他
            pitch = int(pitch) + self.varible.track_base_tuning[self.y_index]
            velocity = 90
            if self.varible.special_note == "Down_Drum":
                note = my_guitar.Down_Drum(name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(6, note)
            if self.varible.special_note == "Up_Drum":
                note = my_guitar.Up_Drum(name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(6, note)
            if self.varible.special_note == "Pitch_Note":
                try:
                    new_pitch = self.bar.bar[self.x_index+1]["group"].group[self.y_index].pitch
                    note = my_guitar.Pitch_start_Note(new_pitch=new_pitch, pitch=pitch, velocity=127, program=self.varible.using_program, name=self.varible.note_type)
                    end_note = my_guitar.Pitch_end_Note(pitch=new_pitch, velocity=127, name=self.varible.note_type)
                    self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
                    end_note.set_pitch_wheel(note.get_pitch())
                    self.bar.bar[self.x_index+1]["group"].set_nodes(self.y_index, end_note)
                    print(pitch, new_pitch)
                except:
                    note = my_guitar.Note(pitch=pitch, velocity=velocity, name=self.varible.note_type)
                    self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
            if self.varible.special_note == "Harm_Note":
                note = my_guitar.Harm_Note(pitch=pitch, velocity=velocity, name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
            if self.varible.special_note == "Vibrato_Note":
                note = my_guitar.Vibrato_Note(pitch=pitch, velocity=velocity, name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
            if self.varible.special_note == "Muffled_Sound":
                note = my_guitar.Muffled_Sound(pitch=pitch, velocity=velocity, name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
            if self.varible.special_note == "Click_Note":
                note = my_guitar.Click_Note(pitch=pitch,velocity=velocity,name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
            if self.varible.special_note == "Cut_Sound":
                note = my_guitar.Cut_Sound(name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
            if self.varible.special_note == "Note":
                note = my_guitar.Note(pitch=pitch,velocity=velocity,name=self.varible.note_type)
                self.bar.bar[self.x_index]["group"].set_nodes(self.y_index, note)
        else:
            self.pitch_input.setText("")

        # print(self.varible.note_type, self.bar.bar[self.x_index]["group"].min_note_type)
        # if self.bar.bar[self.x_index]["group"].min_note_type <= self.varible.note_type:
        #     self.bar.bar[self.x_index]["group"].change_to_new_name(self.varible.note_type)

        self.parse_bar()
        self.repaint()

    def change_pitch(self, pitch):
        if pitch["note"] == "":
            return ""

        new_pitch = str(pitch["note"] - self.varible.track_base_tuning[pitch["index"]])
        return new_pitch
