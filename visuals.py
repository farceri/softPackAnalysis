'''
Created by Francesco
12 October 2021
'''
#functions and script to visualize a 2d dpm packing
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import axes3d, Axes3D
from matplotlib import animation
from matplotlib import cm
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from scipy.spatial import Voronoi, voronoi_plot_2d, Delaunay
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pyvoro
import itertools
import sys
import os
import utils
import spCluster as cluster

def setAxes3D(ax):
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

def set3DPackingAxes(boxSize, ax):
    xBounds = np.array([0, boxSize[0]])
    yBounds = np.array([0, boxSize[1]])
    zBounds = np.array([0, boxSize[2]])
    ax.set_xlim(xBounds[0], xBounds[1])
    ax.set_ylim(yBounds[0], yBounds[1])
    ax.set_ylim(zBounds[0], zBounds[1])
    #ax.set_box_aspect(aspect = (1,1,1))
    #ax.set_aspect('equal', adjustable='box')
    setAxes3D(ax)

def plot3DPacking(dirName, figureName):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    xBounds = np.array([0, boxSize[0]])
    yBounds = np.array([0, boxSize[1]])
    zBounds = np.array([0, boxSize[2]])
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    pos = np.array(np.loadtxt(dirName + os.sep + "particlePos.dat"))
    pos[:,0] -= np.floor(pos[:,0]/boxSize[0]) * boxSize[0]
    pos[:,1] -= np.floor(pos[:,1]/boxSize[1]) * boxSize[1]
    pos[:,2] -= np.floor(pos[:,2]/boxSize[2]) * boxSize[2]
    fig = plt.figure(dpi=100)
    ax = Axes3D(fig)
    set3DPackingAxes(boxSize, ax)
    u = np.linspace(0, 2*np.pi, 120)
    v = np.linspace(0, np.pi, 120)
    colorId = getRadColorList(rad)
    for i in range(pos.shape[0]):
        x = pos[i,0] + rad[i]*np.outer(np.cos(u), np.sin(v))
        y = pos[i,1] + rad[i]*np.outer(np.sin(u), np.sin(v))
        z = pos[i,2] + rad[i]*np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x,y,z, color=colorId[i], rstride=4, cstride=4, alpha=1)
    plt.savefig("/home/francesco/Pictures/soft/packings/3d-" + figureName + ".png", transparent=True, format = "png")
    plt.show()

def setAxes2D(ax):
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])

def setPackingAxes(boxSize, ax):
    xBounds = np.array([0, boxSize[0]])
    yBounds = np.array([0, boxSize[1]])
    ax.set_xlim(xBounds[0], xBounds[1])
    ax.set_ylim(yBounds[0], yBounds[1])
    ax.set_aspect('equal', adjustable='box')
    setAxes2D(ax)

def setZoomPackingAxes(xBounds, yBounds, ax):
    ax.set_xlim(xBounds[0], xBounds[1])
    ax.set_ylim(yBounds[0], yBounds[1])
    ax.set_aspect('equal', adjustable='box')
    setAxes2D(ax)

def setGridAxes(bins, ax):
    xBounds = np.array([bins[0], bins[-1]])
    yBounds = np.array([bins[0], bins[-1]])
    ax.set_xlim(xBounds[0], xBounds[1])
    ax.set_ylim(yBounds[0], yBounds[1])
    ax.set_aspect('equal', adjustable='box')
    setAxes2D(ax)

def setBigBoxAxes(boxSize, ax, delta=0.1):
    xBounds = np.array([-delta, boxSize[0]+delta])
    yBounds = np.array([-delta, boxSize[1]+delta])
    ax.set_xlim(xBounds[0], xBounds[1])
    ax.set_ylim(yBounds[0], yBounds[1])
    ax.set_aspect('equal', adjustable='box')
    setAxes2D(ax)

def getRadColorList(rad):
    colorList = cm.get_cmap('viridis', rad.shape[0])
    colorId = np.zeros((rad.shape[0], 4))
    count = 0
    for particleId in np.argsort(rad):
        colorId[particleId] = colorList(count/rad.shape[0])
        count += 1
    return colorId

def getEkinColorList(ekin):
    colorList = cm.get_cmap('viridis', ekin.shape[0])
    colorId = np.zeros((ekin.shape[0], 4))
    count = 0
    for particleId in np.argsort(ekin):
        colorId[particleId] = colorList(count/ekin.shape[0])
        count += 1
    return colorId

def getColorListFromLabels(labels):
    numLabels = np.unique(labels).shape[0]-1
    colorList = cm.get_cmap('tab20', numLabels)
    colorId = np.zeros((labels.shape[0], 4))
    for particleId in range(labels.shape[0]):
        if(labels[particleId]==-1 or labels[particleId]==0): # particles not in a cluster
            colorId[particleId] = [1,1,1,1]
        else:
            colorId[particleId] = colorList(labels[particleId]/numLabels)
    return colorId

def getDenseColorList(denseList):
    colorId = np.zeros((denseList.shape[0], 4))
    for particleId in range(denseList.shape[0]):
        if(denseList[particleId]==1):
            colorId[particleId] = [0.2,0.2,0.2,0.2]
        else:
            colorId[particleId] = [1,1,1,1]
    return colorId

def plotSPPacking(dirName, figureName, ekmap=False, quiver=False, dense=False, border=False, threshold=0.65, filter='filter', alpha=0.6, lj=False, shear=False, strain=0, numMoved=0, shiftx=0, shifty=0):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    #pos = np.array(np.loadtxt(dirName + os.sep + "particlePos.dat"))
    if(shear == True):
        pos = utils.getLEPBCPositions(dirName + os.sep + "particlePos.dat", boxSize, strain)
    else:
        pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    if(lj == True):
        rad *= 2**(1/6)
    #denseList = np.loadtxt(dirName + os.sep + "denseList.dat")
    #pos = utils.centerPositions(pos, rad, boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty)#1.35, 0 for box21 16k 0, 0.2 for 0.31 16k droplet
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    #xBounds = np.array([1.5, 2.2])
    #yBounds = np.array([0.4, 1])
    #setZoomPackingAxes(xBounds, yBounds, ax)
    #sep = utils.getDirSep(dirName, 'movedLabel')
    #movedLabel = np.loadtxt(dirName + sep + 'movedLabel.dat')
    #numMoved = movedLabel[movedLabel==1].shape[0]
    if(numMoved != 0):
        print("numMoved:", numMoved)
    #setBigBoxAxes(boxSize, ax, 0.05)
    if(dense==True):
        if not(os.path.exists(dirName + os.sep + "particleList.dat")):
            cluster.computeDelaunayCluster(dirName, threshold, filter=filter)
        denseList = np.loadtxt(dirName + os.sep + "particleList.dat")[:,0]
        colorId = getDenseColorList(denseList)
    elif(border==True):
        if not(os.path.exists(dirName + os.sep + "particleList.dat")):
            cluster.computeDelaunayCluster(dirName, threshold, filter=filter)
        borderList = np.loadtxt(dirName + os.sep + "particleList.dat")[:,1]
        colorId = getDenseColorList(borderList)
        interface = []
        for i in range(borderList.shape[0]):
            if(borderList[i]==1 and pos[i,0]>1.5):
                interface.append(pos[i,0])
        print(np.mean(interface))
    elif(ekmap==True):
        vel = np.array(np.loadtxt(dirName + os.sep + "particleVel.dat"))
        ekin = 0.5*np.linalg.norm(vel, axis=1)**2
        colorId = getEkinColorList(ekin)
    else:
        colorId = getRadColorList(rad)
    if(quiver==True):
        vel = np.array(np.loadtxt(dirName + os.sep + "particleVel.dat"))
    for particleId in range(rad.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        if(quiver==True):
            ax.add_artist(plt.Circle([x, y], r, edgecolor=colorId[particleId], facecolor='none', alpha=alpha, linewidth = 0.7))
            vx = vel[particleId,0]
            vy = vel[particleId,1]
            ax.quiver(x, y, vx, vy, facecolor='k', width=0.002, scale=10)#width=0.002, scale=3)20
        else:
            ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth='0.3'))
            #print(particleId)
            #plt.pause(0.5)
            #if(movedLabel[particleId]==1):
            #    ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth=0.3))
            if(particleId<numMoved):
                ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth=0.3))
            #if(particleId == 95):
            #    ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth='0.3'))
    #if(border==True):
    #    plt.tight_layout()
    #    borderPos = pos[borderList==1]
    #    borderPos = utils.sortBorderPos(borderPos, borderList, boxSize)
    #    for particleId in range(1,borderPos.shape[0]):
    #        ax.plot(borderPos[particleId,0], borderPos[particleId,1], marker='*', markeredgecolor='k', color=[0.5,0.5,1], markersize=12, markeredgewidth=0.5)
    #        slope = (borderPos[particleId,1] - borderPos[particleId-1,1]) / (borderPos[particleId,0] - borderPos[particleId-1,0])
    #        intercept = borderPos[particleId-1,1] - borderPos[particleId-1,0] * slope
    #        x = np.linspace(borderPos[particleId-1,0], borderPos[particleId,0])
    #        ax.plot(x, slope*x+intercept, lw=0.7, ls='dashed', color='r')
    #        plt.pause(0.01)
    if(dense==True):
        figureName = "/home/francesco/Pictures/soft/packings/dense-" + figureName + ".png"
    elif(border==True):
        figureName = "/home/francesco/Pictures/soft/packings/border-" + figureName + ".png"
    elif(ekmap==True):
        colorBar = cm.ScalarMappable(cmap='viridis')
        cb = plt.colorbar(colorBar)
        label = "$E_{kin}$"
        cb.set_ticks([0, 1])
        cb.ax.tick_params(labelsize=12)
        ticklabels = [np.format_float_scientific(np.min(ekin), precision=2), np.format_float_scientific(np.max(ekin), precision=2)]
        cb.set_ticklabels(ticklabels)
        cb.set_label(label=label, fontsize=14, labelpad=-20, rotation='horizontal')
        figureName = "/home/francesco/Pictures/soft/packings/ekmap-" + figureName + ".png"
    elif(quiver==True):
        figureName = "/home/francesco/Pictures/soft/packings/velmap-" + figureName + ".png"
    else:
        figureName = "/home/francesco/Pictures/soft/packings/" + figureName + ".png"
    plt.tight_layout()
    plt.savefig(figureName, transparent=False, format = "png")
    plt.show()

def plotSPFixedBoundaryPacking(dirName, figureName, onedim=False, quiver=False, alpha = 0.6):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    pos = np.array(np.loadtxt(dirName + os.sep + "particlePos.dat"))
    #if(onedim == "onedim"):
    #    pos[:,0] -= np.floor(pos[:,0]/boxSize[0]) * boxSize[0]
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    #setBigBoxAxes(boxSize, ax, 0.05)
    colorId = getRadColorList(rad)
    if(quiver==True):
        vel = np.array(np.loadtxt(dirName + os.sep + "particleVel.dat"))
        #vel *= 5
    for particleId in range(rad.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        if(quiver==True):
            ax.add_artist(plt.Circle([x, y], r, edgecolor=colorId[particleId], facecolor='none', alpha=alpha, linewidth = 0.7))
            vx = vel[particleId,0]
            vy = vel[particleId,1]
            ax.quiver(x, y, vx, vy, facecolor='k', width=0.002, scale=10)#width=0.002, scale=3)20
        else:
            ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth='0.3'))
    plt.tight_layout()
    figureName = "/home/francesco/Pictures/soft/packings/fb-" + figureName + ".png"
    plt.savefig(figureName, transparent=True, format = "png")
    plt.show()

def getStressColorList(stress, which='total', droplet='lj'):
    colorList = cm.get_cmap('viridis', stress.shape[0])
    colorId = np.zeros((stress.shape[0], 4))
    count = 0
    if(which=='total'):
        if(droplet=='lj' or droplet=='ra'):
            p = np.sum(stress[:,0:2], axis=1)
        else:
            p = np.sum(stress[:,0:3], axis=1)
    elif(which=='steric'):
        p = stress[:,0]
    elif(which=='thermal'):
        p = stress[:,1]
    elif(which=='active'):
        p = stress[:,2]
    elif(which=='etot'):
        p = stress[:,3]
    for particleId in np.argsort(p):
        colorId[particleId] = colorList(count/p.shape[0])
        count += 1
    return colorId, colorList

def plotSPStressMapPacking(dirName, figureName, which='total', droplet='lj', l1=0.035, shiftx=0, shifty=0, alpha=0.7):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty)
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    if not(os.path.exists(dirName + os.sep + "particleStress!.dat")):
        if(droplet == 'lj'):
            stress = cluster.computeLJParticleStress(dirName)
        elif(droplet == 'ra'):
            stress = cluster.computeRAParticleStress(dirName, l1)
        else:
            stress = cluster.computeParticleStress(dirName)
    stress = np.loadtxt(dirName + os.sep + "particleStress.dat")
    colorId, colorList = getStressColorList(stress, which, droplet)
    for particleId in range(rad.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth='0.3'))
    colorBar = cm.ScalarMappable(cmap=colorList)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='2%', pad=0.05)
    cb = plt.colorbar(colorBar, cax=cax)
    cb.set_ticks(np.linspace(0, 1, 5))
    cb.ax.tick_params(labelsize=10)
    if(which=='total'):
        mintick = np.min(stress[:,0] + stress[:,1] + stress[:,2])
        maxtick = np.max(stress[:,0] + stress[:,1] + stress[:,2])
        label = "$ Total$\n$stress$"
    elif(which=='steric'):
        mintick = np.min(stress[:,0])
        maxtick = np.max(stress[:,0])
        label = "$ Steric$\n$stress$"
    elif(which=='thermal'):
        mintick = np.min(stress[:,1])
        maxtick = np.max(stress[:,1])
        label = "$ Thermal$\n$stress$"
    elif(which=='active'):
        mintick = np.min(stress[:,2])
        maxtick = np.max(stress[:,2])
        label = "$ Active$\n$stress$"
    elif(which=='etot'):
        mintick = np.min(stress[:,3])
        maxtick = np.max(stress[:,3])
        label = "$E_{tot}$"
    tickList = np.linspace(mintick, maxtick, 5)
    for i in range(tickList.shape[0]):
        #tickList[i] = np.format_float_positional(tickList[i], precision=0)
        tickList[i] = np.format_float_scientific(tickList[i], precision=0)
    cb.set_ticklabels(tickList)
    cb.set_label(label=label, fontsize=12, labelpad=25, rotation='horizontal')
    plt.tight_layout()
    figureName = "/home/francesco/Pictures/soft/packings/pmap-" + figureName + ".png"
    plt.savefig(figureName, transparent=True, format = "png")
    plt.show()

def plotSPVoronoiPacking(dirName, figureName, dense=False, threshold=0.84, filter=True, alpha=0.7, shiftx=0, shifty=0, lj=False):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    if(lj==True):
        rad *= 2**(1/6)
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty)
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    colorId = getRadColorList(rad)
    if(dense==True):
        if(os.path.exists(dirName + os.sep + "denseList!.dat")):
            denseList = np.loadtxt(dirName + os.sep + "denseList.dat")
        else:
            denseList,_ = cluster.computeVoronoiCluster(dirName, threshold, filter=filter)
        colorId = getDenseColorList(denseList)
    for particleId in range(rad.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth=0.3))
    cells = pyvoro.compute_2d_voronoi(pos, [[0, boxSize[0]], [0, boxSize[1]]], 1, radii=rad)
    for i, cell in enumerate(cells):
        polygon = cell['vertices']
        ax.fill(*zip(*polygon), facecolor = 'none', edgecolor='k', lw=0.2)
    plt.plot(pos[0,0], pos[0,1], marker='*', markersize=20, color='k')
    plt.plot(pos[cells[0]['faces'][0]['adjacent_cell'],0], pos[cells[0]['faces'][0]['adjacent_cell'],1], marker='*', markersize=20, color='r')
    plt.plot(pos[cells[0]['faces'][1]['adjacent_cell'],0], pos[cells[0]['faces'][1]['adjacent_cell'],1], marker='*', markersize=20, color='b')
    plt.plot(pos[cells[0]['faces'][2]['adjacent_cell'],0], pos[cells[0]['faces'][2]['adjacent_cell'],1], marker='*', markersize=20, color='g')
    plt.tight_layout()
    figureName = "/home/francesco/Pictures/soft/packings/voronoi-" + figureName + ".png"
    plt.savefig(figureName, transparent=False, format = "png")
    plt.show()

def getDenseSimplexColorList(denseList):
    colorId = np.ones(denseList.shape[0])
    for simplexId in range(denseList.shape[0]):
        if(denseList[simplexId]==0):
            colorId[simplexId] = 0
    return colorId

def computeDenseSimplexColorList(densityList):
    colorId = np.ones(densityList.shape[0])
    for simplexId in range(densityList.shape[0]):
        if(densityList[simplexId] > 0.78):
            colorId[simplexId] = 0
        if(densityList[simplexId] < 0.78 and densityList[simplexId] > 0.453):
            colorId[simplexId] = 0.5
    return colorId

def getDenseBorderColorList(denseList, borderList):
    colorId = np.zeros((denseList.shape[0], 4))
    for particleId in range(denseList.shape[0]):
        if(borderList[particleId]==1):
            colorId[particleId] = [0.5,0.5,0.5,0.5]
        else:
            if(denseList[particleId]==1):
                colorId[particleId] = [0,0,0.8,1]#[0.2,0.2,0.2,0.2]
            else:
                colorId[particleId] = [0,0.8,0,1]
    return colorId

def getBorderColorList(borderList):
    colorId = np.zeros((borderList.shape[0], 4))
    for particleId in range(borderList.shape[0]):
        if(borderList[particleId]==1):
            colorId[particleId] = [0.2,0.2,0.2,0.2]
        else:
            colorId[particleId] = [1,1,1,1]
    return colorId

def plotSPDelaunayPacking(dirName, figureName, dense=False, border=False, threshold=0.76, filter='filter', alpha=0.8, colored=False, shiftx=0, shifty=0, lj=False):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    if(lj==True):
        rad *= 2**(1/6)
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty) # for 4k and 16k, -0.3, 0.1 for 8k 0 -0.2
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    #setBigBoxAxes(boxSize, ax, 0.1)
    colorId = getRadColorList(rad)
    if(dense==True):
        if not(os.path.exists(dirName + os.sep + "particleList.dat")):
            cluster.computeDelaunayCluster(dirName, threshold, filter=filter)
        denseList = np.loadtxt(dirName + os.sep + "particleList.dat")[:,0]
        colorId = getDenseColorList(denseList)
    if(border==True):
        if not(os.path.exists(dirName + os.sep + "particleList.dat")):
            cluster.computeDelaunayCluster(dirName, threshold, filter=filter)
        borderList = np.loadtxt(dirName + os.sep + "particleList.dat")[:,1]
        denseList = np.loadtxt(dirName + os.sep + "particleList.dat")[:,0]
        colorId = getBorderColorList(borderList)
    for particleId in range(rad.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=0.5, linewidth=0.3))
    if(colored == 'colored'):
        newPos, simplices, colorId, borderColorId = cluster.computeAugmentedDelaunayCluster(dirName, threshold, filter, shiftx, shifty) # colorId is 0 for dense and 1 for dilute
        if(dense==True):
            plt.tripcolor(newPos[:,0], newPos[:,1], simplices, lw=0.3, facecolors=colorId, edgecolors='k', alpha=0.5, cmap='bwr')
            #plt.tripcolor(newPos[:,0], newPos[:,1], simplices[colorId==0], lw=0.3, facecolors=colorId[colorId==0], edgecolors='k', alpha=0.5, cmap='bwr')
        if(border==True):
            plt.tripcolor(newPos[:,0], newPos[:,1], simplices[borderColorId==0], lw=0.3, facecolors=borderColorId[borderColorId==0], edgecolors='k', alpha=0.5, cmap='bwr')
        plt.triplot(newPos[:,0], newPos[:,1], simplices, lw=0.2, color='k')
        if(filter == 'filter'):
            figureName = "filter-" + figureName
        else:
            figureName = "cluster-" + figureName
    else:
        newPos, newRad, newIndices = utils.augmentPacking(pos, rad, lx=boxSize[0], ly=boxSize[1])
        simplices = Delaunay(newPos).simplices
        simplices = np.unique(np.sort(simplices, axis=1), axis=0)
        insideIndex = utils.getInsideBoxDelaunaySimplices(simplices, newPos, boxSize)
        plt.triplot(newPos[:,0], newPos[:,1], simplices[insideIndex==1], lw=0.2, color='k')
    if(dense==True):
        figureName = "/home/francesco/Pictures/soft/packings/deldense-" + figureName + ".png"
    elif(border==True):
        figureName = "/home/francesco/Pictures/soft/packings/delborder-" + figureName + ".png"
    else:
        figureName = "/home/francesco/Pictures/soft/packings/del-" + figureName + ".png"
    #plt.plot(pos[148,0], pos[148,1], marker='*', markersize=20, color='r')
    #plt.plot(pos[10886,0], pos[10886,1], marker='s', markersize=20, color='b')
    #plt.plot(pos[13250,0], pos[13250,1], marker='o', markersize=20, color='g')
    #plt.plot(pos[13250,0], pos[13250,1], marker='*', markersize=20, color='k')
    #x = np.linspace(0,1,1000)
    #slope = -0.11838938050442274
    #intercept = 0.9852218251735015
    #plt.plot(x, slope*x + intercept, ls='dashed', color='r', lw=1.2)
    #xp = 0.41924684666399464
    #yp = 0.9355874507185185
    #plt.plot(xp, yp, marker='s', markersize=8, markeredgecolor='k', color=[1,0.5,0])
    plt.tight_layout()
    plt.savefig(figureName, transparent=False, format = "png")
    plt.show()

def plotSPDelaunayLabels(dirName, figureName, dense=False, threshold=0.78, filter=False, alpha=0.8, label='dense3dilute'):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, 0, -0.2)
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    # plot simplices belonging to a certain label
    if(filter == 'filter'):
        checkFile = "denseParticleList-filter.dat"
    else:
        checkFile = "denseParticleList.dat"
    if(os.path.exists(dirName + os.sep + "augmented/" + checkFile)):
        denseList = np.loadtxt(dirName + os.sep + "augmented/" + checkFile)
    else:
        cluster.computeAugmentedDelaunayCluster(dirName, threshold, filter, 0, -0.2, label='label')
        denseList = np.loadtxt(dirName + os.sep + "augmented/" + checkFile)
    newRad = np.loadtxt(dirName + os.sep + "augmented/augmentedRad.dat")
    newPos = np.loadtxt(dirName + os.sep + "augmented/augmentedPos.dat")
    simplices = np.array(np.loadtxt(dirName + os.sep + "augmented/simplices.dat"), dtype=int)
    # first plot packing with dense / dilute particle labels
    colorId = getDenseColorList(denseList)
    for particleId in range(rad.shape[0]):
        x = newPos[particleId,0]
        y = newPos[particleId,1]
        r = newRad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=0.5, linewidth=0.3))
    # then plot labels on simplices
    if(filter == 'filter'):
        labelList = np.loadtxt(dirName + os.sep + "augmented/filterDelaunayLabels/" + label + ".dat")
        allNeighborList = np.loadtxt(dirName + os.sep + "augmented/filterDelaunayLabels/" + label + "AllNeighbors.dat")
        neighborList = np.loadtxt(dirName + os.sep + "augmented/filterDelaunayLabels/" + label + "Neighbors.dat")
    else:
        labelList = np.loadtxt(dirName + os.sep + "augmented/delaunayLabels/" + label + ".dat")
        allNeighborList = np.loadtxt(dirName + os.sep + "augmented/delaunayLabels/" + label + "AllNeighbors.dat")
        neighborList = np.loadtxt(dirName + os.sep + "augmented/delaunayLabels/" + label + "Neighbors.dat")
    plt.tripcolor(newPos[:,0], newPos[:,1], simplices[labelList==1], lw=0.3, facecolors=labelList[labelList==1], edgecolors='k', alpha=1)
    plt.tripcolor(newPos[:,0], newPos[:,1], simplices[neighborList==1], lw=0.3, facecolors=neighborList[neighborList==1], edgecolors='k', alpha=0.5)
    plt.tripcolor(newPos[:,0], newPos[:,1], simplices[allNeighborList==1], lw=0.3, facecolors=allNeighborList[allNeighborList==1], edgecolors='k', alpha=0.2)
    plt.tight_layout()
    if(filter == 'filter'):
        figureName = "/home/francesco/Pictures/soft/packings/filter2Labels-" + label + "-" + figureName + ".png"
    else:
        figureName = "/home/francesco/Pictures/soft/packings/labels-" + label + "-" + figureName + ".png"
    plt.savefig(figureName, transparent=False, format = "png")
    plt.show()

def plotSPDelaunayParticleClusters(dirName, figureName, threshold=0.76, filter='filter', alpha=0.7, paused=False, shiftx=0, shifty=0):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    eps = 1.8*np.max(rad)
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty) # for 4k and 16k, -0.3, 0.1 for 8k 0 -0.2
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    #setBigBoxAxes(boxSize, ax, 1)
    labels = cluster.getParticleClusterLabels(dirName, boxSize, eps, threshold=threshold)
    #dropletPos, dropletRad = utils.getDropletPosRad(pos, rad, boxSize, labels)
    #print(np.unique(labels))
    colorId = getColorListFromLabels(labels)
    maxLabel = utils.findLargestParticleCluster(rad, labels)
    print("maxLabel:", maxLabel)
    pos = utils.centerSlab(pos, rad, boxSize, labels, maxLabel)
    if(paused=='paused'):
        #i = 0
        for label in np.unique(labels):
            #print(label)
            for particleId in np.argwhere(labels==label)[:,0]:
                x = pos[particleId,0]
                y = pos[particleId,1]
                r = rad[particleId]
                ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth=0.3))
            plt.tight_layout()
            #if(label!=-1):
            #    print(label, np.mean(pos[np.argwhere(labels==label)], axis=0), "computed:", dropletPos[i])
            #    i += 1
            plt.pause(0.5)
    else:
        for particleId in range(rad.shape[0]):
            x = pos[particleId,0]
            y = pos[particleId,1]
            r = rad[particleId]
            ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth=0.3))
            if(labels[particleId]==maxLabel):
                ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth=0.3))
    figureName = "/home/francesco/Pictures/soft/packings/clusters-" + figureName + ".png"
    plt.tight_layout()
    plt.savefig(figureName, transparent=True, format = "png")
    plt.show()

def getColorListFromSimplexLabels(labels):
    numLabels = np.unique(labels).shape[0]-1
    colorId = np.zeros(labels.shape[0])
    colors = utils.getUniqueRandomList(0, np.max(labels), numLabels)
    for label in range(numLabels):
        colorId[labels==label] = colors[label]
    return colorId

def plotSPDelaunaySimplexClusters(dirName, figureName, threshold=0.76, filter='filter', alpha=0.7, paused=False, shiftx=0, shifty=0):
    sep = utils.getDirSep(dirName, "boxSize")
    boxSize = np.loadtxt(dirName + sep + "boxSize.dat")
    rad = np.array(np.loadtxt(dirName + sep + "particleRad.dat"))
    eps = np.max(rad)
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty) # for 4k and 16k, 0, -0.2 for 8k -0.4 0.05
    fig = plt.figure(0, dpi = 150)
    ax = fig.gca()
    setPackingAxes(boxSize, ax)
    dirAugment = dirName + os.sep + 'augmented'
    if not(os.path.exists(dirAugment + '!')):
        cluster.computeAugmentedDelaunayCluster(dirName, threshold, filter, shiftx, shifty)
    newPos = np.loadtxt(dirAugment + os.sep + 'augmentedPos.dat')
    newRad = np.loadtxt(dirAugment + os.sep + 'augmentedRad.dat')
    simplices = np.loadtxt(dirAugment + os.sep + 'simplices.dat').astype(np.int64)
    denseSimplexList = np.loadtxt(dirAugment + os.sep + 'denseSimplexList-filter.dat')
    # compute simplex positions for clustering algorithm
    if not(os.path.exists(dirAugment + os.sep + 'simplexLabels.dat')):
        simplexPos = utils.computeSimplexPos(simplices, newPos)
        labels = utils.getDBClusterLabels(simplexPos, boxSize*1.1, eps, min_samples=1, denseList=denseSimplexList)
        labels = labels + np.ones(labels.shape[0])
        allLabels = -1*np.ones(denseSimplexList.shape[0])
        allLabels[denseSimplexList==1] = labels
        labels = allLabels.astype(np.int64)
        np.savetxt(dirAugment + os.sep + 'simplexLabels.dat', labels)
    else:
        labels = np.loadtxt(dirAugment + os.sep + 'simplexLabels.dat').astype(np.int64)
    #print(np.unique(labels))
    colorId = getColorListFromSimplexLabels(labels)
    # plot particles
    for particleId in range(newRad.shape[0]):
        x = newPos[particleId,0]
        y = newPos[particleId,1]
        r = newRad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='none', alpha=alpha, linewidth=0.3))
    # plot simplex clusters
    if(paused=='paused'):
        for label in np.unique(labels):
            if(label!=-1):
                plt.tripcolor(newPos[:,0], newPos[:,1], simplices[labels==label], facecolors=labels[labels==label], lw=0.3, edgecolors='k', alpha=alpha, cmap='tab20')
                plt.tight_layout()
                plt.pause(0.5)
    else:
        plt.tripcolor(newPos[:,0], newPos[:,1], simplices[labels!=-1], facecolors=colorId[labels!=-1], lw=0.2, edgecolors='k', alpha=0.9, cmap='tab20c')
    figureName = "/home/francesco/Pictures/soft/packings/simplexClusters-" + figureName + ".png"
    plt.tight_layout()
    plt.savefig(figureName, transparent=False, format = "png")
    plt.show()

def plotSoftParticles(ax, pos, rad, alpha = 0.6, colorMap = True, lw = 0.5):
    colorId = np.zeros((rad.shape[0], 4))
    if(colorMap == True):
        colorList = cm.get_cmap('viridis', rad.shape[0])
    else:
        colorList = cm.get_cmap('Reds', rad.shape[0])
    count = 0
    for particleId in np.argsort(rad):
        colorId[particleId] = colorList(count/rad.shape[0])
        count += 1
    for particleId in range(pos.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth = lw))

def plotSoftParticlesSubSet(ax, pos, rad, maxIndex, alpha = 0.7, lw = 0.5):
    colorId = np.zeros((rad.shape[0], 4))
    colorList = cm.get_cmap('viridis', rad.shape[0])
    count = 0
    for particleId in np.argsort(rad):
        colorId[particleId] = colorList(count/rad.shape[0])
        count += 1
    for particleId in range(pos.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=0.5, linewidth = lw))
        if(particleId < maxIndex):
            ax.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth = lw))

def plotSoftParticleQuiverVel(axFrame, pos, vel, rad, tagList = np.array([]), alpha = '0.6'):#122, 984, 107, 729, 59, 288, 373, 286, 543, 187, 6, 534, 104, 347]):
    colorId = np.zeros((rad.shape[0], 4))
    colorList = cm.get_cmap('viridis', rad.shape[0])
    count = 0
    for particleId in np.argsort(rad):
        colorId[particleId] = colorList(count/rad.shape[0])
        count += 1
    if(tagList.size > 0):
        color = np.array(['g', 'b', 'k'])
        d = 0
        for particleId in range(tagList.shape[0]):
            if(tagList[particleId]==1):
                x = pos[particleId,0]
                y = pos[particleId,1]
                vx = vel[particleId,0]
                vy = vel[particleId,1]
                axFrame.quiver(x, y, vx, vy, facecolor=color[d], width=0.008, minshaft=3, scale=3, headwidth=5)
                d += 1
    else:
        for particleId in range(pos.shape[0]):
            x = pos[particleId,0]
            y = pos[particleId,1]
            r = rad[particleId]
            vx = vel[particleId,0]
            vy = vel[particleId,1]
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor=colorId[particleId], facecolor='none', alpha=alpha, linewidth = 0.7))
            axFrame.quiver(x, y, vx, vy, facecolor='k', width=0.002, scale=10)#width=0.003, scale=1, headwidth=5)

def plotSoftParticleStressMap(axFrame, pos, stress, rad, droplet='lj', alpha = 0.7):
    colorId = np.zeros((rad.shape[0], 4))
    colorList = cm.get_cmap('viridis', rad.shape[0])
    count = 0
    if(droplet=='lj' or droplet=='ra'):
        p = np.sum(stress[:,0:2], axis=1)
    else:
        p = np.sum(stress[:,0:3], axis=1)
    for particleId in np.argsort(p):
        colorId[particleId] = colorList(count/p.shape[0])
        count += 1
    for particleId in range(pos.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=alpha, linewidth='0.3'))

def plotSoftParticleCluster(axFrame, pos, rad, denseList, alpha = 0.4):
    for particleId in range(pos.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        if(denseList[particleId] == 1):
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth = 0.7))
        else:
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=[1,1,1], alpha=alpha, linewidth = 0.7))

def plotSoftParticlePerturb(axFrame, pos, rad, movedLabel, alpha=0.8):
    colorId = np.zeros((rad.shape[0], 4))
    colorList = cm.get_cmap('viridis', rad.shape[0])
    count = 0
    for particleId in np.argsort(rad):
        colorId[particleId] = colorList(count/rad.shape[0])
        count += 1
    for particleId in range(pos.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        if(movedLabel[particleId] == 1):
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth = 0.7))
        else:
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorId[particleId], alpha=0.5, linewidth = 0.7))

def makeSoftParticleClusterFrame(dirName, rad, boxSize, figFrame, frames, clusterList):
    pos = np.array(np.loadtxt(dirName + os.sep + "particlePos.dat"))
    pos[:,0] -= np.floor(pos[:,0]/boxSize[0]) * boxSize[0]
    pos[:,1] -= np.floor(pos[:,1]/boxSize[1]) * boxSize[1]
    gcfFrame = plt.gcf()
    gcfFrame.clear()
    axFrame = figFrame.gca()
    setPackingAxes(boxSize, axFrame)
    plotSoftParticleCluster(axFrame, pos, rad, clusterList)
    figFrame.tight_layout()
    axFrame.remove()
    frames.append(axFrame)

def makeSPPackingClusterMixingVideo(dirName, figureName, numFrames = 20, firstStep = 0, stepFreq = 1e04):
    def animate(i):
        frames[i].figure=fig
        fig.axes.append(frames[i])
        fig.add_axes(frames[i])
        return gcf.artists
    frameTime = 300
    frames = []
    stepList = utils.getStepList(numFrames, firstStep, stepFreq)
    print(stepList)
    #frame figure
    figFrame = plt.figure(dpi=150)
    fig = plt.figure(dpi=150)
    gcf = plt.gcf()
    gcf.clear()
    ax = fig.gca()
    boxSize = np.loadtxt(dirName + os.sep + "boxSize.dat")
    setPackingAxes(boxSize, ax)
    rad = np.array(np.loadtxt(dirName + os.sep + "particleRad.dat"))
    if(os.path.exists(dirName + os.sep + "t" + str(stepList[0]) + "/denseList!.dat")):
        denseList = np.loadtxt(dirName + os.sep + "t" + str(stepList[0]) + "/denseList.dat")
    else:
        denseList,_ = cluster.computeVoronoiCluster(dirName + os.sep + "t" + str(stepList[0]))
    # the first configuration gets two frames for better visualization
    makeSoftParticleClusterFrame(dirName + os.sep + "t" + str(stepList[0]), rad, boxSize, figFrame, frames, denseList)
    for i in stepList:
        dirSample = dirName + os.sep + "t" + str(i)
        makeSoftParticleClusterFrame(dirSample, rad, boxSize, figFrame, frames, denseList)
        anim = animation.FuncAnimation(fig, animate, frames=numFrames+1, interval=frameTime, blit=False)
    anim.save("/home/francesco/Pictures/soft/packings/clustermix-" + figureName + ".gif", writer='imagemagick', dpi=plt.gcf().dpi)

def makeSoftParticleFrame(dirName, rad, boxSize, figFrame, frames, subset = False, firstIndex = 10, npt = False, quiver = False, dense = False, perturb = False, pmap = False, droplet = False, l1=0.03):
    pos = utils.getPBCPositions(dirName + os.sep + "particlePos.dat", boxSize)
    #pos = utils.shiftPositions(pos, boxSize, 0.4, 0)
    #pos = utils.centerPositions(pos, rad, boxSize)
    gcfFrame = plt.gcf()
    gcfFrame.clear()
    axFrame = figFrame.gca()
    if(perturb == "perturb" or subset == "subset"):
        xBounds = np.array([1.5, 2.2])
        yBounds = np.array([0.4, 1])
        setZoomPackingAxes(xBounds, yBounds, axFrame)
    else:
        setPackingAxes(boxSize, axFrame)
    if(subset == "subset"):
        plotSoftParticlesSubSet(axFrame, pos, rad, firstIndex)
        #vel = np.array(np.loadtxt(dirName + os.sep + "particleVel.dat"))
        #plotSoftParticleQuiverVel(axFrame, pos, vel, rad, tagList)
    elif(quiver == "quiver"):
        vel = np.array(np.loadtxt(dirName + os.sep + "particleVel.dat"))
        plotSoftParticleQuiverVel(axFrame, pos, vel, rad)
    elif(pmap == "pmap"):
        if(os.path.exists(dirName + os.sep + "particleStress.dat")):
            if(droplet == 'lj'):
                stress = cluster.computeLJParticleStress(dirName)
            elif(droplet == 'ra'):
                stress = cluster.computeRAParticleStress(dirName, l1)
            else:
                stress = cluster.computeParticleStress(dirName)
        stress = np.loadtxt(dirName + os.sep + "particleStress.dat")
        plotSoftParticleStressMap(axFrame, pos, stress, rad, droplet)
    elif(dense == "dense"):
        if(os.path.exists(dirName + os.sep + "particleList.dat")):
            cluster.computeDelaunayCluster(dirName)
        denseList = np.loadtxt(dirName + os.sep + "particleList.dat")[:,0]
        plotSoftParticleCluster(axFrame, pos, rad, denseList)
    elif(perturb == "perturb"):
        movedLabel = np.loadtxt(dirName + '/../movedLabel.dat')
        plotSoftParticlePerturb(axFrame, pos, rad, movedLabel)
    else:
        if(npt == "npt"):
            boxSize = np.loadtxt(dirSample + "/boxSize.dat")
        plotSoftParticles(axFrame, pos, rad)
    figFrame.tight_layout()
    axFrame.remove()
    frames.append(axFrame)

def makeSPPackingVideo(dirName, figureName, numFrames = 20, firstStep = 0, stepFreq = 1e04, logSpaced = False, subset = False, firstIndex = 0, npt = False, quiver = False, dense = False, perturb = False, pmap = False, droplet = False, l1=0.03, lj=False):
    def animate(i):
        frames[i].figure=fig
        fig.axes.append(frames[i])
        fig.add_axes(frames[i])
        return gcf.artists
    frameTime = 300
    frames = []
    if(logSpaced == False):
        stepList = utils.getStepList(numFrames, firstStep, stepFreq)
    else:
        stepList = utils.getLogSpacedStepList(minDecade=5, maxDecade=9)
        numFrames = stepList.shape[0]
    print(stepList)
    #frame figure
    figFrame = plt.figure(dpi=150)
    fig = plt.figure(dpi=150)
    gcf = plt.gcf()
    gcf.clear()
    ax = fig.gca()
    boxSize = np.loadtxt(dirName + os.sep + "boxSize.dat")
    setPackingAxes(boxSize, ax)
    rad = np.array(np.loadtxt(dirName + os.sep + "particleRad.dat"))
    if(lj==True):
        rad *= 2**(1/6)
    # the first configuration gets two frames for better visualization
    makeSoftParticleFrame(dirName + os.sep + "t" + str(stepList[0]), rad, boxSize, figFrame, frames, subset, firstIndex, npt, quiver, dense, perturb, pmap, droplet, l1)
    vel = []
    for i in stepList:
        dirSample = dirName + os.sep + "t" + str(i)
        makeSoftParticleFrame(dirSample, rad, boxSize, figFrame, frames, subset, firstIndex, npt, quiver, dense, perturb, pmap, droplet, l1)
        anim = animation.FuncAnimation(fig, animate, frames=numFrames+1, interval=frameTime, blit=False)
    if(quiver=="quiver"):
        figureName = "velmap-" + figureName
    if(pmap=="pmap"):
        figureName = "pmap-" + figureName
    if(subset=="subset"):
        figureName = "subset-" + figureName
    anim.save("/home/francesco/Pictures/soft/packings/" + figureName + ".gif", writer='imagemagick', dpi=plt.gcf().dpi)

def makeSPShearPackingVideo(dirName, figureName, maxStrain = 1e-01, strainStep = 1e-03, lj = False):
    def animate(i):
        frames[i].figure=fig
        fig.axes.append(frames[i])
        fig.add_axes(frames[i])
        return gcf.artists
    frameTime = 300
    frames = []
    dirList, strainList = utils.getShearDirectories(dirName)
    #frame figure
    figFrame = plt.figure(dpi=150)
    fig = plt.figure(dpi=150)
    gcf = plt.gcf()
    gcf.clear()
    ax = fig.gca()
    boxSize = np.loadtxt(dirName + os.sep + "../boxSize.dat")
    setPackingAxes(boxSize, ax)
    rad = np.array(np.loadtxt(dirName + os.sep + "../particleRad.dat"))
    if(lj==True):
        rad *= 2**(1/6)
    # the first configuration gets two frames for better visualization
    dirSample = dirName + os.sep + dirList[0]
    pos = utils.getLEPBCPositions(dirSample + os.sep + "particlePos.dat", boxSize, 0)
    gcfFrame = plt.gcf()
    gcfFrame.clear()
    axFrame = figFrame.gca()
    setPackingAxes(boxSize, axFrame)
    plotSoftParticles(axFrame, pos, rad)
    figFrame.tight_layout()
    axFrame.remove()
    frames.append(axFrame)
    numFrames = len(range(0,dirList.shape[0],4)) + 1
    print("numFrames:", numFrames)
    for i in range(0,dirList.shape[0],4):
        dirSample = dirName + os.sep + dirList[i]
        pos = utils.getLEPBCPositions(dirSample + os.sep + "particlePos.dat", boxSize, strainList[i])
        gcfFrame = plt.gcf()
        gcfFrame.clear()
        axFrame = figFrame.gca()
        setPackingAxes(boxSize, axFrame)
        plotSoftParticles(axFrame, pos, rad)
        figFrame.tight_layout()
        axFrame.remove()
        frames.append(axFrame)
        anim = animation.FuncAnimation(fig, animate, frames=numFrames, interval=frameTime, blit=False)
    anim.save("/home/francesco/Pictures/soft/packings/shear-" + figureName + ".gif", writer='imagemagick', dpi=plt.gcf().dpi)

def plotSoftParticleDroplet(axFrame, pos, rad, labels, maxLabel, alpha = 0.7):
    colorList = getColorListFromLabels(labels)
    for particleId in range(pos.shape[0]):
        x = pos[particleId,0]
        y = pos[particleId,1]
        r = rad[particleId]
        if(labels[particleId]==maxLabel):
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor='k', alpha=alpha, linewidth=0.3))
        else:
            axFrame.add_artist(plt.Circle([x, y], r, edgecolor='k', facecolor=colorList[particleId], alpha=alpha, linewidth = 0.3))

def makeSoftParticleDropletFrame(pos, rad, boxSize, figFrame, frames, labels, maxLabel):
    gcfFrame = plt.gcf()
    gcfFrame.clear()
    axFrame = figFrame.gca()
    setPackingAxes(boxSize, axFrame)
    plotSoftParticleDroplet(axFrame, pos, rad, labels, maxLabel)
    figFrame.tight_layout()
    axFrame.remove()
    frames.append(axFrame)

def makeSPPackingDropletVideo(dirName, figureName, numFrames = 20, firstStep = 0, stepFreq = 1e04, threshold=0.78, lj=False, shiftx=0, shifty=0):
    def animate(i):
        frames[i].figure=fig
        fig.axes.append(frames[i])
        fig.add_axes(frames[i])
        return gcf.artists
    frameTime = 300
    frames = []
    stepList = utils.getStepList(numFrames, firstStep, stepFreq)
    print(stepList)
    #frame figure
    figFrame = plt.figure(dpi=150)
    fig = plt.figure(dpi=150)
    gcf = plt.gcf()
    gcf.clear()
    ax = fig.gca()
    boxSize = np.loadtxt(dirName + os.sep + "boxSize.dat")
    setPackingAxes(boxSize, ax)
    rad = np.array(np.loadtxt(dirName + os.sep + "particleRad.dat"))
    eps = 1.8*np.max(rad)
    if(lj==True):
        rad *= 2**(1/6)
    pos = utils.getPBCPositions(dirName + os.sep + "t" + str(stepList[0]) + "/particlePos.dat", boxSize)
    pos = utils.shiftPositions(pos, boxSize, shiftx, shifty)
    labels = cluster.getParticleClusterLabels(dirName + os.sep + "t" + str(stepList[0]), boxSize, eps, threshold=threshold)
    maxLabel = utils.findLargestParticleCluster(rad, labels)
    makeSoftParticleDropletFrame(pos, rad, boxSize, figFrame, frames, labels, maxLabel)
    for i in stepList:
        dirSample = dirName + os.sep + "t" + str(i)
        pos = utils.getPBCPositions(dirSample + os.sep + "particlePos.dat", boxSize)
        pos = utils.shiftPositions(pos, boxSize, shiftx, shifty)
        labels = cluster.getParticleClusterLabels(dirSample, boxSize, eps, threshold=threshold)
        maxLabel = utils.findLargestParticleCluster(rad, labels)
        makeSoftParticleDropletFrame(pos, rad, boxSize, figFrame, frames, labels, maxLabel)
        anim = animation.FuncAnimation(fig, animate, frames=numFrames+1, interval=frameTime, blit=False)
    anim.save("/home/francesco/Pictures/soft/packings/droplet-" + figureName + ".gif", writer='imagemagick', dpi=plt.gcf().dpi)

def makeVelFieldFrame(dirName, numBins, bins, boxSize, numParticles, figFrame, frames):
    gcfFrame = plt.gcf()
    gcfFrame.clear()
    axFrame = figFrame.gca()
    setGridAxes(bins, axFrame)
    grid, field = cluster.computeVelocityField(dirName, numBins, plot=False, boxSize=boxSize, numParticles=numParticles)
    axFrame.quiver(grid[:,0], grid[:,1], field[:,0], field[:,1], facecolor='k', width=0.002, scale=3)
    figFrame.tight_layout()
    axFrame.remove()
    frames.append(axFrame)

def makeSPVelFieldVideo(dirName, figureName, numFrames = 20, firstStep = 0, stepFreq = 1e04, numBins=20):
    def animate(i):
        frames[i].figure=fig
        fig.axes.append(frames[i])
        fig.add_axes(frames[i])
        return gcf.artists
    frameTime = 300
    frames = []
    _, stepList = utils.getOrderedDirectories(dirName)
    #timeList = timeList.astype(int)
    stepList = stepList[np.argwhere(stepList%stepFreq==0)[:,0]]
    stepList = stepList[:numFrames]
    print(stepList)
    #frame figure
    figFrame = plt.figure(dpi=150)
    fig = plt.figure(dpi=150)
    gcf = plt.gcf()
    gcf.clear()
    ax = fig.gca()
    boxSize = np.loadtxt(dirName + os.sep + "boxSize.dat")
    bins = np.linspace(-0.5*boxSize[0],0, numBins)
    bins = np.concatenate((np.array([bins[0]-(bins[1]-bins[0])]), bins))
    bins = np.concatenate((bins, np.linspace(0,0.5*boxSize[0],numBins)[1:]))
    setGridAxes(bins, ax)
    rad = np.array(np.loadtxt(dirName + os.sep + "particleRad.dat"))
    numParticles = int(utils.readFromParams(dirName, "numParticles"))
    # the first configuration gets two frames for better visualization
    makeVelFieldFrame(dirName + os.sep + "t0", numBins, bins, boxSize, numParticles, figFrame, frames)
    vel = []
    for i in stepList:
        dirSample = dirName + os.sep + "t" + str(i)
        makeVelFieldFrame(dirSample, numBins, bins, boxSize, numParticles, figFrame, frames)
        anim = animation.FuncAnimation(fig, animate, frames=numFrames+1, interval=frameTime, blit=False)
    anim.save("/home/francesco/Pictures/soft/packings/velfield-" + figureName + ".gif", writer='imagemagick', dpi=plt.gcf().dpi)


if __name__ == '__main__':
    dirName = sys.argv[1]
    whichPlot = sys.argv[2]
    figureName = sys.argv[3]

    if(whichPlot == "ss"):
        plotSPPacking(dirName, figureName, shiftx=float(sys.argv[4]), shifty=float(sys.argv[5]))

    elif(whichPlot == "lj"):
        plotSPPacking(dirName, figureName, lj=True, shiftx=float(sys.argv[4]), shifty=float(sys.argv[5]))

    if(whichPlot == "shearss"):
        plotSPPacking(dirName, figureName, shear=True, strain=float(sys.argv[4]), shiftx=float(sys.argv[5]), shifty=float(sys.argv[6]))

    elif(whichPlot == "shearlj"):
        plotSPPacking(dirName, figureName, lj=True, shear=True, strain=float(sys.argv[4]), shiftx=float(sys.argv[5]), shifty=float(sys.argv[6]))

    elif(whichPlot == "moved"):
        numMoved = int(sys.argv[4])
        plotSPPacking(dirName, figureName, lj=True, numMoved=numMoved, shiftx=float(sys.argv[5]), shifty=float(sys.argv[6]))

    elif(whichPlot == "ss3d"):
        plot3DPacking(dirName, figureName)

    elif(whichPlot == "ssfixed"):
        onedim = sys.argv[4]
        plotSPFixedBoundaryPacking(dirName, figureName, onedim)

    elif(whichPlot == "ssvel"):
        plotSPPacking(dirName, figureName, quiver=True)

    elif(whichPlot == "ssdense"):
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        plotSPPacking(dirName, figureName, dense=True, threshold=threshold, filter=filter, shiftx=float(sys.argv[6]), shifty=float(sys.argv[7]))

    elif(whichPlot == "ssborder"):
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        plotSPPacking(dirName, figureName, border=True, threshold=threshold, filter=filter, shiftx=float(sys.argv[6]), shifty=float(sys.argv[7]))

    elif(whichPlot == "ssekin"):
        alpha = float(sys.argv[4])
        plotSPPacking(dirName, figureName, ekmap=True, alpha=alpha)

    elif(whichPlot == "stress"):
        which = sys.argv[4]
        droplet = sys.argv[5]
        l1 = float(sys.argv[6])
        plotSPStressMapPacking(dirName, figureName, which, droplet, l1, shiftx=float(sys.argv[7]), shifty=float(sys.argv[8]))

    elif(whichPlot == "ssvoro"):
        plotSPVoronoiPacking(dirName, figureName, shiftx=float(sys.argv[4]), shifty=float(sys.argv[5]))

    elif(whichPlot == "ljvoro"):
        plotSPVoronoiPacking(dirName, figureName, shiftx=float(sys.argv[4]), shifty=float(sys.argv[5]), lj=True)

    elif(whichPlot == "ssdel"):
        plotSPDelaunayPacking(dirName, figureName, shiftx=float(sys.argv[4]), shifty=float(sys.argv[5]))

    elif(whichPlot == "ljdel"):
        plotSPDelaunayPacking(dirName, figureName, shiftx=float(sys.argv[4]), shifty=float(sys.argv[5]), lj=True)

    elif(whichPlot == "ssdeldense"):
        np.seterr(divide='ignore', invalid='ignore')
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        colored = sys.argv[6]
        plotSPDelaunayPacking(dirName, figureName, dense=True, threshold=threshold, filter=filter, colored=colored, shiftx=float(sys.argv[7]), shifty=float(sys.argv[8]))

    elif(whichPlot == "ssdelborder"):
        np.seterr(divide='ignore', invalid='ignore')
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        colored = sys.argv[6]
        plotSPDelaunayPacking(dirName, figureName, border=True, threshold=threshold, filter=filter, colored=colored, shiftx=float(sys.argv[7]), shifty=float(sys.argv[8]))

    elif(whichPlot == "ssdellabel"):
        np.seterr(divide='ignore', invalid='ignore')
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        label = sys.argv[6]
        plotSPDelaunayLabels(dirName, figureName, dense=False, threshold=threshold, filter=filter, label=label)

    elif(whichPlot == "ssdelparticle"):
        np.seterr(divide='ignore', invalid='ignore')
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        paused = sys.argv[6]
        plotSPDelaunayParticleClusters(dirName, figureName, threshold=threshold, filter=filter, paused=paused, shiftx=float(sys.argv[7]), shifty=float(sys.argv[8]))

    elif(whichPlot == "ssdelsimplex"):
        np.seterr(divide='ignore', invalid='ignore')
        threshold = float(sys.argv[4])
        filter = sys.argv[5]
        paused = sys.argv[6]
        plotSPDelaunaySimplexClusters(dirName, figureName, threshold=threshold, filter=filter, paused=paused, shiftx=float(sys.argv[7]), shifty=float(sys.argv[8]))

    elif(whichPlot == "ssvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq)

    elif(whichPlot == "ljvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, lj=True, logSpaced=False)

    elif(whichPlot == "shearvideo"):
        maxStrain = float(sys.argv[4])
        strainStep = float(sys.argv[5])
        makeSPShearPackingVideo(dirName, figureName, maxStrain, strainStep)

    elif(whichPlot == "shearljvideo"):
        maxStrain = float(sys.argv[4])
        strainStep = float(sys.argv[5])
        makeSPShearPackingVideo(dirName, figureName, maxStrain, strainStep, lj=True)

    elif(whichPlot == "ssperturb"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, perturb = "perturb")

    elif(whichPlot == "ljperturb"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, lj=True, perturb = "perturb")

    elif(whichPlot == "velfield"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        numBins = int(sys.argv[7])
        makeSPVelFieldVideo(dirName, figureName, numFrames, firstStep, stepFreq, numBins=numBins)

    elif(whichPlot == "velvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, quiver = "quiver")

    elif(whichPlot == "stressvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, pmap = "pmap")

    elif(whichPlot == "rastressvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        l1 = float(sys.argv[7])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, pmap = "pmap", droplet = "ra", l1=l1)

    elif(whichPlot == "ljstressvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, pmap = "pmap", droplet = "lj")

    elif(whichPlot == "clustervideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, dense = "dense")

    elif(whichPlot == "dropletvideo"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        threshold = float(sys.argv[7])
        makeSPPackingDropletVideo(dirName, figureName, numFrames, firstStep, stepFreq, shiftx=float(sys.argv[8]), shifty=float(sys.argv[9]))

    elif(whichPlot == "clustermix"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingClusterMixingVideo(dirName, figureName, numFrames, firstStep, stepFreq)

    elif(whichPlot == "ssvideosubset"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        firstIndex = int(sys.argv[7])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, subset = "subset", firstIndex = firstIndex)

    elif(whichPlot == "ssvideonpt"):
        numFrames = int(sys.argv[4])
        firstStep = float(sys.argv[5])
        stepFreq = float(sys.argv[6])
        makeSPPackingVideo(dirName, figureName, numFrames, firstStep, stepFreq, npt = "npt")

    else:
        print("Please specify the type of plot you want")
