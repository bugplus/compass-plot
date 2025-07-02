import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import re
import numpy as np
import time

# ===================== 配置区域 =====================
PORT = 'COM4'               # 修改为你实际使用的串口号
BAUD_RATE = 115200          # 波特率（需与设备一致）
TIMEOUT = 1                 # 串口超时时间
X_RANGE = (-300, 300)       # X 轴范围
Y_RANGE = (-300, 300)       # Y 轴范围
UPDATE_INTERVAL = 50        # 更新间隔（毫秒）
# ===================================================

# 正则表达式匹配 mag_x 和 mag_y
pattern = re.compile(r'mag_x=(?P<x>-?\d+).*?mag_y=(?P<y>-?\d+)')

# 初始化数据容器
raw_data = []

# 创建两个画布
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 第一张图：原始数据
line1, = ax1.plot([], [], 'r.', markersize=3)
ax1.set_title("Raw Magnetometer X-Y Data\n(Collecting for Calibration)")
ax1.set_xlabel("mag_x")
ax1.set_ylabel("mag_y")
ax1.axhline(0, color='black', lw=0.5)
ax1.axvline(0, color='black', lw=0.5)
ax1.grid(True)
ax1.axis('equal')
ax1.set_xlim(*X_RANGE)
ax1.set_ylim(*Y_RANGE)

# 第二张图：校准后数据
line2, = ax2.plot([], [], 'b.', markersize=3)
ax2.set_title("Calibrated Magnetometer X-Y Data\n(Center at origin)")
ax2.set_xlabel("mag_x (calibrated)")
ax2.set_ylabel("mag_y (calibrated)")
ax2.axhline(0, color='black', lw=0.5)
ax2.axvline(0, color='black', lw=0.5)
ax2.grid(True)
ax2.axis('equal')
ax2.set_xlim(*X_RANGE)
ax2.set_ylim(*Y_RANGE)

# 打开串口
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=TIMEOUT)
    print(f"[INFO] 已连接到串口 {PORT}")
except Exception as e:
    print(f"[ERROR] 无法打开串口 {PORT}，错误：{e}")
    exit()

# 计算缩放因子（强制 offset 为 0）
def compute_calibration_params(xs, ys):
    xs_centered = np.array(xs)  # 不再减去均值
    ys_centered = np.array(ys)

    x_range = np.ptp(xs_centered)
    y_range = np.ptp(ys_centered)

    scale_x = y_range / x_range if x_range != 0 else 1.0
    return 0.0, 0.0, scale_x, 1.0  # 强制 offset 为 0

# 全局变量
start_time = None
calibration_done = False

# 更新函数
def update(frame):
    global raw_data, start_time, calibration_done

    current_time = time.time()

    # 初始化开始时间
    if start_time is None:
        start_time = current_time

    # 前30秒：采集数据并绘制原始图
    if current_time - start_time <= 30:
        while ser.in_waiting:
            line_str = ser.readline().decode('utf-8', errors='ignore').strip()
            match = pattern.search(line_str)
            if match:
                x = int(match.group('x'))
                y = int(match.group('y'))
                raw_data.append([x, y])
                if len(raw_data) > 1000:
                    raw_data.pop(0)
                print(f"[DATA] mag_x={x}, mag_y={y}")

        if len(raw_data) >= 2:
            xs, ys = zip(*raw_data)
            line1.set_data(xs, ys)
    elif not calibration_done:
        # 30秒后：计算缩放因子，生成校准图
        if len(raw_data) >= 2:
            xs, ys = zip(*raw_data)
            _, _, scale_x, _ = compute_calibration_params(xs, ys)

            # 应用缩放（不进行 offset 校正）
            calibrated_xs = np.array(xs) * scale_x
            calibrated_ys = np.array(ys)

            line2.set_data(calibrated_xs, calibrated_ys)
            ax2.set_title(f"Calibrated Data\n(Scale: x={scale_x:.3f})")

        calibration_done = True
        print("[INFO] 校准完成，已切换至校准图")

    return line1, line2

# 启动动画
ani = FuncAnimation(fig, update, frames=None, interval=UPDATE_INTERVAL, blit=False, cache_frame_data=False, save_count=600)
plt.tight_layout()
plt.show()

# 关闭串口
ser.close()
print("[INFO] 串口已关闭")