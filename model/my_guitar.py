from .my_music import Music
from .program import program_dict
import midi
import json


class Component(Music):
    def __init__(self, fs=None, fluid=-1):
        super().__init__(music=None, fs=fs, fluid=fluid)
        self.track_count = 0
        self.track_msg = []
        self.add_track(24)

    def add_track(self, program):
        track = Trank(program=program, channel=len(self.track_msg), division=self.get_resolution())
        self.track_msg.append(track)
        self.track_count += 1
        return track, track.channel

    def remove_track(self, index):
        r_track = self.track.pop(index)
        return r_track

    # 初始化主音轨
    def _init_main_trank(self):
        pass
        # track.append([0, {"state_code": 255, "name": "Set Tempo", "bpm": self.bpm}])  # 添加音轨信息
        # track.append([100, {"state_code": 255, "name": "End of Track"}])  # 添加结尾标记

    def play_music(self):
        self.parse_track_msg()
        for track in self.track:
            self.play_track(track)

    # 解析一下track信息
    def parse_track_msg(self):
        self.track = []
        for track in self.track_msg:
            track.set_track_msg(self.bpm)
            self.track.append(track.track_msg)

    # 保存成gmusic格式文件
    def save_Gmusic(self, path):
        component = {}
        tracks = []
        for track in self.track_msg:
            track_msg = {}
            bars = []
            track_msg.setdefault("channel", track.channel)
            track_msg.setdefault("division", track.division)
            track_msg.setdefault("program", track.program)
            for bar in track.bars:
                bar_msg = {}
                groups = []
                bar_msg.setdefault("group_count", bar.group_count)
                for group in bar.bar:
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
                bar_msg.setdefault("bar", groups)
                bars.append(bar_msg)
            track_msg.setdefault("bars", bars)
            tracks.append(track_msg)

        component.setdefault("name", self.name)
        component.setdefault("bpm", self.bpm)
        component.setdefault("numerator", self.numerator)
        component.setdefault("denominator", self.denominator)
        component.setdefault("play_format", self._play_format)
        component.setdefault("resolution", self._resolution)
        component.setdefault("tracks", tracks)

        with open(path, "w") as file:
            file.writelines(json.dumps(component))

    # 加载gmusic格式文件信息
    def load_Gmusic(self, path):
        with open(path, "r") as file:
            data = json.load(file)
        self.name = data["name"]
        self.bpm = data["bpm"]
        self.numerator = data["numerator"]
        self.denominator = data["denominator"]
        self.set_play_format(data["play_format"])
        self.set_resolution(data["resolution"])
        self.track_msg = []
        for track in data["tracks"]:
            track_msg = Trank(track["program"], track["channel"], track["division"])
            track_msg.clean_bars()
            for bar in track["bars"]:
                bar_msg = Bar()
                for i, group in enumerate(bar["bar"]):
                    group_msg = NoteGroup(type=group["note_type"])
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
                            note_msg = globals()[note["class"]](note["new_pitch"], note["pitch"], note["velocity"], note["name"], note["channel"], note["division"])
                        else:
                            note_msg = globals()[note["class"]](note["pitch"], note["velocity"], note["name"], note["channel"], note["division"])
                        group_msg.set_nodes(index, note_msg)
                    bar_msg.set_group(i, group_msg)
                track_msg.add_bar(bar_msg)
            self.track_msg.append(track_msg)
        # 重载数据到component中


class None_Note():
    def __init__(self, name=4):
        self.name = name


class Note():
    def __init__(self, pitch, velocity, name=4, channel=0, division=480):
        self.name = name # 标志几分音符
        self.pitch = pitch     # 音符
        self.velocity = velocity  # 音高
        # self.lead_time = 0  # 前置时间
        self.division = division    # 分区
        self.duration = self.set_duration(self.name, division)  # 持续时间（延音可通过64号控制器制作）
        self.channel = channel    # 默认0通道

    def set_duration(self, name, division):
        duration = division * 4 / name
        return duration

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        start = [[tick, {"state_code": 144 + self.channel, "channel": self.channel,
                         "pitch": self.pitch, "velocity": self.velocity}]]
        end = [[self.duration, {"state_code": 128 + self.channel, "channel": self.channel,
                    "pitch": self.pitch, "velocity": self.velocity}]]
        return start, end



# 记录一组音符，哪个位置有音符信息就在哪个位置添加，没有则为空
class NoteGroup():
    def __init__(self, column=6, type=4):
        self.min_note_type = type  # 标志该组中最小为几分音符
        self.group = [None] * 7 # 0-5对应1-6弦，6为通道9打击乐用作打板

    def set_nodes(self, column_index, note):
        self.group[column_index] = note
        if note.name > self.min_note_type:
            self.min_note_type = note.name

    def remove_node(self, colume_index):
        self.group[colume_index] = None

    def change_to_new_name(self, new_name):
        self.min_note_type = new_name
        for note in self.group:
            if not note: continue
            if note.__class__.__name__ == "None_Note":
                note.name = new_name
                continue
            note.name = new_name
            note.duration = note.set_duration(note.name, note.division)


# 记录一小节的音符组
class Bar():
    def __init__(self):
        self.bar = [{"note_type": 4, "group": NoteGroup()}]
        self.group_count = 1
        self.is_using = False   # 标记是否使用过

        self.__max_weight = 64  # 最大权重，标志小节是否已经满了
        self.__current_weight = 0   # 当前权重

    # 重载小节
    def reset(self):
        self.__init__()

    def set_group(self, index, group):
        if self.__current_weight + self.__max_weight / group.min_note_type > self.__max_weight:
            # self.reset()
            return False   # 如果超越权重则表示在这个小节中不能再加入，返回-1
        if index > self.bar.__len__() - 1:
            self.expend_bar()
        if self.bar[index]["group"] is None:
            self.group_count += 1
        self.bar[index] = {"note_type": group.min_note_type, "group": group}
        self.__count_current_weight()
        return True

    def remove_group(self, index):
        self.bar.pop(index)
        self.group_count -= 1

    def add_note(self, note, column_index):
        # for index in range(len(self.bar)):
        # if self.bar[index]["group"] is None:
        group = NoteGroup(type=note.name)
        if note.__class__.__name__ != "None_Note":
            group.set_nodes(column_index, note)
        if not self.is_using:
            self.bar = []
            self.is_using = True
            return self.set_group(self.bar.__len__(), group)
        return self.set_group(self.bar.__len__(), group)
        # return False

    # 扩展小节，主要用于向小节中添加音符组的时候
    def expend_bar(self):
        self.bar.append({"note_type": 0, "group": None})

    # 计算当前权重
    def __count_current_weight(self):
        weight = 0
        for group in self.bar:
            if group["note_type"]:
                weight += (self.__max_weight / group["note_type"])
        self.__current_weight = weight

class Trank():
    def __init__(self, program, channel, division):
        self.track_msg = [] # 用来记录播放信息
        self.bars = []  # 用来记录显示情况

        self.tuning = {"name":"E A D G B E", "sound":[52, 47, 43, 38, 33, 28]}

        self.division = division
        self.channel = channel
        self.program = program
        self.name = program_dict[str(program)]

        self.using_bar = Bar()
        self.bars.append(self.using_bar)

    def add_bar(self, bar):
        self.bars.append(bar)

    def clean_bars(self):
        self.bars = []

    def add_note(self, note, colnmn_index):
        if not self.using_bar.add_note(note, colnmn_index):
            self.using_bar = Bar()
            self.bars.append(self.using_bar)
            self.using_bar.add_note(note, colnmn_index)

    def remove_note(self):
        pass

    # 设置音轨名称
    def set_track_name(self, name):
        self.name = name

    # 设置音轨信息
    def set_track_msg(self, bpm):
        self.track_msg = []
        self.track_msg.append([0, {"state_code": 255, "name": "Set Tempo", "bpm": bpm}])
        self.track_msg.append([0, {"state_code": 255, "name": "Trank Name", "text": "音轨信息"}])   # 添加音轨信息
        # self.track_msg.append([])   # 添加乱七八糟的信息
        self.track_msg.append([0, {"state_code": 176+self.channel, "channel": self.channel,
                    "control": 64, "value": 64}])   # 添加持续音控制器
        self.track_msg.append([0, {"state_code": 192+self.channel, "channel":self.channel, "program":self.program}])   # 添加乐器信息

        next_event = self._change_to_track_message(self.division) # 转换音符

        self.track_msg.append([next_event*8, {"state_code": 176+self.channel, "channel": self.channel,
                    "control": 64, "value": 0}])   # 结束延长音控制器
        self.track_msg.append([100, {"state_code": 255, "name": "End of Track"}])   # 添加结尾标记

    # 转换为可播放信息
    def _change_to_track_message(self, division):
        next_event = 0  # 记录下一个事件的时间
        pending_event = []    # 待处理的事件
        next_penging_time = division   # 下一个待处理事件的时间
        for bar in self.bars:
            for group in bar.bar:
                group_time = (division * 4 / group["note_type"])    # 这个音符组将要进行的时间
                # before_this_event = next_event - division     # 事件的前置时间
                if pending_event:   # 如果之前有待处理事件，就先进行待处理事件
                    pend_list = []
                    for e, event in enumerate(pending_event):
                        if event[0] <= next_penging_time:
                            pend_list.append([e, event])
                        else:
                            event[0] -= next_penging_time
                    if pend_list:
                        for p_e in reversed(pend_list):
                            pending_event.pop(p_e[0])
                        before_tick = 0
                        for p_e in pend_list:
                            p_e = p_e[1]
                            p_e[0] -= before_tick
                            self.track_msg.append(p_e)
                            before_tick += p_e[0]
                    next_event -= next_penging_time
                if group["group"] is None:
                    next_event += group_time
                else:
                    for i, note in enumerate(group["group"].group):
                        if note is None:
                            continue
                        start, end = note.add_to_event(next_event)
                        if end:
                            for e in end:
                                pending_event.append(e)
                                # print(e)
                                next_penging_time = min(e[0], next_penging_time)
                        for event in start:
                            self.track_msg.append(event)
                next_event = group_time
        if pending_event:
            pend_list = []
            for e, event in enumerate(pending_event):
                pend_list.append([e, event])
            before_tick = 0
            for e in reversed(pend_list):
                pending_event.pop(e[0])
            for p_e in pend_list:
                p_e = p_e[1]
                p_e[0] -= before_tick
                self.track_msg.append(p_e)
                before_tick += p_e[0]
        return next_event


# 设置滑音的两个类
class Pitch_end_Note(Note):
    # 设置滑音的note就无需再添加note而是转为pitch_wheel设置滑到的高度即可
    def __init__(self, pitch, velocity, name=4, channel=12, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        start = [[self.duration, {"state_code": 176 + self.channel, "channel": self.channel,
                    "control": 84, "value": 64}],
                 # [self.duration, {"state_code": 224 + self.channel, "channel": self.channel, "pitch": 0}]
                 ]
        end = []
        return start, end

    def set_pitch_wheel(self, wheel):
        self.wheel = wheel

class Pitch_start_Note(Note):
    # 设置滑音的note就无需再添加note而是转为pitch_wheel设置滑到的高度即可
    def __init__(self,new_pitch, pitch, velocity, program, name=4, channel=12, division=480):
        super().__init__(pitch, velocity, name, channel, division)
        # self.before_slide = self.duration
        self.before_slide = self.duration * 0.7
        self.new_pitch = new_pitch
        self.program = program

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        start = [[tick, {"state_code": 224 + self.channel, "channel": self.channel, "pitch": 0}],
                 [tick, {"state_code": 192 + self.channel, "channel": self.channel, "program": self.program}],
                 [tick, {"state_code": 144 + self.channel, "channel": self.channel,"pitch": self.pitch, "velocity": self.velocity}]
        ]
        end = [[self.before_slide, {"state_code": 192 + 15, "channel": 15, "program": 120}],
               [self.before_slide, {"state_code": 144 + 15, "channel": 15, "pitch": self.pitch, "velocity": 30}],
               [self.before_slide, {"state_code": 224 + self.channel, "channel": self.channel, "pitch": self.get_pitch()}],
               [self.duration, {"state_code": 176 + self.channel, "channel": self.channel, "control": 1, "value": 80}],
               [2 * self.before_slide, {"state_code": 176 + self.channel, "channel": self.channel, "control": 1, "value": 0}],
               [2 * self.before_slide, {"state_code": 128 + 15, "channel": 15, "pitch": self.pitch, "velocity": self.velocity}],
               [2 * self.duration, {"state_code": 128 + self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": self.velocity}],
               ]
        return start, end

    def get_pitch(self):
        pitch = (self.new_pitch - self.pitch) * 12 + 64
        if pitch > 127:
            pitch = 127
        if pitch < 0:
            pitch = 0
        return ((pitch << 8) | 0) - 0x2000


# 设置泛音note,目前用的是清音吉他。。不太理想
class Harm_Note(Note):
    def __init__(self,pitch, velocity, name=4, channel=0, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        # start = [[tick, {"state_code": 176 + self.channel, "channel": self.channel, "control": 71, "value": 90}],
        #          [tick, {"state_code": 176 + self.channel, "channel": self.channel, "control": 74, "value": 90}],
        #          [tick, {"state_code": 144 + self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 127}]]
        # end = [[self.duration, {"state_code": 144 + self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 0}],
        #        [self.duration, {"state_code": 128 + self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 60}]]
        start = [[tick, {"state_code": 176+15, "channel": 15, "control": 64, "value": 64}],
                 [tick, {"state_code": 192 + 15, "channel": 15, "program": 25}],
                 [tick, {"state_code": 144 + 15, "channel": 15, "pitch": self.pitch+12, "velocity": 100}]]
        end = [[self.duration, {"state_code": 128 + 15, "channel": 15, "pitch": self.pitch, "velocity": 60}],
               [960, {"state_code": 176+15, "channel": 15, "control": 64, "value": 0}]]
        return start, end


# 颤音音符类
class Vibrato_Note(Note):
    def __init__(self,pitch, velocity, name=4, channel=0, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        start = [[tick, {"state_code": 144 + self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 127}],
                 [tick, {"state_code": 176 + self.channel, "channel": self.channel, "control": 1, "value": 127}]]
        end = [[self.duration, {"state_code": 128 + self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 127}]]
        return start, end


# 闷音
class Muffled_Sound(Note):
    def __init__(self,pitch, velocity, name=4, channel=0, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        start = [[tick, {"state_code": 192 + 15, "channel": 15, "program": 28}],
                 [tick, {"state_code": 144 + 15, "channel": 15, "pitch": self.pitch, "velocity": 100}],]
        end = [[self.duration, {"state_code": 128 + 15, "channel": 15, "pitch": self.pitch, "velocity": 60}]]
        return start, end


# 底鼓
class Down_Drum(Note):
    def __init__(self,pitch=36, velocity=127, name=4, channel=9, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        start = [[tick, {"state_code": 192+self.channel, "channel": self.channel, "program": 116}],
                 [tick, {"state_code": 144+self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": self.velocity}],]
        end = [[self.duration, {"state_code": 128+self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 90}]]
        return start, end


# 指鼓
class Up_Drum(Note):
    def __init__(self,pitch=62, velocity=127, name=4, channel=9, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        start = [[tick, {"state_code": 192+self.channel, "channel": self.channel, "program": 116}],
                 [tick, {"state_code": 144+self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": self.velocity}],]
        end = [[self.duration, {"state_code": 128+self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 90}]]
        return start, end


# # 向下扫弦
# class Down_Strum():
#     pass
#
#
# # 向上扫弦
# class Up_Strum(object):
#     def __init__(self, notes, velocity, name=4, channel=1, division=480):
#         self.name = name  # 标志几分音符
#         self.velocity = velocity  # 音高
#         self.notes = notes
#         # self.lead_time = 0  # 前置时间
#         self.duration = self.set_duration(self.name, division)  # 持续时间（延音可通过64号控制器制作）
#         self.channel = channel  # 默认0通道
#
#     def set_duration(self, name, division):
#         duration = division * 4 / name
#         return duration
#
#     def add_to_event(self, tick):
#         # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
#         start = []
#         end = []
#         for note in self.notes:
#             start.append([tick, {"state_code": 144 + self.channel+1, "channel": self.channel+1, "pitch": note, "velocity": self.velocity}])
#             end.append([self.duration, {"state_code": 128 + self.channel+1, "channel": self.channel+1, "pitch": note, "velocity": self.velocity}])
#         return start, end


# 点弦
class Click_Note(Note):
    def __init__(self,pitch, velocity, name=4, channel=15, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    def add_to_event(self, tick):
        start = [[tick, {"state_code": 192+self.channel, "channel": self.channel, "program": 33}],
                 [tick, {"state_code": 144+self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": self.velocity}],]
        end = [[self.duration, {"state_code": 128+self.channel, "channel": self.channel, "pitch": self.pitch, "velocity": 60}]]
        return start, end


# 空(有问题)
class Cut_Sound(Note):
    def __init__(self,pitch=44, velocity=1, name=4, channel=8, division=480):
        super().__init__(pitch, velocity, name, channel, division)

    # def add_to_event(self, tick):
    #     start = [[tick, {"state_code": 192+9, "channel": 9, "program": 47}],
    #              [tick, {"state_code": 144+9, "channel": 9, "pitch": self.pitch, "velocity": self.velocity}],
    #              [tick, {"state_code": 176 + self.channel, "channel": self.channel, "control": 64, "value": 0}]]
    #     end = [[self.duration, {"state_code": 128 + 9, "channel": 9, "pitch": self.pitch, "velocity": 127}],
    #            [self.duration, {"state_code": 176 + self.channel, "channel": self.channel, "control": 64, "value": 64}]]
    #     return start, end

    def add_to_event(self, tick):
        # 返回一个note_on以及相关的控制器信息等乱七八糟的start,和对应note的结束标志
        start = [[tick, {"state_code": 144 + self.channel, "channel": self.channel,
                         "pitch": self.pitch, "velocity": self.velocity}]]
        end = [[self.duration, {"state_code": 128 + self.channel, "channel": self.channel,
                    "pitch": self.pitch, "velocity": self.velocity}]]
        return start, end


def sort_pend_list(pend_list):
    for i in range(len(pend_list) - 1):
        for j in range(i+1, len(pend_list)):
            if pend_list[i][0] > pend_list[j][0]:
                pend_list[i], pend_list[j] = pend_list[j], pend_list[i]
    return pend_list