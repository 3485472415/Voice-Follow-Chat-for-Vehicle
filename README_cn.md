本项目基于 RDK X5 打造一款大模型陪伴助手，融合 UWB 定位、360° 雷达避障、小车控制机、讯飞语音模块与摄像头感知。它能听懂指令、主动跟随、识别环境并像真人一样陪伴聊天。
终端 1 — 摄像头
source /opt/tros/humble/setup.bash
ros2 run hobot_usb_cam hobot_usb_cam --ros-args -p pixel_format:=mjpeg
终端 2 — 语音服务服务
source ~/ros2_ws/install/setup.bash
ros2 launch ollama_ros_chat ollama_ros_chat.launch.py
终端 3 — 语音交互
source ~/ros2_ws/install/setup.bash
ros2 launch wheeltec_mic_aiui aiui_chat.launch.py usart_port_name:=/dev/ttyACM2
终端 4 — 跟随程序
python3 main.py
终端 5 — 物品识别
source ~/ros2_ws/install/setup.bash
python3 ~/ros2_ws/src/item_vision_pkg/item_vision_pkg/hand_vision.py
