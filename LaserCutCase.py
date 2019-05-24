# Author-Florian
# Description-Laser cut box.

import math

import adsk.core
import adsk.fusion
import traceback

defaultCaseName = 'Case'
defaultMaterialThickness = 4.0
defaultCaseWidth = 300.0
defaultCaseHeight = 300.0

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None


def createNewComponent():
    # Get the active design.
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component


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
                    case.headDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'width':
                    case.bodyDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'height':
                    case.headHeight = unitsMgr.evaluateExpression(input.expression, "mm")

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

    def buildCase(self):
        global newComp
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        xzPlane = newComp.xZConstructionPlane
        sketch = sketches.add(xyPlane)
        center = adsk.core.Point3D.create(0, 0, 0)


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
