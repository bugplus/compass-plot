import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.interpolate import make_interp_spline

# 读取文件中的数据
def read_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            if 'magx,y,z' in line:
                # 提取磁力计数据
                parts = line.split(':')
                if len(parts) > 2:
                    mag_data = parts[-1].strip().split(',')
                    if len(mag_data) == 3:
                        try:
                            x, y, z = map(int, mag_data)
                            data.append((x, y, z))
                        except ValueError:
                            continue
    return data

# 对数据进行平滑处理和插值
def smooth_and_interpolate(data, num_points=1000):
    x = np.array([point[0] for point in data])
    y = np.array([point[1] for point in data])
    z = np.array([point[2] for point in data])

    # 创建插值函数
    tck_x = make_interp_spline(np.arange(len(x)), x, k=3)
    tck_y = make_interp_spline(np.arange(len(y)), y, k=3)
    tck_z = make_interp_spline(np.arange(len(z)), z, k=3)

    # 生成新的数据点
    t_new = np.linspace(0, len(x) - 1, num_points)
    x_new = tck_x(t_new)
    y_new = tck_y(t_new)
    z_new = tck_z(t_new)

    return np.column_stack((x_new, y_new, z_new))

# 绘制三维圆并显示圆心和坐标系原点
def plot_3d_circle(data):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 提取x, y, z坐标
    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]

    # 绘制线图
    ax.plot(x, y, z, c='r', marker='o', label='Magnetic Field Line')

    # 计算数据点的圆心（均值）
    center_x = np.mean(x)
    center_y = np.mean(y)
    center_z = np.mean(z)

    # 在数据点的圆心位置绘制一个点
    ax.scatter(center_x, center_y, center_z, color='blue', s=100, label='Data Center')

    # 在三维坐标系的原点位置绘制一个点
    ax.scatter(0, 0, 0, color='green', s=100, label='Coordinate Origin')

    # 设置坐标轴标签
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # 设置标题
    ax.set_title('3D Circle from Magnetometer Data')

    # 调整坐标轴范围以确保原点可见
    max_range = max(max(x) - min(x), max(y) - min(y), max(z) - min(z)) / 2
    mid_x = (max(x) + min(x)) / 2
    mid_y = (max(y) + min(y)) / 2
    mid_z = (max(z) + min(z)) / 2

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    # 设置视角
    ax.view_init(elev=20, azim=-45)

    # 添加图例
    ax.legend()

    # 显示图形
    plt.show()

# 主函数
if __name__ == "__main__":
    file_path = 'test.txt'  # 替换为你的文件路径
    data = read_data(file_path)
    if data:
        smoothed_data = smooth_and_interpolate(data)
        plot_3d_circle(smoothed_data)
    else:
        print("No valid data found in the file.")