import tomopy
import dxchange
import os

from rapidz import Stream
from bluesky.callbacks.broker import LiveImage
import matplotlib.pyplot as plt
from bluesky.utils import install_qt_kicker
from xpdtools.pipelines.tomo import tomo_prep, tomo_pipeline_piecewise

fname = os.path.expanduser("~/Downloads/tooth.h5")

start = 0
end = 1
proj, flat, dark, theta = dxchange.read_aps_32id(fname, sino=(start, end))
proj = tomopy.normalize(proj, flat, dark)

rot_center = tomopy.find_center(proj, theta, init=290, ind=0, tol=0.5)

backend = "thread"
# backend = 'dask'
# from dask.distributed import Client
# c = Client()

center = Stream(stream_name="center")
proj_node = Stream(stream_name="projection")
theta_node = Stream(stream_name="theta")

install_qt_kicker()

li = LiveImage("hi", cmap="viridis")
li2 = LiveImage("hi", cmap="viridis")

x = Stream()
th = Stream()
th_dim = Stream()
x_dim = Stream()
th_extents = Stream()
x_extents = Stream()
qoi = Stream()

# ns = tomo_prep(
#     x.scatter(backend=backend),
#     th.scatter(backend=backend),
#     th_dim.scatter(backend=backend),
#     x_dim.scatter(backend=backend),
#     th_extents.scatter(backend=backend),
#     x_extents.scatter(backend=backend),
# )
ns = tomo_prep(x, th, th_dim, x_dim, th_extents, x_extents)
# ns2 = tomo_pipeline_piecewise(
#     qoi.scatter(backend=backend),
#     center=center.scatter(backend=backend),
#     th_dimension=len(theta),
#     x_dimension=proj.shape[-1],
#     **ns
# )
ns2 = tomo_pipeline_piecewise(
    qoi,
    center=center,
    th_dimension=len(theta),
    x_dimension=proj.shape[-1],
    **ns
)
ns.update(**ns2)
z = ns["rec"]
z.sink(print)
zz = (
    z
    # .buffer(1000).gather()
    .sink(li.update)
)
(
    ns["sinogram"]
    # .buffer(1000).gather()
    .sink(li2.update)
)

# plt.pause(.1)
# qoi.visualize()

center.emit(rot_center)
th_dim.emit(len(theta))
x_dim.emit(proj.shape[-1])
th_extents.emit([0, 180])
x_extents.emit([0, proj.shape[-1]])

lb = 145
ub = 147

ns["sinogram"].state[:, :lb] = proj[:, 0, :lb]
ns["sinogram"].state[:, ub:] = proj[:, 0, ub:]

for i in range(lb, ub):
    for j in range(0, len(theta)):
        x.emit(i)
        th.emit(j)
        qoi.emit(proj[j, 0, i])
        print(i, j)
        plt.pause(.001)
print("done")

plt.show()
