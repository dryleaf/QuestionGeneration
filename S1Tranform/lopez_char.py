#!/usr/bin/env python 
# -*- coding: utf-8 -*-
__author__ = 'duc_tin'

from matplotlib import pyplot as plt


data = map(int, open('csv.txt').readlines())
x_ = range(len(data))[::-1]

fig, ax = plt.subplots()
ahvs, = ax.plot(x_, data, '-o')#, alpha=0.5)
ax.set_xlabel('Some Xaxis label', fontsize=20)
ax.set_ylabel('Some Yaxis label', fontsize=20)
ax.grid(True)

# set limit
axes = plt.gca()
# draw approximated line
ax.plot(data[::], x_, 'r', lw=2)
# plt.axis('off')
axes.get_xaxis().set_visible(False)

# plt.legend([ahvs, appr], [r'$(\alpha hv)^2$', 'Approximated line'])
fig.tight_layout()

plt.show()
