Mycodo是一个开源的环境监测和调节系统，它是建立在单板计算机上运行的，特别是 [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi)。

Mycodo最初是为培养食用菌而开发的，现在已经发展到可以做得更多。该系统由两部分组成，一个后端（守护程序）和一个前端（网络服务器）。后台执行的任务包括从传感器和设备获取测量值，并协调对这些测量值的各种反应，包括调制输出的能力（开关继电器、生成PWM信号、操作泵、开关无线插座、发布/订阅MQTT等）、用PID控制调节环境条件、安排定时器、捕捉照片和视频流、在测量值满足某些条件时触发行动等等。前端有一个网络界面，可以从任何支持浏览器的设备上查看和配置。

Mycodo有许多不同的用途。一些用户只是简单地存储传感器的测量值，以远程监控条件，其他用户则是调节物理空间的环境条件，而其他用户则是捕捉运动激活或延时摄影，以及其他用途。

输入控制器获取测量值并将其存储在InfluxDB时间序列数据库中。测量值通常来自传感器，但也可能被配置为使用Linux Bash或Python命令的返回值，或数学方程，这使得这是一个非常动态的获取和生成数据的系统。

输出控制器对通用输入/输出（GPIO）引脚产生变化，或者可以配置为执行Linux Bash或Python命令，实现各种潜在用途。有几种不同类型的输出：GPIO引脚的简单开关（高/低），产生脉宽调制（PWM）信号，控制蠕动泵，MQTT发布，等等。

当输入和输出相结合时，功能控制器可用于创建反馈回路，使用输出设备来调节输入所测量的环境条件。某些输入可以与某些输出结合，以创造各种不同的控制和调节应用。除了简单的调节，方法可用于创建一个随时间变化的设定点，实现诸如热循环器、回流炉、饲养箱的环境模拟、食品和饮料的发酵或腌制，以及烹饪食物（[苏式蒸煮](https://en.wikipedia.org/wiki/Sous-vide)），仅举几例。

触发器可以被设置为根据特定的日期和时间，根据时间的长短，或特定经纬度的日出/日落来激活事件。

Mycodo has been translated to several languages. By default, the language of the browser will determine which language is used, but may be overridden in the General Settings, on the `[Gear Icon] -> Configure -> General` page. If you find an issue and would like to correct a translation or would like to add another language, this can be done at [https://translate.kylegabriel.com](https://translate.kylegabriel.com/engage/mycodo/).
