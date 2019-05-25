# Author-Florian
# Description-Laser cut box.

import math

import adsk.core
import adsk.fusion
import traceback
from .EasyFusionAPI import EZFusionAPI

# values in cm
defaultCaseName = 'Case'
defaultMaterialThickness = 4.0
defaultCaseWidth = 300.0
defaultCaseLength = 200.0
defaultCaseHeight = 100.0

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

class CaseCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            case = Case()
            for input in inputs:
                if input.id == 'name':
                    case.name = input.value
                elif input.id == 'materialThickness':
                    case.materialThickness = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'width':
                    case.width = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'length':
                    case.length = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'height':
                    case.height = unitsMgr.evaluateExpression(input.expression, "mm")

            case.buildCase()
            args.isValidResult = True

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CaseCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CaseCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = CaseCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = CaseCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = CaseCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            # define the inputs
            inputs = cmd.commandInputs
            inputs.addStringValueInput('name', 'Case Name', defaultCaseName)

            initBody = adsk.core.ValueInput.createByReal(defaultMaterialThickness)
            inputs.addValueInput('materialThickness', 'Material Thickness', 'mm', initBody)

            initBody = adsk.core.ValueInput.createByReal(defaultCaseWidth)
            inputs.addValueInput('width', 'Width', 'mm', initBody)

            initBody = adsk.core.ValueInput.createByReal(defaultCaseLength)
            inputs.addValueInput('length', 'Length', 'mm', initBody)

            initBody = adsk.core.ValueInput.createByReal(defaultCaseHeight)
            inputs.addValueInput('height', 'Height', 'mm', initBody)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class Case:
    def __init__(self):
        self._name = defaultCaseName
        self._materialThickness = defaultMaterialThickness
        self._width = defaultCaseWidth
        self._length = defaultCaseLength
        self._height = defaultCaseHeight

    # properties
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def materialThickness(self):
        return self._materialThickness

    @materialThickness.setter
    def materialThickness(self, value):
        self._materialThickness = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    def buildCase(self):
        fa = EZFusionAPI()

        # set parameter names
        materialThicknessParamName = 'MaterialThickness' % self.name
        widthParamName = '%sWidth' % self.name
        lengthParamName = '%sLength' % self.name
        heightParamName = '%sHeight' % self.name

        # set sketch parameters
        fa.create_UserParameter(materialThicknessParamName, self.materialThickness, units='mm', favorite=True)
        fa.create_UserParameter(widthParamName, self.width, units='mm', favorite=True)
        fa.create_UserParameter(lengthParamName, self.length, units='mm', favorite=True)
        fa.create_UserParameter(heightParamName, self.height, units='mm', favorite=True)

        # create base
        basePlateSketch = fa.EZSketch()
        basePlateSketch.create.rectangle([(0, 0), (1, 1)], '2pr', fixPoint=0, expressions=[widthParamName, lengthParamName])
        basePlateSketch.sketch.name = '%sBasePlateSketch' % self.name

        box = fa.EZFeatures()
        box.create.extrude(basePlateSketch.get.profiles()[0], materialThicknessParamName)
        box.feature.name = '%sBasePlate' % self.name


def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
        commandDefinitions = ui.commandDefinitions
        # check the command exists or not
        cmdDef = commandDefinitions.itemById('Case')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('Case',
                                                            'Create Case',
                                                            'Create a case.',
                                                            './resources')  # relative resource file path is specified

        onCommandCreated = CaseCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
