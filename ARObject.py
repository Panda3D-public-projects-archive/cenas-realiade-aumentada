from panda3d.core import NodePath
from math import fabs
from panda3d.core import *
from panda3d.bullet import *


class ARObject(object):
    NOTHING = object()
    def __init__(self, *args):
        self.args= args
        self.mainNP= NodePath('ARObject')
        self.bulletNodes= []
        self.junctionPoints= []
        
    #Position as 3 floats
    def setPos(self, X, Y, Z):
        self.mainNP.setPos(X,Y,Z)
    
    #Position as one Point3
    def setPos(self, Pos):
        self.mainNP.setPos(Pos)
        
    #HPR as 3 floats
    def setHpr(self, H, P, R):
        self.mainNP.setHpr(H,P,R)
        
    #HPR as a VBase3
    def setHpr(self, Hpr):
        self.mainNP.setHpr(Hpr)
        
    def reparentTo(self, NP, world):
        #Adding bullet ridig bodies to the world
        for x in self.bulletNodes:
            world.attachRigidBody(x)
        self.mainNP.reparentTo(NP)      
        
        
    def detach(self, world):
        #Removing bullet ridig bodies from the world
        for x in self.bulletNodes:
            world.removeRigidBody(x)
        self.mainNP.detachNode() 
            
    
    def addBulletNode(self, name, *shapes):
        bulletNode= BulletRigidBodyNode(name)
        bulletNode.setDeactivationEnabled(False)
        for x in shapes:
            bulletNode.addShape(x)
        self.bulletNodes.append(bulletNode)
        self.mainNP.attachNewNode(bulletNode)
        return bulletNode
    
    def setMass(self):
        self.bulletNodes[0].setMass(self.args[0])
    
    def setMassZero(self):
        self.bulletNodes[0].setMass(0)
    
        
    def NormalizeVector(self, myVec):
        myVec.normalize()
        return myVec    

    def makeSquare(self, x1,y1,z1, x2,y2,z2, 
                   colorVec=Vec4(1.0,1.0,1.0,1.0),
                   texFunction= NOTHING,
                   colorFunction= NOTHING 
                   ):
        vertexformat=GeomVertexFormat.getV3n3cpt2()
        vdata=GeomVertexData('square', vertexformat, Geom.UHDynamic)
        
        vertex=GeomVertexWriter(vdata, 'vertex')
        normal=GeomVertexWriter(vdata, 'normal')
        color=GeomVertexWriter(vdata, 'color')
        texcoord=GeomVertexWriter(vdata, 'texcoord')
        
        #make sure we draw the square in the right plane
        if x1!=x2:
            vertex.addData3f(x1, y1, z1)
            vertex.addData3f(x2, y1, z1)
            vertex.addData3f(x2, y2, z2)
            vertex.addData3f(x1, y2, z2)
        
            normal.addData3f(self.NormalizeVector(Vec3(2*x1-1, 2*y1-1, 2*z1-1)))
            normal.addData3f(self.NormalizeVector(Vec3(2*x2-1, 2*y1-1, 2*z1-1)))
            normal.addData3f(self.NormalizeVector(Vec3(2*x2-1, 2*y2-1, 2*z2-1)))
            normal.addData3f(self.NormalizeVector(Vec3(2*x1-1, 2*y2-1, 2*z2-1)))
            
        else:
            vertex.addData3f(x1, y1, z1)
            vertex.addData3f(x2, y2, z1)
            vertex.addData3f(x2, y2, z2)
            vertex.addData3f(x1, y1, z2)
            
            normal.addData3f(self.NormalizeVector(Vec3(2*x1-1, 2*y1-1, 2*z1-1)))
            normal.addData3f(self.NormalizeVector(Vec3(2*x2-1, 2*y2-1, 2*z1-1)))
            normal.addData3f(self.NormalizeVector(Vec3(2*x2-1, 2*y2-1, 2*z2-1)))
            normal.addData3f(self.NormalizeVector(Vec3(2*x1-1, 2*y1-1, 2*z2-1)))
        
        if(colorFunction == ARObject.NOTHING):
            self.addColor(color, colorVec)
        else:
            colorFunction(color,colorVec)
            
        if(texFunction == ARObject.NOTHING):
            self.addTexCoord(texcoord, x1,y1,z1,  x2,y2,z2)
        else:
            texFunction(texcoord, x1,y1,z1,  x2,y2,z2)
        
        tri1=GeomTriangles(Geom.UHDynamic)
        tri2=GeomTriangles(Geom.UHDynamic)
        
        tri1.addVertex(0)
        tri1.addVertex(1)
        tri1.addVertex(3)
        
        tri2.addConsecutiveVertices(1,3)
        
        tri1.closePrimitive()
        tri2.closePrimitive()
        
        
        square=Geom(vdata)
        square.addPrimitive(tri1)
        square.addPrimitive(tri2)
        
        return square
    
    
    def addColor(self, color, colorVec):
        color.addData4f(colorVec)
        color.addData4f(colorVec)
        color.addData4f(colorVec)
        color.addData4f(colorVec)
        
    def addTexCoord(self, texcoord, x1,y1,z1,  x2,y2,z2):
        texcoord.addData2f(0.0, 1.0)
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, 1.0)
        
    def __del__(self):
        print "Instance of Class ", self.__class__.__name__ ," Removed."
        




class ARPlane(ARObject):
    def __init__(self, mass, sizeX, sizeY, texture=ARObject.NOTHING, color= Vec4(1.0,1.0,1.0,1.0)):
        ARObject.__init__(self, mass,sizeX,sizeY,texture,color)
        square= self.makeSquare(sizeX/2, sizeY/2, 0, -sizeX/2, -sizeY/2, 0, color)
        snode=GeomNode('square')
        
        bulletShape = BulletConvexHullShape()
        bulletShape.addGeom(square)
        bulletNode= self.addBulletNode("plane", bulletShape)
        bulletNode.setMass(mass)
        
        physicsNP= self.mainNP.attachNewNode(bulletNode)
        
        snode.addGeom(square)
        NP= NodePath(snode)
        
        if(texture != ARObject.NOTHING):
            NP.setTexture(texture)
        NP.setTwoSided(True)
        NP.reparentTo(physicsNP)
        

class ARCube(ARObject):
    def __init__(self, mass, sizeX, sizeY, sizeZ, texture=ARObject.NOTHING, 
                 color= [Vec4(1.0,  0,  0,1.0),
                         Vec4(  0,1.0,  0,1.0),
                         Vec4(  0,  0,1.0,1.0),
                         Vec4(1.0,1.0,  0,1.0),
                         Vec4(1.0,  0,1.0,1.0),
                         Vec4(  0,1.0,1.0,1.0)]):
        ARObject.__init__(self, mass, sizeX, sizeY, sizeZ, texture, color)
        square0= self.makeSquare(-sizeX/2,-sizeY/2,-sizeZ/2, sizeX/2,-sizeY/2, sizeZ/2, color[0])
        square1= self.makeSquare(-sizeX/2, sizeY/2,-sizeZ/2, sizeX/2, sizeY/2, sizeZ/2, color[1])
        square2= self.makeSquare(-sizeX/2, sizeY/2, sizeZ/2, sizeX/2,-sizeY/2, sizeZ/2, color[2])
        square3= self.makeSquare(-sizeX/2, sizeY/2,-sizeZ/2, sizeX/2,-sizeY/2,-sizeZ/2, color[3])
        square4= self.makeSquare(-sizeX/2,-sizeY/2,-sizeZ/2,-sizeX/2, sizeY/2, sizeZ/2, color[4])
        square5= self.makeSquare( sizeX/2,-sizeY/2,-sizeZ/2, sizeX/2, sizeY/2, sizeZ/2, color[5])
        snode=GeomNode('square')
        snode.addGeom(square0)
        snode.addGeom(square1)
        snode.addGeom(square2)
        snode.addGeom(square3)
        snode.addGeom(square4)
        snode.addGeom(square5)
        
        bulletShape0 = BulletConvexHullShape()
        bulletShape0.addGeom(square0)
        bulletShape1 = BulletConvexHullShape()
        bulletShape1.addGeom(square1)
        bulletShape2 = BulletConvexHullShape()
        bulletShape2.addGeom(square2)
        bulletShape3 = BulletConvexHullShape()
        bulletShape3.addGeom(square3)
        bulletShape4 = BulletConvexHullShape()
        bulletShape4.addGeom(square4)
        bulletShape5 = BulletConvexHullShape()
        bulletShape5.addGeom(square5)
        bulletNode= self.addBulletNode("plane", bulletShape0, bulletShape1, bulletShape2, bulletShape3, bulletShape4, bulletShape5)
        bulletNode.setMass(mass)
        

        physicsNP= self.mainNP.attachNewNode(bulletNode)
        physicsNP.setZ(sizeZ/2)
        NP= NodePath(snode)
        if(texture != ARObject.NOTHING):
            NP.setTexture(texture)
        NP.setTwoSided(True)
        
        NP.reparentTo(physicsNP)


class ARSphere(ARObject):
    def __init__(self, mass, radius, texture=ARObject.NOTHING, color= Vec4(1.0,1.0,1.0,1.0)):
        ARObject.__init__(self, mass, radius, texture, color)
        NP = loader.loadModel("smiley.egg")
        NP.setScale(radius)
        NP.setColor(color)
        bulletShape= BulletSphereShape(radius)
        bulletNode= self.addBulletNode("plane", bulletShape)
        bulletNode.setMass(mass)

        physicsNP= self.mainNP.attachNewNode(bulletNode)
        physicsNP.setZ(radius)
        if(texture != ARObject.NOTHING):
            NP.setTexture(texture, 1)
            
        NP.setTwoSided(True)
        NP.reparentTo(physicsNP)

class ARRoad(ARObject):
    def __init__(self, mass, sizeX, sizeY, 
                 roadTexture=ARObject.NOTHING, 
                 guardRail=False, 
                 guardRailTexture=ARObject.NOTHING, 
                 color= Vec4(1.0,1.0,1.0,1.0)):
        ARObject.__init__(self, mass, sizeX, sizeY, roadTexture, guardRail, guardRailTexture)
        self.sizeX= sizeX
        self.sizeY= sizeY
        square0=  self.makeSquare(sizeX/2, sizeY/2, 0,   -sizeX/2, -sizeY/2, 0 , color, self.addTexCoordRoad)
        snode=GeomNode('road')
        snode.addGeom(square0)
            
        NPRoad= NodePath(snode)
        NPRoad.setTwoSided(True)
        
        bulletShape0 = BulletConvexHullShape()
        bulletShape0.addGeom(square0)
        if(guardRail):
            square1= self.makeSquare(sizeX/2, 0, 0, -sizeX/2, 0, sizeY/10, color, self.addTexCoordGuardRail)
            square2= self.makeSquare(sizeX/2, 0, 0, -sizeX/2, 0, sizeY/10, color, self.addTexCoordGuardRail)
            bulletShape1 = BulletConvexHullShape()
            bulletShape1.addGeom(square1)
            bulletShape2 = BulletConvexHullShape()
            bulletShape2.addGeom(square2)
            snodeGuardRail1=GeomNode('guardrail1')
            snodeGuardRail1.addGeom(square1)
            snodeGuardRail2=GeomNode('guardrail2')
            snodeGuardRail2.addGeom(square2)
            NPGuardRail1= NodePath(snodeGuardRail1)
            NPGuardRail2= NodePath(snodeGuardRail2)
            NPGuardRail1.reparentTo(NPRoad)
            NPGuardRail1.setPos(0, sizeY/2 , 0)
            NPGuardRail2.reparentTo(NPRoad)
            NPGuardRail2.setPos(0, -sizeY/2, 0)

            if(guardRailTexture != ARObject.NOTHING):
                NPGuardRail1.setTexture(guardRailTexture)
                NPGuardRail2.setTexture(guardRailTexture)
            NPGuardRail1.setTwoSided(True)
            NPGuardRail2.setTwoSided(True)
              
            bulletNodeGuardRail1= self.addBulletNode("road", bulletShape1)
            bulletNodeGuardRail1.setMass(0)    
            bulletNodeGuardRail2= self.addBulletNode("road", bulletShape2)
            bulletNodeGuardRail2.setMass(0)
            
            
        bulletNodeRoad= self.addBulletNode("road", bulletShape0)
        bulletNodeRoad.setMass(mass)
        
        physicsRoad= self.mainNP.attachNewNode(bulletNodeRoad)
        
        if(guardRail):
            physicsGuardRail1= physicsRoad.attachNewNode(bulletNodeGuardRail1)
            physicsGuardRail2= physicsRoad.attachNewNode(bulletNodeGuardRail2)
            physicsGuardRail1.setPos(0, sizeY/2 , 0)
            physicsGuardRail2.setPos(0, -sizeY/2, 0)

        if(roadTexture != ARObject.NOTHING):
            NPRoad.setTexture(roadTexture)
            
        #Seting up junction points
        """self.junction1= loader.loadModel("smiley.egg")
        self.junction1.setScale(0.03)
        self.junction1.setPos(-sizeX/2,0,0)
        self.junction1.reparentTo(physicsRoad)
        self.junctionPoints.append(self.junction1)
        
        
        self.junction2= loader.loadModel("smiley.egg")
        self.junction2.setScale(0.03)
        self.junction2.setPos(sizeX/2,0,0)
        self.junction2.reparentTo(physicsRoad)
        self.junctionPoints.append(self.junction2)
        """
        NPRoad.reparentTo(physicsRoad)
            
        
                
     
    def addTexCoordRoad(self, texcoord, x1,y1,z1,  x2,y2,z2):
        foo= (fabs(x1)+fabs(x2))/ (fabs(y1)+fabs(y2))
        texcoord.addData2f(0.0, foo)
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, foo)
        
    def addTexCoordGuardRail(self, texcoord, x1,y1,z1,  x2,y2,z2):
        foo= (fabs(x1)+fabs(x2))/5
        texcoord.addData2f(0.0, foo)
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, foo)
    
    def calcPos(self, relativeNode, junction, relativeJunction):
        point= relativeNode.getRelativePoint(relativeJunction, (0,0,0))
        if (junction == self.junction1):
            return point - (-self.sizeX/2,0,0)
        elif (junction == self.junction2):
            return point - ( self.sizeX/2,0,0)
        else:
            print "ERROR"
            return -1


class ARRoadCurve(ARObject):
    def __init__(self, mass, size, 
                 roadTexture=ARObject.NOTHING, 
                 guardRail=False, 
                 guardRailTexture=ARObject.NOTHING, 
                 color= Vec4(1.0,1.0,1.0,1.0)):
        ARObject.__init__(self, mass, size, roadTexture, guardRail, guardRailTexture, color)
        self.size= size
        square0= self.makeSquare(size/2, size/2, 0, -size/2, -size/2, 0, color, self.addTexCoordRoadCurve)
        snode=GeomNode('road')
        snode.addGeom(square0)
        NPRoad= NodePath(snode)
        NPRoad.setTwoSided(True)
        
        bulletShape0 = BulletConvexHullShape()
        bulletShape0.addGeom(square0)
        
        if(guardRail):
            square1= self.makeSquare(size/2, 0, 0, -size/2, 0, size/10, color, self.addTexCoordGuardRail)
            square2= self.makeSquare(size/2, 0, 0, -size/2, 0, size/10, color, self.addTexCoordGuardRail)
            bulletShape1 = BulletConvexHullShape()
            bulletShape1.addGeom(square1)
            bulletShape2 = BulletConvexHullShape()
            bulletShape2.addGeom(square2)
            snodeGuardRail1=GeomNode('guardrail1')
            snodeGuardRail1.addGeom(square1)
            snodeGuardRail2=GeomNode('guardrail2')
            snodeGuardRail2.addGeom(square2)
            
            NPGuardRail1= NodePath(snodeGuardRail1)
            NPGuardRail2= NodePath(snodeGuardRail2)
            NPGuardRail1.reparentTo(NPRoad)
            NPGuardRail1.setPos(0, size/2, 0)
            NPGuardRail2.reparentTo(NPRoad)
            NPGuardRail2.setPos(-size/2, 0, 0)
            NPGuardRail2.setH(90)
            
            if(guardRailTexture != ARObject.NOTHING):
                NPGuardRail1.setTexture(guardRailTexture)
                NPGuardRail2.setTexture(guardRailTexture)
            NPGuardRail1.setTwoSided(True)
            NPGuardRail2.setTwoSided(True)
            
            bulletNodeGuardRail1= self.addBulletNode("road", bulletShape1)
            bulletNodeGuardRail1.setMass(0)    
            bulletNodeGuardRail2= self.addBulletNode("road", bulletShape2)
            bulletNodeGuardRail2.setMass(0)
        
        bulletNodeRoad= self.addBulletNode("road", bulletShape0)
        bulletNodeRoad.setMass(mass)

        physicsRoad= self.mainNP.attachNewNode(bulletNodeRoad)
        
        if(guardRail):
            physicsGuardRail1= physicsRoad.attachNewNode(bulletNodeGuardRail1)
            physicsGuardRail2= physicsRoad.attachNewNode(bulletNodeGuardRail2)
            physicsGuardRail1.setPos(0, size/2, 0)
            physicsGuardRail2.setPos(-size/2, 0, 0)
            physicsGuardRail2.setH(90)
        

        if(roadTexture != ARObject.NOTHING):
            NPRoad.setTexture(roadTexture)
            
        #Seting up junction points
        """
        self.junction1= loader.loadModel("smiley.egg")
        self.junction1.setScale(0.03)
        self.junction1.setPos(size/2,0,0)
        self.junction1.reparentTo(physicsRoad)
        self.junctionPoints.append(self.junction1)
        
        self.junction2= loader.loadModel("smiley.egg")
        self.junction2.setScale(0.03)
        self.junction2.setPos(0,-size/2,0)
        self.junction2.reparentTo(physicsRoad)
        self.junctionPoints.append(self.junction2)
        """
        NPRoad.reparentTo(physicsRoad)
        
    
    def addTexCoordRoadCurve(self, texcoord, x1,y1,z1,  x2,y2,z2):
        texcoord.addData2f(0.0, 1.0)
        texcoord.addData2f(0.0, 0.5)
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, 1.0)
        
    def addTexCoordGuardRail(self, texcoord, x1,y1,z1,  x2,y2,z2):
        foo= (fabs(x1)+fabs(x2))/5
        texcoord.addData2f(0.0, foo)
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, foo)
        
        
    def calcPos(self, relativeNode, junction, relativeJunction):
        point= relativeNode.getRelativePoint(relativeJunction, (0,0,0))
        if (junction == self.junction1):
            return point - ( self.sizeX/2,0,0)
        elif (junction == self.junction2):
            return point - ( 0,-self.sizeX/2,0)
        else:
            print "ERROR"
            return -1