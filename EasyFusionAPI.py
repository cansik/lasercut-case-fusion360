
# Author Dirk Van Essendelft
# Copyright 12/25/2014 21st Century Woodworking
#
# Description: 
# The Easy Fusion API collects and organizes common modeling tasks
# into easy to use functions to cut down code development length
# and time to get a model.
#
# Use:
#  1) copy this file into your mySkripts folder in Fusion 360
#  2) start a new script in Fusion 360
#  3) put "from .EasyFusionAPI import EZFusionAPI" at the head of yoru file
#  4) create an instance with "fa = EasyFusionAPI()"
#     or inherit into your clas by "class YourClass(EasyFusionAPI)"
#     if you need to use __init__ in your class, be sure to call
#     EasyFusionAPI.__init__() as your first statement in __init__
#     if you don't do this, all subclasses will be overwritten by your __init__
#  5) have fun creating geometry
#
# License: 
# This code is covered under the GPL v3 license, which means you must not
# remove this header information and any code derrived from this code must
# also adhere to the GPL v3 license (be open source)
#
# Latest Code Available at www.21stCenturyWoodworking.com


import adsk.core, adsk.fusion, traceback, math

class BaseClass():
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.core = adsk.core
        self.ui = self.app.userInterface
        self.product = self.app.activeProduct
        self.design = adsk.fusion.Design.cast(self.product)
        self.rootComp = self.design.rootComponent
        self._pi = 3.1415926535897932384626433832795028841971693993751058209749445923078164062
        self._globalOrigin = adsk.core.Point3D.create(0,0,0)
        self.extrudes = self.rootComp.features.extrudeFeatures
        self.Utils = UtilityOperations()
        self.smallNumber = 1e-6
        

class EZFusionAPI:
    def __init__(self):
        self.__base__ = BaseClass()
        self.Patterns = PatteringOperations()
        self.EZSketch = EZSketch
        self.EZFeatures = EZFeatures
        
    def create_NewComponent(self,name=None):
        comp = self.__base__.rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
        if not name == None:
            comp._set_name(name)
        return comp
        
    def set_ComponentName(self,component,name):
        component._set_name(name)
        
    def create_UserParameter(self, name, expression, units = None, comment = None, favorite = False):
        '''
        Automates the Process of adding a User Parameter to Fusion 360
        
        name is a string and is the name of the parameter to add
        expression is a number or string and is the value of the parameter
        units is a string matching the units of the parameter
        comment is a string matching the comment to put in the parameter comment
        
        note: the default behavior is to check to see if the parameter already exists,
        if it exists already, it writes over the expression with the expression input
        
        returns the userParameter object just created or modified
        '''
        if units == None:
            units = ' '
        if comment == None:
            comment = ' '
        
        if not isinstance(expression,str):
            expression = str(expression)
        
        self.getUserParameterNames()
        if name in self._userParamDict:
            up = self.__base__.design.userParameters.item(self._userParamDict[name])
            up._set_expression(expression)
        else:
            userValue = self.__base__.core.ValueInput.createByString(expression)
            up = self.__base__.design.userParameters.add(name,userValue,units,comment)
            #up._set_expression(expression)
            self.getUserParameterNames()
            
        if favorite:
            up.isFavorite = True
        return up
        
    def getUserParameterNames(self):
        '''
        returns a dictionary listing the user Parameter names as keys
        and the item number as values
        '''
        existingParameters = self.__base__.design.userParameters
        paramNameDict = {}
        for i in range(existingParameters.count):
            paramNameDict[existingParameters.item(i).name] = i
        self._userParamDict = paramNameDict
        
    def get_UserParameterValue(self,name):
        return self.__base__.design.userParameters.item(self._userParamDict[name]).value
        
    def create_Point3d(self,x,y,z=0):
        return adsk.core.Point3D.create(x,y,z)





















         
class EZSketch:
    '''
    This class creates a sketch feature and contains methods to operate on the sketch
    Since there is only one feature type associated with this class, it can be
    initialized with a plane.  If it is not given a plane, it will create a 
    sketch on the xZ plane of the root component.  If it is given a plane that
    is part of another component, it will set the parent to that component and
    automatically create a sketch on the plane given
    
    plane is either a constructionPlane or bRepFace
    name is a string which sets the name of the sketch
    visibility is a bool which sets the visibility property of the created sketch
    '''
    def __init__(self,plane = None,name = None, visibility = True,startCurveConstruction = False):
        self.__base__ = BaseClass()
        self.sketch = None
        if plane == None:
            self._parentComponent = self.__base__.rootComp
            self._plane = self.__base__.rootComp.xZConstructionPlane
        else:
            if type(plane) is adsk.fusion.ConstructionPlane:
                self._parentComponent = plane.parent
            elif type(plane) is adsk.fusion.BRepFace:
                body = plane.body
                self._parentComponent = body.parentComponent
            else:
                raise Exception('Oops, this plane type is not supported yet')
            self._plane = plane
            
        self._create_Sketch(name, visibility,startCurveConstruction)
        
        self.create = Sketch_Create(self)
        self.constrain = Sketch_Constrain(self)
        self.set = Sketch_Set(self)
        self.get = Sketch_Get(self)
        self.vector = Sketch_Vector(self)
        
    def _create_Sketch(self, name = None, visibility = True, startCurveConstruction = False):
        '''
        don't call this method unless you are sure you know what you are doing        
        
        creates a sketch

        name is a string if given will set the name of the sketch
        visibility is a bool and sets the visibility
        '''
        self.__base__.Utils.checkForExistingSketch(self.sketch)
        self.sketch = self._parentComponent.sketches.add(self._plane)
        self._lines = self.sketch.sketchCurves.sketchLines
        self._points = self.sketch.sketchPoints
        self._arcs = self.sketch.sketchCurves.sketchArcs
        self._circles = self.sketch.sketchCurves.sketchCircles
        self._dims = self.sketch.sketchDimensions
        self._constraints = self.sketch.geometricConstraints
        if visibility == False:
            self.sketch.isVisible = False
        if not name == None:
            self.set_name(name)
            
        if startCurveConstruction:
            sketchCurveCollection = self.sketch.sketchCurves
            for sketchCurve in sketchCurveCollection:
                sketchCurve.isConstruction = True
        
        return self.sketch
            
    def _delete_Sketch(self):
        success = self.sketch.deleteMe()
        if success:
            self.__init__()
        return success
        
class Sketch_Get():
    '''
    subclass of EZSketch that containts all the get methods
    '''
    def __init__(self,parent):
        self.__parent__ = parent
        
    def sketch(self):
        '''
        returns the handle to the sketch
        '''
        return self.__parent__.sketch

        
    def profiles(self):
        '''
        returns a list of profiles in the sketch
        '''
        return self.__parent__.sketch.profiles
        
    def geomectricConstraints(self,obj):
        '''
        returns a list of all constrains associated with obj
        
        obj is a SketchCurve object
        '''
        return self.__parent__.__base__.Utils.adskObjectList2PythonList(obj.geomtricConstraints)
        
    def dimensonConstraints(self,obj):
        '''
        returns a list of all dimensions associated with obj
        
        obj is a SketchCurve object
        '''
        return self.__parent__.__base__.Utils.adskObjectList2PythonList(obj.sketchDimensions)
        
    def arePontsCoincident(self,pt1,pt2):
        '''
        checks to see if two skets points are coincident
        pt1 is a sketchPoint or Point3d object or tuple of coordinates
        pt2 is a sketchPoint or Point3d object or tuple of coordinates
        '''
        pt1 = self.point3d(pt1)
        pt2 = self.point3d(pt2)
        return pt1.isEqualTo(pt2)
        
    def isPointInList(self,pt, ptList):
        '''
        checks to see if a point in in a list of points
        pt is a sketchPoint or Point3d object or tuple of coordinates
        ptList is a python List of points where every element is either
        a sketchPoint or Point3d object or tuple of coordinates
        '''
        
        pt = self.point3d(pt)
        if len(ptList) == 0:
            return False
        for ref in ptList:
            ref = self.point3d(ref)
            if self.arePontsCoincident(ref,pt):
                return True
        return False
        
    def slopeBetweenPoints(self,pt1,pt2):
        '''
        calculates the slope of a line between two points
        pt1 is a sketchPoint or Point3d object or tuple of coordinates
        pt2 is a sketchPoint or Point3d object or tuple of coordinates
        '''
        pt1 = self.point3d(pt1)
        pt2 = self.point3d(pt2)
            
        if pt1.x == pt2.x:
            return float('inf')
            
        dx = pt2.x-pt1.x
        dy = pt2.y-pt1.y
        
        slope = dy/dx
        
        if dx < 0:
            slope *= -1

        return slope
        
    def slopeOfLine(self,line):
        '''
        calculates the slope of a sketchLine object
        line is a sketchLine object
        '''
        return self.slopeBetweenPoints(line.startSketchPoint,line.endSketchPoint)
        
    def areLinesParallel(self,line1,line2):
        '''
        checks if two sketLines are Parallel
        line1 and line2 are sketchLine Objects
        '''
        s1 = self.slopeOfLine(line1)
        s2 = self.slopeOfLine(line2)
        
        if s1 == float('inf') and s2 == float('inf'):
            return True
        elif abs(s1 - s2) < self.__parent__.__base__.smallNumber:
            return True
        else:
            return False
            
    def point3d(self,pt):
        '''
        makes sure pt is a point3d object
        
        pt can be a point3D object or SketchPoint object or a tuple of coordinates
        '''
        if type(pt) is tuple:
            for i in pt:
                if not isinstance(pt[i],(int,float)):
                    raise Exception('tuple elements must be numbers')
            if len(pt) == 2:
                return adsk.core.Point3D.create(pt[0],pt[1],0)
            elif len(pt) == 3:
                return adsk.core.Point3D.create(pt[0],pt[1],pt[2])
            else:
                raise Exception('tuple must be of length 2 or 3')
                    
        elif type(pt) is adsk.core.Point3D or type(pt) is adsk.fusion.SketchPoint:
            try:
                pt = pt.geometry
            except:
                pass
            
            return pt
        else:
            raise Exception('pt must be of type Point3D or SketchPoint')
            
    def orderCurveEndsByDist(self,crv,pt,returnSketchPoint = False):
        '''
        finds the closest end of a SketchCurve object to a point
        
        pt is a sketchPoint or Point3d object or tuple of coordinates
        crv is a SketchCurve Object
        
        returns a touple of Point3d objects ordered by closness to pt
        '''
        pt = self.point3d(pt)
        pt1 = crv.startSketchPoint.geometry
        pt2 = crv.endSketchPoint.geometry
        
        d1 = pt1.distanceTo(pt)
        d2 = pt2.distanceTo(pt)
        
        if returnSketchPoint == False:
            if d1 <= d2:
                return pt1,pt2
            else:
                return pt2,pt1
        else:
            if d1 <= d2:
                return crv.startSketchPoint,crv.endSketchPoint
            else:
                return crv.endSketchPoint,crv.startSketchPoint
            
    def ptTuple(self,pt, threeDimensions = False):
        '''
        gets the coordinates of a point
        
        pt is a sketchPoint or Point3d object or tuple of coordinates
        threeDimensions is a bool specifying if all 3 dimensions are to be returned
        
        returns an touple which contains the ordered x,y or x,y,z coordinates
        '''
        pt = self.point3d(pt)
        if threeDimensions:
            return pt.x, pt.y, pt.z
        else:
            return pt.x, pt.y
        
        

class Sketch_Vector():
    def __init__(self,parent):
        self.__parent__ = parent
    
    def unitVector(self,vect):
        '''
        calculates unit vector from vect
        
        vect is a tuple/list of vector components
        
        returns a vector
        '''
        
        length = self.magnitude(vect)
        
        return vect[0]/length, vect[1]/length
        
    def fromPoints(self,pt1,pt2):
        '''
        calculates the vector pointing from pt1 to pt2
        
        pt1 is a sketchPoint or Point3d object or tuple of coordinates
        pt2 is a sketchPoint or Point3d object or tuple of coordinates
        
        returns a vector
        '''
        pt1 = self.__parent__.get.point3d(pt1)
        pt2 = self.__parent__.get.point3d(pt2)
        
        pt1x = pt1.x
        pt1y = pt1.y
        
        pt2x = pt2.x
        pt2y = pt2.y
        
        dx = pt2x - pt1x
        dy = pt2y - pt1y
        
        return dx,dy
        
    def magnitude(self,vect):
        '''
        returns the magnitude of a vector
        vect is a tuple/list that contains the x and y components of the vecor
        
        returns a scalar
        '''
        return math.sqrt(vect[0]**2 + vect[1]**2)
        
    def addVectorAndPoint(self,vect,pt):
        '''
        adds a vector to a point
        pt is a sketchPoint or Point3d object or tuple of coordinates
        vect is a tupel/list that contains the x and y components of the vector
        
        returns a Point3D object
        '''
        pt = self.__parent__.get.point3d(pt)
        newPt = pt.copy()
        newPt.x += vect[0]
        newPt.y += vect[1]
        return newPt
        
    def perpendicularUnitVector(self,vect):
        '''
        calculates a unit vector that is perpendicular to the vector input
        
        vect is a tupel/list that contains the x and y components of the vector
        
        returns a vector
        '''
        length = self.magnitude(vect)
        return vect[1]/length,-vect[0]/length
        
    def dotProduct(self,v1,v2):
        '''
        calculates the dot product between v1 and v2
        
        v1 and v2 are tupels/lists that contains the x and y components of the vectors
        
        returns the scalar dot product
        '''
        return v1[0] * v2[0] + v1[1] * v2[1]
        
    def crossProduct(self,v1,v2):
        '''
        calculates the cross product between v1 and v2
        
        v1 and v2 are tupels/lists that contains the x and y components of the vectors
        
        returns the scalar cross product
        '''
        return v1[0] * v2[1] - v1[1] * v2[0]
        
    def sweptAngle(self,v1,v2):
        '''
        calculates the angle between v1 and v2
        
        v1 and v2 are tupels/lists that contains the x and y components of the vectors
        
        returns angle value in radians (note, will always return minor angle)
        '''
        cosTheta = self.dotProduct(v1,v2)/self.magnitude(v1)/self.magnitude(v2)
        
        return math.acos(cosTheta)
        
    def arePerpendicular(self,v1,v2):
        '''
        checks to see if v1 and v2 are perpendicular
        
        v1 and v2 are tupels/lists that contains the x and y components of the vectors

        returns a bool        
        '''
        if self.dotProduct(v1,v2) <= self.__parent__.__base__.smallNumber:
            return True
        else:
            return False
            
    def areParallel(self,v1,v2):
        '''
        checks to see if v1 and v2 are parallel
        
        v1 and v2 are tupels/lists that contains the x and y components of the vectors

        returns a bool        
        '''
        
        if self.crossProduct(v1,v2) <= self.__parent__.__base__.smallNumber:
            return True
        else:
            return False
            
    def scaleVector(self,vect,scale):
        '''
        scales a vector
        
        vect is a tupel/list that contains the x and y components of the vector
        scale is the scale factor
        
        returns a vector
        '''
        return vect[0]*scale, vect[1]*scale
        
class Sketch_Constrain():
    '''
    subclass of EZSketch that contains all of the methods to constrain sketch elements
    '''
    def __init__(self,parent):
        self.__parent__ = parent
        self._orientAligned = adsk.fusion.DimensionOrientations.AlignedDimensionOrientation
        self._orientHorizontal = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
        self._orientVertical = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        self._noSketchMessage = 'no sketch defined, use createSketch() to define a sketch'
        
    def geometric(self,objects,constraintType):
        '''
        collectcion of all geometric constraints possible in a sketch
        objects is either a single object or a a list of objects to be constrained
        constraint type is a string indicating the constratint type and is case-insensitive
        -Horizontal or H for horizontal line or horizontal points
        -Vertical or v for vertical line or vertical points
        -Coincident or Coin for coincident
        -Collinear or Col for collinear
        -Midpoint or Mid for midopint
        -Parallel or Par for parallel
        -Perpendicular or Perp for perpendicular
        -Concentric or Con for concentric
        -Tangent or Tan for tangent
        -Symmetry of Sym for symmetry
        -Smooth or S for smooth
        '''
        if type(objects) is not list:
            objects = [objects]
        constraintType = constraintType.lower()
        if (constraintType == "horizontal" or \
            constraintType == "h"):
            
            if len(objects) == 2:
                if type(objects[0]) is adsk.fusion.SketchPoint and \
                    type(objects[1]) is adsk.fusion.SketchPoint:
                
                    return self.__parent__._constraints.addHorizontalPoints(objects[0],objects[1])

            if len(objects) == 1 and type(objects[0]) is adsk.fusion.SketchLine:
                return self.__parent__._constraints.addHorizontal(objects[0])
                
        if (constraintType == "vertical" or \
            constraintType == "v"):
            
            if len(objects) == 2:
                if type(objects[0]) is adsk.fusion.SketchPoint and \
                    type(objects[1]) is adsk.fusion.SketchPoint:
                
                    self.__parent__._constraints.addVerticalPoints(objects[0],objects[1])

            if len(objects) == 1 and type(objects[0]) is adsk.fusion.SketchLine:
                return self.__parent__._constraints.addVertical(objects[0])
                
        if constraintType == "coincident" or constraintType == "coin":
            if isinstance(objects[0],adsk.fusion.SketchCurve) and isinstance(objects[0],adsk.fusion.SketchCurve):
                pass #do find intersection and get points and then pass them in
            return self.__parent__._constraints.addCoincident(objects[0],objects[1])
            
        if constraintType == "colinear" or constraintType == "col":
            return self.__parent__._constraints.addCollinear(objects[0],objects[1])
            
        if constraintType == "midpoint" or constraintType == "mp":
            return self.__parent__._constraints.addMidPoint(objects[0],objects[1])
            
        if constraintType == "parallel" or constraintType == "par":
            return self.__parent__._constraints.addParallel(objects[0],objects[1])
            
        if constraintType == "perpendicular" or constraintType == "perp":
            return self.__parent__._constraints.addPerpendicular(objects[0],objects[1])
            
        if constraintType == "concentric" or constraintType == "con":
            return self.__parent__._constraints.addConcentric(objects[0],objects[1])
            
        if constraintType == "symmetry" or constraintType == "sym":
            return self.__parent__._constraints.addSymmetry(objects[0],objects[1],objects[2])
            
        if constraintType == "tangent" or constraintType == "tan":
            return self.__parent__._constraints.addTangent(objects[0],objects[1])
            
        if constraintType == "smooth" or constraintType == "s":
            return self.__parent__._constraints.addSmooth(objects[0],objects[1])
            
    def dimension(self,objects,dimensionType = None, expression = None, value = None, txtPt = None, orientation = "Aligned"):
        '''
        applies dimensions to an object based on object type as the Fusion 360 GUI does
        Users can override the smart dimensioning by specifying a dimensionType:
        -Distance or d for distance dimension
        -angular or a for angluar dimension
        -radial or r for radial dimension
        -diameter or d for diameter dimension
        -concentric or c for concentric dimension
        -offset or o for offset dimension
        
        objects is a single object or list of objects to be included in the dimensioning operation
        expression is a number or a string to set the dimension expression to
        value is a number to set the value to
        txtPt is a point3D object to set the text point of the dimension to a value
        orientation is specified for distance dimensions "Horizontal" ("h"), "Vertical" ("v"), or "Aligned" ("a")
        '''
        if type(objects) is not list:
            objects = [objects]
            
        if len(objects) == 1:
            obj1 = objects[0]
            obj2 = None
        else:
            obj1 = objects[0]
            obj2 = objects[1]
            
        orientation = orientation.lower()
        errMsg1 = 'Unable to Determine Dimension Type Automatically, Please specify dimensionType parameter'
        if dimensionType == None:
            if obj2 == None:
                if type(obj1) is adsk.fusion.SketchArc:
                    dimensionType = 'r'
                elif type(obj1) is adsk.fusion.SketchCircle:
                    dimensionType = 'dia'
                elif type(obj1) is adsk.fusion.SketchLine:
                    obj1 = obj1.startSketchPoint
                    obj2 = obj1.endSketchPoint
                    dimensionType = 'd'
                else:
                    raise Exception(errMsg1)
            else:
                if type(obj1) is adsk.fusion.SketchPoint and type(obj2) is adsk.fusion.SketchPoint:
                    dimensionType = 'd'
                elif type(obj1) is adsk.fusion.SketchLine and type(obj2) is adsk.fusion.SketchLine:
                    if self.__parent__.get.areLinesParallel(obj1,obj2):
                        self.geometric([obj1,obj2],'par')
                        dimensionType = 'o'
                    else:
                        dimensionType = 'a'
                elif (type(obj1) is adsk.fusion.SketchCircle and type(obj2) is adsk.fusion.SketchCircle) or \
                    (type(obj1) is adsk.fusion.SketchArc and type(obj2) is adsk.fusion.SketchArc):
                    if self.__parent__.get.arePontsCoincident(obj1.centerSketchPoint,obj2.centerSketchPoint):
                        self.geometric([obj1.centerSketchPoint,obj2.centerSketchPoint],'coin')
                        dimensionType = 'c'
                    else:
                        obj1 = obj1.centerSketchPoint
                        obj2 = obj2.centerSketchPoint
                        dimensionType = 'd'
                else:
                    raise Exception(errMsg1)
                

        dimensionType = dimensionType.lower()
        
        
        if dimensionType == "distance" or dimensionType == "d":
            if orientation == "horizontal" or orientation == "h":
                dimOrientation = self._orientHorizontal
            elif orientation == "vertical" or orientation == "v":
                dimOrientation = self._orientVertical
            else:
                dimOrientation = self._orientAligned
            dimObj = self.__parent__._dims.addDistanceDimension(obj1,obj2,dimOrientation,self._handleTxtPt(txtPt,obj1,obj2))       
            
        elif dimensionType == "angular" or dimensionType == "a":
            dimObj = self.__parent__._dims.addAngularDimension(obj1,obj2,self._handleTxtPt(txtPt,obj1.endSketchPoint,obj2.endSketchPoint))       
            
        elif dimensionType == "radial" or dimensionType == "r":
            dimObj = self.__parent__._dims.addRadialDimension(obj1,self._handleTxtPt(txtPt,obj1.startSketchPoint,obj1.endSketchPoint))
            
        elif dimensionType == "diameter" or dimensionType == "dia":
            if txtPt == None:
                txtPt = obj1.centerSketchPoint.geometry
            else:
                radius = obj1.radius
                txtPt = obj1.centerSketchPoint.geometry
                txtPt.x += radius*1.1
                txtPt.y += radius*1.1
            dimObj = self.__parent__._dims.addDiameterDimension(obj1,txtPt)
        elif dimensionType == "concentric" or dimensionType == "c":
            txtPt = obj1.centerSketchPoint.geometry
            r1 = obj1.radius
            r2 = obj2.radius
            aveR = (r1+r2)/2
            txtPt.x += aveR*1.1
            txtPt.y += aveR*1.1
            dimObj = self.__parent__._dims.addConcentricCircleDimension(obj1,obj2,txtPt)
        elif dimensionType == 'offset' or dimensionType == 'o':
            if type(obj2) is adsk.fusion.SketchPoint:
                txtPt = self._handleTxtPt(txtPt,obj1.startSketchPoint,obj2)
            dimObj = self.__parent__._dims.addOffsetDimension(obj1,obj2,self._handleTxtPt(txtPt,obj1.startSketchPoint,obj2.startSketchPoint))
        else:
            raise Exception('Did Not Recognize Dimension Type')
            
        return self._handleDimObjExpressionOrValue(dimObj,expression,value)
        
    def _handleDimObjExpressionOrValue(self,dimObj,expression,value):
        if not expression == None:
            dimObj.parameter._set_expression(expression)
            return dimObj
        if not value == None:
            dimObj.parameter.value = value
        return dimObj
    
    def _handleTxtPt(self,txtPt,pt1,pt2):
        if txtPt == None:
            txtPt = self.__parent__.__base__.Utils.calcMidpoint(pt1,pt2)
        return txtPt

class Sketch_Create():
    '''
    subclass of EZSketch that contains all of the create sketch entity methods
    '''
    def __init__(self,parent):
        self.__parent__ = parent
        
    def point(self,x,y=None,fixed=False):
        '''
        creates a sketchPoint object
        x is either a Point3D object or a number
        y is a number
        if y is used, both x and y must be numbers representing the coordinates in the sketch
        fixed is a bool and sets the fixed propery
        
        returns a sketchPoint object
        '''
            
        if type(x) is adsk.core.Point3D and y == None:
            pt = self.__parent__._points.add(x)
        elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
            pt = self.__parent__._points.add(adsk.core.Point3D.create(x,y,0))
        else:
            raise Exception("Type Error")
        if fixed:
            pt.isFixed = True
        return pt
        
    def line(self,pt1,pt2,construction = False,fixed = False):
        '''
        creates a line between two points
        
        pt1 and pt2 are either tuples with number elements representing point
        coordinates, sketchPoint objects, or point3D objects
        
        constructioin is a bool and sets the construction property
        
        returns a sketchLine object
        '''
        if type(pt1) is tuple:
            pt1 = self.point3d(pt1)

        if type(pt2) is tuple:
            pt2 = self.point3d(pt2)            
            
        line = self.__parent__._lines.addByTwoPoints(pt1,pt2)
        if construction:
            line._set_isConstruction(True)
        if fixed:
            line.isFixed=True
        return line
        
    def curveChain(self,pointList,close = None):
        '''
        Creates a chain of lines/arcs from a list of points.
        Behaves exactly like the create arc by click and drag.
        To specify an arc between two points, add an 'a' or 'arc to the list
        between the points otherwise a line will be made between the points.
        
        pointList is a python list containing tuples containing numbers
        representing point coordinates, sketchPoint object, or point3D object
        
        returns a list of the created sketchCurvs in the order they were created
        in the chain
        '''
        pts = self._handleObjectsChecks(pointList)
        ptList = []
        cmdList = []
        PI = self.__parent__.__base__._pi
        
        for i in range(len(pts)-1):
            if type(pts[i]) is adsk.core.Point3D:
                ptList.append(pts[i])
                if type(pts[i+1]) is str:
                    if pts[i+1].lower() == 'a' or pts[i+1].lower() == 'arc':
                        cmdList.append('a')
                    else:
                        cmdList.append('l')
                elif type(pts[i]) is adsk.core.Point3D:
                    cmdList.append('l')
                else:
                    raise Exception('pointList item type is invalid')
        
        if type(pts[-1]) is adsk.core.Point3D:
            ptList.append(pts[-1])
        
        if close != None:
            ptList.append(pts[0])
            if close == 'a' or close == 'arc':
                cmdList.append('a')
            else:
                cmdList.append('l')
        
        crvList = []
        if cmdList[0] != 'l':
            raise Exception('First geterated element must be a line')
        
        fixedPtList = []
        prevLine = None
        for i,cmd in enumerate(cmdList):
            if cmd == 'l':
                pt1 = ptList[i]
                pt2 = ptList[i+1]
                line = self.line(pt1,pt2)
                if not self.__parent__.get.isPointInList(pt1,fixedPtList):
                    line.startSketchPoint.isFixed = True
                    fixedPtList.append(line.startSketchPoint)
                if not self.__parent__.get.isPointInList(pt2,fixedPtList):
                    line.endSketchPoint.isFixed = True
                    fixedPtList.append(line.endSketchPoint)
                if i>0 and self.__parent__.get.arePontsCoincident(line.startSketchPoint, prevLine.endSketchPoint):
                    self.__parent__.constrain.geometric([line.startSketchPoint,prevLine.endSketchPoint],'coin')
                crvList.append(line)
                prevLine = line
                if i == len(ptList) - 2 and close != None: # case where line is the last command and close is True
                    int1,_ = self.__parent__.get.orderCurveEndsByDist(line,ptList[0],returnSketchPoint = True)
                    int2,_ = self.__parent__.get.orderCurveEndsByDist(crvList[0],ptList[0],returnSketchPoint = True)
                    self.__parent__.constrain.geometric([int1,int2],'coin')
            else:
                crvList.append('arc')
        for i,crv in enumerate(crvList):
            if crv == 'arc':
                if i>0 and type(crvList[i-1]) is adsk.fusion.SketchLine: # case where previous curve is a line
                    # grab handle from previous line
                    line = crvList[i-1]
                    
                    intersectPoint = ptList[i]
                    lineEnd,lineStart = self.__parent__.get.orderCurveEndsByDist(line,intersectPoint,returnSketchPoint=True)
                    
                    vect = self.__parent__.vector.fromPoints(lineStart,lineEnd)
                    unitVect = self.__parent__.vector.unitVector(vect)
                    length = self.__parent__.vector.magnitude(vect)
                    length += self.__parent__.__base__.smallNumber * 100
                    scaledVect = self.__parent__.vector.scaleVector(unitVect,length)
                    guessPointOnAcr = self.__parent__.vector.addVectorAndPoint(scaledVect,lineStart)
                    
                    # get the end point of the arc
                    if i == len(crvList) - 1: # this is the case if an ark is the last command
                        if close == 'arc' or close == 'a':
                            endPoint = crvList[0].startSketchPoint
                        else:
                            endPoint = self.point(ptList[-1])
                            if not self.__parent__.get.isPointInList(endPoint,fixedPtList):
                                line.endSketchPoint.isFixed = True
                                fixedPtList.append(endPoint)
                    else:
                        if type(crvList[i+1]) is adsk.fusion.SketchLine:  # case where next element is a line
                            endPoint = crvList[i+1].startSketchPoint
                        else: # case where next element is an ark
                            endPoint = self.point(ptList[i+1])
                            if not self.__parent__.get.isPointInList(endPoint,fixedPtList):
                                endPoint.isFixed = True
                                fixedPtList.append(endPoint)
                                
                    #create the ark based on end points and guess point
                    arc = self.arc([lineEnd,guessPointOnAcr,endPoint],'3p')
                    self.__parent__.constrain.geometric([arc,line],'tan')
                    crvList[i] = arc
                else: #case where previous curve is an arc
                    
                    # grab handle to previous ark
                    prevArc = crvList[i-1]
                    intersectPoint = ptList[i]
                    prevEndPt,prevStartPt = self.__parent__.get.orderCurveEndsByDist(prevArc,intersectPoint,returnSketchPoint=True)
                    prevCntrPt = prevArc.centerSketchPoint
                    
                    #calculate a guess point on the ark that is just past the end of previous arc
                    startVect = self.__parent__.vector.fromPoints(prevCntrPt,prevStartPt)
                    endVect = self.__parent__.vector.fromPoints(prevCntrPt,prevEndPt)
                
                    prevRadius = prevArc.radius
                    prevLength = prevArc.length

                    if prevLength/(PI*prevRadius*2) > 0.5:
                        rev = True
                    else:
                        rev = False
                    
                    perpVect = self.__parent__.vector.perpendicularUnitVector(endVect)
                    perpVect = self.__parent__.vector.scaleVector(perpVect,self.__parent__.__base__.smallNumber * 100)
                    guessPointOnAcr1 = self.__parent__.vector.addVectorAndPoint(perpVect,prevEndPt)
                    
                    perpVect = self.__parent__.vector.perpendicularUnitVector(endVect)
                    perpVect = self.__parent__.vector.scaleVector(perpVect,-1)
                    perpVect = self.__parent__.vector.scaleVector(perpVect,self.__parent__.__base__.smallNumber * 100)
                    guessPointOnAcr2 = self.__parent__.vector.addVectorAndPoint(perpVect,prevEndPt)
                    
                    gVect1 = self.__parent__.vector.fromPoints(prevCntrPt,guessPointOnAcr1)
                    
                    A = self.__parent__.vector.sweptAngle(startVect,endVect)
                    A1 = self.__parent__.vector.sweptAngle(startVect,gVect1)
                    
                    if rev:
                        if A1 < A:
                            guessPointOnAcr = guessPointOnAcr1
                        else:
                            guessPointOnAcr = guessPointOnAcr2
                    else:
                        if A1 > A:
                            guessPointOnAcr = guessPointOnAcr1
                        else:
                            guessPointOnAcr = guessPointOnAcr2
                    
                    # get the end point of the arc
                    if i == len(crvList) - 1: # this is the case if an ark is the last command
                        if close == 'arc' or close == 'a':
                            endPoint = crvList[0].startSketchPoint
                        else:
                            endPoint = self.point(ptList[-1])
                            if not self.__parent__.get.isPointInList(endPoint,fixedPtList):
                                line.endSketchPoint.isFixed = True
                                fixedPtList.append(endPoint)
                    else:
                        if type(crvList[i+1]) is adsk.fusion.SketchLine:  # case where next element is a line
                            endPoint = crvList[i+1].startSketchPoint
                        else: # case where next element is an ark
                            endPoint = self.point(ptList[i+1])
                            if not self.__parent__.get.isPointInList(endPoint,fixedPtList):
                                endPoint.isFixed = True
                                fixedPtList.append(endPoint)
                                
                    arc = self.arc([prevEndPt,guessPointOnAcr,endPoint],'3p')
                    
                    # add tangent constraint
                    self.__parent__.constrain.geometric([arc,prevArc],'tan')
                    crvList[i] = arc
                    
        for pt in fixedPtList:
            pt.isFixed = False
            
        return crvList
                    
                
        
    def rectangle(self,points,rectType, fixPoint = None,orthogonal = True,axisAligned = True,sideDims = False,expressions=[None,None],construction = False):
        '''
        automates creating a rectangle
        
        points is a list of SketchPoints, Point3D Objects, or tuples that define the point locations
        rectType is a string indicating which of the 3 types of rectangels to create:
        -TwoPointRectangle or 2PR where 2 points are supplied which are the corners and the sides are parallel to cardinal axis
        -CenterPointRectangle or CPR where 2 points are suppled, the first is a center point, the second is a corner, sides are parallel to cardinal axis
        -ThreePointRectangle or TPR where 3 points are supplied, the first 2 are the base, and the 3rd sets the height
        
        fixedPoint is an integer between 0 and 3 or is None which sets one of the corners to be fixed
        orthogonal is a bool and sets perpendicular constraints on the lines
        axisAligned is a bool and sets an axis alignment constraint (turned off for three point rectangle)
        sideDims is a bool and sets weather or not dimensional constraints are imposed
        expressions is a list of two numbers or strings which sets the valueInput of the sideDims if set to True, leave item as none to create the dimension but not set expression
        construction is a bool and sets all created lines to construction if true
        
        Returns a list of the sketch lines created
        '''
        points = self._handleObjectsChecks(points)
        lines=[]
        
        if expressions[0] != None or expressions[1] !=None:
            sideDims = True
        
        rectType = rectType.lower()
        if rectType == 'twopointrectangle' or rectType == '2pr':
            rect = self.__parent__._lines.addTwoPointRectangle(points[0],points[1])
        elif rectType == 'threepointrectangle' or rectType == '3pr':
            if type(points[2]) is not adsk.core.Point3D:
                pt = points[2].geometry
            else:
                pt = points[2]
            rect = self.__parent__._lines.addThreePointRectangle(points[0],points[1],pt)
            axisAligned = False
        elif rectType == 'centerpointrectangle' or rectType == 'cpr':
            if type(points[0]) is not adsk.core.Point3D:
                pt = points[0].geometry
            else:
                pt = points[0]
            rect = self.__parent__._lines.addCenterPointRectangle(pt,points[1])
        else:
            raise Exception('Rectangle Type Not Recognized')
            
        for i in range(4):
            lines.append(rect.item(i))
        
        corners = [rect.item(0).startSketchPoint,rect.item(1).startSketchPoint,rect.item(2).startSketchPoint,rect.item(3).startSketchPoint]
        corners[0].isFixed = True
        corners[2].isFixed = True
        
        if orthogonal:
            for i in range(rect.count-1):
                self.__parent__.constrain.geometric([rect.item(i),rect.item(i+1)],'perp')
                
        if axisAligned:
            self.__parent__.constrain.geometric([rect.item(2)],'v')
        
        if fixPoint != None:
            for i in range(4):
                if i != fixPoint:
                    corners[i].isFixed = False
                else:
                    corners[i].isFixed = True
        else:
            corners[0].isFixed = False
            corners[2].isFixed = False         
        
        if sideDims:
            self.__parent__.constrain.dimension([rect.item(0).startSketchPoint,rect.item(0).endSketchPoint],expression=expressions[0])
            self.__parent__.constrain.dimension([rect.item(1).startSketchPoint,rect.item(1).endSketchPoint],expression=expressions[1])
            
        if construction:
            for i in range(4):
                rect.item(i).isConstruction = True
        
        return lines
        
    def circle(self,objects,circType,radius = None,construction=False,fixed=False,dimension = False, constraints = True, expression = None):
        '''
        automates the process of creating a circle
        
        objects is a single object or a list of objects, points can be defined as a tuple, sketchPoint, or Point3D
        circType is a string indicating which of the 5 types of circles to create:
        -CenterRadius or cr where one point is supplied which is the center of the circle (radius defautlts to 1 if not specified)
        -TwoPoints or 2p where 2 points are suppled, circle is created between the points, center inline
        -ThreePoints or 3p where 3 points are supplied that defines 3 points on the perimeter
        -TwoTangents or 2t where 2 sketchlines are supplied (radius defaults to 1 if not specified)
        -ThreeTangents or 3t where 3 sketlines are supplied to create
        
        radius is a number and the radius of the circle in cm
        construction is a bool and sets the construction property
        fixed is a bool and sets the fixed property
        dimension is a bool and will add a dimension if it doesn't overconstrain the sketch
        constraints is a bool and will add tangent constraints
        expression is a string that sets the expresison for the dimension
        
        returns a list of the sketchCircle, list of constraints, and list of dimensions
        '''
        objects = self._handleObjectsChecks(objects)
        circType = circType.lower()
        
        if expression != None:
            dimension = True
        if radius == None:
                radius = 1
        if circType == 'centerradius'or circType == 'cr':
            cntr = objects[0]
            if type(cntr) is not adsk.core.Point3D:
                cntr = cntr.geometry
            circ =  self.__parent__._circles.addByCenterRadius(cntr,radius)
            
        # Add by points on circumferance
        elif circType == 'twopoints' or circType == '2p':
            circ = self.__parent__._circles.addByTwoPoints(objects[0],objects[1])
        elif circType == 'threepoints' or circType == '3p':
            circ = self.__parent__._circles.addByThreePoints(objects[0],objects[1],objects[2])
                    
        # Add by tangents to lines
        elif circType == 'twotangents' or circType == '2t':
            circ = self.__parent__._circles.addByTwoTangents(objects[0],objects[1],radius)
            if constraints:
                for i in range(2):
                    self.__parent__.constrain.geometric([circ,objects[i]],'tan')
        elif circType == 'threetangents' or circType == '3t':
            circ = self.__parent__._circles.addByThreeTangents(objects[0],objects[1],objects[2])
            if constraints:
                for i in range(3):
                    self.__parent__.constrain.geometric([circ,objects[i]],'tan')
        else:
            raise Exception('Circle Type Not Recognized')
            
        if dimension:
            try:
                self.__parent__.constrain.dimension(circ,expression=expression)
            except:
                pass
            
        if construction:
            circ.isConstruction = construction
        
        if fixed:
            circ.isFixed = fixed
        
        return circ
        
    def arc(self,objects,arcType,radius = None, construction = False,fixed = False, dimension = False, expression = None):
        '''
        automates the process of creating an arc
        objects is a single object or a list of objects, points can be defined as a tuple, sketchPoint, or Point3D
        arcType is the type of arc to create
        -ThreePoint or 3p where 3 points are supplied that are on the arc (startpoint, point, endpont)
        -CenterStartSweep or CSS where 3 points are given that are ordered by center, start point, end point
        -Fillet or F where two pairs of sketLine, Point3d are supplied
        radius sets the radius of the arc defaults to 1
        constructioin is a bool and sets the construction property
        fixed is a bool and sets the fixed property
        dimension is a bool and determins if a dimension is added
        expression is a str that sets the expression value
        '''
        objects = self._handleObjectsChecks(objects)
        arcType = arcType.lower()
        
        if expression != None:
            dimension = True
            
        if radius == None:
            radius = 1

        if arcType == 'threepoint' or arcType == '3p':
            if type(objects[1]) is not adsk.core.Point3D:
                objects[1] = objects[1].geometry
            arc = self.__parent__._arcs.addByThreePoints(objects[0], objects[1], objects[2])
        elif arcType == 'centerstartsweep' or arcType == 'css':
            arc = self.__parent__._arcs.addByCenterStartSweep(objects[0], objects[1], objects[2])
        elif arcType == 'fillet' or arcType == 'f':
            arc = self.__parent__._arcs.addFillet(objects[0], objects[1], objects[2],objects[3],radius)
        else:
            raise Exception('Arc Type Not Recognized')
            
        if construction:
            arc.isConstruction = True
            
        if fixed:
            arc.isFixed = True
            
        if dimension:
            self.__parent__.constrain.dimension(arc,expression=expression)
        
        if arc.geomtricConstraints.count != 0:
            for i in range(arc.geomtricConstraints.count):
                arc.geomtricConstraints.item(i)
        
        return arc
    
    def _handleObjectsChecks(self,objects):
        if type(objects) is not list:
            objects = [objects]
        return self.__parent__.__base__.Utils.handleObjectList2Points(objects)
        
class Sketch_Set():
    def __init__(self,parent):
        self.__parent__ = parent
        
    def sketch_Visibility(self,vis):
        '''
        sets the visibility of the sketch in the EZSketch instance
        
        vis is a bool
        '''
        self.__parent__.sketch.isVisible = vis
        
    def sketch_Name(self,name):
        '''
        sets the name of the sketch
        
        name is a string
        '''            
        self.__parent__.sketch._set_name(name)
        
    def object_Fix(self,sketchObject,fix):
        '''
        sets the fixed propery of an object
        
        fix is a bool
        '''
        sketchObject.isFixed = fix






















       
        
class EZFeatures:
    '''
    This class creates a body feature and contains methods to operate on the
    created body.  Since there are multiple kinds of body features, the instance
    of the class must be created first followed by one of the "create_" methods.
    
    Only one feature is allowed per EZFeature Instance, create multiple instances
    to create multiple features.
    '''
    def __init__(self):
        self.__base__ = BaseClass()
        self.feature = None
        self._featureType = None
        
        self.modify = Features_modify(self)
        self.create = Features_Create(self)
        self.get = Features_Get(self)
        
class Features_Get():
    def __init__(self,parent):
        self.__parent__ = parent
        
    def faces(self,faceType = 'all'):
        '''
        gets all faces associated with the EZFeature instance
        
        faceType is a string indicating the type of face to grab
        -all will attempt to grab all faces
        -end will attempt to grab the end faces if the property is available
        -start will attempt to grab the start faces if the property is available
        -side will attempt to grab the side faces if the property is availble
        
        returns a face collection or None if it didn't find the property
        '''
        faceType = faceType.lower()
        faces = None
        try:
            if faceType == 'all':
                faces = self.__parent__.feature.faces
            elif faceType == 'end':
                faces = self.__parent__.feature.endFaces
            elif faceType == 'start':
                faces = self.__parent__.feature.startFaces
            elif faceType == 'side':
                faces = self.__parent__.feature.sideFaces
        except:
            pass
        return faces
            
    def bRepBody(self):
        '''
        gets the body associated with the EZFeature instance
        '''
        return self.faces('all')[0].body
        
    def allEdges_List(self):
        '''
        returns a list of all the edges in the feature
        '''
        edgesObjs = self.bRepBody().edges
        return self.__parent__.__base__.Utils.adskObjectList2PythonList(edgesObjs)
        
    def allEdges_ObjectCollection(self):
        '''
        returns an object collection of all the edges in a feature
        '''
        edges = self.bRepBody().edges
        return self.__parent__.__base__.Utils.makeObjectCollection(edges)

class Features_Create():
    def __init__(self,parent):
        self.__parent__ = parent
        
    def extrude(self,profile, distance, isSymmetric=False, distanceUnits='in'):
        '''
        Automates the task of extruding a profile a given distance
        
        profile is the profile to extrude
        distance is the distance to extrude, it can be a numeric value or a string or an expression
        isSymetric defines if the extrusion is to happen on both sides of the profile
        
        This is considered a primary feature, as in this feature is not dependant
        on other features to be created.  The feature must be created in the same
        component as the profile given, so the parent component is set automatically
        to the parent component of the profile
        
        returns the extruded feature
        '''
        self._primaryFeatureChecks(profile)
        distance = self.__parent__.__base__.Utils.createValueInput(distance,distanceUnits)
        features = self.__parent__._parentComponent.features.extrudeFeatures
        featureInput = features.createInput(profile,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        featureInput.setDistanceExtent(isSymmetric,distance)
        self.__parent__.feature = features.add(featureInput)
        self.__parent__._featureType = 'extrude'
        return self.__parent__.feature
        
    def revolve(self,profile, axis, angularDistance = None, angularUnits='deg'):
        '''
        Automates the task of revolving a profile
        
        profile is the profile to revolve
        axis is the axis about which the revolve will occur
        angularDistance is the angular distance to revolve, it can be a numeric 
            value or a string or an expression
        
        This is considered a primary feature, as in this feature is not dependant
        on other features to be created.  The feature must be created in the same
        component as the profile given, so the parent component is set automatically
        to the parent component of the profile
        
        returns the revolve feature
        '''
        self._primaryFeatureChecks(profile)
        if angularDistance is None:
            angularDistance = 360
        angularDistance = self.__parent__.__base__.Utils.createValueInput(angularDistance,angularUnits)        
        features = self.__parent__._parentComponent.features.revolveFeatures
        featureInput = features.createInput(profile,axis,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        featureInput.setAngleExtent(True,angularDistance)
        self.__parent__.feature = features.add(featureInput)
        self.__parent__._featureType = 'revolve'
        return self.__parent__.feature
        
    def _primaryFeatureChecks(self,profile):
        self.__parent__.__base__.Utils.checkForExistingFeatrue(self.__parent__.feature)
        self.__parent__._parentComponent = self.__parent__.__base__.Utils.getParentComponentOfProfile(profile)

class Features_modify():
    def __init__(self,parent):
        self.__parent__ = parent        
        
    def material(self,material):
        '''
        sets the material of a feature to one of the materials in the Fusion 360 Material Library
        
        material is a string matching the name of one of the materials in fusion 360
        feature is an adsk feature object (leave None to operate on the EzFeature)A
        note: material names are case sensitive and must be spelled exactly as they
        appear in the Fusion 360 material library
        '''
        body = self.__parent__.get.bRepBody()
        materialLibName = 'Fusion 360 Material Library'
        materialLibs = self.__parent__.__base__.app.materialLibraries
        materials = materialLibs.itemByName(materialLibName).materials
        body.material = materials.itemByName(material)
        
    def appearance(self,Appearance):
        '''
        sets the appearance of a feature to one of the appearance in the Fusion 360 Appearance Library
        
        Appearance is a string matching the name of one of the appearances in fusion 360
        feature is an adsk feature object (leave None to operate on the EzFeature)
        note: appearance names are case sensitive and must be spelled exactly as they
        appear in the Fusion 360 Appearance library
        '''
        body = self.__parent__.get.bRepBody()
        appearanceLibName = 'Fusion 360 Appearance Library'
        materialLibs = self.__parent__.__base__.app.materialLibraries
        appearances = materialLibs.itemByName(appearanceLibName).appearances
        body.appearance = appearances.itemByName(Appearance)
        
    def fillet(self, edgeColl, radius, distanceUnits = 'in'):
        '''
        creates a fillet with the current feature and returns a new EZFeature
        instance of the fillet
        
        edgeColl is the collection of edges that will be filleted and should
        be edges belonging to the current feature.
        radius is the fillet radius
        
        This is considered a derrivative feature, as in this feature is dependant
        on other features.  The feature must be created in the same
        component as the parent feature, so the parent component is set automatically
        to the parent component of the parent feature 
        
        returns a new instance of an EZFeature containing the fillet feature
        '''
        newFeature = EZFeatures()
        newFeature.modify._create_Fillet(edgeColl, radius, distanceUnits = distanceUnits)
        return newFeature
        
    def shell(self,faceColl, shellThickness, distanceUnits = 'in'):
        '''
        creates a shell with the current feature and returns a new EZFeature
        instance of the shell
        
        faceColl is the collection of faces that will be shelled and should
        be faces belonging to the current feature
        shellThickness is the thickness that will be created on the shell
        
        This is considered a derrivative feature, as in this feature is dependant
        on other features.  The feature must be created in the same
        component as the parent feature, so the parent component is set automatically
        to the parent component of the parent feature     
        
        returns a new instance of an EZFeature containing the shell feature
        '''
        newFeature = EZFeatures()
        newFeature.modify._create_Shell(faceColl, shellThickness, distanceUnits = distanceUnits)
        return newFeature
        
    def _create_Fillet(self, edgeColl, radius, distanceUnits = 'in'):
        '''
        dont't call this function unless you are calling it for the first time
        on a newly created EZFeature Object.  You will write over the handle
        to the existing feature. Use modify_Fillet instead.
        '''
        self._derrivativeFeatureChecks(edgeColl.item(0))
        radius = self.__parent__.__base__.Utils.createValueInput(radius,distanceUnits)
        features = self.__parent__._parentComponent.features.filletFeatures        
        featureInput = features.createInput()
        featureInput.addConstantRadiusEdgeSet(edgeColl, radius, True)
        self.__parent__.feature = features.add(featureInput)
        self.__parent__.featureType = 'fillet'
        return self.__parent__.feature
        
    def _create_Shell(self,faceColl, shellThickness, distanceUnits = 'in'):
        '''
        dont't call this function unless you are calling it for the first time
        on a newly created EZFeature Object.  You will write over the handle
        to the existing feature. Use modify_Shell instead.
        '''
        self._derrivativeFeatureChecks(faceColl.item(0))
        distance = self.__parent__.__base__.Utils.createValueInput(shellThickness,distanceUnits)
        features = self.__parent__._parentComponent.features.shellFeatures
        featureInput = features.createInput(faceColl)
        featureInput.insideThickness = distance
        self.__parent__.feature = features.add(featureInput)
        self.__parent__.featureType = 'shell'
        return self.__parent__.feature
        
    def _derrivativeFeatureChecks(self,obj):
        self.__parent__._parentComponent = self.__parent__.__base__.Utils.getParentFromBRep(obj)

#______ Patterning Features _______
class PatteringOperations(BaseClass):
    def __init__(self):
        BaseClass.__init__(self)
        
    def circularPatternFeature(self,feature, axis = None, n = 6, totalAngle = 360):
        '''
        automates the process of createing a circular pattern inside of a component
        
        feature is a Feature object that is to be patterned
        axis is an object with an axis, if None it will default to the global y axis
        n is the number of feature components
        total angle is the total swept angle in degrees
        
        note: there appears to be a bug in the circular pattern method which creates an
        extra phanotm body in the component tree which doesn't exist in the model
        if you even mouse over that extra body it will crash fusion360
        '''
        totalAngle +=1e-13
        n += 1
        if axis == None:
            axis = self.rootComp.yConstructionAxis
            
        if not isinstance(n,str):
            n = str(n)
        if not isinstance(totalAngle,str):
            totalAngle = str(totalAngle)
        
        totalAngle += ' deg'
        
        #Create a new component to stick the pattern in
        newOcc = self.rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        
        # grab the body from the feature anc create an Assembly Context in the new component
        body = self.Utils.getBodyFromFeature(feature)
        body = body.createForAssemblyContext(newOcc)
        
        # create an assembly contect for the axis as well in the new component
        axis = self.rootComp.yConstructionAxis.createForAssemblyContext(newOcc)
        
        # create an object collection and add the body to it   
        entities = adsk.core.ObjectCollection.create()
        entities.add(body)
        
        # create a circular pattern
        circularPatterns = self.rootComp.features.circularPatternFeatures
        patternInput = circularPatterns.createInput(entities,axis)
        numInstances = adsk.core.ValueInput.createByString(n)
        totalAngle = adsk.core.ValueInput.createByString(totalAngle)
        patternInput.quantity = numInstances
        patternInput.totalAngle = totalAngle
        circularPatterns.add(patternInput)
        return newOcc
        
      
    
        
#_____ Utility Functions ______
class UtilityOperations:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        
    def getBodyFromFeature(self,feature):
        '''
        returns the body associated with a feature
        '''
        faces = feature.faces
        return faces[0].body
        
    def raiseMessage(self,mssg,stopExecution = False):
        self.ui.messageBox(mssg)
        if stopExecution == True:
            raise Exception(mssg)
            
    def raiseError(self):
        self.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
    def youMadeItHere(self,mssg = 'You Made It Here'):
        self.ui.messageBox(mssg)
        
    def calcMidpoint(self,pt1,pt2):
        '''
        calculates the midpoint between two sketchPoint or point3D objects
        
        returns a Point3d object
        '''
        try:
            pt1 = pt1.geometry
        except:
            pass
        
        try:
            pt2 = pt2.geometry
        except:
            pass
        
        return adsk.core.Point3D.create((pt1.x + pt2.x) / 2, (pt1.y + pt2.y) / 2, 0)
        
    def createValueInput(self,dim,dimUnits):
        '''
        creates a value input
        
        dim can be a number or a string
        dimUnits is a string matching the allowed units in the adsk API
        '''
        if not isinstance(dim,str):
            dim = str(dim)
            if dimUnits != None:
                dim += ' ' + dimUnits
        return adsk.core.ValueInput.createByString(dim)
        
    def checkForExistingSketch(self,sketch):
        if sketch is not None:
            raise Exception('Only one sketch per EZSketch instance is allowed, create a new instance to create a new sketch')
            
    def checkForExistingFeatrue(self,feature):
        if feature is not None:
            raise Exception('Only one feature per EZFeature instance is allowed, create a new instance to create a new feature')
            
    def getParentComponentOfProfile(self,profile):
        parentSketch = profile.parentSketch
        return parentSketch.parentComponent
        
    def getParentFromBRep(self,obj):
        if type(obj) is adsk.fusion.BRepBody:
            return obj.parentComponent
        else:
            body = obj.body
            return body.parentComponent
            
    def makeObjectCollection(self,objects):
        objectCollection = adsk.core.ObjectCollection.create()
        for obj in objects:
            objectCollection.add(obj)
            
        return objectCollection
        
    def adskObjectList2PythonList(self,objectList):
        pyList = []
        for i in range(objectList.count):
            pyList.append(objectList.item(i))
        return pyList
        
    def tuple2Point3d(self,tpl):
        for i in tpl:
            if not isinstance(i,(int,float)):
                raise Exception("tuple must contain int or float objects")
        
        if len(tpl) == 2:
            z = 0
            x = tpl[0]
            y = tpl[1]
        elif len(tpl) == 3:
            x = tpl[0]
            y = tpl[1]
            z = tpl[2]
        else:
            raise Exception("tuple must be of length 2 or 3")
            
            
        return adsk.core.Point3D.create(x,y,z)
        
    def handleObjectList2Points(self,lst):
        for i, obj in enumerate(lst):
            if type(obj) is tuple:
                lst[i] = self.tuple2Point3d(obj)
        return lst
                
    def findUnitPerpPoints(self,obj1,obj2=None, lineEnd = 'end'):
        '''
        finds 2 points that are perpendicular to a line
        
        the line can actually be a sketchLine if set to obj1
        otherwise it can be 2 points that define a line from obj1 to obj2
        in this case, obj1 and obj2 can be sketchPoint or point3D objects
        
        lineEnd is the end of the line to find perpendicular unit points
        '''
        if type(obj1) is adsk.fusion.SketchLine:
            if lineEnd == 'end':
                pt1 = obj1.startSketchPoint.geometry
                pt2 = obj1.endSketchPoint.geometry
            else:
                pt2 = obj1.startSketchPoint.geometry
                pt1 = obj1.endSketchPoint.geometry
        elif (type(obj1) is adsk.core.Point3D or type(obj1) is adsk.fusion.SketchPoint) \
            and (type(obj2) is adsk.core.Point3D or type(obj2) is adsk.fusion.SketchPoint):
            
            if lineEnd == 'end':
                try:
                    pt1 = obj1.geometry
                except:
                    pt1 = obj1
                    
                try:
                    pt2 = obj2.geometry
                except:
                    pt2 = obj2
            else:
                try:
                    pt2 = obj1.geometry
                except:
                    pt2 = obj1
                    
                try:
                    pt1 = obj2.geometry
                except:
                    pt1 = obj2
        else:
            raise Exception('Unsupported type')
            
        dx = pt2.x - pt1.x
        dy = pt2.y - pt1.y
        
        length = math.sqrt(dx*dx + dy*dy)
        
        out1 = pt2.copy()
        out2 = pt2.copy()
        
        out1.x += dy/length
        out1.y -= dx/length
        
        out2.x -= dy/length
        out2.y += dx/length
        
        return out1,out2