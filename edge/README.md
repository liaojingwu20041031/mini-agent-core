# Edge Runtime 预留说明

V0.1 不把 C++ 作为主线，只预留一个轻量边缘运行时位置。

推荐后续做法：

- Python Agent Core 通过 HTTP、Unix Socket、ROS2 Service 或串口网关调用边缘工具。
- C++ Edge Runtime 负责 GPIO、CAN、串口、摄像头、ROS2、实时控制等低层能力。
- ARM Linux 板上可把 whisper.cpp、sherpa-onnx、Piper 等本地语音能力封装成服务，再通过 adapter 接入。

