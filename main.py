from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.gui.DirectGui import *
from panda3d.bullet import *
from panda3d.vision import WebcamVideo, ARToolKit
from direct.showbase.InputStateGlobal import inputState
import sys
from ARObject import *
if (len(sys.argv)>=3):
    if(int(sys.argv[2])==1): #Turn on steroscopic vision
        loadPrcFileData("", "red-blue-stereo 1")
        
#loadPrcFileData("", "want-directtools 1")
#loadPrcFileData("", "want-tk 1")
loadPrcFileData("", "textures-power-2 none") #the webcam feed can not be made into a power of two texture
loadPrcFileData("", "show-frame-rate-meter 1") #show fps
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.


 
class MyApp(ShowBase):
    def __init__(self, webCamFeed=-1):
        ShowBase.__init__(self)
        self.disableMouse()
        self.physics= False
        for x,option in enumerate(WebcamVideo.getOptions()): 
            print option ,x
        print "choose webcam and resolution by index" 
        
        #Starting Webcam and placing the feed on the background card
        if(webCamFeed==-1):
            
            option = WebcamVideo.getOption(int(raw_input()))
        else:
            option = WebcamVideo.getOption(webCamFeed)
        
        self.tex = MovieTexture(option) 
        self.tex.setKeepRamImage(True)
        cm = CardMaker("card") 
        cm.setUvRange(Point2(0, 0), Point2(1, 1)) 
        cm.setFrame(-1, 1, -1, 1) 
        card = render2d.attachNewNode(cm.generate()) 
        card.setTexture(self.tex)

        
        
        #Loading Textures. Textures provided by: http://www.cgtextures.com/
        self.texRoad= loader.loadTexture("textures/asphalt2.jpg")
        self.texBrick= loader.loadTexture("textures/brick.jpg")
        self.texGuardRail= loader.loadTexture("textures/guardrail.jpg")

        #Starting Physics
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, -9.81, 0))
        self.dt = globalClock.getDt()
            
        #Physics Debug (very slow)
        debugNode = BulletDebugNode('Debug')
        debugNode.showWireframe(True)
        debugNode.showConstraints(True)
        debugNode.showBoundingBoxes(False)
        debugNode.showNormals(False)
        self.debugNP = render.attachNewNode(debugNode)
        #self.debugNP.show()
        self.world.setDebugNode(self.debugNP.node())
        
        #Starting ARToolkit
        base.cam.node().getDisplayRegion(0).setSort(20) 
        self.ar = ARToolKit.make(base.cam, "./camera_para.dat", 2)
        self.ar2 = ARToolKit.make(base.cam, "./camera_para.dat", 1)
        self.centerNP = NodePath('centerNP')
        self.zup = loader.loadModel("zup-axis.egg")
        self.zup.setScale(0.2)
        self.zup.reparentTo(self.centerNP)
        self.zup.hide()
        self.centerNP.reparentTo(self.render)
        self.ar.attachPattern("./patt.kanji", self.centerNP)

        #Initializing the Ground
        shape = BulletPlaneShape(Vec3(0,0,1), 0)
        body = BulletRigidBodyNode('Ground')
        body.addShape(shape)
        self.centerNP.attachNewNode(body)
        self.world.attachRigidBody(body)
        
        #Adding Events
        self.accept("space",self.attachPattern)
        self.accept("arrow_left", self.changeObject, ["left"])
        self.accept("arrow_right", self.changeObject, ["right"])
        self.accept("enter", self.switchPhysics)
        
        #Adding list with geometry and default parameters for creating said geometry
        self.geometry=[
                  [ARPlane,         [0, 0.5, 0.5, self.texBrick]],
                  [ARCube,          [1.0, 0.5, 0.5, 0.5, self.texBrick]],
                  [ARSphere,        [1.0, 0.25, ARObject.NOTHING]], #The sphere already have a smiley texture
                  [ARRoad,          [0, 1.0, 1.0, self.texRoad, 1, self.texGuardRail]],
                  [ARRoadCurve,     [0, 1.0, self.texRoad, 1, self.texGuardRail]]]
        self.currentGeometry=0
        self.objects= []
        
        
        #Setting up the GUI
        self.sliderTextMass = OnscreenText("Mass",
                style=1, fg=(1,1,1,1), pos=(-1.1,-0.61), scale = 0.04)
        self.sliderMass = DirectSlider(pos = Vec3(-1.1,0,-0.65), value = .50, range=(0,3), scale=0.2,
                command = self.setMass)
        
        self.sliderTextX = OnscreenText("Size X",
                style=1, fg=(1,1,1,1), pos=(-1.1,-0.71), scale = 0.04)
        self.sliderSizeX = DirectSlider(pos = Vec3(-1.1,0,-0.75), value = .50, range=(0.1,3), scale=0.2,
                command = self.setSizeX)
        
        self.sliderTextY = OnscreenText("Size Y",
                style=1, fg=(1,1,1,1), pos=(-1.1,-0.81), scale = 0.04)
        self.sliderSizeY = DirectSlider(pos = Vec3(-1.1,0,-0.85), value = .50, range=(0.1,3), scale=0.2,
                command = self.setSizeY)
        
        self.sliderTextZ = OnscreenText("Size Z",
                style=1, fg=(1,1,1,1), pos=(-1.1,-0.91), scale = 0.04)
        self.sliderSizeZ = DirectSlider(pos = Vec3(-1.1,0,-0.95), value = .50, range=(0.1,3), scale=0.2,
                command = self.setSizeZ)
        
        self.objectText = OnscreenText("Object:",
                style=1, fg=(1,1,1,1), pos=(-0.75,-0.75), scale = 0.06)
        self.buttonLeftObject= DirectButton(text = "Previous", pos=Vec3(-0.53,0,-0.75), scale=.05, command=self.changeObject, extraArgs=["left"])
        self.buttonRightObject= DirectButton(text = "Next", pos=Vec3(-0.35,0,-0.75), scale=.05, command=self.changeObject, extraArgs=["right"])
        
        #self.textureText = OnscreenText("Texture:",
        #        style=1, fg=(1,1,1,1), pos=(-0.77,-0.85), scale = 0.06)
        #self.buttonLeftTexture= DirectButton(text = "Previous", pos=Vec3(-0.53,0,-0.85), scale=.05, command=self.changeTexture, extraArgs=["left"])
        #self.buttonRightTexture= DirectButton(text = "Next", pos=Vec3(-0.35,0,-0.85), scale=.05, command=self.changeTexture, extraArgs=["right"])
        
        self.checkGuardRail= DirectCheckButton(text = "Guard Rail", pos=Vec3(-0.7,0,-0.95),scale=.05, command= self.toggleGuardRail)
        
        self.checkToggleDebug= DirectCheckButton(text = "Toggle Debug", pos=Vec3(1.15,0,-0.95),scale=.05, command= self.toggleDebug)
        
        
        self.prep=False
        self.changeObject(-1)
        
        
        taskMgr.add(self.updatePhysics, 'updatePhysics')
        taskMgr.add(self.updatePatterns, 'updatePatterns')
        
    def changeTexture(self):
        pass
    
    
    def toggleDebug(self, status):
        if (status):
            self.debugNP.show()
            self.zup.show()
        else:
            self.debugNP.hide()
            self.zup.hide()
    
    def toggleGuardRail(self, status):
        print self.geometry[self.currentGeometry]
        if (self.geometry[self.currentGeometry][0]== ARRoad):
            self.geometry[self.currentGeometry][1][4]= status
        elif (self.geometry[self.currentGeometry][0]==ARRoadCurve):
            self.geometry[self.currentGeometry][1][3]= status
        self.changeObject("changed")
    
    
    def setMass(self):
        self.geometry[self.currentGeometry][1][0]= self.sliderMass["value"]
        self.changeObject("changed")
    
    def setSizeX(self):
        self.geometry[self.currentGeometry][1][1]= self.sliderSizeX["value"]
        self.changeObject("changed")
    
    def setSizeY(self):
        objectClass= self.geometry[self.currentGeometry][0]
        if (objectClass== ARCube) or (objectClass== ARPlane):
            self.geometry[self.currentGeometry][1][2]= self.sliderSizeY["value"]
            self.changeObject("changed")
        elif (objectClass== ARRoadCurve) or (objectClass== ARRoad):
            self.geometry[4][1][1]= self.sliderSizeY["value"]
            self.geometry[3][1][2]= self.sliderSizeY["value"]
            self.changeObject("changed")
            
    
    def setSizeZ(self):
        if (self.geometry[self.currentGeometry][0]== ARCube):
            self.geometry[self.currentGeometry][1][3]= self.sliderSizeZ["value"]
            self.changeObject("changed")
    
        
    #Attaching secondary pattern object to main pattern
    def attachPattern(self):
        self.patt1.detach(self.world)
        Pos= self.centerNP.getRelativePoint(self.patt1.mainNP, VBase3(0,0,0))
        Hpr= self.patt1.mainNP.getHpr(self.centerNP)
        self.patt1.setMass()
        self.patt1.reparentTo(self.centerNP, self.world)
        self.patt1.setPos(Pos)
        self.patt1.setHpr(Hpr)
        self.objects.append(self.patt1)
        self.changeObject("none")
        
    #Changing selected object on secondary pattern
    def changeObject(self, action):
        self.ar2.detachPatterns()
        if (action=="left"):
            print "left"
            #saving the parameters as default for the old object
            self.geometry[self.currentGeometry][1]= list(self.patt1.args)
            self.currentGeometry= self.currentGeometry-1
            if(self.currentGeometry==-1):
                self.currentGeometry= len(self.geometry)-1
            self.patt1.detach(self.world)
            
        elif (action=="right"):
            print "right"
            #saving the parameters as default for the old object
            self.geometry[self.currentGeometry][1]= list(self.patt1.args)
            self.currentGeometry= self.currentGeometry+1
            if(self.currentGeometry >= len(self.geometry)):
                self.currentGeometry= 0
            self.patt1.detach(self.world)
            
        elif (action=="changed"):
            self.patt1.detach(self.world)
        
        #Using a trick to build the right object:
        #self.geometry[i][0] has a reference to a class
        #self.geometry[i][1] has the arguments to instanciate said class as a list		
        #So self.geometry[i][0] (*self.geometry[i][1]) instanciates the class indexed by i using the arguments indexed by i
        
        objectClass= self.geometry[self.currentGeometry][0]
        objectParameters= self.geometry[self.currentGeometry][1]
        if (action=="none"):
            #object was attached to the centerNP, keeping the parameters values
            self.patt1=  objectClass(*(self.patt1.args))
        else:
            #object changed, using the default parameters for the new object
            self.patt1= objectClass(*objectParameters)
            
        
            
        #Changing GUI to the values. Hiding unused elements from the GUI
        if (objectClass == ARRoad) or (objectClass == ARRoadCurve):
            self.checkGuardRail.show()
            if (objectClass == ARRoad):
                self.checkGuardRail["indicatorValue"]= objectParameters[4]
            else:
                self.checkGuardRail["indicatorValue"]= objectParameters[3]
            self.checkGuardRail.setIndicatorValue()
        else:
            self.checkGuardRail.hide()
        
        
        #These parameters are in the same position for all objects
        if(action!="changed"):  #prevents a recursive call from the event triggered by altering the GUI
            self.sliderMass.setValue(objectParameters[0])

    
        if (objectClass== ARPlane):
            self.sliderTextY.show()
            self.sliderSizeY.show()
            if(action!="changed"):
                self.sliderSizeY.setValue(objectParameters[2])
            
            self.sliderTextZ.hide()
            self.sliderSizeZ.hide()
            
        elif (objectClass== ARCube):
            self.sliderTextY.show()
            self.sliderSizeY.show()
            if(action!="changed"):
                self.sliderSizeY.setValue(objectParameters[2])
            
            
            self.sliderTextZ.show()
            self.sliderSizeZ.show()
            if(action!="changed"):
                self.sliderSizeZ.setValue(objectParameters[3])
            
        elif (objectClass== ARSphere):
            self.sliderTextY.hide()
            self.sliderSizeY.hide()
            
            self.sliderTextZ.hide()
            self.sliderSizeZ.hide()
            
        elif (objectClass== ARRoad):
            self.sliderTextY.show()
            self.sliderSizeY.show()
            if(action!="changed"):
                self.sliderSizeY.setValue(objectParameters[2])
            
            self.sliderTextZ.hide()
            self.sliderSizeZ.hide()
            
        
        #Road Curve is the only one that doesn't have a sizeX component
        if (objectClass== ARRoadCurve):            
            self.sliderTextX.hide()
            self.sliderSizeX.hide()
            
            self.sliderTextY.show()
            self.sliderSizeY.show()
            if(action!="changed"):
                self.sliderSizeY.setValue(objectParameters[1])
            
            self.sliderTextZ.hide()
            self.sliderSizeZ.hide()
        else:
            self.sliderTextX.show()
            self.sliderSizeX.show()
            if(action!="changed"):
                self.sliderSizeX.setValue(objectParameters[1])
            
        
        self.patt1.setMassZero()
        self.ar2.attachPattern("./patt.sample1", self.patt1.mainNP)
        self.patt1.reparentTo(self.render, self.world)

    
    def switchPhysics(self):
        self.physics= not self.physics
        if (self.physics):
            self.patt1.setMass()
        else:
            self.patt1.setMassZero()
        print 'Physics is: ', self.physics
        

    def updatePhysics(self, task):
        gravity= self.centerNP.getQuat().getUp() * -9.81
        self.world.setGravity(gravity)
        if(self.physics):
            self.world.doPhysics(self.dt)
        return task.cont
    
  
    
    def updatePatterns(self, task):
        self.ar.analyze(self.tex)
        self.ar2.analyze(self.tex)
        return task.cont 
        
        
        
if(len(sys.argv)>1):
    app = MyApp(int(sys.argv[1]))
else:
    app = MyApp(-1)
app.run()