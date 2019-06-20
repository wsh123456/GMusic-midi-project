'''
    辅助函数
'''
from model.my_music import Music
from mingus.midi import pyfluidsynth
import midi
import midi2audio

# 加载音色库
def load_soundfont(soundfont):
    try:
        fs = pyfluidsynth.Synth()
        fluid = fs.sfload(soundfont)
        if fluid:
            print("音源加载成功")
    except:
        fs = None
        fluid = -1
        print("音源加载失败")
    return fs, fluid

# 读取midi文件
def read_midi(file):
    result = midi.read_midifile(file)
    return result

# 转换midi文件到可播放的music,传入midi.pattern类
def change_pattern_to_music(pattern):
    music = Music(pattern)
    return music

# 转换music类到可存储的pattern类
def change_music_to_pattern(music):
    music.parse_track_msg()
    # music._init_main_trank()

    pattern = midi.Pattern()
    pattern.resolution = music.get_resolution()
    pattern.format = music.get_play_format()
    for track in reversed(music.track):
        t = midi.Track()
        for event in track:
            event_tick = int(event[0])
            event_event = event[1]
            state_code = event_event["state_code"]
            if state_code == 255:
                if event_event["name"] == 'Set Tempo':
                    eve = midi.SetTempoEvent(
                        tick=event_tick, bpm=event_event["bpm"]
                    )
                elif event_event["name"] == 'Trank Name':
                    eve = midi.TrackNameEvent(
                        tick=event_tick, text=event_event["text"]
                    )
                elif event_event["name"] == 'Copyright Notice':
                    eve = midi.CopyrightMetaEvent(
                        tick=event_tick, text=event_event["text"]
                    )
                elif event_event["name"] == 'SMPTE Offset':
                    eve = midi.SmpteOffsetEvent(
                        tick=event_tick, text=event_event["text"]
                    )
                elif event_event["name"] == 'Time Signature':
                    eve = midi.TimeSignatureEvent(
                        tick=event_tick,numerator=event_event["numerator"],
                        denominator=event_event["denominator"],
                        metronome=event_event["metronome"],
                        thirtyseconds=event_event["thirtyseconds"]
                    )
                elif event_event["name"] == "End of Track":
                    eve = midi.EndOfTrackEvent(tick=event_tick)
                else:
                    continue
            elif 240 <= state_code <= 254:
                # 系统码
                eve = midi.SysexEvent()
            elif 224 <= state_code <= 239:
                # 滑音
                eve = midi.PitchWheelEvent(
                    tick=event_tick, channel=event_event["channel"], pitch=event_event["pitch"])
            elif 208 <= state_code <= 223:
                # After Touch
                eve = midi.AfterTouchEvent()
            elif 192 <= state_code <= 207:
                # 乐器转换
                eve = midi.ProgramChangeEvent(
                    tick=event_tick, channel=event_event["channel"], data=[event_event["program"]])
            elif 176 <= state_code <= 191:
                # midi控制器
                eve = midi.ControlChangeEvent(
                    tick=event_tick, channel=event_event["channel"],
                    data=[event_event["control"], event_event["value"]])
            elif 160 <= state_code <= 175:
                continue
            elif 144 <= state_code <= 159:
                # note on
                eve = midi.NoteOnEvent(
                    tick=event_tick, channel=event_event["channel"],
                    velocity=event_event["velocity"], pitch=event_event["pitch"]
                )
            elif 128 <= state_code <= 143:
                # note off
                eve = midi.NoteOffEvent(
                    tick=event_tick, channel=event_event["channel"],
                    velocity=event_event["velocity"], pitch=event_event["pitch"]
                )
            elif state_code <= 127:
                continue

            t.append(eve)
        pattern.append(t)
    return pattern

# 播放music
def play_music(music):
    music.play_music()

# 保存midi
def save_midi_file(file, pattern):
    try:
        midi.write_midifile(file, pattern)
        print("写入成功")
    except:
        raise IOError

def save_wav_file(file, pattern):
    # subprocess这个有点问题，windows下使用需要再查一下，暂时先不做
    midi2audio.FluidSynth("soundfont/fluid120mb2.sf2", sample_rate=22050).midi_to_audio("midi/test.mid", "test.wav")



