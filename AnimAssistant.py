'''
Author :
Alexander Smirnov - onefabis@gmail.com
Version:3.0

To launch the script use this command:
import AnimAssistant
AnimAssistant.start()

'''

import maya.cmds as mc
import os as os
from os.path import dirname, abspath
from functools import partial
from collections import OrderedDict
import maya.mel as mel
import ast
import maya.utils as mu
import maya.OpenMayaUI as omUI

try:
    import PySide.QtGui as QtGui
    import shiboken as shiboken
    from shiboken import wrapInstance
except ImportError:
    import PySide2.QtGui as QtGui
    import PySide2.QtWidgets as QtWidgets
    import shiboken2 as shiboken
    from shiboken2 import wrapInstance


class AnimAssistant(object):
    Lheight = 18
    Fieldheight = 20
    checkboxList = {}
    selectedCameras = []

    def __init__(self):
        pass

    def AnimAssistantUI(self):
        global AAlineNum
        name = 'Anim_Assist'
        nameD = 'AnimAssistDock'
        TFBG = [0.10, 0.10, 0.10]
        self.mayaVer = mc.about(v=1)[3]

        if mc.window(name, ex=1):
            mc.deleteUI(name)
        if mc.dockControl(nameD, ex=1):
            mc.deleteUI(nameD)

        if int(self.mayaVer) < 7:
            self.AMainWindow = mc.window(name, bgc=(0.20, 0.20, 0.20))
        else:
            self.AMainWindow = mc.window(name, bgc=(0.20, 0.20, 0.20), nde=1)

        valDict = {}
        PBDict = {}
        if mc.objExists('AANode'):
            AAData = mc.getAttr('AANode.data')
            PBData = mc.getAttr('AANode.playblast')
            if AAData:
                valDict = ast.literal_eval(AAData)
            if PBData:
                PBDict = ast.literal_eval(PBData)
        else:
            mc.createNode('geometryVarGroup', n='AANode')
            mc.addAttr('AANode', dt='string', ln='data')
            mc.addAttr('AANode', dt='string', ln='playblast')

        try:
            AAlineNum
        except:
            AAlineNum = []

        oDict = OrderedDict(sorted(valDict.items(), key=lambda t: t[0]))
        # Create general form layout that includes scrolllist and common UI elements
        self.generalLayout = mc.formLayout(parent=self.AMainWindow)

        # Create filter form
        self.filterField = mc.textField(h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]), aie=1,
                                        ec=lambda *args: self.filterNames(), p=self.generalLayout)
        mc.popupMenu(p=self.filterField)
        mc.menuItem(l='Clear', c=lambda *args: self.clearFilter())
        # Color range button
        self.rangeColor = mc.iconTextButton(w=16, h=18, bgc=(1, 0, 0), p=self.generalLayout)

        # Create scroll layout for rearrange ability
        self.mScrollLayout = mc.scrollLayout(cr=1, w=100, mcw=100, parent=self.generalLayout)
        mc.popupMenu(p=self.mScrollLayout)
        mc.menuItem(l='Delete', c=partial(self.deleteLines, -1))
        mc.menuItem(l='Store takes', c=partial(self.storeTakes))
        mc.menuItem(l='Export', c=partial(self.exportSetup))
        mc.menuItem(l='Import', c=partial(self.importSetup))

        # Generate list
        self.colDict = {}
        if len(oDict) > 0:
            for k, v in oDict.iteritems():
                self.revealNewLine(k, v[0], v[1], v[2], v[3])
        self.addNewLine('create')

        # Common UI elements

        # Manage section
        self.nameTextField = mc.textField(h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                          cc=lambda *args: self.editLineFields('name'),
                                          rfc=lambda *args: self.restoreButtons('edit'), p=self.generalLayout)
        self.moveUpButton = mc.button(l='^', w=20, h=21, c=partial(self.moveLines, 'up'), p=self.generalLayout)
        mc.popupMenu(p=self.moveUpButton)
        mc.menuItem(l='To the top', c=partial(self.moveLines, 'upTop'))
        self.moveDownButton = mc.button(l='v', w=20, h=21, c=partial(self.moveLines, 'down'), p=self.generalLayout)
        mc.popupMenu(p=self.moveDownButton)
        mc.menuItem(l='To the bottom', c=partial(self.moveLines, 'downBottom'))
        self.addButton = mc.button(l='+', w=20, h=21, c=lambda *args: self.revealNewLine(-100, None, None, None, None),
                                   p=self.generalLayout)
        self.removeButton = mc.button(l='-', w=20, h=21, c=partial(self.deleteLines, -1), p=self.generalLayout)

        # Get initial color data
        if mc.optionVar(ex='AAInitColor'):
            commonColor = mc.optionVar(q='AAInitColor')
        else:
            commonColor = [0.36, 0.36, 0.36]
            mc.optionVar(fv=('AAInitColor', 0.36))
            mc.optionVar(fva=('AAInitColor', 0.36))
            mc.optionVar(fva=('AAInitColor', 0.36))
        # Color button
        self.commonColor = mc.iconTextButton(w=16, h=self.Lheight, bgc=(commonColor[0], commonColor[1], commonColor[2]),
                                             p=self.generalLayout)

        self.startTextField = mc.textField(w=40, h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                           cc=lambda *args: self.editLineFields('start'),
                                           rfc=lambda *args: self.restoreButtons('edit'), p=self.generalLayout)
        mc.popupMenu(p=self.startTextField)
        mc.menuItem(l='Start', c=partial(self.insertFieldsFrames, 'sF', 'start'))
        mc.menuItem(l='End', c=partial(self.insertFieldsFrames, 'sF', 'end'))
        mc.menuItem(l='Current', c=partial(self.insertFieldsFrames, 'sF', 'current'))
        mc.menuItem(l='Both', c=partial(self.insertFieldsFrames, 'sF', 'both'))

        self.endTextField = mc.textField(w=40, h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                         cc=lambda *args: self.editLineFields('end'),
                                         rfc=lambda *args: self.restoreButtons('edit'), p=self.generalLayout)
        mc.popupMenu(p=self.endTextField)
        mc.menuItem(l='Start', c=partial(self.insertFieldsFrames, 'eF', 'start'))
        mc.menuItem(l='End', c=partial(self.insertFieldsFrames, 'eF', 'end'))
        mc.menuItem(l='Current', c=partial(self.insertFieldsFrames, 'eF', 'current'))
        mc.menuItem(l='Both', c=partial(self.insertFieldsFrames, 'eF', 'both'))
        mc.menuItem(l='Both', c=partial(self.insertFieldsFrames, 'eF', 'both'))
        mc.menuItem(l='Both', c=partial(self.insertFieldsFrames, 'eF', 'both'))

        # Playblast section
        self.PBsep = mc.separator(style='in', p=self.generalLayout)
        self.PBpathTextField = mc.textField(h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                            cc=partial(self.playBlastData),
                                            rfc=lambda *args: self.restoreButtons('edit'), p=self.generalLayout)
        self.PBbrowseButton = mc.button(l='Browse', w=51, h=19, c=partial(self.browsePB), p=self.generalLayout)

        self.PBpreTextField = mc.textField(w=45, h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                           cc=partial(self.playBlastData),
                                           rfc=lambda *args: self.restoreButtons('edit'), p=self.generalLayout)
        self.PBprepostText = mc.text(w=40, h=self.Lheight, l='- name -', p=self.generalLayout)
        self.PBpostTextField = mc.textField(w=45, h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                            cc=partial(self.playBlastData),
                                            rfc=lambda *args: self.restoreButtons('edit'), p=self.generalLayout)
        self.PBblastButton = mc.button(l='Playblast', w=51, h=19, c=partial(self.playBlastCom, 'separate'),
                                       p=self.generalLayout)
        mc.popupMenu(p=self.PBblastButton)
        mc.menuItem(l='Merge selected', c=partial(self.playBlastCom, 'merge'))
        mc.menuItem(l='Playblast setup', c=partial(self.playBlastCom, 'setup'))
        self.PBcamTextField = mc.textField(w=45, h=self.Fieldheight, bgc=(TFBG[0], TFBG[1], TFBG[2]),
                                           cc=partial(self.playBlastData), p=self.generalLayout)
        self.PBcamPopMenu = mc.popupMenu(pmc=lambda *x: self.findCamera(), p=self.PBcamTextField)

        # Layout common UI elements inside general layout

        mc.formLayout(self.generalLayout, e=1, af=(self.filterField, 'top', 2))
        mc.formLayout(self.generalLayout, e=1, af=(self.filterField, 'left', 1))
        mc.formLayout(self.generalLayout, e=1, ac=(self.filterField, 'right', 2, self.rangeColor))

        mc.formLayout(self.generalLayout, e=1, af=(self.rangeColor, 'top', 3))
        mc.formLayout(self.generalLayout, e=1, af=(self.rangeColor, 'right', 2))

        mc.formLayout(self.generalLayout, e=1, ac=(self.mScrollLayout, 'top', 0, self.filterField))
        mc.formLayout(self.generalLayout, e=1, af=(self.mScrollLayout, 'left', 0))
        mc.formLayout(self.generalLayout, e=1, af=(self.mScrollLayout, 'right', 0))
        mc.formLayout(self.generalLayout, e=1, ac=(self.mScrollLayout, 'bottom', 2, self.nameTextField))

        mc.formLayout(self.generalLayout, e=1, af=(self.nameTextField, 'left', 1))
        mc.formLayout(self.generalLayout, e=1, af=(self.nameTextField, 'right', 2))
        mc.formLayout(self.generalLayout, e=1, ac=(self.nameTextField, 'bottom', 2, self.moveUpButton))

        mc.formLayout(self.generalLayout, e=1, af=(self.moveUpButton, 'left', 2))
        mc.formLayout(self.generalLayout, e=1, ac=(self.moveUpButton, 'bottom', 4, self.PBsep))
        mc.formLayout(self.generalLayout, e=1, ac=(self.moveDownButton, 'left', 2, self.moveUpButton))
        mc.formLayout(self.generalLayout, e=1, ac=(self.moveDownButton, 'bottom', 4, self.PBsep))
        mc.formLayout(self.generalLayout, e=1, ac=(self.addButton, 'left', 2, self.moveDownButton))
        mc.formLayout(self.generalLayout, e=1, ac=(self.addButton, 'bottom', 4, self.PBsep))
        mc.formLayout(self.generalLayout, e=1, ac=(self.removeButton, 'left', 2, self.addButton))
        mc.formLayout(self.generalLayout, e=1, ac=(self.removeButton, 'bottom', 4, self.PBsep))

        mc.formLayout(self.generalLayout, e=1, ac=(self.commonColor, 'right', 2, self.startTextField))
        mc.formLayout(self.generalLayout, e=1, ac=(self.commonColor, 'bottom', 6, self.PBsep))

        mc.formLayout(self.generalLayout, e=1, ac=(self.startTextField, 'right', 1, self.endTextField))
        mc.formLayout(self.generalLayout, e=1, ac=(self.startTextField, 'bottom', 5, self.PBsep))
        mc.formLayout(self.generalLayout, e=1, af=(self.endTextField, 'right', 2))
        mc.formLayout(self.generalLayout, e=1, ac=(self.endTextField, 'bottom', 5, self.PBsep))

        mc.formLayout(self.generalLayout, e=1, af=(self.PBsep, 'left', 0))
        mc.formLayout(self.generalLayout, e=1, af=(self.PBsep, 'right', 0))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBsep, 'bottom', 2, self.PBpathTextField))

        mc.formLayout(self.generalLayout, e=1, af=(self.PBpathTextField, 'left', 2))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBpathTextField, 'right', 2, self.PBbrowseButton))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBpathTextField, 'bottom', 2, self.PBpreTextField))

        mc.formLayout(self.generalLayout, e=1, af=(self.PBbrowseButton, 'right', 3))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBbrowseButton, 'bottom', 2, self.PBpreTextField))

        mc.formLayout(self.generalLayout, e=1, af=(self.PBpreTextField, 'left', 2))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBpreTextField, 'bottom', 3, self.PBcamTextField))

        mc.formLayout(self.generalLayout, e=1, ac=(self.PBprepostText, 'bottom', 4, self.PBcamTextField))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBprepostText, 'left', 0, self.PBpreTextField))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBprepostText, 'right', 0, self.PBpostTextField))

        mc.formLayout(self.generalLayout, e=1, ac=(self.PBpostTextField, 'bottom', 3, self.PBcamTextField))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBpostTextField, 'right', 2, self.PBblastButton))

        mc.formLayout(self.generalLayout, e=1, af=(self.PBblastButton, 'right', 3))
        mc.formLayout(self.generalLayout, e=1, ac=(self.PBblastButton, 'bottom', 3, self.PBcamTextField))

        mc.formLayout(self.generalLayout, e=1, af=(self.PBcamTextField, 'bottom', 3))
        mc.formLayout(self.generalLayout, e=1, af=(self.PBcamTextField, 'right', 2))
        mc.formLayout(self.generalLayout, e=1, af=(self.PBcamTextField, 'left', 2))

        counter = 0
        for k in mc.listCameras():
            self.currentCameraControl = mc.checkBox(label=k, align='left', p=self.generalLayout);
            self.checkboxList[k] = self.currentCameraControl
            if counter == 0:
                mc.formLayout(self.generalLayout, e=1, ac=(self.PBcamTextField, 'bottom', 2, self.currentCameraControl))
            else:
                mc.formLayout(self.generalLayout, e=1, ac=(prevCameraControl, 'bottom', 2, self.currentCameraControl))

            mc.formLayout(self.generalLayout, e=1, af=(self.currentCameraControl, 'bottom', 3))
            mc.formLayout(self.generalLayout, e=1, af=(self.currentCameraControl, 'right', 3))
            mc.formLayout(self.generalLayout, e=1, af=(self.currentCameraControl, 'left', 3))


            prevCameraControl = self.currentCameraControl
            counter += 1
            # mc.formLayout(self.generalLayout, e=1, ac=( self.mScrollLayout, 'top', 2, self.CameraControl ) )

        # Change the basic color sheme
        if int(self.mayaVer) < 7:
            # Change color button in filter section
            rangeColor = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.rangeColor)), QtGui.QPushButton)

            # Change buttons color in manage section
            moveUpButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.moveUpButton)), QtGui.QPushButton)
            moveDownButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.moveDownButton)),
                                                   QtGui.QPushButton)
            addButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addButton)), QtGui.QPushButton)
            removeButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.removeButton)), QtGui.QPushButton)
            commonColor = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.commonColor)), QtGui.QPushButton)

            # Change text field style in manage section
            NameTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.nameTextField)), QtGui.QLineEdit)
            StartTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.startTextField)), QtGui.QLineEdit)
            EndTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.endTextField)), QtGui.QLineEdit)

            # Change buttons color in playblast section
            PBlastB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBblastButton)), QtGui.QPushButton)
            PBrowseB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBbrowseButton)), QtGui.QPushButton)
            PPrepostTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBprepostText)), QtGui.QLabel)

            # Change text field style in playblast section
            PathTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBpathTextField)), QtGui.QLineEdit)
            PathTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
            PreTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBpreTextField)), QtGui.QLineEdit)
            PreTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
            PostTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBpostTextField)), QtGui.QLineEdit)
            PostTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
            CamTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBcamTextField)), QtGui.QLineEdit)
            CamTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
        else:
            # Change color button in filter section
            rangeColor = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.rangeColor)), QtWidgets.QPushButton)

            # Change buttons color in manage section
            moveUpButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.moveUpButton)),
                                                 QtWidgets.QPushButton)
            moveDownButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.moveDownButton)),
                                                   QtWidgets.QPushButton)
            addButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addButton)), QtWidgets.QPushButton)
            removeButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.removeButton)),
                                                 QtWidgets.QPushButton)
            commonColor = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.commonColor)), QtWidgets.QPushButton)

            # Change text field style in manage section
            NameTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.nameTextField)), QtWidgets.QLineEdit)
            StartTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.startTextField)), QtWidgets.QLineEdit)
            EndTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.endTextField)), QtWidgets.QLineEdit)

            # Change buttons color in playblast section
            PBlastB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBblastButton)), QtWidgets.QPushButton)
            PBrowseB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBbrowseButton)), QtWidgets.QPushButton)
            PPrepostTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBprepostText)), QtWidgets.QLabel)

            # Change text field style in playblast section
            PathTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBpathTextField)), QtWidgets.QLineEdit)
            PreTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBpreTextField)), QtWidgets.QLineEdit)
            PostTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBpostTextField)), QtWidgets.QLineEdit)
            CamTF = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.PBcamTextField)), QtWidgets.QLineEdit)

        # Change color button in filter section
        rangeColor.setStyleSheet(
            'QPushButton { border-radius: 2px; border: 1px solid #4f4d49; background-color: rgb(255,0,0) }')

        # Change buttons color in manage section
        moveUpButton.setStyleSheet(
            'QPushButton { border: 1px solid #091b30 ; background-color: #1c3b5d; color: #a6c0dc } QPushButton:hover{background-color: #1f518a; } QPushButton:pressed{ background-color: #112741; } ')
        moveDownButton.setStyleSheet(
            'QPushButton { border: 1px solid #091b30 ; background-color: #1c3b5d; color: #a6c0dc } QPushButton:hover{background-color: #1f518a; } QPushButton:pressed{ background-color: #112741; } ')
        addButton.setStyleSheet(
            'QPushButton { border: 1px solid #0a2b04 ; background-color: #27541e; color: #a8d79f } QPushButton:hover{background-color: #2c711f; } QPushButton:pressed{ background-color: #183811; } ')
        removeButton.setStyleSheet(
            'QPushButton { border: 1px solid #4f1306 ; color: #d8b2a9; background-color: #8f2d18; } QPushButton:hover{background-color: #b42e11; } QPushButton:pressed{ background-color: #642010; } ')
        commonColor.setStyleSheet('QPushButton { border-radius: 2px; border: 1px solid #4f4d49 }')

        # Change text field style in manage section
        NameTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
        StartTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
        EndTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')

        # Change buttons color in playblast section
        PBlastB.setStyleSheet(
            'QPushButton {border: 1px solid #0c2d05; background-color: #27541e; color: #a8d79f} QPushButton:hover{background-color: #2c711f; } QPushButton:pressed{ background-color: #183811; } ')
        PBrowseB.setStyleSheet(
            'QPushButton {border: 1px solid #321707; background-color: #7e3910; color: #d6bcad} QPushButton:hover{background-color: #9a430f; } QPushButton:pressed{ background-color: #582a0f; }')
        PPrepostTF.setStyleSheet('QLabel {color: #9b9b9b;} ')

        # Change text field style in playblast section
        PathTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
        PreTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
        PostTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')
        CamTF.setStyleSheet('QLineEdit {color: #a9a7a3; border-radius: 2px; border: 1px solid #393939;} ')

        # Add initial data to the fields
        try:
            if len(AAlineNum) == 1:
                num = AAlineNum[0]
                nameB = mc.iconTextButton(self.colDict['self.nameButton' + str(num)], q=1, l=1)
                startB = mc.iconTextButton(self.colDict['self.startFrame' + str(num)], q=1, l=1)
                if startB.lstrip('0') == '':
                    startB = 0
                else:
                    startB = startB.lstrip('0')
                endB = mc.iconTextButton(self.colDict['self.endFrame' + str(num)], q=1, l=1)
                if endB.lstrip('0') == '':
                    endB = 0
                else:
                    endB = endB.lstrip('0')
                mc.textField(self.nameTextField, e=1, tx=nameB)
                mc.textField(self.startTextField, e=1, tx=startB)
                mc.textField(self.endTextField, e=1, tx=endB)
        except:
            pass

        if len(PBDict) > 0:
            for k, v in PBDict.iteritems():
                mc.textField(self.PBpathTextField, e=1, tx=k)
                mc.textField(self.PBpreTextField, e=1, tx=v[0])
                mc.textField(self.PBpostTextField, e=1, tx=v[1])
        # Dock initial data
        if mc.optionVar(ex=('AADockState')):
            floatState = mc.optionVar(q='AADockState')
        else:
            mc.optionVar(iv=('AADockState', 0))
            floatState = 0

        if mc.optionVar(ex=('AADockArea')):
            dockArea = mc.optionVar(q='AADockArea')
        else:
            mc.optionVar(sv=('AADockArea', 'left'))
            dockArea = 'left'

        if mc.optionVar(ex='AADockHeight'):
            dockHeight = mc.optionVar(q='AADockHeight')
        else:
            mc.optionVar(iv=('AADockHeight', 200))
            dockHeight = 200

        self.dockWin = mc.dockControl(nameD, area=dockArea, w=230, fl=floatState, content=self.AMainWindow,
                                      h=dockHeight, fcc=partial(self.changeDockState), l=nameD, aa=('left', 'right'))

        global openAAScrJob
        try:
            openAAScrJob
        except:
            openAAScrJob = mc.scriptJob(event=("SceneOpened", "import AnimAssistant; AnimAssistant.start()"))

    # Function to refresh cameras
    def findCamera(self):
        camera = mc.ls(typ='camera')
        mc.popupMenu(self.PBcamPopMenu, e=1, dai=1)
        for c in camera:
            camName = mc.listRelatives(c, p=1)[0]
            mc.menuItem(l=camName, p=self.PBcamPopMenu, c=partial(self.addCamName, camName))

    def addCamName(self, camName, part):
        mc.textField(self.PBcamTextField, e=1, tx=camName)

    # Function to tobble buttons and text fields visibility with transfering labels to the text of the textfield

    def changeName(self, name, button):

        self.restoreButtons('edit')

        # Displays the 'name' text field with preserves the label inside the TF and hides the button
        if button == 'name':
            mc.iconTextButton(self.colDict['self.nameButton' + str(name)], e=1, vis=0)
            nameCTf = mc.iconTextButton(self.colDict['self.nameButton' + str(name)], q=1, l=1)
            mc.setFocus(self.colDict['self.nameTextField' + str(name)])
            mc.textField(self.colDict['self.nameTextField' + str(name)], e=1, vis=1, tx=nameCTf)

        # Displays the 'start frame' text field with preserves the label inside the TF and hides the button
        elif button == 'sframe':

            startCTf = mc.iconTextButton(self.colDict['self.startFrame' + str(name)], q=1, l=1)
            mc.setFocus(self.colDict['self.startTextField' + str(name)])
            mc.textField(self.colDict['self.startTextField' + str(name)], e=1, vis=1, tx=startCTf.lstrip("0"))
            mc.formLayout(self.colDict['self.formFrames' + str(name)], e=1, ac=(
            self.colDict['self.framesDash' + str(name)], 'left', 0, self.colDict['self.startTextField' + str(name)]))
        # mc.iconTextButton( self.colDict[ 'self.startFrame' + str(name) ], e=1, vis=0 )

        # Displays the 'end frame' text field with preserves the label inside the TF and hides the button
        else:
            mc.iconTextButton(self.colDict['self.endFrame' + str(name)], e=1, vis=0)
            endCTf = mc.iconTextButton(self.colDict['self.endFrame' + str(name)], q=1, l=1)
            mc.setFocus(self.colDict['self.endTextField' + str(name)])
            mc.textField(self.colDict['self.endTextField' + str(name)], e=1, vis=1, tx=endCTf.lstrip("0"))

    def restoreButtons(self, mode):
        # Detecs the count of the childs in scroll Layout
        filterName = mc.textField(self.filterField, q=1, tx=1)
        valDict = {}
        if mc.objExists('AANode'):
            AAData = mc.getAttr('AANode.data')
            if AAData:
                valDict = ast.literal_eval(AAData)

        filteredDict = {}
        keyIndex = []
        if filterName:
            if len(filterName) > 1 and filterName[0] == '*' and filterName[-1] != '*':
                for k, v in valDict.iteritems():
                    if v[0].endswith(filterName[1:]):
                        filteredDict[k] = v
                        keyIndex.append(k)
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] != '*':
                for k, v in valDict.iteritems():
                    if v[0].startswith(filterName[:-1]):
                        filteredDict[k] = v
                        keyIndex.append(k)
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] == '*':
                for k, v in valDict.iteritems():
                    if filterName[1:-1] in v[0]:
                        filteredDict[k] = v
                        keyIndex.append(k)
            elif len(filterName) == 1 and filterName == '*':
                pass
            else:
                for k, v in valDict.iteritems():
                    if v[0] == filterName:
                        filteredDict[k] = v
                        keyIndex.append(k)
        else:
            for k, v in valDict.iteritems():
                filteredDict[k] = v
                keyIndex.append(k)

        # Restoring visibility state of every element in the list
        for i in keyIndex:

            # Restoring 'name' buttons and text fields
            mc.textField(self.colDict['self.nameTextField' + str(i)], e=1, vis=0)
            nameTf = mc.textField(self.colDict['self.nameTextField' + str(i)], q=1, tx=1)
            if nameTf:
                mc.iconTextButton(self.colDict['self.nameButton' + str(i)], e=1, l=nameTf)
            mc.iconTextButton(self.colDict['self.nameButton' + str(i)], e=1, vis=1)
            mc.iconTextButton(self.colDict['self.nameSpaceButton' + str(i)], e=1, vis=1)

            # Restoring 'start frame' buttons and text fields
            mc.textField(self.colDict['self.startTextField' + str(i)], e=1, vis=0)
            startTf = mc.textField(self.colDict['self.startTextField' + str(i)], q=1, tx=1)
            if startTf:
                mc.iconTextButton(self.colDict['self.startFrame' + str(i)], e=1, l=startTf.zfill(4))
            mc.iconTextButton(self.colDict['self.startFrame' + str(i)], e=1, vis=1)
            mc.formLayout(self.colDict['self.formFrames' + str(i)], e=1, ac=(
            self.colDict['self.framesDash' + str(i)], 'left', 0, self.colDict['self.startFrame' + str(i)]))

            # Restoring 'end frame' buttons and text fields
            mc.textField(self.colDict['self.endTextField' + str(i)], e=1, vis=0)
            endTf = mc.textField(self.colDict['self.endTextField' + str(i)], q=1, tx=1)
            if endTf:
                mc.iconTextButton(self.colDict['self.endFrame' + str(i)], e=1, l=endTf.zfill(4))
            mc.iconTextButton(self.colDict['self.endFrame' + str(i)], e=1, vis=1)

            qName = mc.iconTextButton(self.colDict['self.nameButton' + str(i)], q=1, l=1)
            qStart = mc.iconTextButton(self.colDict['self.startFrame' + str(i)], q=1, l=1)
            qEnd = mc.iconTextButton(self.colDict['self.endFrame' + str(i)], q=1, l=1)

            for k, v in filteredDict.iteritems():
                if k == i:
                    if v[1] != qStart:
                        filteredDict[k][1] = qStart
                    if v[2] != qEnd:
                        filteredDict[k][2] = qEnd
                    if v[0] != qName:
                        filteredDict[k][0] = qName
            if mode == 'edit':
                qName = mc.iconTextButton(self.colDict['self.nameButton' + str(i)], q=1, l=1)
                qStart = mc.iconTextButton(self.colDict['self.startFrame' + str(i)], q=1, l=1)
                qEnd = mc.iconTextButton(self.colDict['self.endFrame' + str(i)], q=1, l=1)
                qColor = mc.iconTextButton(self.colDict['self.canvasLine' + str(i)], q=1, bgc=1)
                filteredDict[i] = [qName, qStart, qEnd, (qColor[0], qColor[1], qColor[2])]
            elif mode == 'add' and keyIndex > 1:
                qName = mc.iconTextButton(self.colDict['self.nameButton' + str(i)], q=1, l=1)
                qStart = mc.iconTextButton(self.colDict['self.startFrame' + str(i)], q=1, l=1)
                qEnd = mc.iconTextButton(self.colDict['self.endFrame' + str(i)], q=1, l=1)
                qColor = mc.iconTextButton(self.colDict['self.canvasLine' + str(i)], q=1, bgc=1)
                filteredDict[i] = [qName, qStart, qEnd, (qColor[0], qColor[1], qColor[2])]

        mc.setAttr('AANode.data', valDict, type='string')

    # Hides the current clicked button and reveals the textfield with entered label of the button inside
    def editName(self, name, button, part):
        global AAlineNum
        valDict = {}
        chExist = ''
        chName = 0
        AAData = mc.getAttr('AANode.data')
        if AAData is not None and len(AAData) > 0:
            valDict = ast.literal_eval(AAData)
        for k, v in valDict.iteritems():
            if name == k:
                chName = k
                chExist = v[0]
                break

        if button == 'name':
            nValue = mc.textField(self.colDict['self.nameTextField' + str(name)], q=1, tx=1)
            if nValue == '':
                nValue = mc.iconTextButton(self.colDict['self.nameButton' + str(name)], q=1, l=1)
            sValue = mc.iconTextButton(self.colDict['self.startFrame' + str(name)], q=1, l=1)
            eValue = mc.iconTextButton(self.colDict['self.endFrame' + str(name)], q=1, l=1)
            mc.iconTextButton(self.colDict['self.nameButton' + str(name)], e=1, vis=1, l=nValue)
            mc.textField(self.colDict['self.nameTextField' + str(name)], e=1, vis=0)
            # mc.iconTextButton( self.colDict[ 'self.nameSpaceButton' + str(name) ], e=1, vis=1 )
            if chExist != '':
                valDict[chName][0] = chExist
            else:
                valDict[name] = [nValue, sValue, eValue, (0.16, 0.16, 0.16)]
            # Paste new name in the 'name' text field
            if AAlineNum and len(AAlineNum) == 1:
                if AAlineNum[0] == name:
                    mc.textField(self.nameTextField, e=1, tx=nValue)

        elif button == 'sframe':
            nValue = mc.iconTextButton(self.colDict['self.nameButton' + str(name)], q=1, l=1)
            sValue = mc.textField(self.colDict['self.startTextField' + str(name)], q=1, tx=1)
            eValue = mc.iconTextButton(self.colDict['self.endFrame' + str(name)], q=1, l=1)
            mc.iconTextButton(self.colDict['self.startFrame' + str(name)], e=1, vis=1, l=sValue.zfill(4))
            mc.textField(self.colDict['self.startTextField' + str(name)], e=1, vis=0)
            mc.formLayout(self.colDict['self.formFrames' + str(name)], e=1, ac=(
            self.colDict['self.framesDash' + str(name)], 'left', 0, self.colDict['self.startFrame' + str(name)]))
            if chExist != '':
                valDict[chName][1] = sValue
            # Paste new start frame in the 'start' text field
            if AAlineNum and len(AAlineNum) == 1:
                if AAlineNum[0] == name:
                    mc.textField(self.startTextField, e=1, tx=sValue)
        else:
            nValue = mc.iconTextButton(self.colDict['self.nameButton' + str(name)], q=1, l=1)
            sValue = mc.iconTextButton(self.colDict['self.startFrame' + str(name)], q=1, l=1)
            eValue = mc.textField(self.colDict['self.endTextField' + str(name)], q=1, tx=1)
            mc.iconTextButton(self.colDict['self.endFrame' + str(name)], e=1, vis=1, l=eValue.zfill(4))
            mc.textField(self.colDict['self.endTextField' + str(name)], e=1, vis=0)
            if chExist != '':
                valDict[chName][2] = eValue

            # Paste new end frame in the 'end' text field
            if AAlineNum and len(AAlineNum) == 1:
                if AAlineNum[0] == name:
                    mc.textField(self.endTextField, e=1, tx=eValue)
        '''
        if chExist =='':
            valDict[chName] = [nValue, sValue, eValue,(0.16,0.16,0.16)]
        '''

        mc.setAttr('AANode.data', valDict, type='string')

    # Highlight selected items, i.e. make the font weight - bold
    def selectHighlight(self, mode, num):

        filterName = mc.textField(self.filterField, q=1, tx=1)

        valDict = {}
        if mc.objExists('AANode'):
            AAData = mc.getAttr('AANode.data')
            if AAData:
                valDict = ast.literal_eval(AAData)

        filteredDict = {}
        keyIndex = []
        if filterName:
            if len(filterName) > 1 and filterName[0] == '*' and filterName[-1] != '*':
                for k, v in valDict.iteritems():
                    if v[0].endswith(filterName[1:]):
                        filteredDict[k] = v
                        keyIndex.append(k)
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] != '*':
                for k, v in valDict.iteritems():
                    if v[0].startswith(filterName[:-1]):
                        filteredDict[k] = v
                        keyIndex.append(k)
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] == '*':
                for k, v in valDict.iteritems():
                    if filterName[1:-1] in v[0]:
                        filteredDict[k] = v
                        keyIndex.append(k)
            elif len(filterName) == 1 and filterName == '*':
                pass
            else:
                for k, v in valDict.iteritems():
                    if v[0] == filterName:
                        filteredDict[k] = v
                        keyIndex.append(k)
        else:
            for k, v in valDict.iteritems():
                filteredDict[k] = v
                keyIndex.append(k)

        mu.executeDeferred(self.restoreButtons('edit'))

        gMod = mc.getModifiers()
        global AAlineNum
        try:
            if AAlineNum:
                pass
        except:
            AAlineNum = []
        if gMod == 4:
            if num in AAlineNum:
                AAlineNum.remove(num)
            else:
                AAlineNum.append(num)
        elif gMod == 0:
            AAlineNum = []
            AAlineNum.append(num)
        elif gMod == 1:
            maxLine = max(AAlineNum)
            minLine = min(AAlineNum)
            if num < minLine:
                rangeFromMin = list(xrange(num, minLine))
                AAlineNum.extend(rangeFromMin)
            elif num > maxLine:
                rangeFromMax = list(xrange(maxLine, num + 1))
                AAlineNum.extend(rangeFromMax)

        for i in keyIndex:
            mc.iconTextButton(self.colDict['self.lineNumber' + str(i)], e=1, l="   " + str(i).zfill(3))

        self.restyleButtons(keyIndex, 'regular')

        if num > -1:
            for a in AAlineNum:
                mc.iconTextButton(self.colDict['self.lineNumber' + str(a)], e=1, l="> " + str(a).zfill(3))

        self.restyleButtons(AAlineNum, 'bold')

        # Change the range if mode 'range' set
        if mode == 'range' and AAlineNum:
            minRange = []
            maxRange = []
            for a in AAlineNum:
                minRange.append(mc.iconTextButton(self.colDict['self.startFrame' + str(a)], q=1, l=1))
                maxRange.append(mc.iconTextButton(self.colDict['self.endFrame' + str(a)], q=1, l=1))
            if min(minRange) != max(maxRange) and min(minRange) < max(maxRange):
                mc.playbackOptions(min=min(minRange), max=max(maxRange))

        if len(AAlineNum) == 1 and AAlineNum[0] >= 0:
            nValue = mc.iconTextButton(self.colDict['self.nameButton' + str(AAlineNum[0])], q=1, l=1)
            sValue = mc.iconTextButton(self.colDict['self.startFrame' + str(AAlineNum[0])], q=1, l=1)
            eValue = mc.iconTextButton(self.colDict['self.endFrame' + str(AAlineNum[0])], q=1, l=1)
            mc.textField(self.nameTextField, e=1, tx=nValue)
            mc.textField(self.startTextField, e=1, tx=(0 if sValue.lstrip("0") == '' else sValue.lstrip("0")))
            mc.textField(self.endTextField, e=1, tx=(0 if eValue.lstrip("0") == '' else eValue.lstrip("0")))

        else:
            mc.textField(self.nameTextField, e=1, tx='')
            mc.textField(self.startTextField, e=1, tx='')
            mc.textField(self.endTextField, e=1, tx='')

    def restyleButtons(self, nums, mode):
        if mode == 'bold':
            fontWeight = 'bold'
            color = 'white'
        else:
            fontWeight = 'normal'
            color = '#d6d6d6'
        for n in nums:
            if n >= 0:
                if int(self.mayaVer) < 7:
                    # Re-style 'name' button
                    self.colDict['self.nameButtonSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.nameButton' + str(n)])), QtGui.QPushButton)
                    # Re-style 'line number' button
                    self.colDict['self.lineNumberSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.lineNumber' + str(n)])), QtGui.QPushButton)
                    # Re-style 'spacer' button
                    self.colDict['self.nameSpaceButtonSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.nameSpaceButton' + str(n)])),
                        QtGui.QPushButton)
                    # Re-style 'start frame' button
                    self.colDict['self.startFrameSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.startFrame' + str(n)])), QtGui.QPushButton)
                    # Re-style 'dash' button
                    self.colDict['self.framesDashSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.framesDash' + str(n)])), QtGui.QPushButton)
                    # Re-style 'end frame' button
                    self.colDict['self.endFrameSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.endFrame' + str(n)])), QtGui.QPushButton)
                else:
                    # Re-style 'name' button
                    self.colDict['self.nameButtonSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.nameButton' + str(n)])), QtWidgets.QPushButton)
                    # Re-style 'line number' button
                    self.colDict['self.lineNumberSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.lineNumber' + str(n)])), QtWidgets.QPushButton)
                    # Re-style 'spacer' button
                    self.colDict['self.nameSpaceButtonSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.nameSpaceButton' + str(n)])),
                        QtWidgets.QPushButton)
                    # Re-style 'start frame' button
                    self.colDict['self.startFrameSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.startFrame' + str(n)])), QtWidgets.QPushButton)
                    # Re-style 'dash' button
                    self.colDict['self.framesDashSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.framesDash' + str(n)])), QtWidgets.QPushButton)
                    # Re-style 'end frame' button
                    self.colDict['self.endFrameSt' + str(n)] = shiboken.wrapInstance(
                        long(omUI.MQtUtil.findControl(self.colDict['self.endFrame' + str(n)])), QtWidgets.QPushButton)

                self.colDict['self.nameButtonSt' + str(n)].setStyleSheet(
                    'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
                self.colDict['self.lineNumberSt' + str(n)].setStyleSheet(
                    'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
                self.colDict['self.nameSpaceButtonSt' + str(n)].setStyleSheet(
                    'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
                self.colDict['self.startFrameSt' + str(n)].setStyleSheet(
                    'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
                self.colDict['self.framesDashSt' + str(n)].setStyleSheet(
                    'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
                self.colDict['self.endFrameSt' + str(n)].setStyleSheet(
                    'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')

    # Changes the color of the line
    def changeColor(self, num):
        mc.colorEditor()
        valDict = {}
        value = False
        AAData = mc.getAttr('AANode.data')
        if len(AAData) > 0:
            valDict = ast.literal_eval(AAData)
        global AAlineNum
        try:
            if AAlineNum:
                pass
        except:
            AAlineNum = []
        if mc.colorEditor(q=1, r=1):
            value = mc.colorEditor(q=1, rgb=1)

        filterName = mc.textField(self.filterField, q=1, tx=1)

        keyIndex = []
        if filterName:
            if len(filterName) > 1 and filterName[0] == '*' and filterName[-1] != '*':
                for k, v in valDict.iteritems():
                    if v[0].endswith(filterName[1:]):
                        keyIndex.append(k)
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] != '*':
                for k, v in valDict.iteritems():
                    if v[0].startswith(filterName[:-1]):
                        keyIndex.append(k)
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] == '*':
                for k, v in valDict.iteritems():
                    if filterName[1:-1] in v[0]:
                        keyIndex.append(k)
            elif len(filterName) == 1 and filterName == '*':
                pass
            else:
                for k, v in valDict.iteritems():
                    if v[0] == filterName:
                        keyIndex.append(k)
        else:
            for k, v in valDict.iteritems():
                keyIndex.append(k)

        filteredNum = set(keyIndex).intersection(AAlineNum)

        # Set the color value for the color picker
        if value:
            if num in filteredNum:
                for i in filteredNum:
                    mc.formLayout(self.colDict['self.formLine' + str(i)], e=1, bgc=(value[0], value[1], value[2]))
                    mc.iconTextButton(self.colDict['self.canvasLine' + str(i)], e=1, bgc=(value[0], value[1], value[2]))
                    for k, v in valDict.iteritems():
                        if i == k:
                            valDict[k][3] = (value[0], value[1], value[2])
            else:
                mc.formLayout(self.colDict['self.formLine' + str(num)], e=1, bgc=(value[0], value[1], value[2]))
                mc.iconTextButton(self.colDict['self.canvasLine' + str(num)], e=1, bgc=(value[0], value[1], value[2]))
            # valDict[k][3]=( value[0], value[1], value[2] )
            mc.setAttr('AANode.data', valDict, type='string')

    # Universal function for adding new empty or filled line
    def revealNewLine(self, num, name, start, end, color):
        global AAlineNum
        tempLine = None
        try:
            # Query the text inside 'name' textField
            textFieldName = mc.textField(self.nameTextField, q=1, tx=1)
            # If this textField is not empty, assign it to the 'name' variable
            if textFieldName and name is None and num != -200:
                name = textFieldName
                mc.textField(self.colDict['self.nameTextField' + str(name)], e=1, tx=name)
        except:
            pass

        try:
            # Query the text inside 'start' textField
            textFieldStart = mc.textField(self.startTextField, q=1, tx=1)
            # If this textField is not empty, assign it to the 'start' variable
            if textFieldStart and start is None and num != -200:
                start = textFieldStart
        except:
            pass

        try:
            # Query the text inside 'end' textField
            textFieldEnd = mc.textField(self.endTextField, q=1, tx=1)
            # If this textField is not empty, assign it to the 'end' variable
            if textFieldEnd and end is None and num != -200:
                end = textFieldEnd
        except:
            pass

        if num is None:
            self.restoreButtons('add')
        elif num == -100:
            tempLine = AAlineNum
            try:
                AAlineNum = []
            except:
                pass
            num = None
            self.restoreButtons('add')
        elif num == -200:
            num = None
            self.restoreButtons('add')

        childNum = num if num is not None else (mc.scrollLayout(self.mScrollLayout, q=1, nch=1) - 1)
        formNameVal = name if name is not None else 'animation ' + str(childNum).zfill(3)
        formStartVal = start.zfill(4) if start is not None and start != '' else '0'.zfill(4)
        formEndVal = end.zfill(4) if end is not None and start != '' else '0'.zfill(4)
        colorVal = color if color is not None else (0.164, 0.164, 0.164)
        nI = childNum
        try:
            if nI in AAlineNum:
                defFont = 'boldLabelFont'
                defNumber = "> " + str(childNum).zfill(3)
            else:
                defFont = 'plainLabelFont'
                defNumber = "   " + str(childNum).zfill(3)
        except:
            defFont = 'plainLabelFont'
            defNumber = "   " + str(childNum).zfill(3)
        # Create single main form Line
        self.colDict['self.mainLine' + str(nI)] = mc.formLayout(w=70, h=self.Lheight, p=self.mScrollLayout)
        mc.popupMenu(p=self.colDict['self.mainLine' + str(nI)])
        mc.menuItem(l='Delete', c=partial(self.deleteLines, nI))
        mc.menuItem(l='Store takes', c=partial(self.storeTakes))
        mc.menuItem(l='Export', c=partial(self.exportSetup))
        mc.menuItem(l='Import', c=partial(self.importSetup))
        # Create single color editor of the line
        print(colorVal)
        self.colDict['self.canvasLine' + str(nI)] = mc.iconTextButton(l='', w=10, h=self.Lheight,
                                                                      bgc=(float(colorVal[0]), float(colorVal[1]), float(colorVal[2])),
                                                                      c=partial(self.changeColor, nI),
                                                                      p=self.colDict['self.mainLine' + str(nI)])

        # Create single form Line for each line
        self.colDict['self.formLine' + str(nI)] = mc.formLayout(h=self.Lheight,
                                                                bgc=(float(colorVal[0]), float(colorVal[1]), float(colorVal[2])),
                                                                p=self.colDict['self.mainLine' + str(nI)])

        # Create single number button which indicates order of the line
        self.colDict['self.lineNumber' + str(nI)] = mc.iconTextButton(l=defNumber, w=40, h=self.Lheight,
                                                                      style='textOnly', fn=defFont,
                                                                      c=partial(self.selectHighlight, 'select', nI),
                                                                      p=self.colDict['self.formLine' + str(nI)])

        # Create name button with the hidden text field
        self.colDict['self.formName' + str(nI)] = mc.formLayout(w=70, h=self.Lheight,
                                                                p=self.colDict['self.formLine' + str(nI)])
        self.colDict['self.nameButton' + str(nI)] = mc.iconTextButton(l=formNameVal, h=self.Lheight, style='textOnly',
                                                                      fn=defFont,
                                                                      c=partial(self.selectHighlight, 'select', nI),
                                                                      dcc=partial(self.changeName, nI, 'name'),
                                                                      p=self.colDict['self.formName' + str(nI)])
        self.colDict['self.nameSpaceButton' + str(nI)] = mc.iconTextButton(l='', h=self.Lheight, style='textOnly',
                                                                           vis=1,
                                                                           c=partial(self.selectHighlight, 'select',
                                                                                     nI),
                                                                           dcc=partial(self.changeName, nI, 'name'),
                                                                           p=self.colDict['self.formName' + str(nI)])

        if num is None:
            self.colDict['self.nameTextField' + str(nI)] = mc.textField(h=self.Lheight - 1, vis=1, aie=1,
                                                                        ec=partial(self.editName, nI, 'name'),
                                                                        p=self.colDict['self.formName' + str(nI)])
            if name is not None:
                mc.textField(self.colDict['self.nameTextField' + str(nI)], e=1, tx=name)
            mc.setFocus(self.colDict['self.nameTextField' + str(nI)])
        else:
            self.colDict['self.nameTextField' + str(nI)] = mc.textField(h=self.Lheight - 1, vis=0, aie=1,
                                                                        ec=partial(self.editName, nI, 'name'),
                                                                        p=self.colDict['self.formName' + str(nI)])

        # Create frames buttons with hidden text fields
        self.colDict['self.formFrames' + str(nI)] = mc.formLayout(h=self.Lheight,
                                                                  p=self.colDict['self.formLine' + str(nI)])

        # Start frame button with hidden text field
        self.colDict['self.startFrame' + str(nI)] = mc.iconTextButton(l=formStartVal, h=self.Lheight, w=31,
                                                                      style='textOnly', fn=defFont,
                                                                      c=partial(self.selectHighlight, 'range', nI),
                                                                      dcc=partial(self.changeName, nI, 'sframe'),
                                                                      p=self.colDict['self.formFrames' + str(nI)])
        mc.popupMenu(p=self.colDict['self.startFrame' + str(nI)])
        mc.menuItem(l='Start', c=partial(self.insertFrame, 'start', 'sB', nI))
        mc.menuItem(l='End', c=partial(self.insertFrame, 'end', 'sB', nI))
        mc.menuItem(l='Current', c=partial(self.insertFrame, 'current', 'sB', nI))
        mc.menuItem(l='Both', c=partial(self.insertFrame, 'both', 'sB', nI))

        self.colDict['self.startTextField' + str(nI)] = mc.textField(h=self.Lheight - 1, vis=0, aie=1,
                                                                     ec=partial(self.editName, nI, 'sframe'),
                                                                     p=self.colDict['self.formFrames' + str(nI)])

        # Dash between start frame and end frame
        self.colDict['self.framesDash' + str(nI)] = mc.iconTextButton(h=self.Lheight, l=' - ', w=10, fn=defFont,
                                                                      style='textOnly',
                                                                      c=partial(self.selectHighlight, 'range', nI),
                                                                      p=self.colDict['self.formFrames' + str(nI)])

        # End frame button with hidden text field
        self.colDict['self.endFrame' + str(nI)] = mc.iconTextButton(l=formEndVal, h=self.Lheight, w=31,
                                                                    style='textOnly', fn=defFont,
                                                                    c=partial(self.selectHighlight, 'range', nI),
                                                                    dcc=partial(self.changeName, nI, 'eframe'),
                                                                    p=self.colDict['self.formFrames' + str(nI)])
        mc.popupMenu(p=self.colDict['self.endFrame' + str(nI)])
        mc.menuItem(l='Start', c=partial(self.insertFrame, 'start', 'eB', nI))
        mc.menuItem(l='End', c=partial(self.insertFrame, 'end', 'eB', nI))
        mc.menuItem(l='Current', c=partial(self.insertFrame, 'current', 'eB', nI))
        mc.menuItem(l='Both', c=partial(self.insertFrame, 'both', 'eB', nI))

        self.colDict['self.endTextField' + str(nI)] = mc.textField(h=15, vis=0, aie=1,
                                                                   ec=partial(self.editName, nI, 'eframe'),
                                                                   p=self.colDict['self.formFrames' + str(nI)])

        # Edit main form line elements position
        mc.formLayout(self.colDict['self.mainLine' + str(nI)], e=1,
                      af=(self.colDict['self.canvasLine' + str(nI)], 'right', 0))
        mc.formLayout(self.colDict['self.mainLine' + str(nI)], e=1, ac=(
        self.colDict['self.formLine' + str(nI)], 'right', 1, self.colDict['self.canvasLine' + str(nI)]))
        mc.formLayout(self.colDict['self.mainLine' + str(nI)], e=1,
                      af=(self.colDict['self.formLine' + str(nI)], 'left', 0))

        # Edit form Frames elements position
        mc.formLayout(self.colDict['self.formFrames' + str(nI)], e=1,
                      af=(self.colDict['self.startTextField' + str(nI)], 'left', 0))
        mc.formLayout(self.colDict['self.formFrames' + str(nI)], e=1,
                      af=(self.colDict['self.startFrame' + str(nI)], 'left', 0))

        mc.formLayout(self.colDict['self.formFrames' + str(nI)], e=1, ac=(
        self.colDict['self.framesDash' + str(nI)], 'left', 0, self.colDict['self.startFrame' + str(nI)]))
        mc.formLayout(self.colDict['self.formFrames' + str(nI)], e=1, ac=(
        self.colDict['self.endFrame' + str(nI)], 'left', 0, self.colDict['self.framesDash' + str(nI)]))
        mc.formLayout(self.colDict['self.formFrames' + str(nI)], e=1, ac=(
        self.colDict['self.endTextField' + str(nI)], 'left', 0, self.colDict['self.framesDash' + str(nI)]))

        # Edit form Line elements position
        mc.formLayout(self.colDict['self.formLine' + str(nI)], e=1,
                      af=(self.colDict['self.lineNumber' + str(nI)], 'left', 0))
        mc.formLayout(self.colDict['self.formLine' + str(nI)], e=1,
                      af=(self.colDict['self.formFrames' + str(nI)], 'right', 0))
        mc.formLayout(self.colDict['self.formLine' + str(nI)], e=1, ac=(
        self.colDict['self.formName' + str(nI)], 'left', 0, self.colDict['self.lineNumber' + str(nI)]))
        mc.formLayout(self.colDict['self.formLine' + str(nI)], e=1, ac=(
        self.colDict['self.formName' + str(nI)], 'right', 0, self.colDict['self.formFrames' + str(nI)]))

        # Edit form Name element position
        mc.formLayout(self.colDict['self.formName' + str(nI)], e=1,
                      af=(self.colDict['self.nameButton' + str(nI)], 'left', 0))
        mc.formLayout(self.colDict['self.formName' + str(nI)], e=1, ac=(
        self.colDict['self.nameSpaceButton' + str(nI)], 'left', 0, self.colDict['self.nameButton' + str(nI)]))
        mc.formLayout(self.colDict['self.formName' + str(nI)], e=1,
                      af=(self.colDict['self.nameSpaceButton' + str(nI)], 'right', 0))
        mc.formLayout(self.colDict['self.formName' + str(nI)], e=1,
                      af=(self.colDict['self.nameTextField' + str(nI)], 'left', 0))
        mc.formLayout(self.colDict['self.formName' + str(nI)], e=1,
                      af=(self.colDict['self.nameTextField' + str(nI)], 'right', 0))

        # Append the 'add' button at the end of the list
        if num is None:
            self.addNewLine('add')

        # Change the style of the buttons
        if defFont == 'boldLabelFont':
            fontWeight = 'bold'
            color = 'white'
        else:
            fontWeight = 'normal'
            color = '#d6d6d6'

        if int(self.mayaVer) < 7:
            # Re-style 'name' button
            self.colDict['self.nameButtonSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.nameButton' + str(nI)])), QtGui.QPushButton)
            # Re-style 'line number' button
            self.colDict['self.lineNumberSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.lineNumber' + str(nI)])), QtGui.QPushButton)
            # Re-style 'spacer' button
            self.colDict['self.nameSpaceButtonSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.nameSpaceButton' + str(nI)])), QtGui.QPushButton)
            # Re-style 'start frame' button
            self.colDict['self.startFrameSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.startFrame' + str(nI)])), QtGui.QPushButton)
            # Re-style 'dash' button
            self.colDict['self.framesDashSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.framesDash' + str(nI)])), QtGui.QPushButton)
            # Re-style 'end frame' button
            self.colDict['self.endFrameSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.endFrame' + str(nI)])), QtGui.QPushButton)
        else:
            # Re-style 'name' button
            self.colDict['self.nameButtonSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.nameButton' + str(nI)])), QtWidgets.QPushButton)
            # Re-style 'line number' button
            self.colDict['self.lineNumberSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.lineNumber' + str(nI)])), QtWidgets.QPushButton)
            # Re-style 'spacer' button
            self.colDict['self.nameSpaceButtonSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.nameSpaceButton' + str(nI)])), QtWidgets.QPushButton)
            # Re-style 'start frame' button
            self.colDict['self.startFrameSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.startFrame' + str(nI)])), QtWidgets.QPushButton)
            # Re-style 'dash' button
            self.colDict['self.framesDashSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.framesDash' + str(nI)])), QtWidgets.QPushButton)
            # Re-style 'end frame' button
            self.colDict['self.endFrameSt' + str(nI)] = shiboken.wrapInstance(
                long(omUI.MQtUtil.findControl(self.colDict['self.endFrame' + str(nI)])), QtWidgets.QPushButton)

        self.colDict['self.nameButtonSt' + str(nI)].setStyleSheet(
            'QPushButton { border: 1px hidden white;} QLabel { font-weight: ' + fontWeight + ';color: ' + color + '} ')
        self.colDict['self.lineNumberSt' + str(nI)].setStyleSheet(
            'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
        self.colDict['self.nameSpaceButtonSt' + str(nI)].setStyleSheet(
            'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
        self.colDict['self.startFrameSt' + str(nI)].setStyleSheet(
            'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')
        self.colDict['self.endFrameSt' + str(nI)].setStyleSheet(
            'QPushButton {border: 1px hidden white;} QLabel {font-weight: ' + fontWeight + ';color: ' + color + '} ')

        if tempLine:
            AAlineNum = tempLine

    def addNewLine(self, mode):
        # Create 'add' button
        if mode == 'add':
            mc.deleteUI(self.addLine, lay=1)

        # Create 'add' button
        self.addLine = mc.formLayout(p=self.mScrollLayout)
        self.sepAdd = mc.separator(w=40, st='none', p=self.addLine)
        self.addLineButton = mc.iconTextButton(l='add...', h=self.Lheight, al='left', style='textOnly',
                                               c=partial(self.revealNewLine, -200, None, None, None, None),
                                               p=self.addLine)
        self.addHButton = mc.iconTextButton(l='', h=self.Lheight, al='left', style='textOnly',
                                            c=partial(self.revealNewLine, -200, None, None, None, None), p=self.addLine)
        mc.formLayout(self.addLine, e=1, af=(self.sepAdd, 'left', 0))
        mc.formLayout(self.addLine, e=1, ac=(self.addLineButton, 'left', 0, self.sepAdd))
        mc.formLayout(self.addLine, e=1, ac=(self.addHButton, 'left', 0, self.addLineButton))
        mc.formLayout(self.addLine, e=1, af=(self.addHButton, 'right', 0))

        if int(self.mayaVer) < 7:
            addLineButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addLineButton)), QtGui.QPushButton)
            addSpacerButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addHButton)), QtGui.QPushButton)
        else:
            addLineButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addLineButton)),
                                                  QtWidgets.QPushButton)
            addSpacerButton = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addHButton)),
                                                    QtWidgets.QPushButton)

        addLineButton.setStyleSheet('QPushButton {border: 1px hidden white;} QLabel {color: #d6d6d6} ')
        addSpacerButton.setStyleSheet('QPushButton {border: 1px hidden white;} QLabel {color: #d6d6d6} ')

    # Delete selected lines
    def deleteLines(self, num, part):
        global AAlineNum

        AAData = mc.getAttr('AANode.data')
        if AAData:
            valDict = ast.literal_eval(AAData)
        unsortDict = {}
        if num == -1:
            num = AAlineNum[0]
        # Re-Create the dict without selected items
        # If several items selected
        if AAlineNum and num in AAlineNum:
            for k, v in valDict.iteritems():
                if k not in AAlineNum:
                    unsortDict[k] = v
        # If one item selected
        else:
            for k, v in valDict.iteritems():
                if k != num:
                    unsortDict[k] = v

        # Create new sorted dictionary with reassigned ordering values for storing them in setAttr
        sortDict = OrderedDict(sorted(unsortDict.items(), key=lambda k: k[0]))
        count = 0
        NewsortDict = {}
        for k, v in sortDict.iteritems():
            NewsortDict[count] = sortDict[k]
            count += 1

        AAlineNum = []
        self.selectHighlight('select', -1)
        mc.setAttr('AANode.data', NewsortDict, type='string')
        self.filterNames()

    # Move selected lines up or down
    def moveLines(self, mode, part):

        global AAlineNum
        valDict = {}
        NewvalDict = {}

        selItems = list(sorted(set(AAlineNum)))
        AAData = mc.getAttr('AANode.data')
        if AAData:
            valDict = ast.literal_eval(AAData)
        # Move selected lines on step up
        if mode == 'up':
            AAlineNum = []
            for s in selItems:
                for k, v in valDict.iteritems():
                    if s - 1 >= 0 and s - selItems.index(s) != 0:
                        AAlineNum.append(s - 1)
                        if s - 1 == k:
                            NewvalDict[k + 1] = valDict[k]
                        elif s == k:
                            NewvalDict[k - 1] = valDict[k]
                        else:
                            NewvalDict[k] = valDict[k]
                    else:
                        NewvalDict[k] = valDict[k]
                        AAlineNum.append(s)
                valDict = NewvalDict.copy()

        # Move selected lines on step down
        elif mode == 'down':
            AAlineNum = []
            for s in reversed(selItems):
                for k, v in valDict.iteritems():
                    if s + 1 <= len(valDict) - 1 and len(selItems) - selItems.index(s) + s - 1 < len(valDict) - 1:
                        AAlineNum.append(s + 1)
                        if s + 1 == k:
                            NewvalDict[k - 1] = valDict[k]
                        elif s == k:
                            NewvalDict[k + 1] = valDict[k]
                        else:
                            NewvalDict[k] = valDict[k]
                    else:
                        NewvalDict[k] = valDict[k]
                        AAlineNum.append(s)
                valDict = NewvalDict.copy()

        # Move selected lines to the top
        elif mode == 'upTop':
            AAlineNum = []
            for s in selItems:
                for k, v in valDict.iteritems():
                    AAlineNum.append(selItems.index(s))
                    for i in xrange(selItems.index(s), s):
                        NewvalDict[i + 1] = valDict[i]
                    if s == k:
                        NewvalDict[selItems.index(s)] = valDict[k]
                    elif s < k:
                        NewvalDict[k] = valDict[k]
                valDict = NewvalDict.copy()

        # Move selected lines to the bottom
        elif mode == 'downBottom':
            AAlineNum = []
            for s in reversed(selItems):
                for k, v in valDict.iteritems():
                    AAlineNum.append(len(valDict) - (len(selItems) - selItems.index(s)))
                    for i in xrange(s + 1, len(valDict) + 1 - (len(selItems) - selItems.index(s))):
                        NewvalDict[i - 1] = valDict[i]
                    if s == k:
                        NewvalDict[len(valDict) - (len(selItems) - selItems.index(s))] = valDict[k]
                    elif s > k:
                        NewvalDict[k] = valDict[k]
                valDict = NewvalDict.copy()

        # Save collected data into the attribute
        mc.setAttr('AANode.data', NewvalDict, type='string')
        # Clear current items from the scroll List
        cArray = mc.scrollLayout(self.mScrollLayout, q=1, ca=1)
        mu.executeDeferred('mc.deleteUI( ' + str(cArray) + ', lay=1 )')

        filterName = mc.textField(self.filterField, q=1, tx=1)

        # Create 'add' line-button at the end of the list
        if not filterName:
            mu.executeDeferred(self.addNewLine, 'create')

        # Create new list from reverse ordered dict for correct ordered line creation

        filteredDict = {}
        if filterName:
            if len(filterName) > 1 and filterName[0] == '*' and filterName[-1] != '*':
                for k, v in NewvalDict.iteritems():
                    if v[0].endswith(filterName[1:]):
                        filteredDict[k] = v
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] != '*':
                for k, v in NewvalDict.iteritems():
                    if v[0].startswith(filterName[:-1]):
                        filteredDict[k] = v
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] == '*':
                for k, v in NewvalDict.iteritems():
                    if filterName[1:-1] in v[0]:
                        filteredDict[k] = v
            elif len(filterName) == 1 and filterName == '*':
                pass
            else:
                for k, v in NewvalDict.iteritems():
                    if v[0] == filterName:
                        filteredDict[k] = v
        else:
            for k, v in NewvalDict.iteritems():
                filteredDict[k] = v

        createDict = OrderedDict(sorted(filteredDict.items(), key=lambda k: k[0], reverse=True))

        if len(createDict) > 0:
            for k, v in createDict.iteritems():
                mu.executeDeferred(self.revealNewLine, k, v[0], v[1], v[2], v[3])

    # Edit the text fields
    def editLineFields(self, field):

        global AAlineNum
        AAData = mc.getAttr('AANode.data')
        if AAData:
            valDict = ast.literal_eval(AAData)

        # If there is any single line selected, edit this line from the 'name' text field
        if AAlineNum and len(AAlineNum) == 1:
            for k, v in valDict.iteritems():
                if k == AAlineNum[0]:
                    if field == 'name':
                        newName = mc.textField(self.nameTextField, q=1, tx=1)
                        if newName != v[0]:
                            if newName == '':
                                newName = mc.iconTextButton(self.colDict['self.nameButton' + str(AAlineNum[0])], q=1,
                                                            l=1)
                            valDict[k] = [newName, v[1], v[2], v[3]]
                            mc.iconTextButton(self.colDict['self.nameButton' + str(AAlineNum[0])], e=1, l=newName)
                            # Save collected data into the attribute
                            mc.setAttr('AANode.data', valDict, type='string')
                    elif field == 'start':
                        startFrame = mc.textField(self.startTextField, q=1, tx=1)
                        if startFrame != v[1]:
                            if startFrame == '':
                                startFrame == startFrame.zfill(4)
                            valDict[k] = [v[0], startFrame, v[2], v[3]]
                            mc.iconTextButton(self.colDict['self.startFrame' + str(AAlineNum[0])], e=1,
                                              l=startFrame.zfill(4))
                            # Save collected data into the attribute
                            mc.setAttr('AANode.data', valDict, type='string')
                    else:
                        endFrame = mc.textField(self.endTextField, q=1, tx=1)
                        if endFrame != v[1]:
                            if endFrame == '':
                                endFrame == endFrame.zfill(4)
                            valDict[k] = [v[0], v[1], endFrame, v[3]]
                            mc.iconTextButton(self.colDict['self.endFrame' + str(AAlineNum[0])], e=1,
                                              l=endFrame.zfill(4))
                            # Save collected data into the attribute
                            mc.setAttr('AANode.data', valDict, type='string')
        elif AAlineNum and len(AAlineNum) == 0:
            if field == 'name':
                newName = mc.textField(self.nameTextField, q=1, tx=1)
                self.revealNewLine(None, newName, None, None, None)
            elif field == 'start':
                startFrame = mc.textField(self.startTextField, q=1, tx=1)
                self.revealNewLine(None, None, startFrame, None, None)
            elif field == 'end':
                endFrame = mc.textField(self.endTextField, q=1, tx=1)
                self.revealNewLine(None, None, None, endFrame, None)

    # Insert frames from the items popup menu
    def insertFrame(self, button, mode, num, part):
        global AAlineNum
        try:
            if AAlineNum:
                pass
        except:
            AAlineNum = []
        valDict = {}
        aData = mc.getAttr('AANode.data')
        valDict = ast.literal_eval(aData)
        if button == 'start':
            st = mc.playbackOptions(q=1, min=1)
            en = mc.playbackOptions(q=1, min=1)
        elif button == 'end':
            st = mc.playbackOptions(q=1, max=1)
            en = mc.playbackOptions(q=1, max=1)
        elif button == 'current':
            st = mc.currentTime(q=1)
            en = mc.currentTime(q=1)
        elif button == 'both':
            st = mc.playbackOptions(q=1, min=1)
            en = mc.playbackOptions(q=1, max=1)

        if mode == 'sB':
            if num in AAlineNum:
                for a in AAlineNum:
                    mc.iconTextButton(self.colDict['self.startFrame' + str(a)], e=1, l=str(int(st)).zfill(4))
                    mc.textField(self.colDict['self.startTextField' + str(a)], e=1, tx=str(int(st)))
                    if button == 'both':
                        mc.iconTextButton(self.colDict['self.endFrame' + str(a)], e=1, l=str(int(en)).zfill(4))
                        mc.textField(self.colDict['self.endTextField' + str(a)], e=1, tx=str(int(en)))
                    for k, v in valDict.iteritems():
                        if k == a:
                            valDict[k][1] = str(int(st)).zfill(4)
                            if button == 'both':
                                valDict[k][2] = str(int(en)).zfill(4)
                if len(AAlineNum) == 1:
                    mc.textField(self.startTextField, e=1, tx=str(int(st)))
                    if button == 'both':
                        mc.textField(self.endTextField, e=1, tx=str(int(en)))
            else:
                mc.iconTextButton(self.colDict['self.startFrame' + str(num)], e=1, l=str(int(st)).zfill(4))
                mc.textField(self.colDict['self.startTextField' + str(num)], e=1, tx=str(int(st)))
                if button == 'both':
                    mc.iconTextButton(self.colDict['self.endFrame' + str(num)], e=1, l=str(int(en)).zfill(4))
                    mc.textField(self.colDict['self.endTextField' + str(num)], e=1, tx=str(int(en)))
                for k, v in valDict.iteritems():
                    if k == num:
                        valDict[k][1] = str(int(st)).zfill(4)
                        if button == 'both':
                            valDict[k][2] = str(int(en)).zfill(4)
        else:
            if num in AAlineNum:
                for a in AAlineNum:
                    mc.iconTextButton(self.colDict['self.endFrame' + str(a)], e=1, l=str(int(en)).zfill(4))
                    mc.textField(self.colDict['self.endTextField' + str(a)], e=1, tx=str(int(en)))
                    if button == 'both':
                        mc.iconTextButton(self.colDict['self.startFrame' + str(a)], e=1, l=str(int(st)).zfill(4))
                        mc.textField(self.colDict['self.startTextField' + str(a)], e=1, tx=str(int(st)))
                    for k, v in valDict.iteritems():
                        if k == a:
                            valDict[k][2] = str(int(en)).zfill(4)
                            if button == 'both':
                                valDict[k][1] = str(int(st)).zfill(4)
                if len(AAlineNum) == 1:
                    mc.textField(self.endTextField, e=1, tx=str(int(en)))
                    if button == 'both':
                        mc.textField(self.startTextField, e=1, tx=str(int(st)))
            else:
                mc.iconTextButton(self.colDict['self.endFrame' + str(num)], e=1, l=str(int(en)).zfill(4))
                mc.textField(self.colDict['self.endTextField' + str(num)], e=1, tx=str(int(en)))
                if button == 'both':
                    mc.iconTextButton(self.colDict['self.startFrame' + str(num)], e=1, l=str(int(st)).zfill(4))
                    mc.textField(self.colDict['self.startTextField' + str(num)], e=1, tx=str(int(st)))
                for k, v in valDict.iteritems():
                    if k == num:
                        valDict[k][2] = str(int(en)).zfill(4)
                        if button == 'both':
                            valDict[k][1] = str(int(st)).zfill(4)
        mc.setAttr('AANode.data', valDict, type='string')

    # Insert frames from the fields popup menu
    def insertFieldsFrames(self, field, menu, part):
        if menu == 'start':
            st = mc.playbackOptions(q=1, min=1)
            en = mc.playbackOptions(q=1, min=1)
        elif menu == 'end':
            st = mc.playbackOptions(q=1, max=1)
            en = mc.playbackOptions(q=1, max=1)
        elif menu == 'current':
            st = mc.currentTime(q=1)
            en = mc.currentTime(q=1)
        elif menu == 'both':
            st = mc.playbackOptions(q=1, min=1)
            en = mc.playbackOptions(q=1, max=1)
        if field == 'sF':
            mc.textField(self.startTextField, e=1, tx=str(int(st)))
            if menu == 'both':
                mc.textField(self.endTextField, e=1, tx=str(int(en)))
        else:
            mc.textField(self.endTextField, e=1, tx=str(int(en)))
            if menu == 'both':
                mc.textField(self.startTextField, e=1, tx=str(int(st)))
        self.editLineFields('end')
        self.editLineFields('start')

    # Change dock state
    def changeDockState(self):
        if mc.dockControl('AnimAssistDock', ex=1):
            floatState = mc.dockControl('AnimAssistDock', q=1, fl=1)
            areaState = mc.dockControl('AnimAssistDock', q=1, area=1)
            dockHeight = mc.dockControl('AnimAssistDock', q=1, h=1)
            mc.optionVar(iv=('AADockState', floatState))
            mc.optionVar(sv=('AADockArea', areaState))
            mc.optionVar(iv=('AADockHeight', dockHeight))

    # Set playblast data
    def playBlastData(self, part):
        path = mc.textField(self.PBpathTextField, q=1, tx=1)
        pre = mc.textField(self.PBpreTextField, q=1, tx=1)
        post = mc.textField(self.PBpostTextField, q=1, tx=1)
        cam = mc.textField(self.PBcamTextField, q=1, tx=1)
        PBdict = {}
        PBdict[path] = [pre, post, cam]
        mc.setAttr('AANode.playblast', PBdict, type='string')

    # Brpowse for the path to the playblat
    def browsePB(self, part):
        sn = ''
        pre = mc.textField(self.PBpreTextField, q=1, tx=1)
        post = mc.textField(self.PBpostTextField, q=1, tx=1)
        try:
            sn = mc.file(q=1, exn=1).rsplit('/', 1)[0]
        except:
            pass
        getPath = mc.fileDialog2(dir=sn, fm=3)
        if getPath:
            PBdict = {}
            mc.textField(self.PBpathTextField, e=1, tx=getPath[0])
            PBdict[getPath[0]] = [pre, post]
            mc.setAttr('AANode.playblast', PBdict, type='string')

    def playBlastCom(self, mode, part):

        if mode == 'setup':
            mc.playblast(options=True)
            return

        for k, v in self.checkboxList.items():
            if cmds.checkBox(str(v), query=True, value=True):
                self.selectedCameras.append(k)
                print('selected camera: ' + k)

        # Collect initial data from optionVars
        fform = mc.optionVar(q='playblastFormat')
        percent = mc.optionVar(q='playblastScale')
        videoSource = mc.optionVar(q='playblastDisplaySizeSource')
        scaleV = percent * 100
        qual = mc.optionVar(q='playblastQuality')
        compress = mc.optionVar(q='playblastCompression')
        pad = mc.optionVar(q='playblastPadding')
        isViewer = mc.optionVar(q='playblastViewerOn')
        isShowOrnaments = mc.optionVar(q='playblastShowOrnaments')

        # Get playblas fields data
        path = mc.textField(self.PBpathTextField, q=1, tx=1)
        pre = mc.textField(self.PBpreTextField, q=1, tx=1)
        post = mc.textField(self.PBpostTextField, q=1, tx=1)
        camera = mc.textField(self.PBcamTextField, q=1, tx=1)
        focusMP = mc.getPanel(wf=1)
        if mc.modelEditor(focusMP, ex=1):
            currentCam = mc.modelPanel(focusMP, q=1, cam=1)
            if camera != currentCam:
                mc.modelPanel(focusMP, e=1, cam=camera)

        for currentCamera, v in self.checkboxList.items():
            if cmds.checkBox(str(v), query=True, value=True):
                self.selectedCameras.append(currentCamera)
                mc.modelPanel(focusMP, e=1, cam=currentCamera)
                aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
                activeSound = mc.timeControl(aPlayBackSliderPython, q=1, s=1)

                if videoSource == 1:
                    width = 0
                    height = 0
                elif videoSource == 3:
                    width = mc.optionVar(q='playblastWidth')
                    height = mc.optionVar(q='playblastHeight')
                elif videoSource == 2:
                    width = mc.getAttr("defaultResolution.width")
                    height = mc.getAttr("defaultResolution.height")

                selV = []
                global AAlineNum
                try:
                    selV = AAlineNum
                except:
                    pass
                # Temporary fix for custom locator
                allLoc = mc.ls(typ='csLocator')
                for a in allLoc:
                    mc.setAttr(a + '.visibility', 0)

                if selV:
                    if mode == 'separate':
                        for s in selV:
                            getName = mc.iconTextButton(self.colDict['self.nameButton' + str(s)], q=1, l=1)
                            getStFr = mc.iconTextButton(self.colDict['self.startFrame' + str(s)], q=1, l=1)
                            getEnFr = mc.iconTextButton(self.colDict['self.endFrame' + str(s)], q=1, l=1)

                            if pre:
                                prefix = pre + '_'
                            else:
                                prefix = ''

                            if post:
                                postfix = '_' + post
                            else:
                                postfix = ''

                            mc.playblast(forceOverwrite=1, ae=0, fmt=fform, sound=activeSound, p=scaleV,
                                         compression=compress, quality=qual, viewer=isViewer,
                                         showOrnaments=isShowOrnaments, fp=pad, st=float(getStFr),
                                         widthHeight=(width, height), et=float(getEnFr),
                                         f=(path + '/' + currentCamera + '_' + prefix + getName + postfix))
                    else:
                        getNameA = []
                        getStFrA = []
                        getEnFrA = []
                        for s in selV:
                            getNameA.append(mc.iconTextButton(self.colDict['self.nameButton' + str(s)], q=1, l=1))
                            getStFrA.append(
                                float(mc.iconTextButton(self.colDict['self.startFrame' + str(s)], q=1, l=1)))
                            getEnFrA.append(float(mc.iconTextButton(self.colDict['self.endFrame' + str(s)], q=1, l=1)))
                        mc.playblast(forceOverwrite=1, ae=0, fmt=fform, p=scaleV, compression=compress, quality=qual,
                                     viewer=isViewer, showOrnaments=isShowOrnaments, fp=pad, st=min(getStFrA),
                                     widthHeight=(width, height), et=max(getEnFrA),
                                     f=(path + '/' + currentCamera + '_' + prefix + '_'.join(getNameA) + postfix))

                # Temporary fix for custom locator
                allLoc = mc.ls(typ='csLocator')
                for a in allLoc:
                    mc.setAttr(a + '.visibility', 1)

        mc.modelPanel(focusMP, e=1, cam=currentCam)

    def getCurrentDirectory(self):
        return dirname(abspath(mc.file(q=True, sn=True)))

    def exportSetup(self, *args):
        path = mc.textField(self.PBpathTextField, q=1, tx=1)

        valDict = {}
        if mc.objExists('AANode'):
            AAData = mc.getAttr('AANode.data')
            if AAData:
                valDict = ast.literal_eval(AAData)


        with open(self.getCurrentDirectory() + '/blastSetup.txt', 'w') as outfile:
                for i, k in valDict.items():
                    resultString = str(k[1]) + " " + str(k[2]) + " " + str(k[0] + '\n')
                    outfile.write(resultString)
        outfile.close()

    def importSetup(self, *args):
        global AAlineNum
        txtFilesInWorkingDir = []
        txtFile = '';
        workingDirectory = self.getCurrentDirectory()
        print('Search for config in:')
        print(workingDirectory)
        for file in os.listdir(workingDirectory):

            if file.endswith(".txt"):

                txtFilesInWorkingDir.append(file)
                txtFile = str(file)

        if len(txtFilesInWorkingDir) > 1:
            mc.confirmDialog(message="В каталоге сцены обнаружено несколько текстовых файлов. Оставьте только один с настройками", button=["ok"])
            return
        elif len(txtFilesInWorkingDir) == 0:
            mc.confirmDialog(message="Текстовых файлов в каталоге сцены не обнаружено", button=["ok"])
            return

        configFilePath = os.path.join(workingDirectory, txtFile)

        #cArray = mc.scrollLayout(self.mScrollLayout, q=1, ca=1)
        #mu.executeDeferred('mc.deleteUI( ' + str(cArray) + ', lay=1 )')

        color = (float(0.16), float(0.16), float(0.16))
        counter = 0

        with open(configFilePath, 'r') as outfile:
            fileContent = outfile.readlines()

        NewsortDict = {}
        lineCount = 0
        for line in fileContent:
            print(line)
            setup = line.split()
            if not setup:
                continue
            counter += 1
            start = setup[0]
            end = setup[1]
            name = setup[2:]
            printName = ' '.join(name)
            lineList = [printName, start, end, color]
            NewsortDict[lineCount] = lineList
            lineCount += 1

        AAlineNum = []
        self.selectHighlight('select', -1)
        mc.setAttr('AANode.data', NewsortDict, type='string')
        self.filterNames()

    def storeTakes(self, part):
        valDict = {}
        aData = mc.getAttr('AANode.data')
        valDict = ast.literal_eval(aData)
        mel.eval('FBXExportSplitAnimationIntoTakes -c')
        for k, v in valDict.iteritems():
            mel.eval('FBXExportSplitAnimationIntoTakes -v ' + v[0] + ' ' + v[1] + ' ' + v[2])

    def filterNames(self):
        filterName = mc.textField(self.filterField, q=1, tx=1)

        valDict = {}
        if mc.objExists('AANode'):
            AAData = mc.getAttr('AANode.data')
            if AAData:
                valDict = ast.literal_eval(AAData)

        filteredDict = {}
        if filterName:
            if len(filterName) > 1 and filterName[0] == '*' and filterName[-1] != '*':
                for k, v in valDict.iteritems():
                    if v[0].endswith(filterName[1:]):
                        filteredDict[k] = v
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] != '*':
                for k, v in valDict.iteritems():
                    if v[0].startswith(filterName[:-1]):
                        filteredDict[k] = v
            elif len(filterName) > 1 and filterName[-1] == '*' and filterName[0] == '*':
                for k, v in valDict.iteritems():
                    if filterName[1:-1] in v[0]:
                        filteredDict[k] = v
            elif len(filterName) == 1 and filterName == '*':
                pass
            else:
                for k, v in valDict.iteritems():
                    if v[0] == filterName:
                        filteredDict[k] = v
            oDict = OrderedDict(sorted(filteredDict.items(), key=lambda t: t[0]))

            # Clear current items from the scroll List
            cArray = mc.scrollLayout(self.mScrollLayout, q=1, ca=1)
            mu.executeDeferred('mc.deleteUI( ' + str(cArray) + ', lay=1 )')

            if len(oDict) > 0:
                for k, v in oDict.iteritems():
                    self.revealNewLine(k, v[0], v[1], v[2], v[3])

            mc.button(self.addButton, e=1, en=0)
            # Change the basic color sheme
            if int(self.mayaVer) < 7:
                addB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addButton)), QtGui.QPushButton)
            else:
                addB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addButton)), QtWidgets.QPushButton)
            addB.setStyleSheet('QPushButton { border: 1px solid #232323 ; background-color: #535353; color: #d5d5d5 } ')

        else:
            for k, v in valDict.iteritems():
                filteredDict[k] = v

            oDict = OrderedDict(sorted(filteredDict.items(), key=lambda t: t[0]))

            # Clear current items from the scroll List
            cArray = mc.scrollLayout(self.mScrollLayout, q=1, ca=1)
            mu.executeDeferred('mc.deleteUI( ' + str(cArray) + ', lay=1 )')

            if len(oDict) > 0:
                for k, v in oDict.iteritems():
                    self.revealNewLine(k, v[0], v[1], v[2], v[3])
            self.addNewLine('create')

            mc.button(self.addButton, e=1, en=1)
            if int(self.mayaVer) < 7:
                addB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addButton)), QtGui.QPushButton)
            else:
                addB = shiboken.wrapInstance(long(omUI.MQtUtil.findControl(self.addButton)), QtWidgets.QPushButton)
            addB.setStyleSheet(
                'QPushButton { border: 1px solid #0a2b04 ; background-color: #27541e; color: #a8d79f } QPushButton:hover{background-color: #2c711f; } QPushButton:pressed{ background-color: #183811; } ')

    def clearFilter(self):
        mc.textField(self.filterField, e=1, tx='')
        self.filterNames()


def start():
    AnimAssistant().AnimAssistantUI()


AnimAssistant().AnimAssistantUI()