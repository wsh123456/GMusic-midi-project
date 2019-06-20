# GMusic-midi-project
该项目主要是作者对计算机辅助制谱，作曲较感兴趣，查找各方资料，参照guitar pro做的一个小项目，
其中走了不少弯路，遇到不少困难，在一些地方依然存在bug，后续进行更新，欢迎指出不足。

main.py : 程序主入口

fluidsynth.dll ：
mingus库的32位windows的c扩展，程序使用python3的mingus库，该库对python3的支持较差，需要手动修改一些库代码来兼容

soundfont ：音色库(soundfont)

model ：自定义的一些类，包括音符，组，小节，音轨，音乐等

GUI ：前端处理，使用pyqt5

file ： 一些文件，gmusic文件主要记录了编曲数据，png为曲谱，midi可直接播放(音效根据系统音色库而定)

assistant ：一些辅助函数
