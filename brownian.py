# Brownian Motion on the Unit Cube
# Parameters
# wallParameter - wall spacing (given in terms of [side length of hole, wall to hole ratio])
# particleM - effective particle mass
# NP - particle number
# Temp - temperature which dictates thermal distribution (set k_B = 1)

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from numpy import ma


def genIC(boxSize, kB, NP, particleM, Temp):
    particleX = boxSize*np.random.rand(NP,3)
    particleX[:,0] = 0.5 * particleX[:,0]
    particleV = np.random.normal(0,np.sqrt(kB*Temp/particleM),(NP,3))
    return (particleX, particleV)

def getState(boxSize,particleV, particleX,plot=False):
    #3D quiver plots and particle counting
    NP = particleX.shape[0]
    if plot:
        normalizedX = np.copy(particleX) 
        normalizedV = np.copy(particleV)
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        plt.axis([0,boxSize,0,boxSize])
        ax.set_zbound(lower=0, upper=boxSize)
        ax.quiver(normalizedX[:,0],normalizedX[:,1],normalizedX[:,2],normalizedV[:,0],normalizedV[:,1],normalizedV[:,2], length = 0.05 * boxSize)
        ax.set_xlabel('X axis (normal to membrane)')
        ax.set_ylabel('Y axis (impenetrable walls)')
        ax.set_zlabel('Z axis (periodic boundary )')
        plt.show()
    left = np.sum(particleX[:,0] < boxSize * 0.5,dtype=int)
    if plot:
        return left, NP-left,ax #left and right halves
    return left, NP-left

def totalEnergy(kB,particleM,particleV,Temp):
    NP = particleV.shape[0]
    T = 0.5 * particleM * sum(particleV[:,0] ** 2 + particleV[:,1] ** 2 + particleV[:,2] ** 2) / NP
    print('Observed average kinetic energy per particle (NP = ' + str(NP) + ') = ' +str(T))
    print('Equipartition predicts (6-3 = 3) QDOF: ' + str(1.5 * kB *Temp))
    return T
    
def updateV(gamma,kB,particleM,particleV,Temp,timeStep):
    stoch = np.sqrt(24*kB*Temp*gamma/timeStep)*np.random.normal(0,np.sqrt(1.0/12.0),(particleV.shape[0],3))
    drag = -gamma * particleV
    dV = ((drag + stoch)/particleM) * timeStep
    return particleV + dV

# def handleCollision(boxSize, particleV,projectedX,wallParam):
#     # Reflect off a wall
#     b = boxSize
#     for i in range(projectedX.shape[0]):
#         x,y,z = projectedX[i,:]
#         xd,yd,zd = particleV[i,:]
#         while(x < 0 or x > b or y < 0 or y > b or z<0 or z>b):
#             if x < 0:
#                 x = abs(x)
#                 xd = -xd
#             elif x > b:
#                 x = 2*b - x
#                 xd = -xd
#             elif y < 0:
#                 y = abs(y)
#                 yd = -yd
#             elif y > b:
#                 y = 2*b - y
#                 yd = -yd           
#             elif z < 0:
#                 z = abs(z)
#                 zd = -zd
#             elif z > b:
#                 z = 2*b - z
#                 zd = -zd
#         projectedX[i,:] = [x,y,z]
#         particleV[i,:] = [xd,yd,zd]
#     return projectedX,particleV

def membraneCheck(projectedX, wallParam, boxSize, particleR,NP):
    holeSize = wallParam[0]
    ratio = wallParam[1]
    wallSize = ratio*holeSize
    modArray = (holeSize + wallSize)*np.ones(NP)
    # check if collision with wall in x coordinate
    # AND if y/z coordinates collide with membrane
    # AND prevent sneakarounds
    return ((projectedX[:,0] < (particleR + 0.5*boxSize))*(projectedX[:,0] > (-particleR + 0.5*boxSize))) \
                  * ((np.fmod(projectedX[:,1],modArray) < wallSize) + (np.fmod(projectedX[:,2],modArray) < wallSize)) \
                  #+ (projectedX[:,1] < 0) + (projectedX[:,1] > boxSize))#check if outside the box in y axis (so that the particle can't sneak around the side)

def handleCollision(boxSize, particleV, projectedX, wallParam, NP, particleR):
    # Check if x & y coordinates are out of the range (0, boxSize)
    projectedX[:,2] = np.fmod(projectedX[:,2],boxSize)
    toohigh = projectedX > boxSize - particleR
    toolow  = projectedX < 0 + particleR
    #hitMembraneRight = (particleV[:,0] >= 0) * membraneCheck(projectedX, wallParam, boxSize, particleR,NP) 
    #hitMembraneLeft = (particleV[:,0] < 0) * membraneCheck(projectedX, wallParam, boxSize, particleR,NP)
    
    particleV[toolow] = -particleV[toolow]
    particleV[toohigh]= -particleV[toohigh]
    #particleV[hitMembraneRight,0] = -particleV[hitMembraneRight,0]
    #particleV[hitMembraneLeft,0] = -particleV[hitMembraneLeft,0]

    projectedX[toolow] = -projectedX[toolow] + particleR
    projectedX[toohigh] = 2*boxSize - projectedX[toohigh] - particleR
    #projectedX[hitMembraneRight,0] = 2*(0.5*boxSize - particleR) - projectedX[hitMembraneRight,0]
    #projectedX[hitMembraneLeft,0] = 2*(0.5*boxSize + particleR) - projectedX[hitMembraneLeft,0] 

    return projectedX, particleV

def randomWalk(boxSize,eta,kB,NP,particleM,particleR,particleV0,particleX0,Temp,timeStep,totalSteps,wallParam):
    # gamma = 6*pi*eta*a, where
    # eta = fluid viscosity
    # a = effective radius
    lefts = np.zeros(totalSteps)
    gamma = (6*np.pi*eta*particleR)
    (particleX,particleV) = (particleX0,particleV0)
    
    for i in range(0,totalSteps):
        lefts[i],right = getState(boxSize, particleV, particleX, plot=False)
        if i%10000 == 0:
            print("Timestep: "   +  str(i))
            print("# on left: "  + str(lefts[i]))
            print("# on right: " + str(right))
        #Step forward
        projectedX = particleX + particleV * timeStep
        #Handle collisions
        particleX, particleV = handleCollision(boxSize, particleV,projectedX, wallParam, NP, particleR)
        #Update the velocities stochastically
        particleV = updateV(gamma,kB,particleM,particleV,Temp,timeStep)
    totalEnergy(kB,particleM,particleV,Temp)
    return particleX,particleV

kB = 1.4*10**(-23) # Boltzmann's constant
boxSize = 2e-6 # Our box is 2 mu m right now 
#totalTime = 1e-8 # seconds of diffusion
NP = 400 # typical nicotine concentration in blood
Temp = 310 # 310 Kelvin
particleM = (162.0/18.0)*(3 * 10 ** (-26)) # molecular mass of nicotine in kg
particleR = 3 * 10 ** (-10) # nicotine is a three angstrom radius sphere, yolo
eta = 1.0 * 10 ** (-6) # viscosity of water in m^2 / s
wallParam = [1,1] #[Hole Size (side), hole to wall ratio]
gamma = 6*np.pi*eta*particleR
timeStep = 1e-11
totalSteps = 100000 #int(totalTime / timeStep)

#Generate ICs, get some statistics, run random walk, more statistics
particleX0,particleV0 = genIC(boxSize,kB,NP,particleM,Temp)
totalEnergy(kB,particleM,particleV0,Temp)
getState(boxSize, particleV0, particleX0, True)
particleX,particleV = randomWalk(boxSize,eta,kB,NP,particleM,particleR,particleV0,particleX0,Temp,timeStep,totalSteps,wallParam)
totalEnergy(kB,particleM,particleV,Temp)
getState(boxSize, particleV, particleX, True)

def beforeAfter(particleX0,particleV0,particleX,particleV,boxSize):
        normalizedX0 = np.copy(particleX0) 
        normalizedV0 = np.copy(particleV0)
        normalizedX = np.copy(particleX) 
        normalizedV = np.copy(particleV)
        
        fig = plt.figure(figsize = plt.figaspect(2.))
        ax1 = fig.add_subplot(2,1,1,projection='3d')
        plt.axis([0,boxSize,0,boxSize])
        ax1.set_zbound(lower=0, upper=boxSize)
        ax1.quiver(normalizedX0[:,0],normalizedX0[:,1],normalizedX0[:,2],normalizedV0[:,0],normalizedV0[:,1],normalizedV0[:,2], length = 0.05 * boxSize)
        ax1.set_xlabel('X axis (normal to membrane)')
        ax1.set_ylabel('Y axis (impenetrable walls)')
        ax1.set_zlabel('Z axis (periodic boundary )')

        ax2 = fig.add_subplot(2,1,2,projection='3d')
        plt.axis([0,boxSize,0,boxSize])
        ax2.set_zbound(lower=0, upper=boxSize)
        ax2.quiver(normalizedX[:,0],normalizedX[:,1],normalizedX[:,2],normalizedV[:,0],normalizedV[:,1],normalizedV[:,2], length = 0.05 * boxSize)
        ax2.set_xlabel('X axis (normal to membrane)')
        ax2.set_ylabel('Y axis (impenetrable walls)')
        ax2.set_zlabel('Z axis (periodic boundary )')
        plt.show()
    
#if __name__ == "__main__":
#    main()

def 
