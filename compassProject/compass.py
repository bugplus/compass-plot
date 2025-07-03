# -*- coding: utf-8 -*-
"""
compass_calibration_three_steps_optimized.py

功能说明：
- 接收 mag_x 和 mag_y 数据
- 绘制三张图：
  1. 原始数据（前30秒持续更新）
  2. 仅缩放后的正圆（30秒后一次性绘制）
  3. 完全校准后（30秒后一次性绘制）
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import serial
import time
import warnings

# 抑制 matplotlib 的 UserWarning
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# ===================== 配置区域 =====================
PORT = 'COM4'               # 修改为你实际使用的串口号
BAUD_RATE = 115200          # 波特率（需与设备一致）
TIMEOUT = 1                 # 串口超时时间
UPDATE_INTERVAL = 50        # 更新间隔（毫秒）
MAX_POINTS = 600            # 最大数据点数
# ===================================================

# 初始化数据容器
raw_data = []

# 创建三个画布
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

# 图1：原始数据
line1, = ax1.plot([], [], 'r.', markersize=3)
ax1.set_title("Raw Magnetometer X-Y Data\n(Collecting for Calibration)")
ax1.set_xlabel("mag_x")
ax1.set_ylabel("mag_y")
ax1.axhline(0, color='black', lw=0.5)
ax1.axvline(0, color='black', lw=0.5)
ax1.grid(True)
ax1.axis('equal')
ax1.set_xlim(-300, 300)  # 设置一个合理的初始范围
ax1.set_ylim(-300, 300)

# 图2：仅缩放后的正圆
line2, = ax2.plot([], [], 'g.', markersize=3)
ax2.set_title("After Scaling Only\n(Scale: x=?, y=?)")  # 初始标题，后续更新
ax2.set_xlabel("mag_x (scaled)")
ax2.set_ylabel("mag_y (scaled)")
ax2.axhline(0, color='black', lw=0.5)
ax2.axvline(0, color='black', lw=0.5)
ax2.grid(True)
ax2.axis('equal')

# 图3：最终校准图（去中心化 + 缩放）
line3, = ax3.plot([], [], 'b.', markersize=3)
ax3.set_title("Fully Calibrated\n(Offset: (0.0, 0.0), Scale: x=1.000, y=1.000)")  # 初始标题，后续更新
ax3.set_xlabel("mag_x (calibrated)")
ax3.set_ylabel("mag_y (calibrated)")
ax3.axhline(0, color='black', lw=0.5)
ax3.axvline(0, color='black', lw=0.5)
ax3.grid(True)
ax3.axis('equal')

# 打开串口
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=TIMEOUT)
    print(f"[INFO] 已连接到串口 {PORT}")
except Exception as e:
    print(f"[ERROR] 无法打开串口 {PORT}，错误：{e}")
    exit()

# 全局变量
start_time = None
calibration_done = False
scale_x = scale_y = 1.0
center_x = center_y = 0.0
data_collection_started = False  # 是否已开始采集数据
x_range_final = None
y_range_final = None


# 更新函数
def update(_):  # 使用 '_' 来忽略 frame 参数
    global raw_data, start_time, calibration_done, scale_x, scale_y, center_x, center_y
    global data_collection_started, x_range_final, y_range_final

    current_time = time.time()

    # 尝试读取串口数据
    while ser.in_waiting:
        line_str = ser.readline().decode('utf-8', errors='replace').strip()
        try:
            data = line_str.split(',')
            if len(data) >= 2:
                x = int(data[0].split('=')[1])
                y = int(data[1].split('=')[1])
                raw_data.append((x, y))
                if len(raw_data) > MAX_POINTS:
                    raw_data.pop(0)

                # 只在 30 秒采集阶段打印数据
                if data_collection_started and (current_time - start_time <= 30):
                    print(f"Received Data: mag_x={x}, mag_y={y}")

                # 第一次接收到数据，开始计时
                if not data_collection_started:
                    start_time = current_time
                    data_collection_started = True

        except Exception as e:
            print(f"[ERROR] 数据解析失败: {e}")
            continue

    # 更新原始数据图（前30秒持续更新）
    if len(raw_data) >= 2 and not calibration_done:
        xs = np.array([x[0] for x in raw_data])
        ys = np.array([y[1] for y in raw_data])
        line1.set_data(xs, ys)

        # 动态调整图一的坐标范围
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        margin = 50
        ax1.set_xlim(x_min - margin, x_max + margin)
        ax1.set_ylim(y_min - margin, y_max + margin)

    # 如果已经开始采集，并且还没校准完成
    if data_collection_started and not calibration_done and (current_time - start_time > 30):
        if len(raw_data) >= 6:
            xs = np.array([x[0] for x in raw_data])
            ys = np.array([y[1] for y in raw_data])

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            # 保存统一范围用于设置所有图
            margin = 50
            x_range_final = (x_min - margin, x_max + margin)
            y_range_final = (y_min - margin, y_max + margin)

            x_range = x_max - x_min
            y_range = y_max - y_min

            if x_range >= y_range:
                scale_x = 1.0
                scale_y = x_range / y_range
            else:
                scale_x = y_range / x_range
                scale_y = 1.0

            scaled_xs = xs * scale_x
            scaled_ys = ys * scale_y

            line2.set_data(scaled_xs, scaled_ys)
            ax2.set_title(f"After Scaling Only\n(Scale: x={scale_x:.3f}, y={scale_y:.3f})")

            center_x = (max(scaled_xs) + min(scaled_xs)) / 2
            center_y = (max(scaled_ys) + min(scaled_ys)) / 2

            calibrated_xs = scaled_xs - center_x
            calibrated_ys = scaled_ys - center_y

            line3.set_data(calibrated_xs, calibrated_ys)
            ax3.set_title(f"Fully Calibrated\n(Offset: ({center_x:.1f}, {center_y:.1f}), Scale: x={scale_x:.3f}, y={scale_y:.3f})")

            # 设置所有图的相同坐标范围
            for ax in [ax1, ax2, ax3]:
                ax.set_xlim(x_range_final)
                ax.set_ylim(y_range_final)

        calibration_done = True
        print("[INFO] 校准完成，已切换至校准图")

    return line1, line2, line3


# 启动动画
ani = FuncAnimation(fig, update, frames=None, interval=UPDATE_INTERVAL, blit=False, cache_frame_data=False)
plt.tight_layout()
plt.show()

# 关闭串口
ser.close()
print("[INFO] 串口已关闭")