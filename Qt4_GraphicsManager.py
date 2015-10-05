#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

"""
Qt4_GraphicsManager keeps track of the current shapes the user has created. 
The shapes handled are any that inherits the Shape base class.
All shapes (graphics items) are based on Qt native GraphicsItem that all
displayed on GraphicsScene and GraphicsViewer.

Implemented graphics items:
 - GraphicsItem : base class for all items
 - GraphicsItemBeam : beam shape
 - GraphicsItemPoint : centring point
 - GraphicsItemLine : line between two centring points
 - GraphicsItemGrid : 2D grid
 - GraphicsItemScale : scale 
 - GraphicsItemOmegaReference : omega rotation line
 - GraphicsItemCentringLine : 3 click centring line
 - GraphicsItemMeasureDistance : distance measure line
 - GraphicsItemMeasureAngle : object to measure angle between two lines
 - GraphicsItemMeasureArea : area measurement item

For more details see each item docstring
"""

import copy
import math
import types
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import queue_model_objects_v1 as queue_model_objects

from HardwareRepository.BaseHardwareObjects import HardwareObject
from HardwareRepository.HardwareRepository import dispatcher


SELECTED_COLOR = QtCore.Qt.green
NORMAL_COLOR = QtCore.Qt.yellow


class Qt4_GraphicsManager(HardwareObject):
    """
    Descript. : Keeps track of the current shapes the user has created. The
                shapes handled are any that inherits the Shape base class.
                Diffractometer and BeamInfo are mandotary
    """
    def __init__(self, name):
        HardwareObject.__init__(self, name)

        self.diffractometer_hwobj = None
        self.camera_hwobj = None
        self.beam_info_hwobj = None
     
        self.pixels_per_mm = [0, 0]
        self.beam_position = [0, 0]
        self.beam_size = [0, 0]
        self.beam_shape = None
        self.beam_info_dict = {}
        self.graphics_scene_size = [0, 0]
        self.mouse_position = [0, 0] 

        self.omega_axis_info_dict = {}
        self.in_centring_state = False
        self.in_grid_drawing_state = False
        self.in_measure_distance_state = None
        self.in_measure_angle_state = None
        self.in_measure_area_state = None
        self.point_count = 0
        self.line_count = 0
        self.grid_count = 0
        self.shape_dict = {}
        self.selected_centring_points = []

        self.graphics_scene_size = None

        self.graphics_view = None
        self.graphics_camera_frame = None
        self.graphics_beam_item = None
        self.graphics_scale_item = None
        self.graphics_omega_reference_item = None
        self.graphics_centring_lines_item = None
        self.graphics_grid_draw_item = None
        self.graphics_measure_distance_item = None
        self.graphics_measure_angle_item = None
        self.graphics_measure_area_item = None
 
    def init(self):
        """
        Descript. :
        """
        self.graphics_view = GraphicsView()
         
        self.graphics_camera_frame = GraphicsCameraFrame()
        self.graphics_scale_item = GraphicsItemScale(self)
        self.graphics_omega_reference_item = GraphicsItemOmegaReference(self)
        self.graphics_beam_item = GraphicsItemBeam(self)
        self.graphics_centring_lines_item = GraphicsItemCentringLines(self)
        self.graphics_centring_lines_item.hide()
        self.graphics_measure_distance_item = GraphicsItemMeasureDistance(self)
        self.graphics_measure_distance_item.hide()
        self.graphics_measure_angle_item = GraphicsItemMeasureAngle(self)
        self.graphics_measure_angle_item.hide()
        self.graphics_measure_area_item = GraphicsItemMeasureArea(self)
        self.graphics_measure_area_item.hide()
         
        self.graphics_view.graphics_scene.addItem(self.graphics_camera_frame) 
        self.graphics_view.graphics_scene.addItem(self.graphics_omega_reference_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_beam_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_centring_lines_item) 
        self.graphics_view.graphics_scene.addItem(self.graphics_scale_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_measure_distance_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_measure_angle_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_measure_area_item)

        self.graphics_view.scene().mouseClickedSignal.connect(\
             self.mouse_clicked)
        self.graphics_view.scene().mouseDoubleClickedSignal.connect(\
             self.mouse_double_clicked)
        self.graphics_view.scene().mouseReleasedSignal.connect(\
             self.mouse_released)
        self.graphics_view.scene().itemClickedSignal.connect(\
             self.item_clicked)
        self.graphics_view.scene().itemDoubleClickedSignal.connect(\
             self.item_double_clicked)
        self.graphics_view.mouseMovedSignal.connect(self.mouse_moved)
        self.graphics_view.keyPressedSignal.connect(self.key_pressed)

        self.diffractometer_hwobj = self.getObjectByRole("diffractometer")
        if self.diffractometer_hwobj:
            self.diffractometer_zoom_changed()
            self.connect(self.diffractometer_hwobj, "minidiffStateChanged", 
                         self.diffractometer_changed)
            self.connect(self.diffractometer_hwobj, "centringAccepted", 
                         self.diffractometer_centring_accepted)
            self.connect(self.diffractometer_hwobj, "centringSuccessful", 
                         self.diffractometer_centring_successful)
            self.connect(self.diffractometer_hwobj, "centringFailed", 
                         self.diffractometer_centring_failed)
            self.connect(self.diffractometer_hwobj, "zoomMotorPredefinedPositionChanged", 
                         self.diffractometer_changed) 
            self.connect(self.diffractometer_hwobj, "omegaReferenceChanged", 
                         self.diffractometer_omega_reference_changed)
        else:
             logging.getLogger("HWR").error("GraphicsManager: Diffractometer hwobj not defined")

        self.beam_info_hwobj = self.getObjectByRole("beam_info")
        if self.beam_info_hwobj:
            self.beam_info_dict = self.beam_info_hwobj.get_beam_info()
            self.connect(self.beam_info_hwobj, "beamPositionChanged", self.beam_position_changed)
            self.connect(self.beam_info_hwobj, "beamInfoChanged", self.beam_info_changed)
        else:
            logging.getLogger("HWR").error("GraphicsManager: BeamInfo hwobj not defined")

        self.camera_hwobj = self.getObjectByRole("camera")
        if self.camera_hwobj:
            self.graphics_scene_size = self.camera_hwobj.get_image_dimensions()
            self.set_graphics_scene_size(self.graphics_scene_size, False)
            self.camera_hwobj.start_camera()
            self.connect(self.camera_hwobj, "imageReceived", self.camera_image_received) 
        else:         
            logging.getLogger("HWR").error("GraphicsManager: Camera hwobj not defined")
 
    def camera_image_received(self, camera_image):
        """
        Descript. :
        """
        pixmap_image = QtGui.QPixmap.fromImage(camera_image)
        self.graphics_camera_frame.setPixmap(pixmap_image) 

    def beam_position_changed(self, position):
        """
        Descript. :
        """
        if position:
            self.graphics_beam_item.set_position(beam_position[0],
                                                 beam_position[1])

    def beam_info_changed(self, beam_info):
        """
        Descript. :
        """
        if beam_info:
            self.graphics_beam_item.set_beam_info(beam_info)
            self.graphics_view.graphics_scene.update()

    def diffractometer_changed(self, *args):
        """
        Descript. :
        """
        if self.diffractometer_hwobj.isReady():
            for shape in self.get_shapes():
                for cpos in shape.get_centred_positions():
                    new_x, new_y = self.diffractometer_hwobj.\
                        motor_positions_to_screen(cpos.as_dict())
                shape.set_position(new_x, new_y)
            for shape in self.get_shapes():
                shape.show()
        else:
            for shape in self.get_shapes():
                shape.hide()

    def diffractometer_centring_started(self, centring_method, flexible):
        """
        Descript. :
        """
        self.current_centring_method = centring_method
        self.emit("centringStarted")  

    def diffractometer_centring_accepted(self, centring_state, centring_status):
        """
        Descript. : creates a new centring position and adds it to graphics point
        Args.     : centring_state, centring_status
        Return    : None
        """
        p_dict = {}

        if 'motors' in centring_status and \
                'extraMotors' in centring_status:

            p_dict = dict(centring_status['motors'],
                          **centring_status['extraMotors'])
        elif 'motors' in centring_status:
            p_dict = dict(centring_status['motors'])

        if p_dict:
            cpos = queue_model_objects.CentredPosition(p_dict)
            screen_pos = self.diffractometer_hwobj.\
                    motor_positions_to_screen(cpos.as_dict())
            point = GraphicsItemPoint(cpos, True, screen_pos[0], screen_pos[1])
            if point:
                self.add_shape(point)
                cpos.set_index(point.index)
        self.emit("centringInProgress", False)

    def diffractometer_centring_successful(self, method, centring_status):
        """
        Descript. :
        """
        self.set_centring_state(False)
        self.emit("centringSuccessful", method, centring_status)

    def diffractometer_centring_failed(self, method, centring_status):
        """
        Descript. :
        """
        self.set_centring_state(False) 
        self.emit("centringFailed", method, centring_status)

    def diffractometer_zoom_changed(self, position = None, offset = None):
        """
        Descript. :
        """
        pixels_per_mm = self.diffractometer_hwobj.get_pixels_per_mm()
        if pixels_per_mm: 
            if pixels_per_mm != self.pixels_per_mm:
                self.pixels_per_mm = pixels_per_mm
                for item in self.graphics_view.graphics_scene.items():
                    if isinstance(item, GraphicsItem):
                        item.set_pixels_per_mm(self.pixels_per_mm)
                self.graphics_view.graphics_scene.update()

    def diffractometer_omega_reference_changed(self, omega_reference):
        """
        Descript. :
        """
        self.graphics_omega_reference_item.set_reference(omega_reference)
        
    def mouse_clicked(self, x, y):
        """
        Descript. :
        """ 
        self.selected_centring_points = [] 
        if self.in_centring_state:
            self.graphics_centring_lines_item.set_coordinates(x, y)
            self.diffractometer_hwobj.image_clicked(x, y)
        elif self.in_grid_drawing_state:
            self.graphics_grid_draw_item.show()
            self.graphics_grid_draw_item.set_draw_mode(True)
            self.graphics_grid_draw_item.set_draw_start_position(x, y)
        elif self.in_measure_distance_state:
            QtGui.QApplication.restoreOverrideCursor()
            self.in_measure_distance_state = None
        elif self.in_measure_angle_state:
            self.in_measure_angle_state = self.graphics_measure_angle_item.store_coord()
            if not self.in_measure_distance_state:
                QtGui.QApplication.restoreOverrideCursor()
        elif self.in_measure_area_state:
            self.graphics_measure_area_item.store_coord()
        else:
            for graphics_item in self.graphics_view.scene().items():
                graphics_item.setSelected(False)
                if type(graphics_item) in [GraphicsItemPoint, GraphicsItemLine, GraphicsItemGrid]:
                    self.emit("shapeSelected", graphics_item, False)  

    def mouse_double_clicked(self, x, y):
        """
        Descript. :
        """
        if self.in_measure_area_state:
            QtGui.QApplication.restoreOverrideCursor()  
            self.in_measure_area_state = False
            self.graphics_measure_area_item.store_coord(last=True)
        else: 
            self.diffractometer_hwobj.move_to_coord(x, y)

    def mouse_released(self, x, y):
        """
        Descript. :
        """
        if self.in_grid_drawing_state:
           self.graphics_grid_draw_item.set_draw_mode(False)
           self.graphics_grid_draw_item.fix_motor_pos_center()
           self.in_grid_drawing_state = False
           self.grid_count += 1
           self.emit("shapeCreated", self.graphics_grid_draw_item, "Grid")
           self.shape_dict[self.graphics_grid_draw_item.get_display_name()] = \
                self.graphics_grid_draw_item
           self.graphics_grid_draw_item.setSelected(True)
           
    def mouse_moved(self, x, y):
        """
        Descript. :
        """
        self.emit("graphicsMouseMoved", x, y)
        self.mouse_position = [x, y]
        if self.in_centring_state:
            self.graphics_centring_lines_item.set_coordinates(x, y)
        elif self.in_grid_drawing_state:
            if self.graphics_grid_draw_item.is_draw_mode():
                self.graphics_grid_draw_item.set_draw_end_position(x, y)
        elif self.in_measure_distance_state:
            self.graphics_measure_distance_item.set_end_coord(self.mouse_position)
        elif self.in_measure_angle_state:
            self.graphics_measure_angle_item.set_coord(self.mouse_position)
        elif self.in_measure_area_state:
            self.graphics_measure_area_item.set_coord(self.mouse_position)

    def key_pressed(self, key_event):
        """
        Descript. :
        """
        if key_event == "Delete":
            for item in self.graphics_view.graphics_scene.items():
                if item.isSelected():
                    self.delete_shape(item)
 
    def item_clicked(self, item, state):
        """
        Descript. :
        """
        print "item_clicked. ", item, state
        # before changing state this signal is emited
        # so we hve to revert state
        # TODO fix this correct state
        if isinstance(item, GraphicsItemPoint):
            if not state:
                self.selected_centring_points.append(item)
            else:
                self.selected_centring_points.remove(item)
        if type(item) in [GraphicsItemPoint, GraphicsItemLine, GraphicsItemGrid]: 
            self.emit("shapeSelected", item, not state)

    def item_double_clicked(self, item):
        """
        Descript. :
        """ 
        if isinstance(item, GraphicsItemPoint):
            self.diffractometer_hwobj.move_to_centred_position(item.centred_position)

    def get_graphics_view(self):
        """
        Descript. :
        """
        return self.graphics_view

    def get_camera_frame(self):
        """
        Descript. :
        """
        return self.graphics_camera_frame 

    def set_graphics_scene_size(self, size, fixed):
        """
        Descript. :
        """
        if not self.graphics_scene_size or fixed:
            self.graphics_scene_size = size
            self.graphics_scale_item.set_position(10, self.graphics_scene_size[1] - 10)
            self.graphics_view.setFixedSize(size[0], size[1])

    def get_graphics_beam_item(self):
        """
        Descript. :
        """
        return self.graphics_beam_item

    def get_scale_item(self):
        """
        Descript. :
        """
        return self.graphics_scale_item

    def get_omega_reference_item(self):
        """
        Descript. :
        """
        return self.graphics_omega_reference_item

    def set_centring_state(self, state):
        """
        Descript. :
        """
        self.in_centring_state = state
        self.graphics_centring_lines_item.set_visible(state)

    def get_shapes(self):
        """
        Returns: All the shapes currently handled.
        """
        shapes_list = []
        for shape in self.graphics_view.graphics_scene.items():
            if type(shape) in (GraphicsItemPoint, GraphicsItemLine, GraphicsItemGrid):
                shapes_list.append(shape)                 
        return shapes_list

    def get_points(self):
        """
        Descript. : returns: All points currently handled
        """
        current_points = []

        for shape in self.get_shapes():
            if isinstance(shape, GraphicsItemPoint):
                current_points.append(shape)

        return current_points
        
    def add_shape(self, shape):
        """
        Descrip.t : Adds the shape <shape> to the list of handled objects.

        :param shape: Shape to add.
        :type shape: Shape object.
        """
        self.de_select_all()
        if isinstance(shape, GraphicsItemPoint):
            self.point_count += 1
            shape.index = self.point_count
            self.selected_centring_points.append(shape)
            self.emit("shapeCreated", shape, "Point")
        elif isinstance(shape, GraphicsItemLine):
            self.line_count += 1
            shape.index = self.line_count
            self.emit("shapeCreated", shape, "Line")
        elif isinstance(shape, GraphicsItemGrid):
            self.grid_count += 1
            shape.index = self.grid_count
            self.emit("shapeCreated", shape, "Grid")
        self.shape_dict[shape.get_display_name()] = shape
        self.graphics_view.graphics_scene.addItem(shape)
        shape.setSelected(True)
        self.emit("shapeSelected", shape, True)

    def delete_shape(self, shape):
        """
        Removes the shape <shape> from the list of handled shapes.

        :param shape: The shape to remove
        :type shape: Shape object.
        """
        if isinstance(shape, GraphicsItemPoint):
            for s in self.get_shapes():
                if isinstance(s, GraphicsItemLine):
                    if shape in (s.cp_start, s.cp_end):
                        self._delete_shape(s)
                        break
        shape_type = ""
        if isinstance(shape, GraphicsItemPoint):
            shape_type = "Point"
        elif isinstance(shape, GraphicsItemLine):
            shape_type = "Line"
        elif isinstance(shape, GraphicsItemGrid):
            shape_type = "Grid"

        self.emit("shapeDeleted", shape, shape_type)
        self.graphics_view.graphics_scene.removeItem(shape)
        self.graphics_view.graphics_scene.update()

    def get_shape_by_name(self, shape_name):
        """
        Descript. :
        """
        return self.shape_dict.get(shape_name)            

    def clear_all(self):
        """
        Descript. : Clear the shape history, remove all contents.
        """
        self.point_count = 0
        self.line_count = 0
        self.grid_count = 0

        for shape in self.get_shapes():
            self.delete_shape(shape)
        self.graphics_view.graphics_scene.update()

    def de_select_all(self):
        """
        Descript. :
        """
        self.graphics_view.graphics_scene.clearSelection()

    def select_shape_with_cpos(self, cpos):
        """
        Descript. :
        """
        self.de_select_all()
        for shape in self.get_shapes():
            if isinstance(shape, GraphicsItemPoint):
                if shape.get_centred_positions()[0] == cpos:
                    shape.setSelected(True)

    def get_grid(self):
        """
        Returns the current grid object.
        """
        grid_dict = dict()
        dispatcher.send("grid", self, grid_dict)
        return grid_dict

    #def set_grid_data(self, key, result_data):
    #    dispatcher.send("set_grid_data", self, key, result_data)

    def get_selected_shapes(self):
        """
        Descript. :
        """
        selected_shapes = []
        for item in self.graphics_view.graphics_scene.items():
            if (type(item) in [GraphicsItemPoint, GraphicsItemGrid, GraphicsItemLine] and
                item.isSelected()):
                selected_shapes.append(item) 
        return selected_shapes

    def get_selected_points(self):
        """
        Descript. :
        """
        return self.selected_centring_points

    def add_new_centring_point(self, state, centring_status, beam_info):
        """
        Descript. :
        """
        new_point = GraphicsItemPoint(self)
        self.centring_points.append(new_point)
        self.graphics_view.graphics_scene.addItem(new_point)        

    def get_snapshot(self, shape_list=None):
        """
        Descript. :
        """
        if shape_list:
            self.de_select_all()
            for shape in shape_list:
                shape.setSelected(True)

        image = QtGui.QImage(self.graphics_view.graphics_scene.sceneRect().\
            size().toSize(), QtGui.QImage.Format_ARGB32)
        image.fill(QtCore.Qt.transparent)
        image_painter = QtGui.QPainter(image)
        self.graphics_view.render(image_painter)
        image_painter.end()
        return image

    def set_grid_draw_state(self, state):
        """
        Descript. :
        """
        self.in_grid_drawing_state = state

    def start_measure_distance(self):
        """
        Descript. :
        """ 
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BusyCursor))
        self.in_measure_distance_state = True
        self.graphics_measure_distance_item.set_start_coord(self.mouse_position)
        self.graphics_measure_distance_item.show()
        self.graphics_view.graphics_scene.update()

    def start_measure_angle(self):
        """
        Descript. :
        """
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BusyCursor))
        self.in_measure_angle_state = True
        self.graphics_measure_angle_item.set_start_coord(self.mouse_position)
        self.graphics_measure_angle_item.show()
        self.graphics_view.graphics_scene.update()

    def start_measure_area(self):
        """
        Descript. :
        """
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BusyCursor))
        self.in_measure_area_state = True
        self.graphics_measure_area_item.set_start_coord(self.mouse_position)
        self.graphics_measure_area_item.show()
        self.graphics_view.graphics_scene.update()

    def stop_measure_distance(self):
        """
        Descript. :
        """
        self.in_measure_distance_state = False
        self.graphics_measure_distance_item.hide()
        self.graphics_view.graphics_scene.update()

    def stop_measure_angle(self):
        """
        Descript. :
        """
        self.in_measure_angle_state = False
        self.graphics_measure_angle_item.hide()
        self.graphics_view.graphics_scene.update()

    def stop_measure_area(self):
        """
        Descript. :
        """
        QtGui.QApplication.restoreOverrideCursor()
        self.in_measure_area_state = False
        self.graphics_measure_area_item.hide()
        self.graphics_view.graphics_scene.update()

    def start_centring(self, tree_click = None):
        """
        Descript. :
        """ 
        self.emit("centringInProgress", True)
        if tree_click:
            self.set_centring_state(True) 
            self.diffractometer_hwobj.start_centring_method(\
                 self.diffractometer_hwobj.MANUAL3CLICK_MODE)
        else:
            self.diffractometer_hwobj.start_2D_centring(\
                 self.mouse_position[0], self.mouse_position[1])

    def accept_centring(self):
        """
        Descript. :
        """
        self.diffractometer_hwobj.accept_centring()

    def reject_centring(self):
        """
        Descript. :
        """ 
        self.diffractometer_hwobj.reject_centring()  

    def cancel_centring(self, reject = False): 
        """
        Descript. :
        """
        self.diffractometer_hwobj.cancel_centring_method(reject = reject)

    def start_visual_align(self):
        """
        Descript. :
        """
        if len(self.selected_centring_points) == 2:
            self.diffractometer_hwobj.visual_align(\
                 self.selected_centring_points[0],
                 self.selected_centring_points[1])
        else:
            msg = "Select two centred position (CTRL click) to continue"
            logging.getLogger("user_level_log").error(msg)  

    def create_line(self):
        """
        Descript. :
        """
        if len(self.selected_centring_points) > 1:
            line = GraphicsItemLine(self.selected_centring_points[0],
                                    self.selected_centring_points[1])
            self.add_shape(line)
        else:
            msg = "Please select two points (with same kappa and phi) " + \
                  "to create a helical line"
            logging.getLogger("user_level_log").error(msg)

    def create_grid_drag(self, spacing = (0, 0)):
        """
        Descript. :
        """ 
        self.graphics_grid_draw_item = GraphicsItemGrid(self, self.beam_info_dict, 
             spacing, self.pixels_per_mm)
        self.graphics_grid_draw_item.index = self.grid_count
        self.graphics_view.graphics_scene.addItem(self.graphics_grid_draw_item)
        self.graphics_grid_draw_item.show()
        self.in_grid_drawing_state = True

    def create_grid_click(self):
        """
        Descript. :
        """
        pass

    def refresh_camera(self):
        """
        Descript. :
        """
        pass

 
class GraphicsItem(QtGui.QGraphicsItem):
    """
    Descript. : Base class for all items.
                All items have minimal set of attributes that are
                needed to draw item on the GraphicsScene
    """
    def __init__(self, parent=None, position_x = 0, position_y = 0):
        QtGui.QGraphicsItem.__init__(self)
        self.index = None
        self.base_color = None
        self.used_count = 0
        self.pixels_per_mm = [None, None]
        self.rect = QtCore.QRectF(0, 0, 0, 0)
        self.solid_line_style = QtCore.Qt.SolidLine

        self.setPos(position_x, position_y)
        self.setMatrix = QtGui.QMatrix()

    def set_index(self):
        return self.index

    def get_index(self, index):
        self.index = index

    def boundingRect(self):
        return self.rect.adjusted(-2, -2, 2, 2)

    def set_size(self, width, height):
        self.rect.setWidth(width)
        self.rect.setHeight(height)

    def set_position(self, position_x, position_y):
        if (position_x is not None and
            position_y is not None):
            self.setPos(position_x, position_y)

    def set_visible(self, is_visible):
        if is_visible: 
            self.show()
        else:
            self.hide()

    def set_pixels_per_mm(self, pixels_per_mm):
        self.pixels_per_mm = pixels_per_mm
        self.update_item()

    def get_display_name(self):
        return "Item %d" % self.index

    def get_full_name(self): 
        return self.get_display_name() 

    def set_base_color(self, color):
        self.base_color = color 

    def update_item(self):
        self.scene().update()

    def mousePressEvent(self, event):
        self.update()
        self.scene().itemClickedSignal.emit(self, self.isSelected())

class GraphicsItemBeam(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.__shape_is_rectangle = True
        self.__size_pix = [0, 0]
        self.__position_x = position_x
        self.__position_y = position_y
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | \
                      QtGui.QGraphicsItem.ItemIsSelectable)
        
    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)
        if option.state & QtGui.QStyle.State_Selected:
            pen.setColor(QtCore.Qt.red)
        else:
            pen.setColor(QtCore.Qt.blue)
        painter.setPen(pen)
        if self.__shape_is_rectangle:
            painter.drawRect(self.__position_x - self.__size_pix[0] / 2,
                             self.__position_y - self.__size_pix[1] / 2,
                             self.__size_pix[0], self.__size_pix[1])
        else:
            painter.drawEllipse(self.__position_x - self.__size_pix[0] / 2,
                                self.__position_y - self.__size_pix[1] / 2,
                                self.__size_pix[0], self.__size_pix[1])
        pen.setColor(QtCore.Qt.red) 
        painter.setPen(pen)
        painter.drawLine(self.__position_x - 15, self.__position_y,
                         self.__position_x + 15, self.__position_y)
        painter.drawLine(self.__position_x, self.__position_y - 15, 
                         self.__position_x, self.__position_y + 15)  

    def set_position(self, position_x, position_y):
        self.__position_x = position_x
        self.__position_y = position_y
 
    def set_beam_info(self, beam_info_dict):
        self.__shape_is_rectangle = beam_info_dict.get("shape") == "rectangular"
        self.__size_pix = [beam_info_dict.get("size_x") * self.pixels_per_mm[0],
                           beam_info_dict.get("size_y") * self.pixels_per_mm[1]]

class GraphicsItemPoint(GraphicsItem):
    """
    Descrip. : Centred point class.
    Args.    : parent, centred position (motors position dict, 
               full_centring (True if 3click centring), initial position)
    """
    def __init__(self, centred_position = None, full_centring = True,
                 position_x = 0, position_y = 0):
        GraphicsItem.__init__(self, position_x, position_y)

        self.__full_centring = full_centring
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)

        if centred_position is None:
            self.__centred_position = queue_model_objects.CentredPosition()
            self.__centred_position.centring_method = False
        else:
            self.centred_position = centred_position
        self.set_size(20, 20)
        self.set_position(position_x, position_y)

    def get_display_name(self):
        return "Point %d" % self.index

    def get_centred_positions(self):
        return [self.__centred_position]

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)

        if option.state & QtGui.QStyle.State_Selected:
            pen.setColor(QtCore.Qt.green)
        else:
            if self.base_color:
                pen.setColor(self.base_color)
            else:
                pen.setColor(QtCore.Qt.yellow)

        painter.setPen(pen)
        painter.drawEllipse(self.rect.left(), self.rect.top(),
                            20, 20)
        painter.drawLine(self.rect.left(), self.rect.top(),
                         self.rect.right(), self.rect.bottom())
        painter.drawLine(self.rect.right(), self.rect.top(),
                         self.rect.left(), self.rect.bottom())
        if self.index:
            display_str = str(self.index)
        else:
            display_str = "#"
        if self.isSelected():
            display_str += " selected"

        painter.drawText(self.rect.right() + 2, self.rect.top(), display_str)

    def get_position(self):
        return self.__position_x, self.__position_y

    def set_position(self, position_x, position_y):
        self.__position_x = position_x
        self.__position_y = position_y
        self.setPos(self.__position_x - 10, self.__position_y - 10)

    def mouseDoubleClickEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.scene().itemDoubleClickedSignal.emit(self)
        self.update()


class GraphicsItemLine(GraphicsItem):
    """
    Descrip. : Line class.
    """
    def __init__(self, cp_start, cp_end):
        GraphicsItem.__init__(self)

        self.__cp_start = cp_start
        self.__cp_end = cp_end
        self.setPos(0, 0)
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)

    def get_display_name(self):
        return "Line %d" % self.index

    def get_full_name(self):
        return "Line (points: %d, %d / kappa: %.2f phi: %.2f)" % \
                (self.__cp_start.index, 
                 self.__cp_end.index,
                 self.__cp_start.centred_position.kappa,
                 self.__cp_end.centred_position.kappa_phi)

    def get_graphics_points(self):
        return [self.__cp_start, self.__cp_end]

    def get_centred_positions(self):
        return [self.__cp_start.centred_position, self.__cp_end.centred_position]

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(2)

        if option.state & QtGui.QStyle.State_Selected:
            pen.setColor(QtCore.Qt.green)
        else:
            pen.setColor(QtCore.Qt.yellow)
        painter.setPen(pen)
        (start_cp_x, start_cp_y) = self.__cp_start.get_position()
        (end_cp_x, end_cp_y) = self.__cp_end.get_position()

        painter.drawLine(start_cp_x, start_cp_y,
                         end_cp_x, end_cp_y)
        if self.index:
            #line_inf = "Line %d (%d : %d)" %(self.index, self.cp_start.index,
            #           self.cp_end.index)
            painter.drawText(self.rect.right() + 2, 
                             self.rect.top(), 
                             str(self.index))
        else:
            painter.drawText(self.rect.right() + 2, 
                             self.rect.top(), "#")

    def setSelected(self, state):
        GraphicsItem.setSelected(self, state)
        self.__cp_start.setSelected(state)
        self.__cp_end.setSelected(state)

    def get_points_index(self):
        return (self.__cp_start.index, self.__cp_end.index)

    def set_position(self, position_x, position_y):
        return


class GraphicsItemGrid(GraphicsItem):
    """
    Descrip. : Grid representation is based on two grid states:
               __draw_mode = True: user defines grid size
                             False: grid is defined
               In draw mode during the draw grid size is esitmated and based
               on the cell size and number of col and row actual grid
               object is painted. After drawing corner_points are added. These
               4 corner points are motor position dict. When one or several 
               motors are moved corner_cord are updated and grid is painted
               in projection mode.              
    """
    def __init__(self, parent, beam_info, spacing, pixels_per_mm):
        GraphicsItem.__init__(self, parent)

        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)  

        self.__diffractometer_hwobj = parent.diffractometer_hwobj
        self.pixels_per_mm = pixels_per_mm
        self.__beam_size_microns = [beam_info.get("size_x"), 
                                    beam_info.get("size_y")]
        self.__beam_size_pix = [0, 0] 
        self.__beam_is_rectangle = beam_info.get("shape") == "rectangle"
        self.__spacing_microns = spacing
        self.__spacing_pix = [0, 0]
        self.__cell_size_microns = [0, 0]
        self.__cell_size_pix = [0, 0]
        self.__corner_coord = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.__num_colls = 0      
        self.__num_rows = 0
        self.__num_lines = 0
        self.__num_images_per_line = 0
        self.__first_image_num = 1
        self.__centred_point = None
        self.__draw_mode = False
        self.__draw_projection = False

        self.__motor_pos_corner = None
        self.__motor_pos_center = None
        self.__grid_range_pix = {}
        self.__grid_direction = {"fast": (0, 1), "slow": (1, 0)}
        self.__reversing_rotation = True
        self.__score = None 
         
        self.update_item()

    def get_display_name(self):
        return "Grid %d" % self.index

    def get_full_name(self):
        return "Grid %d (hor. spacing: %.1f, ver. spacing: %.1f, beam size: %d, %d)" %\
               (self.index, self.__spacing_microns[0], self.__spacing_microns[1],
                self.__beam_size_microns[0], self.__beam_size_microns[1])

    def update_item(self):
        self.__cell_size_microns = [self.__beam_size_microns[0] + self.__spacing_microns[0] * 2,
                                    self.__beam_size_microns[1] + self.__spacing_microns[1] * 2]
        self.__spacing_pix = [self.pixels_per_mm[0] * self.__spacing_microns[0],
                              self.pixels_per_mm[1] * self.__spacing_microns[1]]
        self.__beam_size_pix = [self.pixels_per_mm[0] * self.__beam_size_microns[0],
                                self.pixels_per_mm[1] * self.__beam_size_microns[1]]
        self.__cell_size_pix = [self.pixels_per_mm[0] * self.__cell_size_microns[0],
                                self.pixels_per_mm[1] * self.__cell_size_microns[1]]

    def set_draw_start_position(self, pos_x, pos_y):
        self.__corner_coord[0][0] = pos_x
        self.__corner_coord[0][1] = pos_y
        self.__corner_coord[1][1] = pos_y
        self.__corner_coord[2][0] = pos_x
        self.scene().update()

    def set_draw_end_position(self, pos_x, pos_y):
        self.__corner_coord[1][0] = pos_x
        self.__corner_coord[2][1] = pos_y
        self.__corner_coord[3][0] = pos_x
        self.__corner_coord[3][1] = pos_y
        self.scene().update()

    def update_motor_pos_corner(self):
        self.__motor_pos_corner = []
        for corner_coord in self.__corner_coord:
            #motor_pos = self.__diffractometer_hwobj.get_centred_point_from_coord(\
            #      corner_coord[0], corner_coord[1])
            #self.__motor_pos_corner.append(motor_pos)     
            pass        

    def set_spacing(self, spacing):
        self.__spacing_microns = spacing
        self.update_item()
        self.scene().update()

    def set_draw_mode(self, draw_mode):
        self.__draw_mode = draw_mode 

    def is_draw_mode(self):
        return self.__draw_mode

    def get_properties(self):
        return {"name": "Grid %d" % self.index,
                "beam_hor" : self.__beam_size_microns[0],
                "beam_ver" : self.__beam_size_microns[1],
                "spacing_hor": self.__spacing_microns[0],
                "spacing_ver": self.__spacing_microns[1],  
                "corner_points" : self.__corner_points,
                "corner_coord" : self.__corner_coord,
                "num_col" : self.__num_colls,
                "num_row" : self.__num_rows,
                "num_lines": self.__num_lines,
                "num_images_per_line": self.__num_images_per_line,
                "first_image_num": self.__first_image_num}

    def set_properties(self, properties_dict):
        self.__beam_size_hor = properties_dict.get("beam_hor")
        self.__beam_size_ver = properties_dict.get("beam_ver")
        self.__cell_width = properties_dict.get("cell_width")
        self.__cell_height = properties_dict.get("cell_height")
        self.__corner_points = properties_dict.get("corner_pos") 
        self.__corner_coord = properties_dict.get("corner_coord")
        self.__num_col = properties_dict.get("num_col")
        self.__num_row = properties_dict.get("num_row")

    def get_corner_coord(self):
        return self.__corner_coord

    def set_motor_pos_corner(self, motor_pos_corner):
        self.__motor_pos_corner = motor_pos_corner

    def get_motor_pos_corner(self):
        return self.__motor_pos_corner

    def fix_motor_pos_center(self):
        motor_pos = self.__diffractometer_hwobj.\
             get_centred_point_from_coord(self.__x_mid, self.__y_mid)
        self.__motor_pos_center = queue_model_objects.CentredPosition(motor_pos)

    def get_motor_pos_center(self):
        return self.__motor_pos_center

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setColor(QtCore.Qt.darkGray)
        pen.setWidth(1)
        brush = QtGui.QBrush(self.solid_line_style)
        brush_color = QtGui.QColor(70,70,165)
        brush_color.setAlpha(70)
        brush.setColor(brush_color)
        brush.setStyle(QtCore.Qt.SolidPattern)

        if self.__draw_mode:
            pen.setStyle(QtCore.Qt.DotLine)
        if self.__draw_mode or self.isSelected():
            pen.setColor(QtCore.Qt.green)

        painter.setPen(pen)
        painter.setBrush(brush)
       
        #During the drawing estimates number of colls and rows
        if self.__draw_mode:
           if self.__cell_size_pix[0] > 0:
               self.__num_colls = int((abs(self.__corner_coord[1][0] - \
                    self.__corner_coord[0][0]) / self.__cell_size_pix[0]))
           if self.__cell_size_pix[1] > 0:
               self.__num_rows = int(abs((self.__corner_coord[3][1] - \
                    self.__corner_coord[1][1]) / self.__cell_size_pix[1]))

        if not self.__draw_projection:
            if self.__num_rows * self.__num_colls > pow(2, 16):
                msg_text = "Unable to draw grid containing more than %d cells!" % pow(2, 16)
                logging.getLogger("user_level_log").info(msg_text)
                return

            self.__grid_size_pix = [self.__num_colls * self.__cell_size_pix[0],
                                    self.__num_rows * self.__cell_size_pix[1]]

            self.__num_cells = self.__num_rows * self.__num_colls
            #Based on the grid directions estimates number of lines and 
            #number of images per line
            self.__num_lines =  abs(self.__grid_direction['fast'][1] * \
                 self.__num_colls) + abs(self.__grid_direction['slow'][1] * \
                 self.__num_rows)
            self.__num_images_per_line = abs(self.__grid_direction['fast'][0] * \
                self.__num_colls) + abs(self.__grid_direction['slow'][0] * \
                self.__num_rows)

            #Also grid range is estimated 
            self.__grid_range_pix["fast"] = abs(self.__grid_direction['fast'][0] * \
                 (self.__grid_size_pix[0] - self.__cell_size_pix[0])) + \
                 abs(self.__grid_direction['fast'][1] * \
                 (self.__grid_size_pix[1] - self.__cell_size_pix[1]))
            self.__grid_range_pix["slow"] = abs(self.__grid_direction['slow'][0] * \
                 (self.__grid_size_pix[0] - self.__cell_size_pix[0])) + \
                 abs(self.__grid_direction['slow'][1] * \
                 (self.__grid_size_pix[1] - self.__cell_size_pix[1]))

            #cell width and height for drawing are estimated
            if self.__corner_coord[0][0] < self.__corner_coord[1][0]:
                self.__x_mid = self.__corner_coord[0][0] + self.__grid_size_pix[0] / 2
            else:
                self.__x_mid = self.__corner_coord[0][0] - self.__grid_size_pix[0] / 2
            if self.__corner_coord[0][1] < self.__corner_coord[3][1]:
                self.__y_mid = self.__corner_coord[0][1] + self.__grid_size_pix[1] / 2
            else:
                self.__y_mid = self.__corner_coord[0][1] - self.__grid_size_pix[1] / 2 

            #pen.setStyle(self.solid_line_style)
            #painter.setPen(pen)
            for i in range(0, self.__num_colls + 1):
                offset = i * self.__cell_size_pix[0]
                painter.drawLine(self.__corner_coord[0][0] + offset,
                                 self.__corner_coord[0][1],
                                 self.__corner_coord[0][0] + offset,
                                 self.__corner_coord[0][1] + self.__num_rows * self.__cell_size_pix[1])
            for i in range(0, self.__num_rows + 1):
                offset = i * self.__cell_size_pix[1]
                painter.drawLine(self.__corner_coord[0][0],
                                 self.__corner_coord[0][1] + offset,
                                 self.__corner_coord[0][0] + self.__num_colls * self.__cell_size_pix[0],
                                 self.__corner_coord[0][1] + offset)    

            #Draws beam shape and displays number of image if 
            #less than 1000 cells and size is greater than 20px
            cell_index = 0
            if self.__num_cells < 1000 and self.__cell_size_pix[1] > 20:
                for col in range(self.__num_colls):
                    coll_offset = col * self.__cell_size_pix[0]
                    for row in range(self.__num_rows):
                        row_offset = row * self.__cell_size_pix[1]
                        if self.__beam_is_rectangle:
                            painter.drawRect(self.__corner_coord[0][0] + coll_offset + self.__spacing_pix[0],
                                             self.__corner_coord[0][1] + row_offset + self.__spacing_pix[1],
                                             self.__beam_size_pix[0], self.__beam_size_pix[1])
                        else:
                            painter.drawEllipse(self.__corner_coord[0][0] + coll_offset + self.__spacing_pix[0],
                                                self.__corner_coord[0][1] + row_offset + self.__spacing_pix[1],
                                                self.__beam_size_pix[0], self.__beam_size_pix[1])
                        line, image = self.get_line_image_num(cell_index + self.__first_image_num)
                        x, y = self.get_coord_from_line_image(line, image)
                        tr = QtCore.QRect(x - self.__cell_size_pix[0] / 2, 
                                          y - self.__cell_size_pix[1] / 2,
                                          self.__cell_size_pix[0], 
                                          self.__cell_size_pix[1])
                        if self.__score:
                            painter.drawText(tr, QtCore.Qt.AlignCenter, "%0.3f" % \
                                    self.__score[cell_index - 1])
                        else:
                            painter.drawText(tr, QtCore.Qt.AlignCenter, \
                                    str(cell_index + self.__first_image_num))
                        cell_index += 1
            painter.drawText(self.__corner_coord[0][0] + self.__grid_size_pix[0] + 3,
                             self.__corner_coord[1][1] - 3,
                             "Grid %d" % (self.index + 1)) 
 
        else:
            print "draw projection"
 
    def move_by_pix(self, move_direction):
        move_delta_x = 0
        move_delta_y = 0
        if move_direction == "left":
            move_delta_x = - 1
        elif move_direction == "right":
            move_delta_x = 1        
        elif move_direction == "up":
            move_delta_y = - 1
        elif move_direction == "down":
            move_delta_y = 1
        for corner_coord in self.__corner_coord:
            corner_coord[0] += move_delta_x
            corner_coord[1] += move_delta_y    
        self.update_motor_pos_corner()
        self.scene().update()

    def get_grid_size_pix(self):
        width_pix = self.__cell_size_pix[0] * self.__num_colls
        height_pix = self.__cell_size_pix[1] * self.__num_rows
        return (width_pix, height_pix) 

    def get_line_image_num(self, image_number):
        """
        Descript. :  from serial frame (==image) number returns a number 
                     of line == grid coord. along scan slow direction,
                     image == grid coord. along scan fast direction
        """
        line =  int((image_number - self.__first_image_num) / \
                     self.__num_images_per_line)
        image = image_number - self.__first_image_num - \
                line * self.__num_images_per_line
        return line, image

    def get_coord_from_line_image(self, line, image):
        """
        Descript. : returns the screen coordinates x, y in pixel, of a middle 
                    of the cell that correspoinds to 
        Args.     : number an frame #image in line #line  
        """
        a, b = self.get_coord_ref_from_line_image(line, image)

        coord_x = self.__x_mid + self.__grid_range_pix['fast'] * \
                  self.__grid_direction['fast'][0] * a  + \
                  self.__grid_range_pix['slow'] * \
                  self.__grid_direction['slow'][0] * b
        coord_y = self.__y_mid + self.__grid_range_pix['fast'] * \
                  self.__grid_direction['fast'][1] * a  + \
                  self.__grid_range_pix['slow'] * \
                  self.__grid_direction['slow'][1] * b
        return coord_x, coord_y

    def get_coord_ref_from_line_image(self, line, image):
        """
        Descript. : returns nameless constants used in conversion between 
                    scan and screen coordinates. 
        """
        a = 0.5
        if self.__num_images_per_line > 1:
            a = 0.5 - float(image) / (self.__num_images_per_line - 1)
        if self.__reversing_rotation:
            a = pow(-1, line % 2) * a

        b = 0.5
        if self.__num_lines > 1:
            b = 0.5 - float(line)  / (self.__num_lines - 1)
        return a, b
 
class GraphicsItemScale(GraphicsItem):
    """
    Descrip. : Displays vertical and horizontal scale on the bottom, left 
               corner. Horizontal scale is scaled to 50 or 100 microns and
               vertical scale is two times shorter.
    """
    HOR_LINE_LEN = [500, 200, 100, 50]

    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.__scale_len = 0

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(3)
        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
      
        hor_scale_len_pix = self.pixels_per_mm[0] * self.__scale_len / 1000 
        ver_scale_len_pix = self.pixels_per_mm[1] * self.__scale_len / 1000 / 2

        painter.drawLine(0, 0, hor_scale_len_pix, 0)
        painter.drawText(hor_scale_len_pix + 3, - 5, "%d" % self.__scale_len)
        painter.drawLine(0, 0, 0, - ver_scale_len_pix)
        painter.drawText(3, - ver_scale_len_pix, "%d" % (self.__scale_len / 2))

    def set_pixels_per_mm(self, pixels_per_mm):
        self.pixels_per_mm = pixels_per_mm
        
        for line_len in GraphicsItemScale.HOR_LINE_LEN:
            if self.pixels_per_mm[0] * line_len / 1000 <= 250:
               self.__scale_len = line_len
               break

class GraphicsItemOmegaReference(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.parent = parent
        self.__start_x = 0
        self.__start_y = 0
        self.__end_x = 0
        self.__end_y = 0

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.white)
        painter.setPen(pen)
        painter.drawLine(self.__start_x, self.__start_y, 
                         self.__end_x, self.__end_y)

    def set_reference(self, omega_reference):
        line_length = self.parent.graphics_scene_size
        if omega_reference[0] > 0:
            #Omega reference is a vertical axis
            self.__start_x = omega_reference[0]
            self.__end_x = omega_reference[0]
            self.__start_y = 0
            self.__end_y = line_length[1]
        else:
            self.__start_x = 0
            self.__end_x = line_length[0]
            self.__start_y = omega_reference[1]
            self.__end_y = omega_reference[1]

class GraphicsItemCentringLines(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        #self.parent = parent

        self.__coord_x = 200
        self.__coord_y = 100

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.yellow)
        painter.setPen(pen)
        painter.drawLine(self.__coord_x, 0, 
                         self.__coord_x, self.scene().height())
        painter.drawLine(0, self.__coord_y, 
                         self.scene().width(), self.__coord_y)

    def set_coordinates(self, x, y):
        self.__coord_x = x
        self.__coord_y = y 
        self.scene().update()        

class GraphicsItemMeasureDistance(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.__start_x = 0 
        self.__start_y = 0
        self.__end_x = 0
        self.__end_y = 0
        self.__dist_microns = 0
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
        painter.drawLine(self.__start_x, self.__start_y,
                         self.__end_x, self.__end_y)
        painter.drawText(self.__end_x + 10, self.__end_y + 10,
                         "%.2f %s" % (self.__dist_microns, u"\u00B5"))
 
    def set_start_coord(self, coord):
        self.__start_x = coord[0]
        self.__start_y = coord[1]

    def set_end_coord(self, coord):
        self.__end_x = coord[0]
        self.__end_y = coord[1]
        self.__dist_microns = math.sqrt(pow((self.__start_x - self.__end_x) / \
            self.pixels_per_mm[0], 2) + pow((self.__start_y - self.__end_y) / \
            self.pixels_per_mm[1], 2)) * 1000
        self.scene().update()

class GraphicsItemMeasureAngle(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.measure_points = None
        self.current_measure_point = None
        self.measured_angle = None

        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
        if len(self.measure_points) > 1:
             painter.drawLine(self.measure_points[0][0], self.measure_points[0][1],
                              self.measure_points[1][0], self.measure_points[1][1])
             if len(self.measure_points) > 2:
                 painter.drawLine(self.measure_points[1][0], self.measure_points[1][1],
                                  self.measure_points[2][0], self.measure_points[2][1])
                 painter.drawText(self.measure_points[2][0] + 10, 
                                  self.measure_points[2][1] + 10, 
                                  "%.2f %s" % (self.measured_angle, u"\u00B0"))

    def set_start_coord(self, coord):
        self.measured_angle = 0
        self.measure_points = []
        self.measure_points.append([coord[0], coord[1]])
        self.measure_points.append([coord[0], coord[1]])
        self.current_measure_point = 1

    def set_coord(self, coord):
        self.measure_points[len(self.measure_points) - 1][0] = coord[0]
        self.measure_points[len(self.measure_points) - 1][1] = coord[1]
        if len(self.measure_points) == 3: 
            self.measured_angle = - math.degrees(math.atan2(self.measure_points[2][1] - \
                 self.measure_points[1][1], self.measure_points[2][0] - \
                 self.measure_points[1][0]) - math.atan2(self.measure_points[0][1] - \
                 self.measure_points[1][1], self.measure_points[0][0] - \
                 self.measure_points[1][0]))
        self.scene().update()

    def store_coord(self):
        self.measure_points.append([self.measure_points[len(self.measure_points) - 1][0],
                                    self.measure_points[len(self.measure_points) - 1][1]])
        return not len(self.measure_points) > 3        

class GraphicsItemMeasureArea(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.measured_area = None
        self.current_point = None
        self.last_point_set = None
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        self.measure_polygon = QtGui.QPolygon(self) 
        self.current_point = QtCore.QPoint(0,0)
        self.min_max_coord = None

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.solid_line_style)
        pen.setWidth(1)
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
        brush = QtGui.QBrush(self.solid_line_style)
        brush_color = QtGui.QColor(70,70,165)
        brush_color.setAlpha(120)
        brush.setColor(brush_color)
        brush.setStyle(QtCore.Qt.Dense4Pattern)
        painter.setBrush(brush)

        painter.drawLine(self.measure_polygon.last(),
                         self.current_point)
        painter.drawPolygon(self.measure_polygon, QtCore.Qt.OddEvenFill)
        painter.drawText(self.current_point.x() + 10,
                         self.current_point.y() + 10,
                         "%.2f %s" % (self.measured_area, u"\u00B5"))
        
        if self.min_max_coord:
            hor_size = abs(self.min_max_coord[0][0] - self.min_max_coord[1][0]) /\
                       self.pixels_per_mm[0] * 1000
            ver_size = abs(self.min_max_coord[0][1] - self.min_max_coord[1][1]) /\
                       self.pixels_per_mm[1] * 1000
            painter.drawLine(self.min_max_coord[0][0] - 10,
                             self.min_max_coord[0][1],
                             self.min_max_coord[0][0] - 10,
                             self.min_max_coord[1][1])
            painter.drawText(self.min_max_coord[0][0] - 40,
                             self.min_max_coord[0][1],
                             "%.1f %s" % (ver_size, u"\u00B5"))
            painter.drawLine(self.min_max_coord[0][0],
                             self.min_max_coord[1][1] + 10,
                             self.min_max_coord[1][0],
                             self.min_max_coord[1][1] + 10)  
            painter.drawText(self.min_max_coord[1][0],
                             self.min_max_coord[1][1] + 25,
                             "%.1f %s" % (hor_size, u"\u00B5")) 
                             

    def set_start_coord(self, coord):
        self.min_max_coord = None
        self.measured_area = 0
        self.measure_polygon.clear()
        self.measure_polygon.append(QtCore.QPoint(coord[0], coord[1]))
        self.current_point = QtCore.QPoint(coord[0], coord[1])

    def set_coord(self, coord):
        if not self.last_point_set:
            self.current_point.setX(coord[0])
            self.current_point.setY(coord[1])
            self.measured_area = 0
            if self.measure_polygon.count() > 2:
                for point_index in range(self.measure_polygon.count() - 1):
                    self.measured_area += self.measure_polygon.value(point_index).x() * \
                                          self.measure_polygon.value(point_index + 1).y()
                    self.measured_area -= self.measure_polygon.value(point_index).y() * \
                                          self.measure_polygon.value(point_index + 1).x()
                self.measured_area += self.measure_polygon.value(len(self.measure_polygon) - 1).x() * \
                                      self.measure_polygon.value(0).y()
                self.measured_area -= self.measure_polygon.value(len(self.measure_polygon) - 1).y() * \
                                      self.measure_polygon.value(0).x() 
                self.measured_area /= self.pixels_per_mm[0] * self.pixels_per_mm[1]
            self.scene().update()

    def store_coord(self, last = None):
        self.last_point_set = last
        self.measure_polygon.append(self.current_point) 
        if self.min_max_coord is None:
            self.min_max_coord = [[self.measure_polygon.value(0).x(),
                                  self.measure_polygon.value(0).y()],  
                                  [self.measure_polygon.value(0).x(),
                                  self.measure_polygon.value(0).y()]]
        for point_index in range(1, self.measure_polygon.count()):
            if self.measure_polygon.value(point_index).x() < self.min_max_coord[0][0]:
                self.min_max_coord[0][0] = self.measure_polygon.value(point_index).x()
            elif self.measure_polygon.value(point_index).x() > self.min_max_coord[1][0]: 
                self.min_max_coord[1][0] = self.measure_polygon.value(point_index).x() 
            if self.measure_polygon.value(point_index).y() < self.min_max_coord[0][1]:
                self.min_max_coord[0][1] = self.measure_polygon.value(point_index).y()
            elif self.measure_polygon.value(point_index).y() > self.min_max_coord[1][1]: 
                self.min_max_coord[1][1] = self.measure_polygon.value(point_index).y()
        self.scene().update()


class GraphicsView(QtGui.QGraphicsView):
    mouseMovedSignal = QtCore.pyqtSignal(int, int)
    keyPressedSignal = QtCore.pyqtSignal(str)

    def __init__ (self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.graphics_scene = GraphicsScene(self)
        self.setScene(self.graphics_scene)  
        self.graphics_scene.clearSelection()
        self.setMouseTracking(True)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def mouseMoveEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.mouseMovedSignal.emit(position.x(), position.y())
        self.update()
 
    def keyPressEvent(self, event):
        key_type = None
        if event.key() in(QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):  
            key_type = "Delete"
        if key_type:
            self.keyPressedSignal.emit(key_type)


class GraphicsScene(QtGui.QGraphicsScene):
    mouseClickedSignal = QtCore.pyqtSignal(int, int)
    mouseDoubleClickedSignal = QtCore.pyqtSignal(int, int)  
    mouseReleasedSignal = QtCore.pyqtSignal(int, int)
    itemDoubleClickedSignal = QtCore.pyqtSignal(GraphicsItem)
    itemClickedSignal = QtCore.pyqtSignal(GraphicsItem, bool) 

    def __init__ (self, parent=None):
        super(GraphicsScene, self).__init__ (parent)


class GraphicsCameraFrame(QtGui.QGraphicsPixmapItem):
    def __init__ (self, parent=None):
        super(GraphicsCameraFrame, self).__init__(parent)

    def mousePressEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.scene().mouseClickedSignal.emit(position.x(), position.y())
        self.update()  

    def mouseDoubleClickEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.scene().mouseDoubleClickedSignal.emit(position.x(), position.y())
        self.update()

    def mouseReleaseEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.scene().mouseReleasedSignal.emit(position.x(), position.y())
        self.update()
        self.setSelected(True)
