#!/usr/bin/env python3
"""收到触发信号 → 拍照 → 发给Qwen-VL识别 → 结果发回TTS"""
import os
import base64
import threading

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String, Bool
from cv_bridge import CvBridge
import cv2
import requests
import numpy as np
from rclpy.qos import QoSProfile, ReliabilityPolicy   # 文件顶部 import 区加
# class HandVision(Node):
#     def __init__(self):
#         super().__init__('hand_vision')
#         self.bridge = CvBridge()

#         self.latest_frame = None
#         self.lock = threading.Lock()

#         # 摄像头话题，注意确认实际话题名（ros2 topic list | grep -i image）
#         # self.create_subscription(Image, '/image', self.img_cb, 1)
        
#         qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
#         self.create_subscription(CompressedImage, '/image', self.img_cb, qos)


#         # 触发信号：收到 true 就拍照识别
#         self.create_subscription(Bool, '/trigger_item_identify', self.trigger_cb, 10)

#         # 识别结果发布出去，供其他模块（比如TTS）订阅
#         self.result_pub = self.create_publisher(String, '/item_identify_result', 10)

#         # DashScope (Qwen-VL) API 配置
#         self.api_url = "https://ws-69455228qb6ws396.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
#         self.api_key = "sk-ws-H.EMRIDML.PMz2.MEUCIFtgs2d7sGSpzqAPQ8BreqyS3CoBEouuryN-4mqi7L34AiEAoebOzwxIqtvBZlJP4UPYM27l14ZyuTfU5wlSkFkN7cs"
#         if not self.api_key:
#             self.get_logger().warn("未检测到环境变量 DASHSCOPE_API_KEY，视觉识别功能将无法调用！")

#         self.get_logger().info("手部物品视觉节点已启动")

#     # def img_cb(self, msg):
#     #     with self.lock:
#     #         self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
#     def img_cb(self, msg):
#         with self.lock:
#             # JPEG 格式直接用 data 字段，不需要 CvBridge 解码
#             self.latest_frame = cv2.imdecode(
#                 np.frombuffer(bytes(msg.data), dtype=np.uint8),
#                 cv2.IMREAD_COLOR
#             )


#     def trigger_cb(self, msg):
#         if not msg.data:
#             return
#         with self.lock:
#             frame_available = self.latest_frame is not None
#         if not frame_available:
#             self.get_logger().warn("尚未收到摄像头图像，无法识别")
#             return

#         # 即时反馈，避免云端推理延迟让用户以为没反应
#         wait_msg = String()
#         wait_msg.data = "好的，我看看"
#         self.result_pub.publish(wait_msg)

#         threading.Thread(target=self.do_identify, daemon=True).start()

#     def do_identify(self):
#         with self.lock:
#             frame = self.latest_frame.copy()
#             _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
#             img_b64 = base64.b64encode(buf).decode()

#             prompt = (
#                 "顾客把一个物品放在了摄像头前，想知道这是什么、有什么用。"
#                 "请你识别图片中的物品，用2-3句话简要介绍这个物品是什么、"
#                 "有什么用途或好处。如果画面中看不清或没有明显物品，就说没看清楚。"
#             )

#         payload = {
#             "model": "qwen-vl-plus",
#             "messages": [{
#                 "role": "user",
#                 "content": [
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
#                     {"type": "text", "text": prompt}
#                 ]
#             }]
#         }
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }

#         try:
#             resp = requests.post(self.api_url, json=payload, headers=headers, timeout=15)
#             resp.raise_for_status()
#             reply = resp.json()['choices'][0]['message']['content']
#             self.get_logger().info(f"AI识别结果: {reply}")

#             out_msg = String()
#             out_msg.data = reply
#             self.result_pub.publish(out_msg)
#         except Exception as e:
#             self.get_logger().error(f"视觉识别失败: {e}")
#             out_msg = String()
#             out_msg.data = "抱歉，我没看清这个东西"
#             self.result_pub.publish(out_msg)
#!/usr/bin/env python3
"""收到触发信号 → 拍照 → 发给Qwen-VL识别 → 结果发回TTS"""
import os
import base64
import threading
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String, Bool
from cv_bridge import CvBridge
import cv2
import requests  # 保留 requests，但需正确构造 body
import json      # 新增：用于构造 JSON 请求体
from rclpy.qos import QoSProfile, ReliabilityPolicy

class HandVision(Node):
    def __init__(self):
        super().__init__('hand_vision')
        self.bridge = CvBridge()
        self.latest_frame = None
        self.lock = threading.Lock()

        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(CompressedImage, '/image', self.img_cb, qos)
        self.create_subscription(Bool, '/trigger_item_identify', self.trigger_cb, 1)

        # === 修改点1：API 配置 ===
        self.api_url = "https://ws-69455228qb6ws396.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.api_key = "sk-ws-H.EMRIHLI.P52q.MEQCIDxCqkhREfxzbD53aI1YWl7K-Qn9kerhFTrxQZRLv_rfAiBvpbDilA2Qlrq6JOrXX6M-lMTlRQLRlznR5W-1TmI6PQ"

        # TTS 发布者（假设）
        self.tts_pub = self.create_publisher(String, '/feedback_words', 10)

    def img_cb(self, msg):
        try:
            cv_img = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")
            with self.lock:
                self.latest_frame = cv_img.copy()
        except Exception as e:
            self.get_logger().error(f"图像转换失败: {e}")

    def trigger_cb(self, msg):
        if not msg.data:
            return

        with self.lock:
            if self.latest_frame is None:
                self.get_logger().warn("无可用图像帧")
                return
            frame = self.latest_frame.copy()

        # 图像转 base64
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        img_b64 = base64.b64encode(buffer).decode('utf-8')

        # === 修改点2：构造符合 OpenAI Vision 格式的请求体 ===
        payload = {
            "model": "qwen3.7-plus",  # ←←← 关键：必须指定模型
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                        {"type": "text", "text": "这是什么物品？请用一句话回答。"}
                    ]
                }
            ],
            "max_tokens": 100,
            "stream": True   # 改成流式
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30, stream=True)
            response.raise_for_status()
            
            full_text = ""
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data_str = line[len("data: "):]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        full_text += delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
            
            result = full_text.strip()
            self.get_logger().info(f"Qwen-VL 识别结果: {result}")
            
            tts_msg = String()
            tts_msg.data = result
            self.tts_pub.publish(tts_msg)

        except Exception as e:
            self.get_logger().error(f"视觉识别失败: {e}")

def main():
    rclpy.init()
    node = HandVision()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
