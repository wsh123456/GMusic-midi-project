from mingus.midi import pyfluidsynth
import time

# 音乐类
class Music(object):
    def __init__(self, music=None, fs=None, fluid=-1):
        self._init(music, fs, fluid)
        if self.fs is None:
            self.fs = pyfluidsynth.Synth()
            self.fluid = self.fs.sfload("soundfont/Hubbe64MB.sf2")
            self.fs.start()

    def _init(self, music, fs, fluid):
        self.name = "music"
        self.artist = "artist"

        self._track_count = 0  # 音轨数量
        self.bpm = 120  # 速度
        self.numerator = 4  # 分子
        self.denominator = 4  # 分母
        self._play_format = 1  # 播放模式(0，1，2)
        self._resolution = 480 # 一个四分音符的tick数
        self.calculate_tick_with_bpm(self.bpm, self._resolution, self.denominator)
        self.track = []

        self.fs = fs
        self.fluid = fluid

        if music is not None:
            self._track_count = music.__len__()
            self._play_format = music.format
            self._resolution = music.resolution
            for i in range(self._track_count):
                self.parse_track(music[i])
                # self.track.append(music[i])

    # 设置声音字体
    # def set_soundfont(self, sf2):
    #     self.fs = sf2

    def _init_main_trank(self):
        pass

    # 播放音乐
    def play_music(self):
        for track in self.track:
            self.play_track(track)

    # 解析一下track信息
    def parse_track_msg(self):
        pass

    # 播放音轨
    def play_track(self, track):
        for t in track:
            state_code = t[1]["state_code"]
            try:
                time.sleep(t[0] * self._tick_speed)
            except Exception as e:
                print(e)
            if state_code == 255:
                pass
            elif 240 <= state_code <= 254:
                print("系统码")
            elif 224 <= state_code <= 239:
                print("滑音")
                self.fs.pitch_bend(t[1]["channel"], t[1]["pitch"])
            elif 208 <= state_code <= 223:
                print("Aftertouch")
            elif 192 <= state_code <= 207:
                print("乐器转换", self.fluid)
                self.fs.program_select(t[1]["channel"], self.fluid, 0, t[1]["program"])
            elif 176 <= state_code <= 191:
                print("控制器")
                self.fs.cc(t[1]["channel"], t[1]["control"], t[1]["value"])
            elif 160 <= state_code <= 175:
                print("Key after Touch")
            elif 144 <= state_code <= 159:
                print("按下音符")
                self.fs.noteon(t[1]["channel"], t[1]["pitch"], t[1]["velocity"])
            elif 128 <= state_code <= 143:
                print("松开音符")
                self.fs.noteoff(t[1]["channel"], t[1]["pitch"])
            elif state_code <= 127:
                print("非midi元事件")
            else:
                pass

    # 添加音符
    def add_note(self):
        pass

    # 移除音符
    def remove_note(self):
        pass

    # 添加一条音轨
    def add_track(self, program):
        pass

    # 移除一条音轨
    def remove_track(self, index):
        pass

    # 解析一条音轨
    def parse_track(self, track):
        result = []
        for data in track:
            tick = data.tick
            event = self.parse_event(data)
            result.append([tick, event])
        self.track.append(result)

    # 解析event事件
    def parse_event(self, event):
        state_code = event.statusmsg
        if state_code == 255:
            if event.name == 'Set Tempo':
                self.bpm = event.bpm
                self.mpqn = event.mpqn
                self._tick_speed = self.calculate_tick_with_mpqn(self.mpqn, self._resolution)
                return {"state_code": state_code, "name":"Set Tempo",
                        "bpm":event.bpm, "mpqn":event.mpqn}
            elif event.name == 'Trank Name':
                return {"state_code": state_code, "name": "Trank Name",
                        "text": event.text}
            elif event.name == 'Copyright Notice':
                return {"state_code": state_code, "name": "Trank Name",
                        "text": event.text}
            elif event.name == 'SMPTE Offset':
                return {"state_code": state_code, "name": "Trank Name",
                        "text": event.data}
            elif event.name == 'Time Signature':
                self.denominator = event.denominator
                self.numerator = event.numerator
                self._tick_speed = self.calculate_tick_with_bpm(self.bpm, self._resolution, self.denominator)
                return {"state_code": state_code, "name": "Time Signature",
                        "numerator": event.numerator, "denominator":event.denominator,
                        "metronome": event.metronome, "thirtyseconds": event.thirtyseconds}
            elif event.name == 'End of Track':
                return {"state_code": state_code, "name": "End of Track"}
            else:
                return {"state_code": state_code, "name": event.name}
        elif 240 <= state_code <= 254:
            # 系统码
            return {"state_code": state_code, "channel": event.channel,
                    "name": "SysEx", "data": event.data}
        elif 224 <= state_code <= 239:
            # 滑音
            return {"state_code": state_code, "channel": event.channel, "pitch":event.pitch}
        elif 208 <= state_code <= 223:
            #
            return {"state_code": state_code, "channel": event.channel}
        elif 192 <= state_code <= 207:
            # 乐器转换
            return {"state_code": state_code, "channel":event.channel, "program":event.value}
        elif 176 <= state_code <= 191:
            # midi控制器
            return {"state_code": state_code, "channel": event.channel,
                    "control": event.control, "value": event.value}
        elif 160 <= state_code <= 175:
            return {"state_code": state_code, "channel": event.channel}
        elif 144 <= state_code <= 159:
            # note on
            return {"state_code": state_code, "channel": event.channel,
                    "pitch": event.pitch, "velocity":event.velocity}
        elif 128 <= state_code <= 143:
            # note off
            return {"state_code": state_code, "channel": event.channel,
                    "pitch": event.pitch, "velocity": event.velocity}
        elif state_code <= 127:
            return {"state_code": state_code, "channel": event.channel}
        else:
            return {"state_code": state_code, "channel": event.channel}


    # 计算1 tick换算时长为秒,传入mpqn，以几分音符为一拍,每四分音符的tick数
    @staticmethod
    def calculate_tick_with_mpqn(mpqn, count_of_4):
        seconds = mpqn / 1000000 / count_of_4
        return seconds

    # 计算1 tick换算时长为秒,传入bpm，以几分音符为一拍,每四分音符的tick数
    def calculate_tick_with_bpm(self, bpm, count_of_4, beat):
        self._tick_speed = 60 / bpm / (count_of_4 * 4 / beat)

    def get_track_count(self):
        return self._track_count

    def get_play_format(self):
        return self._play_format

    def set_play_format(self, play_format):
        self._play_format = play_format

    def set_resolution(self, resolution):
        self._resolution = resolution

    def get_resolution(self):
        return self._resolution