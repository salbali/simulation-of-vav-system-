# 风管类
# 输入 流量，管长，局部阻力系数
# 输出 选择的管径，流速，S，压力损失
class Duct(object):
    def __init__(self, G, L, kexi, r=0, v=4, style='round'):
        self.G = G  # m3/h
        self.L = L  # m
        self.kexi = kexi
        self.r = r
        self.v = v
        self.style = style
        self.A = self.G / 3600 / self.v

        # 管径
        round_d = [0.015, 0.02, 0.025, 0.032, 0.04, 0.04, 0.07, 0.08, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.35,
                   0.4, 0.45, 0.5, 0.6, 0.7, 0.8]
        round_r = [x / 2 for x in round_d]
        if self.style is 'round' and self.r == 0:
            for r in round_r:
                if 3.1415 * (r ** 2) > self.A:
                    self.r = r
                    break

        # 反推
        self.A = 3.1415 * self.r ** 2
        self.v = self.G / 3600 / self.A
        self.d = self.r * 2
        self.S = (0.02 * self.L / self.d + self.kexi) * 8 * 1.2 / (3.1415 ** 2) / (self.d ** 4)

        self.p = self.S * (self.G / 3600) ** 2

d1 = Duct(4342, 0.78, 2.6)
#print(d1.r, d1.v, d1.S, d1.p)
#print((4342/3600)**2*19.7)


# 水泵 风机
# 性能曲线拟合
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve


class Poly(object):
    """多项式拟合 y是x的多项式 输出k是拟合好的系数"""
    def __init__(self, x, y, dim):
        self.x = np.array(x, dtype=float)
        self.y = np.array(y, dtype=float)
        self.dim = dim
        # please make sure len(self.x) == len(self.y)

        self.dim_ = True  # 是否能满足dim
        if len(self.x) < self.dim + 1:
            self.dim = len(self.x) - 1
            self.dim_ = False

        # 求x的多项式矩阵
        self.x_mat = np.mat([np.power(self.x, i) for i in range(self.dim + 1)]).T

        # 求解
        if len(self.x) == self.dim + 1:  # 精确解
            self.k = self.x_mat.I * np.mat(self.y).T
        elif len(self.x) > self.dim + 1:  # 最优解
            self.k = (self.x_mat.T * self.x_mat).I * self.x_mat.T * np.mat(self.y).T

        # 预测
        self.prediction = self.x_mat * self.k

    def plot(self):
        plt.scatter(self.x, self.y)
        plot_x = np.linspace(self.x.min(), self.x.max())
        plot_x_mat = np.mat([np.power(plot_x, i) for i in range(self.dim + 1)]).T
        plot_y = plot_x_mat * self.k
        plt.plot(plot_x, plot_y)
        plt.show()
'''
x = [0, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800]
y = [443, 383, 348, 305, 277, 249, 216, 172, 112, 30]
p = Poly(x, y, 3)
print(p.prediction)
p.plot()
'''


class Fan(object):
    """风机特性曲线 x是风量 z是频率 y是不同频率和风量下的压力"""
    def __init__(self, x, y, z, dim1=3, dim2=5):
        self.x = x
        self.y = y
        self.z = z
        self.dim1 = dim1
        self.dim2 = dim2

        # 对不同频率下的风量和压力拟合，求出曲线的系数
        self.h1 = [Poly(self.x[0:len(yi)], yi, self.dim1) for yi in self.y]
        self.k1 = np.array([hi.k for hi in self.h1]).reshape(-1, dim1 + 1)

        # 对不同频率下的曲线的系数拟合
        self.h2 = [Poly(self.z, k1i, dim2) for k1i in self.k1.T]
        self.k2 = np.array([hi.k for hi in self.h2]).reshape(-1, dim2 + 1)

        # check_k1
        self.k1_prediction = np.array([h2i.prediction for h2i in self.h2]).T.reshape(-1, dim1 + 1)
        # k1精度校核

        # check_y
        self.prediction = [np.array(self.k1_prediction[i] * self.h1[i].x_mat.T).flatten() for i in range(len(self.h1))]
        # y精度校核

    # 绘图
    def plot(self):
        for i in range(len(self.h1)):
            plt.scatter(self.h1[i].x, self.h1[i].y)
            plt.plot(self.h1[i].x, self.prediction[i])
        plt.grid(True)
        plt.show()

    # 预测(应用)
    def p(self, g0, inv0):
        g0 = np.array(g0, dtype=float)
        inv0 = np.array(inv0, dtype=float)

        inv_mat = np.mat([np.power(inv0, i) for i in range(self.dim2 + 1)])
        k1_prediction = inv_mat * self.k2.T
        g_mat = np.mat([np.power(g0, i) for i in range(self.dim1 + 1)])

        return np.array(k1_prediction * g_mat.T).flatten()

# 测试
g = [0, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800]
p = []
p.append([443, 383, 348, 305, 277, 249, 216, 172, 112, 30])
p.append([355, 296, 256, 238, 207, 182, 148, 97, 21])
p.append([342, 284, 246, 217, 190, 161, 121, 62])
p.append([336, 278, 236, 206, 178, 145, 97, 38])
p.append([320, 264, 223, 189, 153, 109, 50])
p.append([300, 239, 194, 153, 110, 55])
p.append([260, 200, 152, 107, 52])
p.append([179, 129, 79, 24])
inv = [50, 45, 40, 35, 30, 25, 20, 15]
'''
f = Fan(g, p, inv)
print(f.k1)
print(f.k1_prediction)
print(f.prediction)
f.plot()
print(f.p(600, 40))
'''
g1 = list(map(lambda x: x * 4342 / 1200, g))
p1 = [[x * 270 / 216 for x in pi] for pi in p]
#print(p1)
f2 = Fan(g1, p1, inv)
#print(f.k1)
#print(f.k1_prediction)
#print(f.prediction)
#print(f.p(2000, 50))
#f2.plot()
'''
f1_x = f2.h1[0].x
f1_y = f2.h1[0].y
for i in range(8):
    hz = 50 - 5 * i
    x = f1_x * hz / 50
    y = f1_y * (hz / 50) ** 2
    plt.plot(x, y)
    plt.scatter(x, y)
plt.grid(True)
plt.show()
'''
g2 = list(map(lambda x: x * 4342 / 1200, g))
p2 = [[x * 35 / 216 for x in pi] for pi in p]
f1 = Fan(g2, p2, inv)
#f1.plot()

x = np.linspace(0, 5000)
'''
y1 = []
y2 = []
ub = []
ua = []
#print(((f1.p(x[1], 50) - 3.2 * x[1] ** 2) / 20.6))

for i in range(len(x)):
    ub.append((f1.p(x[i], 50) - 3.2 * (x[i]/3600) ** 2))
    ua.append((f2.p(x[i], 50) - 172.1 * (x[i]/3600) ** 2))
    if ub[i] > 0:
        y1.append((x[i]/3600) - np.sqrt((f1.p(x[i], 50) - 3.2 * (x[i]/3600) ** 2) / 20.6))
    else:
        y1.append(None)
    if ua[i] > 0:
        y2.append((x[i]/3600) - np.sqrt((f2.p(x[i], 50) - 172.1 * (x[i]/3600) ** 2) / 10.6))
    else:
        y2.append(None)
'''
'''
plt.scatter(x, y1)
plt.scatter(x, y2)
plt.scatter(x, ub)
plt.scatter(x, ua)
plt.show()
'''
from mpl_toolkits.mplot3d import Axes3D

#fig = plt.figure()
#ax = Axes3D(fig)
'''
a = []
b = []
c = []
for i in x:
    for j in x:
        a.append(i)
        b.append(j)
        if ((f1.p(i, 50) - 3.2 * (i/3600)**2 + f2.p(j, 50) - 172.1 * (j/3600)**2)/9.1) >0:
            c.append(np.sqrt((f1.p(i, 50) - 3.2 * (i/3600)**2 + f2.p(j, 50) - 172.1 * (j/3600)**2)/9.1))
        else:
            c.append(0.001)
#ax =plt.subplot(111, projection = '3d')
#ax.scatter(a,b,c)
#plt.show()


def f_1(x):
    if (f1.p(x, 50) - 3.2 * (x/3600) ** 2)>0:
        return x - np.sqrt((f1.p(x, 50) - 3.2 * (x/3600) ** 2)/20.6)
    else:
        return 0

def f_2(x):
    if (f2.p(x, 50) - 172.1 * (x/3600) ** 2)>0:
        return x - np.sqrt((f2.p(x, 50) - 172.1 * (x/3600) ** 2)/10.6)
    else:
        return 0

epsilon = 1

def erfen2(f, max, min, y0):
    """y = f(x) 单调，求x"""
    mid = (max + min) / 2
    y = f(mid)
    error = abs(y - y0)
    if error < epsilon:
        return mid
    elif (f(max) - f(min)) * (y - y0) > 0:
        return erfen(f, mid, min, y0)
    else:
        return erfen(f, max, mid, y0)

def erfen(f, max, min, y0):
    """y = f(x) 单调，求x"""
    error = epsilon + 1
    while error > epsilon:
        mid = (max + min) / 2
        y = f(mid)
        error = abs(y - y0)
        if error < epsilon:
            return mid
        elif (f(max) - f(min)) * (y - y0) > 0:
            max = mid
        else:
            min = mid

# print(erfen(f, 5000, 0, y0))

def g(x):  # !!!!!!g(x)没有用到x
    g1 = erfen(f_1, 5000, 0, x)
    g2 = erfen(f_2, 5000, 0, x)
    if (f1.p(g1, 50) - 3.2 * (g1/3600)**2 + f2.p(g2, 50) - 172.1 * (g2/3600)**2)>0:
        return np.sqrt(((f1.p(g1, 50) - 3.2 * (g1/3600)**2 + f2.p(g2, 50) - 172.1 * (g2/3600)**2)/9.1))-x/3600
    else:
        return 0

#g3 = erfen(g, 5000, 0, 0)
#print(g3)

def g1_max_f(x):
    return f1.p(x, 50)-3.2 * (x/3600) ** 2
def g2_max_f(x):
    return f2.p(x, 50)-172.1 * (x/3600) ** 2
g1_max = erfen(g1_max_f, 10000, 0, 0)
g2_max = erfen(g2_max_f, 10000, 0, 0)
print(g2_max)
# print(g1_max)

g11 = np.linspace(0, g1_max)
g31 = [g11i/3600 - np.sqrt((f1.p(g11i, 50) - 3.2 * (g11i/3600) ** 2)/20.6)*3600 for g11i in g11]
g21 = []

def g2_f(x):
    return x/3600 - np.sqrt((f2.p(x, 50) - 72.1 * (x/3600) ** 2)/10.6)

for i in g31:
    g21.append(erfen(g2_f, g2_max, 0, i/3600))

#plt.scatter(g11, g21)
plt.plot(g11)
plt.plot(g21)
plt.plot(g31)
plt.show()
'''



def f(x):
    x1 = float(x[0])
    x2 = float(x[1])
    x3 = float(x[2])
    return np.array([
        f1.p(x1, 50) - 3.2 * (x1/3600) ** 2 - 20.6 * ((x1 - x3)/3600) ** 2,
        f2.p(x2, 50) - 172.1 * (x2/3600) ** 2 - 10.6 * ((x2 - x3)/3600) ** 2,
        f1.p(x1, 50) - 3.2 * (x1/3600) ** 2 - 9.1 * (x3/3600) ** 2 - 172.1 * (x2/3600) ** 2 + f2.p(x2, 50)
    ]).flatten()

result = fsolve(f, np.array([1, 1, 1]))

#x1/3600 - np.sqrt((f1.p(x1, 50) - 3.2 * (x1/3600) ** 2) / 20.6) - x3/3600, x2/3600 - np.sqrt((f2.p(x2, 50) - 172.1 * (x2/3600) ** 2) / 10.6) - x3/3600,

print(result)
print(f(result))
'''

g1 = 5478
g2 = 5478
p1 = (f1.p(g1, 50))
p2 = (f2.p(g2, 50))
ub = p1 - 3.2 * (g1/3600) ** 2
ua = p2 - 172.1 * (g2/3600) ** 2
g31 = g1/3600 - (ub/20.6) ** 0.5
g32 = g2/3600 - (ua/10.6) ** 0.5
g33 = ((ub - ua)/9.1) ** 0.5

print(g1/3600, g2/3600, p1, p2, ub, ua, g31, g32, g33)
'''