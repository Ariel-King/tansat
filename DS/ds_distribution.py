# coding=UTF-8
__author__ = 'wangpeng'

import sys, os
from configobj import ConfigObj
import matplotlib
from matplotlib.font_manager import FontProperties
matplotlib.use('Agg')
from pylab import *
from math import ceil
from mpl_toolkits.basemap import Basemap  # @UnresolvedImport

def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为2个
    args_nums = len(xArg)
    if args_nums != 2:
        print 'input error: args nums is 1!'
        return
    # 获取处理文件时间和文件类型
    I_FILE = xArg[0]
    O_FILE = xArg[1]

    if os.path.exists(I_FILE):
        fp = open(I_FILE, 'r')
        data = fp.readlines()
        fp.close()

    LON = []
    LAT = []
    NAME = []

    for line in data:
        NAME.append(line.split()[0])
        LON.append(float (line.split()[1]) )
        LAT.append(float (line.split()[2]) )

    O_DIR, OFILE = os.path.split(O_FILE)

    draw_sites(LON, LAT, NAME, O_DIR, OFILE)

def draw_sites(lons, lats, str_values, outpath, pic_name, Overwrite = True):
    '''
    在地图标注观测站点
    lons 经度列表
    lats 纬度列表
    outpath 图像输出路径
    '''

   # GRAY = '#7b7b7b'
   # OCEAN = '#64a0d9'
   # LAND = '#e6c9a1'

    # OCEAN = '#b3d11f'   # color of googlemap
    OCEAN = '#b3d1ff'   # color of googlemap
    LAND = '#f4f3f0'
    GRAY = '#707070'
    GRAY2 = '#5E5E5E'

#     china_nlat = 60
#     china_slat = 0
#     china_wlon = 50
#     china_elon = 140
    china_nlat = 90
    china_slat = -90
    china_wlon = -180
    china_elon = 180

    # mpl全局参数设定
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = ['Arial']
#     mpl.rcParams['font.sans-serif'] = ['YaHei Consolas Hybrid']

#     mpl.rcParams['legend.numpoints'] = 1
#     mpl.rcParams['legend.fontsize'] = 9
    mpl.rcParams['font.size'] = 10
    mpl.rcParams['axes.linewidth']  = 0.6   # for colorbar


    try:
        if not os.path.isdir(outpath):
            os.makedirs(outpath)
    except:
        print('**[%s]**mkdir error' % outpath)
        return

    figfp = os.path.join(outpath, '%s.png' % pic_name)

    if Overwrite == False and os.path.isfile(figfp):
        return  # 图像存在，则不覆盖

    fig = figure()
    ax = subplot(111)

#     # 调整figure大小
#     fig.set_size_inches(8, 4.3)

    # 调整subplot大小
    subplots_adjust(left = 0.05, right = 0.97, top = 0.96, bottom = 0.03)

    # setup Lambert Conformal basemap.
#     m = Basemap(lon_0 = 0, lat_0 = 0,
#                 projection='cyl', resolution='c')
    m = Basemap(llcrnrlon = floor(china_wlon), llcrnrlat = floor(china_slat),
                urcrnrlon = ceil(china_elon), urcrnrlat = ceil(china_nlat),
                projection='cyl', resolution='l') # resolution = 'h' for high-res coastlines

    # 背景颜色
    m.drawmapboundary(fill_color=OCEAN)
    # fill continents, set lake color same as ocean color.
    m.fillcontinents(color=LAND, lake_color=OCEAN, zorder = 0)

    # 画 海岸线 和 国境线
    m.drawcoastlines(linewidth = 0.3, color=GRAY)
    m.drawcountries(linewidth = 0.9, color='w', zorder = 1) # 为国境线添加白边，美观，模仿googleMap
    m.drawcountries(linewidth = 0.3, color=GRAY, zorder = 2)

    # draw parallels
    delat = 30.
    circles = np.arange(0., 91., delat).tolist() +\
              np.arange(-delat, -91., -delat).tolist()
    m.drawparallels(circles, linewidth=0.2, labels=[1, 0, 0, 1], dashes = [1, 1])

    # draw meridians
    delon = 30.
    meridians = np.arange(0., 180., delon).tolist() +\
                np.arange(-delon, -180., -delon).tolist()
    m.drawmeridians(meridians, linewidth=0.2, labels=[1, 0, 1, 0], dashes = [1, 1])

    # to make parallels and meridians' color deeper, draw again
    fig.canvas.draw()
    m.drawparallels(circles, linewidth=0.1, labels=[1, 0, 0, 1], dashes = [1, 1])
    m.drawmeridians(meridians, linewidth=0.1, labels=[1, 0, 1, 0], dashes = [1, 1])

    # shape
    # m.readshapefile(os.path.join(localpath, 'CHN_adm/CHN_adm1'), 'province', linewidth = 0.2, color='w')
    # m.readshapefile(os.path.join(localpath, 'CHN_adm/CHN_adm1'), 'province', linewidth = 0.2, color=GRAY)

    # 颜色标尺
    cmap = mpl.cm.prism    # mpl.cm.jet_r
    colorlst = np.array(getColorNum(len(lons)))
    colorlst = mpl.cm.prism(colorlst)

#     norm = mpl.colors.Normalize(vmin = 0.0, vmax = len(lons))

    # 画站点
    # m.scatter(lons, lats, s=10, c='#fd0006', cmap = cmap, marker='o', linewidths = 0, alpha=1, zorder = 10)
    m.scatter(lons, lats, s=40, c=GRAY2, marker='o', linewidths = 0, alpha=1, zorder = 40)
    # m.scatter(lons, lats, s=12, c=colorlst, marker='+', linewidths = 0.6, alpha=1, zorder = 10)

    # legend
#     labels = ('Factor 1', 'Factor 2', 'Factor 3', 'Factor 4', 'Factor 5')
#     legend = plt.legend(labels, loc=(0.9, .95), labelspacing=0.1)

    # add colorbar
    '''
    cax = fig.add_axes([0.21, 0.08, 0.6, 0.02])

    cb1 = mpl.colorbar.ColorbarBase(cax, cmap = cmap,
                                    norm=norm,
                                    orientation='horizontal')
    ax.set_title(nm)
    '''
    ## --------- display 1 ----------
    for i in range(len(lons)):
        # print lons[i], lats[i]+0.1, str_values[i]
        ax.text(lons[i], lats[i]+0.1, str_values[i], {'color' : colorlst[i], 'fontsize' : 10},
                horizontalalignment='left', #'center'
                verticalalignment='bottom',
                zorder = 30)

    # 设定Map边框粗细
    spines = ax.spines
    for eachspine in spines:
        spines[eachspine].set_linewidth(0.6)

    # 保存图像
    plt.savefig(figfp, dpi = 300)

    #plt.close()
    fig.clear()


def getColorNum(num):
    aa = range(num)
#     return aa
    bb = aa[::2]
    cc = list(np.array(bb) + 1)
    cc = cc[:len(aa)-len(bb)]
    cc.reverse()
    return bb + cc



if __name__ == '__main__':
    main()

