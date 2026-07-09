#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import serial
import struct
import threading
import time
import subprocess
import os
import signal
import sys
import math
import json
# #xgd
from std_msgs.msg import Bool
# ==========================================
# 1. 底盘驱动与 UWB 解析 (保持原有逻辑不变)
# ==========================================
class ChassisDriver:
    def __init__(self, port='/dev/ttyACM1'):
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.1)
        except Exception as e:
            print(f"[底盘错误] {e}"); sys.exit(1)

    def set_motors(self, v_l, v_r):
        if not self.ser or not self.ser.is_open:
            print("[DEBUG] 串口未打开，指令未下发！")
            return
        data = struct.pack('>hhhh', int(v_l), int(v_r), int(v_l), int(v_r))
        frame = bytearray([0xAA, 0x55, 0x0D, 0x01]) + data
        frame.append(sum(frame) & 0xFF)
        try:
            self.ser.write(frame)
        except Exception as e:
            print(f"[DEBUG] 串口写入异常: {e}")

    def stop_all(self): self.set_motors(0, 0)

class UWBReader(threading.Thread):
    def __init__(self, port='/dev/uwb_usb'):
        super().__init__(daemon=True)
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.1)
        except Exception as e:
            print(f"[UWB错误] {e}"); sys.exit(1)
        self.target_dist, self.target_angle, self.last_update = 0, 0, 0

    def run(self):
        buf = bytearray()
        while True:
            if self.ser.in_waiting > 0:
                buf.extend(self.ser.read(self.ser.in_waiting))
                while len(buf) >= 30:
                    if buf[0:4] == b'\xff\xff\xff\xff':
                        p_len = struct.unpack('>H', buf[4:6])[0]
                        if len(buf) < p_len: break
                        if struct.unpack('>H', buf[8:10])[0] == 0x2001:
                            self.target_dist = struct.unpack('>I', buf[20:24])[0]
                            self.target_angle = struct.unpack('>h', buf[24:26])[0]
                            self.last_update = time.time()
                        buf = buf[p_len:]
                    else: buf.pop(0)
            else: time.sleep(0.01)

# ==========================================
# 2. 主控节点 (引入 APF 调优参数)
# ==========================================
class AutoFollowNode(Node):
    def __init__(self):
        super().__init__('auto_follow_apf')
        
        # 加载校准配置文件
        try:
            with open('robot_config.json', 'r') as f:
                self.cfg = json.load(f)
        except:
            self.get_logger().error("未找到配置文件，请先运行校准程序！"); sys.exit(1)

        self.chassis = ChassisDriver()
        self.uwb = UWBReader()
        self.uwb.start()
        
        self.lidar_dist_min = 99.0
        self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)
        
        # --- [APF 参数调节区 - 你可以根据实际表现调整这些数值] ---
        self.UWB_OFFSET = 0.01    # UWB 零位偏移
        self.SAFE_DIST = 50.0      # 期望跟随距离 (cm)
        
        # 1. 向前的引力系数 (控制追赶的欲望)
        self.K_ATT = 20.0           
        
        # 2. 墙壁的斥力系数 (控制避障的力度)
        self.K_REP = 1000.0          
        
        # 3. 斥力作用半径 (m) (雷达在这个距离内才开始产生排斥力)
        self.REP_LIMIT = 0.6       
        
        # 4. 小车最大速度限制
        self.MAX_SPEED = 2500       
        # ---------------------------------------------------

        self.create_timer(0.05, self.control_loop)
        self.get_logger().info("APF 优化跟随程序启动！")
        # #xgd
        self.follow_enabled = False
        self.create_subscription(Bool, '/follow_enable', self.follow_callback, 10)
    def scan_callback(self, msg):
        # 仅关注正前方 40 度范围内的障碍物，且过滤无效数据
        front_ranges = []
        for i, dist in enumerate(msg.ranges):
            if dist < 0.05 or math.isinf(dist) or math.isnan(dist): continue
            
            angle = math.degrees(msg.angle_min + i * msg.angle_increment)
            if self.cfg.get("lidar_mirror", False): angle = -angle
            if self.cfg.get("lidar_flip", False): angle += 180
            while angle > 180: angle -= 360
            while angle < -180: angle += 360
            
            if abs(angle) < 30:
                front_ranges.append(dist)
                
        self.lidar_dist_min = min(front_ranges) if front_ranges else 99.0
    #xgd
    def follow_callback(self, msg):
        self.follow_enabled = msg.data
        self.get_logger().info(f"[DEBUG] follow_callback收到: {msg.data}, follow_enabled现在是: {self.follow_enabled}")
        if not msg.data:
            self.chassis.stop_all()

    def control_loop(self):
        #xgd
        if not self.follow_enabled:
            return
        uwb_age = time.time() - self.uwb.last_update
        #xgd
        if uwb_age > 1.0:
            self.get_logger().warn(f"[DEBUG] UWB信号过期 {uwb_age:.2f}秒，停止跟随下发")
            self.chassis.stop_all(); return
        
        self.get_logger().info(f"[DEBUG] 正常控制中: dist={self.uwb.target_dist}, angle={self.uwb.target_angle}")
        #xgd

        # --- A. 计算引力 (Attraction) ---
        # 距离偏差 = 当前距离 - 期望距离
        dist_err = self.uwb.target_dist - self.SAFE_DIST
        v_att = dist_err * self.K_ATT

        # --- B. 计算斥力 (Repulsion) ---
        v_rep = 0.0
        if self.lidar_dist_min < self.REP_LIMIT:
            # 斥力公式：K_REP * (1/d - 1/limit)
            v_rep = self.K_REP * (1.0 / self.lidar_dist_min - 1.0 / self.REP_LIMIT)

        # --- C. 合力叠加计算线速度 ---
        # 最终线速度 = 引力速度 - 斥力速度
        linear_v = (v_att - v_rep) * self.cfg.get("linear_inv", 1)

        # --- D. 转向逻辑 (保持原有的 P 控制) ---
        err_angle = self.uwb.target_angle - self.UWB_OFFSET
        if self.cfg.get("uwb_reverse", False): err_angle = -err_angle
        while err_angle > 180: err_angle -= 360
        while err_angle < -180: err_angle += 360
        
        angular_w = int(err_angle * 14.0) * self.cfg.get("angular_inv", 1)

        # 速度死区与限幅处理
        if abs(linear_v) < 80: linear_v = 0.0
        linear_v = max(-self.MAX_SPEED, min(self.MAX_SPEED, linear_v))
        angular_w = max(-self.MAX_SPEED, min(self.MAX_SPEED, angular_w))
        self.get_logger().info(
            f"[DEBUG] linear_v={linear_v:.1f}, angular_w={angular_w:.1f}, "
            f"最终指令=({linear_v+angular_w:.1f}, {linear_v-angular_w:.1f})"
        )
        # 下发底盘指令
        self.chassis.set_motors(linear_v + angular_w, linear_v - angular_w)

# ==========================================
# 3. 运行入口
# ==========================================
def main():
    driver_proc = None
    try:
        # 后台拉起雷达驱动
        driver_proc = subprocess.Popen(
            ['ros2', 'launch', 'ydlidar_ros2_driver', 'ydlidar_launch.py'],
            preexec_fn=os.setsid
        )
        time.sleep(4) 
        
        rclpy.init()
        node = AutoFollowNode()
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.chassis.stop_all()
            node.destroy_node()
    finally:
        if driver_proc:
            os.killpg(os.getpgid(driver_proc.pid), signal.SIGINT)
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
