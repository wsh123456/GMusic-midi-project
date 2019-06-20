class My_Note():
    def __init__(self):
        self.name = 4
        self.pitch = 60     # 音符
        self.velocity = 70  # 音高
        self.lead_time = 0  # 前置时间
        self.duration = 960 # 持续时间（过多久停止播放，目前设置为两倍的分区）
        self.channel = 0    # 默认0通道