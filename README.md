Powered by RDK X5, this smart companion integrates LLM, vision, and iFlytek voice technology. Utilizing UWB positioning and 360° LiDAR, it offers safe, precise following. More than just a robot, it "sees" you and converses naturally like a real human, serving as your truly empathetic friend.
Terminal 1 — Camera
source /opt/tros/humble/setup.bash
ros2 run hobot_usb_cam hobot_usb_cam --ros-args -p pixel_format:=mjpeg
Terminal 2 — Voice Service
source ~/ros2_ws/install/setup.bash
ros2 launch ollama_ros_chat ollama_ros_chat.launch.py
Terminal 3 — Voice Interaction
source ~/ros2_ws/install/setup.bash
ros2 launch wheeltec_mic_aiui aiui_chat.launch.py usart_port_name:=/dev/ttyACM2
Terminal 4 — Following Program
python3 main.py
Terminal 5 — Object Recognition
source ~/ros2_ws/install/setup.bash
python3 ~/ros2_ws/src/item_vision_pkg/item_vision_pkg/hand_vision.py
