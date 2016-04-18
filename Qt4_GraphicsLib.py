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
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

"""
Graphics item library:
 - GraphicsItem : base class for all items
 - GraphicsItemBeam : beam shape
 - GraphicsItemPoint : centring point
 - GraphicsItemLine : line between two centring points
 - GraphicsItemGrid : 2D grid
 - GraphicsItemScale : scale 
 - GraphicsItemOmegaReference : omega rotation line
 - GraphicsItemCentringLine : centring lines for 3 click centring
 - GraphicsItemMeasureDistance : line to measure distance
 - GraphicsItemMeasureAngle : object to measure angle between two lines
 - GraphicsItemMeasureArea : item to measure area
 - GraphicsSelectTool : item selection tool
 - GraphicsItemMoveBeamMark : item to move beam mark
 - GraphicsCameraFrame : camera frame
 - GraphicsScene : scene where all items are displayed
 - GraphicsView : widget that contains GraphicsScene
"""

import copy
import math
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import queue_model_objects_v1 as queue_model_objects

SELECTED_COLOR = QtCore.Qt.green
NORMAL_COLOR = QtCore.Qt.yellow
SOLID_LINE_STYLE = QtCore.Qt.SolidLine


class GraphicsItem(QtGui.QGraphicsItem):
    """Base class for all graphics items.
    """

    def __init__(self, parent=None, position_x=0, position_y=0):
        """
        
        :param position_x: x coordinate in the scene
        :type position_x: int
        :param position_y: y coordinate in the scene
        :type position_y: int
        """
      
        QtGui.QGraphicsItem.__init__(self)
        self.index = None
        self.base_color = None
        self.used_count = 0
        self.pixels_per_mm = [0, 0]
        self.start_coord = [0, 0]
        self.end_coord = [0, 0]
        self.beam_size_microns = [0, 0]
        self.beam_size_pix = [0, 0]
        self.beam_is_rectangle = False
        self.rect = QtCore.QRectF(0, 0, 0, 0)
        self.display_beam_shape = None

        self.setPos(position_x, position_y)
        self.setMatrix = QtGui.QMatrix()

        self.custom_pen = QtGui.QPen(SOLID_LINE_STYLE)
        self.custom_pen.setWidth(1)
        self.custom_pen.setColor(QtCore.Qt.white)

        self.custom_brush = QtGui.QBrush(SOLID_LINE_STYLE)
        brush_color = QtGui.QColor(70, 70, 165)
        brush_color.setAlpha(70)
        self.custom_brush.setColor(brush_color)
        self.custom_brush.setStyle(QtCore.Qt.SolidPattern)

    def boundingRect(self):
        """Returns adjusted rect
      
        :returns: QRect
        """
 
        return self.rect.adjusted(0, 0, 0, 0)

    def set_size(self, width, height):
        """Sets fixed size

        :param width: width
        :type width: int
        :param height: height
        :type height: int
        """

        self.rect.setWidth(width)
        self.rect.setHeight(height)

    def set_start_position(self, position_x, position_y):
        """Sets start position
        """
       
        if (position_x is not None and
            position_y is not None):
            self.start_coord = [position_x, position_y]
        self.scene().update()

    def get_start_position(self):
        """Returns start coordinate of the shape
 
        :return: list with two int
        """

        return self.start_coord

    def set_end_position(self, position_x, position_y):
        if (position_x is not None and
            position_y is not None):
            self.end_coord = [position_x, position_y]
        self.scene().update()

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

    def toggle_selected(self):
        self.setSelected(not self.isSelected()) 
        self.update()

    def set_beam_info(self, beam_info):
        self.beam_is_rectangle = beam_info.get("shape") == "rectangular"
        self.beam_size_microns[0] = beam_info.get("size_x", 0)
        self.beam_size_microns[1] = beam_info.get("size_y", 0) 
        self.beam_size_pix[0] = self.beam_size_microns[0] * self.pixels_per_mm[0]
        self.beam_size_pix[1] = self.beam_size_microns[1] * self.pixels_per_mm[1]

    def set_pixels_per_mm(self, pixels_per_mm):
        self.pixels_per_mm = pixels_per_mm
        self.beam_size_pix[0] = self.beam_size_microns[0] * self.pixels_per_mm[0]
        self.beam_size_pix[1] = self.beam_size_microns[1] * self.pixels_per_mm[1]

class GraphicsItemBeam(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.beam_is_rectangle = True
        self.start_coord = [position_x, position_y]
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable)
        
    def paint(self, painter, option, widget):
        self.custom_pen.setColor(QtCore.Qt.blue)
        painter.setPen(self.custom_pen)
        if self.beam_is_rectangle:
            painter.drawRect(self.start_coord[0] - self.beam_size_pix[0] / 2, 
                             self.start_coord[1] - self.beam_size_pix[1] / 2,
                             self.beam_size_pix[0], self.beam_size_pix[1])
        else:
            painter.drawEllipse(self.start_coord[0] - self.beam_size_pix[0] / 2, 
                                self.start_coord[1] - self.beam_size_pix[1] / 2,
                                self.beam_size_pix[0], self.beam_size_pix[1])
        self.custom_pen.setColor(QtCore.Qt.red) 
        painter.setPen(self.custom_pen)
        painter.drawLine(self.start_coord[0] - 10, self.start_coord[1],
                         self.start_coord[0] + 10, self.start_coord[1]) 
        painter.drawLine(self.start_coord[0], self.start_coord[1] - 10,
                         self.start_coord[0], self.start_coord[1] + 10) 


class GraphicsItemPoint(GraphicsItem):
    """Centred point class.
    """

    def __init__(self, centred_position = None, full_centring = True,
                 position_x = 0, position_y = 0):
        """
        :param: parent
        :param centred position: motor positions 
        :type centred_position: dict with motors positions
        :param full_centring: indicates centring method
        :type full_centring : bool. True if 3click centring
        """ 

        GraphicsItem.__init__(self, position_x, position_y)

        self.__full_centring = full_centring
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)

        if centred_position is None:
            self.__centred_position = queue_model_objects.CentredPosition()
            self.__centred_position.centring_method = False
        else:
            self.__centred_position = centred_position
        self.set_size(20, 20)

        self.start_coord = [position_x, position_y] 
        self.setPos(position_x - 10, position_y - 10)

    def get_display_name(self):
        return "Point %d" % self.index

    def get_full_name(self):
        full_name = "Point %d" % self.index
        if self.__centred_position.kappa and \
           self.__centred_position.kappa_phi:
            full_name += " (kappa: %0.2f phi: %0.2f)" % \
                (self.__centred_position.kappa,
                 self.__centred_position.kappa_phi)
        return full_name

    def get_centred_position(self):
        return self.__centred_position

    def set_centred_position(self, centred_position):
        self.__centred_position = centred_position

    def paint(self, painter, option, widget):
        if option.state & QtGui.QStyle.State_Selected:
            self.custom_pen.setColor(SELECTED_COLOR)
            self.custom_pen.setWidth(2)
        else:
            self.custom_pen.setWidth(1)
            if self.base_color:
                self.custom_pen.setColor(self.base_color)
            else:
                self.custom_pen.setColor(NORMAL_COLOR)

        painter.setPen(self.custom_pen)
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

        if self.__centred_position.used_for_collection > 0: 
            painter.drawText(self.rect.right() + 2, self.rect.top() + 10, 
              "Used %d time(s)" % self.__centred_position.used_for_collection)            

    def set_start_position(self, position_x, position_y):
        if (position_x is not None and
            position_y is not None):
            self.start_coord = [position_x, position_y]
            self.setPos(position_x - 10, position_y - 10)
            self.scene().update() 

    #def get_position(self):
    #    return self.start_coord[0], self.start_coord[1]

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

        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        self.__cp_start = cp_start
        self.__cp_end = cp_end
        self.__num_images = 0
        self.__display_overlay = False
        self.__fill_alpha = 120

        brush_color = QtGui.QColor(70, 70, 165)
        brush_color.setAlpha(5)
        self.custom_brush.setColor(brush_color)

    def set_fill_alpha(self, value):
        self.__fill_alpha = value
        brush_color = QtGui.QColor(70, 70, 165, self.__fill_alpha)
        self.custom_brush.setColor(brush_color)

    def set_display_overlay(self, state):
        self.__display_overlay = state
 
    def get_display_name(self):
        return "Line %d" % self.index

    def get_full_name(self):
        start_cpos = self.__cp_start.get_centred_position()
        end_cpos = self.__cp_end.get_centred_position()
        return "Line (points: %d, %d / kappa: %.2f phi: %.2f)" % \
                (self.__cp_start.index, 
                 self.__cp_end.index,
                 start_cpos.kappa,
                 end_cpos.kappa_phi)

    def get_graphics_points(self):
        return [self.__cp_start, self.__cp_end]

    def paint(self, painter, option, widget):
        painter.setBrush(self.custom_brush)
        (start_cp_x, start_cp_y) = self.__cp_start.get_start_position()
        (end_cp_x, end_cp_y) = self.__cp_end.get_start_position()
        mid_x = min(start_cp_x, end_cp_x) + abs((start_cp_x - end_cp_x) / 2.0)
        mid_y = min(start_cp_y, end_cp_y) + abs((start_cp_y - end_cp_y) / 2.0) 

        if option.state & QtGui.QStyle.State_Selected and \
           self.__num_images and self.__display_overlay:
              painter.setPen(QtCore.Qt.NoPen)
              for beam_index in range(self.__num_images):
                  coord_x = start_cp_x + (end_cp_x - start_cp_x) * \
                       beam_index / float(self.__num_images)
                  coord_y = start_cp_y + (end_cp_y - start_cp_y) * \
                       beam_index / float(self.__num_images)
                  painter.drawEllipse(coord_x - self.beam_size_pix[0] / 2, 
                                      coord_y - self.beam_size_pix[1] / 2, 
                                      self.beam_size_pix[0], 
                                      self.beam_size_pix[1])

        info_txt = "Line %d (%d->%d)" % (self.index,
               self.__cp_start.index, self.__cp_end.index)

        if option.state & QtGui.QStyle.State_Selected:
            self.custom_pen.setColor(SELECTED_COLOR)
            info_txt += " selected"
            painter.drawText(mid_x + 5, mid_y, info_txt)
            if self.__num_images:
                info_txt += " (%d images)" % self.__num_images
        else:
            self.custom_pen.setColor(NORMAL_COLOR)

        self.custom_pen.setWidth(2)
        painter.setPen(self.custom_pen)

        painter.drawLine(start_cp_x, start_cp_y,
                         end_cp_x, end_cp_y)
        painter.drawText(mid_x + 5, mid_y, info_txt)

    def set_num_images(self, num_images):
        self.__num_images = num_images
        self.update_item()

    def get_points_index(self):
        return (self.__cp_start.index, self.__cp_end.index)

    def get_graphical_points(self):
        return (self.__cp_start, self.__cp_end)

    def get_centred_positions(self):
        return (self.__cp_start.get_centred_position(), \
                self.__cp_end.get_centred_position())

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
    def __init__(self, parent, beam_info, spacing_microns, pixels_per_mm):
        GraphicsItem.__init__(self, parent)

        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)  

        self.pixels_per_mm = pixels_per_mm
        self.beam_size_microns = [beam_info.get("size_x") * 1000, 
                                  beam_info.get("size_y") * 1000]
        self.__spacing_microns = spacing_microns
        self.__spacing_pix = [0, 0]
        self.__cell_size_microns = [0, 0]
        self.__cell_size_pix = [0, 0]
        self.__corner_coord = (QtCore.QPoint(),
                               QtCore.QPoint(),
                               QtCore.QPoint(),
                               QtCore.QPoint())
        self.__center_coord = QtCore.QPoint()
        self.__num_cols = 0      
        self.__num_rows = 0
        self.__num_lines = 0
        self.__num_images_per_line = 0
        self.__first_image_num = 1
        self.__centred_point = None
        self.__draw_mode = False
        self.__draw_projection = False

        self.__osc_start = None
        self.__motor_pos_corner = []
        self.__centred_position = None
        self.__snapshot = None
        self.__grid_size_pix = [0, 0]
        self.__grid_range_pix = {"fast": 0, "slow": 0}
        self.__reversing_rotation = True
        self.__score = None 
        self.__automatic = False
        self.__fill_alpha = 120
        self.__display_overlay = True
        
        self.update_item()

    @staticmethod
    def set_grid_direction(grid_direction):
        GraphicsItemGrid.grid_direction = grid_direction

    def get_display_name(self):
        return "Grid %d" % (self.index + 1)

    def get_full_name(self):
        return "Grid %d (hor. spacing: %.1f, ver. spacing: %.1f, beam size: %d, %d)" % \
               (self.index + 1, self.__spacing_microns[0], self.__spacing_microns[1],
                self.beam_size_microns[0], self.beam_size_microns[1])
  
    def get_col_row_num(self):
        return self.__num_cols, self.__num_rows

    def get_grid_range_mm(self):
        return (float(self.__cell_size_microns[0] * (self.__num_cols - 1) / 1000), \
                float(self.__cell_size_microns[1] * (self.__num_rows - 1) / 1000))
 
    def get_grid_size_mm(self):
        return (float(self.__cell_size_microns[0] * self.__num_cols / 1000), \
                float(self.__cell_size_microns[1] * self.__num_rows / 1000)) 
 
    def update_item(self):
        self.__cell_size_microns = [self.beam_size_microns[0] + self.__spacing_microns[0] * 2,
                                    self.beam_size_microns[1] + self.__spacing_microns[1] * 2]
        self.__spacing_pix = [self.pixels_per_mm[0] * self.__spacing_microns[0] / 1000,
                              self.pixels_per_mm[1] * self.__spacing_microns[1] / 1000]
        self.beam_size_pix = [self.pixels_per_mm[0] * self.beam_size_microns[0] / 1000,
                              self.pixels_per_mm[1] * self.beam_size_microns[1] / 1000]
        self.__cell_size_pix = [self.pixels_per_mm[0] * self.__cell_size_microns[0] / 1000,
                                self.pixels_per_mm[1] * self.__cell_size_microns[1] / 1000]

    def set_osc_range(self, osc_range):
        self.__osc_range = osc_range

    def set_draw_start_position(self, pos_x, pos_y):
        if self.__draw_mode:
            self.__corner_coord[0].setX(pos_x)
            self.__corner_coord[0].setY(pos_y)
            self.__corner_coord[1].setY(pos_y)
            self.__corner_coord[2].setX(pos_x)
        self.scene().update()

    def set_draw_end_position(self, pos_x, pos_y):
        """
        Descript. : Actual drawing moment, when grid size is defined
        """
        if self.__draw_mode:
            self.__corner_coord[1].setX(pos_x)
            self.__corner_coord[2].setY(pos_y)
            self.__corner_coord[3].setX(pos_x)
            self.__corner_coord[3].setY(pos_y)
  
        #Number of columns and rows is calculated
        num_cols = int(abs(self.__corner_coord[1].x() - \
            self.__corner_coord[0].x()) / self.__cell_size_pix[0])
        num_rows = int(abs((self.__corner_coord[3].y() - \
            self.__corner_coord[1].y()) / self.__cell_size_pix[1]))

        if num_rows * num_cols > pow(2, 16):
            msg_text = "Unable to draw grid containing more than %d cells!" % pow(2, 16)
            logging.getLogger("user_level_log").info(msg_text)
        else:
            self.__num_cols = num_cols
            self.__num_rows = num_rows

            #Based on the grid directions estimates number of lines and 
            #number of images per line
            self.__num_lines =  abs(self.grid_direction['fast'][1] * \
                 self.__num_cols) + abs(self.grid_direction['slow'][1] * \
                 self.__num_rows)
            self.__num_images_per_line = abs(self.grid_direction['fast'][0] * \
                self.__num_cols) + abs(self.grid_direction['slow'][0] * \
                self.__num_rows)

            self.update_grid_draw_parameters()
            self.__center_coord.setX(min(self.__corner_coord[0].x(),
                 self.__corner_coord[1].x()) + self.__grid_size_pix[0] / 2.0)
            self.__center_coord.setY(min(self.__corner_coord[0].y(),
                 self.__corner_coord[3].y()) + self.__grid_size_pix[1] / 2.0)
            self.scene().update() 

    def update_grid_draw_parameters(self):
        self.__grid_size_pix = [self.__num_cols * self.__cell_size_pix[0],
                                self.__num_rows * self.__cell_size_pix[1]]
        #Also grid range is estimated 
        self.__grid_range_pix["fast"] = abs(self.grid_direction['fast'][0] * \
             (self.__grid_size_pix[0] - self.__cell_size_pix[0])) + \
             abs(self.grid_direction['fast'][1] * \
             (self.__grid_size_pix[1] - self.__cell_size_pix[1]))
        self.__grid_range_pix["slow"] = abs(self.grid_direction['slow'][0] * \
             (self.__grid_size_pix[0] - self.__cell_size_pix[0])) + \
             abs(self.grid_direction['slow'][1] * \
             (self.__grid_size_pix[1] - self.__cell_size_pix[1]))

    def set_corner_coord(self, corner_coord):
        self.update_grid_draw_parameters()
        for index, coord in enumerate(corner_coord):
            self.__corner_coord[index].setX(coord[0])
            self.__corner_coord[index].setY(coord[1])
        self.__draw_projection = True

    def set_center_coord(self, center_coord):
        self.__center_coord.setX(center_coord[0])
        self.__center_coord.setY(center_coord[1])

    def set_spacing(self, spacing):
        self.__spacing_microns = spacing
        self.update_item()
        self.update_grid_draw_parameters()
        self.scene().update()

    def set_draw_mode(self, draw_mode):
        self.__draw_mode = draw_mode 

    def is_draw_mode(self):
        return self.__draw_mode

    def set_projection_mode(self, mode):
        self.__draw_projection = mode 

    def get_properties(self):
        (dx_mm, dy_mm) = self.get_grid_range_mm()
        return {"name": "Grid %d" % (self.index + 1),
                "direction":  self.grid_direction,
                "reversing_rotation": self.__reversing_rotation,
                "steps_x": self.__num_cols,
                "steps_y": self.__num_rows, 
                "xOffset": self.__spacing_microns[0],
                "yOffset": self.__spacing_microns[1],  
                "dx_mm": dx_mm,
                "dy_mm": dy_mm,
                "beam_x": self.beam_size_microns[0], 
                "beam_y": self.beam_size_microns[1],
                "num_lines": self.__num_lines,
                "num_images_per_line": self.__num_images_per_line,
                "first_image_num": self.__first_image_num}

    def set_automatic_size(self, corner_coord):
        """
        self.set_draw_start_position(\
             beam_position[0] - self.__grid_size_pix[0] / 2,
             beam_position[1] - self.__grid_size_pix[1] / 2)
        self.set_draw_end_position( + \
             beam_position[0] + self.__grid_size_pix[0] / 2 + 5,
             beam_position[1] + self.__grid_size_pix[1] / 2 + 5)
        """
        self.set_draw_start_position(corner_coord[0][0], 
                                     corner_coord[0][1])
        self.set_draw_end_position(corner_coord[1][0],
                                   corner_coord[1][1])
        self.__draw_projection = True
        self.__automatic = True

    def get_center_coord(self):
        return self.__center_coord.x(), self.__center_coord.y()

    def get_corner_coord(self):
        return self.__corner_coord

    def set_motor_pos_corner(self, motor_pos_corner):
        self.__motor_pos_corner = motor_pos_corner

    def get_motor_pos_corner(self):
        return self.__motor_pos_corner

    def set_centred_position(self, centred_position):
        self.__centred_position = centred_position
        self.__osc_start = self.__centred_position.phi

    def get_centred_position(self): 
        return self.__centred_position

    def set_score(self, score):
        self.__score = score

    def get_snapshot(self):
        return self.__snapshot

    def set_snapshot(self, snapshot):
        self.__snapshot = snapshot

    def set_fill_alpha(self, value):
        self.__fill_alpha = value

    def set_display_overlay(self, state):
        self.__display_overlay = state

    def paint(self, painter, option, widget):
        self.custom_pen.setColor(QtCore.Qt.darkGray)
        self.custom_pen.setWidth(1)

        if self.__draw_mode:
            self.custom_pen.setStyle(QtCore.Qt.DashLine)
        if self.__draw_mode or self.isSelected():
            self.custom_pen.setColor(SELECTED_COLOR)

        painter.setPen(self.custom_pen)
        painter.setBrush(self.custom_brush)
      
        if self.__draw_projection:
            #In projection mode, just the frame is displayed
            painter.drawLine(self.__corner_coord[0], self.__corner_coord[1])
            painter.drawLine(self.__corner_coord[0], self.__corner_coord[2])
            painter.drawLine(self.__corner_coord[3], self.__corner_coord[1])
            painter.drawLine(self.__corner_coord[3], self.__corner_coord[2])
        else:
            draw_start_x = self.__center_coord.x() - self.__grid_size_pix[0] / 2.0
            draw_start_y = self.__center_coord.y() - self.__grid_size_pix[1] / 2.0

            # Horizontal and vertical grid lines
            for i in range(0, self.__num_cols + 1):
                offset = i * self.__cell_size_pix[0]
                painter.drawLine(draw_start_x + offset, draw_start_y,
                                 draw_start_x + offset, draw_start_y + \
                                 self.__num_rows * self.__cell_size_pix[1])
            for i in range(0, self.__num_rows + 1):
                offset = i * self.__cell_size_pix[1]
                painter.drawLine(draw_start_x, draw_start_y + offset,
                                 draw_start_x + self.__num_cols * self.__cell_size_pix[0],
                                 draw_start_y + offset)    

            #Draws beam shape and displays number of image if 
            #less than 1000 cells and size is greater than 20px
            cell_index = 0
            if self.__num_cols * self.__num_rows < 1000 and self.__cell_size_pix[1] > 20:
                for col in range(self.__num_cols):
                    for row in range(self.__num_rows):
                        #Estimate area where frame number or score will be displayed
                        line, image = self.get_line_image_num(cell_index + self.__first_image_num)
                        pos_x, pos_y = self.get_coord_from_line_image(line, image)
                        paint_rect = QtCore.QRect(\
                            pos_x - self.__cell_size_pix[0] / 2, 
                            pos_y - self.__cell_size_pix[1] / 2,
                            self.__cell_size_pix[0], 
                            self.__cell_size_pix[1])

                        #If score exists overlay color may change
                        cell_score = None
                        brush_color = QtGui.QColor(70, 70, 165, self.__fill_alpha)
                        if self.__display_overlay: 
                            #painter.setBrush(QtGui.QColor(70, 70, 165))
                            if self.__score is not None:
                                cell_score = self.__score[cell_index]
                                if self.__score.max() > 0:
                                    cell_score = float(cell_score) / self.__score.max()
                                    brush_color.setHsv(0 + 60 * cell_score, 255, 255 * cell_score, self.__fill_alpha)
                            self.custom_brush.setColor(brush_color)
                            painter.setBrush(self.custom_brush)
                        else:
                            painter.setBrush(QtCore.Qt.transparent)

                        if self.beam_is_rectangle:
                            painter.drawRect(pos_x - self.beam_size_pix[0] / 2,
                                             pos_y - self.beam_size_pix[1] / 2,
                                             self.beam_size_pix[0],
                                             self.beam_size_pix[1])
                        else:
                            painter.drawEllipse(pos_x - self.beam_size_pix[0] / 2,
                                                pos_y - self.beam_size_pix[1] / 2,
                                                self.beam_size_pix[0],
                                                self.beam_size_pix[1])
                        painter.drawText(paint_rect, QtCore.Qt.AlignCenter, \
                              str(cell_index + self.__first_image_num))
                        cell_index += 1

        #Draws x in the middle of the grid
        painter.drawLine(self.__center_coord.x() - 5, self.__center_coord.y() - 5,
                         self.__center_coord.x() + 5, self.__center_coord.y() + 5)
        painter.drawLine(self.__center_coord.x() + 5, self.__center_coord.y() - 5,
                         self.__center_coord.x() - 5, self.__center_coord.y() + 5)
 
        grid_info = "Grid %d" % (self.index + 1)
        if self.__automatic:
            grid_info += " (automatic)"
        painter.drawText(self.__center_coord.x() + self.__grid_size_pix[0] / 2.0 + 3,
                         self.__center_coord.y() - self.__grid_size_pix[1] / 2.0 - 3,
                         grid_info)
        painter.drawText(self.__center_coord.x() + self.__grid_size_pix[0] / 2.0 + 3,
                         self.__center_coord.y() - self.__grid_size_pix[1] / 2.0 + 12,
                         "%d x %d" % (self.__num_lines, self.__num_images_per_line))
 
            
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
            corner_coord.setX(corner_coord.x() + move_delta_x)
            corner_coord.setY(corner_coord.y() + move_delta_y)    
        self.__center_coord.setX(self.__center_coord.x() + move_delta_x)
        self.__center_coord.setY(self.__center_coord.y() + move_delta_y)
        self.scene().update()

    def get_size_pix(self):
        width_pix = self.__cell_size_pix[0] * self.__num_cols
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
        ref_fast, ref_slow = self.get_coord_ref_from_line_image(line, image)

        coord_x = self.__center_coord.x() + self.__grid_range_pix['fast'] * \
                  self.grid_direction['fast'][0] * ref_fast  + \
                  self.__grid_range_pix['slow'] * \
                  self.grid_direction['slow'][0] * ref_slow
        coord_y = self.__center_coord.y() + self.__grid_range_pix['fast'] * \
                  self.grid_direction['fast'][1] * ref_fast  + \
                  self.__grid_range_pix['slow'] * \
                  self.grid_direction['slow'][1] * ref_slow
        return coord_x, coord_y

    def get_coord_ref_from_line_image(self, line, image):
        """
        Descript. : returns nameless constants used in conversion between 
                    scan and screen coordinates. 
        """
        fast_ref = 0.5
        if self.__num_images_per_line > 1:
            fast_ref = 0.5 - float(image) / (self.__num_images_per_line - 1)
        if self.__reversing_rotation:
            fast_ref = pow(-1, line % 2) * fast_ref

        slow_ref = 0.5
        if self.__num_lines > 1:
            slow_ref = 0.5 - float(line)  / (self.__num_lines - 1)
        return fast_ref, slow_ref

    def get_direction_parameters(self):
        start_x, start_y = self.get_coord_from_line_image(0, 0)
        end_x, end_y = self.get_coord_from_line_image(0, 2)
        return {'start_x' : start_x, 
                'start_y': start_y, 
                'end_x': end_x, 
                'end_y': end_y}

    def get_image_from_col_row(self, col, row):
        """
        Descipt: calculate image serial number, number of line and number of
                 image in line from col and row
                 col and row can be floats
        """
        image = int(self.__num_images_per_line / 2.0 + \
                    self.grid_direction['fast'][0] * (self.__num_cols / 2.0 - col) - \
                    self.grid_direction['fast'][1] * (self.__num_rows / 2.0 - row))
        line  = int(self.__num_lines / 2.0 + \
                 self.grid_direction['slow'][0] * (self.__num_cols / 2.0 - col) - \
                 self.grid_direction['slow'][1] * (self.__num_rows / 2.0 - row))


        if self.__reversing_rotation and line % 2 :
            image_serial = self.__first_image_num + \
                self.__num_images_per_line * (line + 1) - 1 - image
        else:
            image_serial = self.__first_image_num + \
                self.__num_images_per_line * line + image

        return image, line, image_serial

    def get_col_row_from_image_serial(self, image_serial):
        line, image = self.get_line_image_num(image_serial)
        return self.get_col_row_from_line_image(line, image)

    def get_col_row_from_line_image(self, line, image):
        """
        Descript. :  converts frame grid coordinates from scan grid 
                     ("slow","fast") to screen grid ("col","raw"),
                     i.e. rotates/inverts the scan coordinates into 
                     grid coordinates.
        """
        ref_fast, ref_slow = self.get_coord_ref_from_line_image(line, image)
   
        col = self.__num_cols / 2.0 + (self.__num_images_per_line - 1) * \
              self.grid_direction['fast'][0] * ref_fast + \
              (self.__num_lines - 1) * \
              self.grid_direction['slow'][0] * ref_slow
        row = self.__num_rows / 2.0 + (self.__num_images_per_line - 1) * \
              self.grid_direction['fast'][1] * ref_fast + \
              (self.__num_lines - 1) * \
              self.grid_direction['slow'][1] * ref_slow
        return int(col), int(row)

    def get_motor_pos_from_col_row(self, col, row, as_cpos=False):
        """
        Descript. : x = x(click - x_middle_of_the_plot), y== the same 
        """
        new_point = copy.deepcopy(self.__centred_position.as_dict())
        (hor_range, ver_range) = self.get_grid_size_mm()
        hor_range = - hor_range * (self.__num_cols / 2.0 - col) / self.__num_cols
        ver_range = - ver_range * (self.__num_rows / 2.0 - row) / self.__num_rows
        #image, line, image_serial = self.get_image_from_col_row(col, row)

        #Add correct omega


        """
        MD3
        omega_ref = 163.675
        new_point['sampx'] = new_point['sampx'] - hor_range  * \
                             math.sin(math.pi * (self.__osc_start - omega_ref) / 180.0)
        new_point['sampy'] = new_point['sampy'] + hor_range  * \
                             math.cos(math.pi * (self.__osc_start - omega_ref) / 180.0)
        new_point['phiy'] = new_point['phiy'] - ver_range
        """

        #MD2
        new_point['sampx'] = new_point['sampx'] + ver_range * \
                             math.sin(math.pi * (self.__osc_start - \
                             self.grid_direction["omega_ref"]) / 180.0)
        new_point['sampy'] = new_point['sampy'] - ver_range  * \
                             math.cos(math.pi * (self.__osc_start - \
                             self.grid_direction["omega_ref"]) / 180.0)
        new_point['phiy'] = new_point['phiy'] - hor_range

        if as_cpos:
            return queue_model_objects.CentredPosition(new_point)
        else:
            return new_point
 
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
        self.__display_grid = None
        self.__radiation_dose_info = None     
        
    def paint(self, painter, option, widget):
        hor_scale_len_pix = self.pixels_per_mm[0] * self.__scale_len / 1000
        ver_scale_len_pix = self.pixels_per_mm[1] * self.__scale_len / 1000 / 2

        if self.__display_grid:
            self.custom_pen.setStyle(QtCore.Qt.DotLine)
            self.custom_pen.setWidth(1)
            self.custom_pen.setColor(QtCore.Qt.gray)
            painter.setPen(self.custom_pen)
            for col in range(1, int(self.scene().width() / hor_scale_len_pix) + 1): 
                painter.drawLine(col * hor_scale_len_pix, 0, 
                                 col * hor_scale_len_pix, self.scene().height())
            for row in range(1, int(self.scene().height() / ver_scale_len_pix) + 1):
                painter.drawLine(0, row * ver_scale_len_pix,
                                 self.scene().width(), row * ver_scale_len_pix)

        self.custom_pen.setStyle(SOLID_LINE_STYLE)
        self.custom_pen.setWidth(3)
        self.custom_pen.setColor(SELECTED_COLOR)
        painter.setPen(self.custom_pen)

        painter.drawLine(10, self.start_coord[1] - 15,
                         10 + hor_scale_len_pix, self.start_coord[1] - 15)
        painter.drawText(hor_scale_len_pix - 10,
                         self.start_coord[1] - 20,
                         "%d %s" % (self.__scale_len, u"\u00B5"))
        painter.drawLine(10, self.start_coord[1] - 15,
                         10, self.start_coord[1] - 15 - ver_scale_len_pix)
        painter.drawText(3, self.start_coord[1] - 20 - ver_scale_len_pix,
                         "%d %s" % (self.__scale_len / 2, u"\u00B5"))

        if self.__radiation_dose_info:
            painter.drawText(5, 15, self.__radiation_dose_info)

    def set_pixels_per_mm(self, pixels_per_mm):
        self.pixels_per_mm = pixels_per_mm
        for line_len in GraphicsItemScale.HOR_LINE_LEN:
            if self.pixels_per_mm[0] * line_len / 1000 <= 250:
                self.__scale_len = line_len
                break

    def set_start_position(self, position_x, position_y):
        if (position_x is not None and
            position_y is not None):
            self.start_coord = [position_x, position_y]

    def set_display_grid(self, display_grid):
        self.__display_grid = display_grid
     
    def set_radiation_dose_info(self, info):
        self.__radiation_dose_info = info   

class GraphicsItemOmegaReference(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.phi_position = None

    def paint(self, painter, option, widget):
        painter.setPen(self.custom_pen)
        painter.drawLine(self.start_coord[0], self.start_coord[1], 
                         self.end_coord[0], self.end_coord[1])
        if self.phi_position:
            painter.drawText(self.end_coord[0] - 40, 
                             self.end_coord[1] - 10,
                             "%d %s" % (self.phi_position, u"\u00b0"))

    def set_phi_position(self, phi_position):
        self.phi_position = phi_position

    def set_reference(self, omega_reference):
        if omega_reference[0] > 0:
            #Omega reference is a vertical axis
            self.start_coord = [omega_reference[0], 0]
            self.end_coord = [omega_reference[0], self.scene().height()]
        else:
            self.start_coord = [0, omega_reference[1]]
            self.end_coord = [self.scene().width(), omega_reference[1]] 

class GraphicsSelectTool(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)

        self.custom_pen.setColor(SELECTED_COLOR)

    def paint(self, painter, option, widget):
        painter.setPen(self.custom_pen)
        painter.drawRect(min(self.start_coord[0], self.end_coord[0]),
                         min(self.start_coord[1], self.end_coord[1]),
                         abs(self.start_coord[0] - self.end_coord[0]),
                         abs(self.start_coord[1] - self.end_coord[1]))


class GraphicsItemCentringLines(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)

        self.custom_pen.setColor(NORMAL_COLOR)

    def paint(self, painter, option, widget):
        painter.setPen(self.custom_pen)
        painter.drawLine(self.start_coord[0], 0, 
                         self.start_coord[0], self.scene().height())
        painter.drawLine(0, self.start_coord[1],
                         self.scene().width(), self.start_coord[1])


class GraphicsItemMoveBeamMark(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.custom_pen.setColor(SELECTED_COLOR)

    def paint(self, painter, option, widget):
        self.custom_pen.setStyle(SOLID_LINE_STYLE)
        painter.setPen(self.custom_pen)
        painter.drawLine(self.start_coord[0], self.start_coord[1],
                         self.end_coord[0], self.end_coord[1])
        if self.beam_size_pix:
            self.custom_pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(self.custom_pen)
            painter.drawEllipse(self.end_coord[0] - self.beam_size_pix[0] / 2,
                                self.end_coord[1] - self.beam_size_pix[1] / 2,
                                self.beam_size_pix[0], self.beam_size_pix[1])


class GraphicsItemBeamDefine(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)

        self.center_coord = [0, 0]
        self.width_microns = 0
        self.height_microns = 0
        
    def paint(self, painter, option, widget):
        self.custom_pen.setColor(SELECTED_COLOR)
        painter.setPen(self.custom_pen)
        painter.setBrush(self.custom_brush)
        painter.drawRect(min(self.start_coord[0], self.end_coord[0]),
                         min(self.start_coord[1], self.end_coord[1]),
                         abs(self.start_coord[0] - self.end_coord[0]),
                         abs(self.start_coord[1] - self.end_coord[1]))
        painter.drawText(self.end_coord[0] + 5, self.end_coord[1] + 5,
                         "%d x %d %s" % (self.width_microns, 
                         self.height_microns, u"\u00B5"))

        self.custom_pen.setColor(QtCore.Qt.red)
        painter.setPen(self.custom_pen)
        painter.drawLine(self.center_coord[0] - 10, self.center_coord[1],
                         self.center_coord[0] + 10, self.center_coord[1])
        painter.drawLine(self.center_coord[0], self.center_coord[1] - 10,
                         self.center_coord[0], self.center_coord[1] + 10)

    def set_end_position(self, position_x, position_y):
        self.end_coord = [position_x, position_y]

        pix_width = max(self.start_coord[0], self.end_coord[0]) - \
                    min(self.start_coord[0], self.end_coord[0])
        pix_height = max(self.start_coord[1], self.end_coord[1]) - \
                     min(self.start_coord[1], self.end_coord[1])
        self.center_coord[0] = min(self.start_coord[0], self.end_coord[0]) + \
             pix_width / 2
        self.center_coord[1] = min(self.start_coord[1], self.end_coord[1]) + \
             pix_height / 2
        self.width_microns = pix_width / self.pixels_per_mm[0] * 1000
        self.height_microns = pix_height / self.pixels_per_mm[1] * 1000

        self.scene().update()


class GraphicsItemMeasureDistance(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        self.do_measure = None
        self.measure_points = None
        self.measured_distance = None

        self.custom_pen.setColor(SELECTED_COLOR)

    def paint(self, painter, option, widget):
        painter.setPen(self.custom_pen)
        painter.drawLine(self.measure_points[0], self.measure_points[1])
        painter.drawText(self.measure_points[1].x() + 15, 
                         self.measure_points[1].y() + 10,
                         "%.2f %s" % (self.measured_distance, u"\u00B5"))
 
    def set_start_position(self, position_x, position_y):
        self.measured_distance = 0
        self.measure_points = []
        self.measure_points.append(QtCore.QPoint(position_x, position_y))
        self.measure_points.append(QtCore.QPoint(position_x, position_y))
 
    def set_coord(self, coord):
        self.measure_points[len(self.measure_points) - 1].setX(coord[0])
        self.measure_points[len(self.measure_points) - 1].setY(coord[1])
        if len(self.measure_points) == 2:
            self.measured_distance = math.sqrt(pow((self.measure_points[0].x() - 
                self.measure_points[1].x()) / self.pixels_per_mm[0], 2) + \
                pow((self.measure_points[0].y() - self.measure_points[1].y()) / \
                self.pixels_per_mm[1], 2)) * 1000
            self.scene().update()

    def store_coord(self, position_x, position_y):
        if len(self.measure_points) == 3:
            self.measure_points = []
            self.measure_points.append(QtCore.QPoint(position_x, position_y))
        self.measure_points.append(QtCore.QPoint(position_x, position_y)) 
 
class GraphicsItemMeasureAngle(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent):
        GraphicsItem.__init__(self, parent)
        self.measure_points = None
        self.measured_angle = None
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)

        self.custom_pen.setColor(SELECTED_COLOR)

    def paint(self, painter, option, widget):
        painter.setPen(self.custom_pen)
        if len(self.measure_points) > 1:
            painter.drawLine(self.measure_points[0], self.measure_points[1])
            if len(self.measure_points) > 2:
                painter.drawLine(self.measure_points[1],
                                 self.measure_points[2])
                painter.drawText(self.measure_points[2].x() + 10,
                                 self.measure_points[2].y() + 10, 
                                 "%.2f %s" % (self.measured_angle, u"\u00B0"))

    def set_start_position(self, position_x, position_y):
        self.measured_angle = 0
        self.measure_points = []
        self.measure_points.append(QtCore.QPoint(position_x, position_y))
        self.measure_points.append(QtCore.QPoint(position_x, position_y))

    def set_coord(self, coord):
        self.measure_points[len(self.measure_points) - 1].setX(coord[0])
        self.measure_points[len(self.measure_points) - 1].setY(coord[1])
        if len(self.measure_points) == 3: 
            self.measured_angle = - math.degrees(math.atan2(self.measure_points[2].y() - \
                 self.measure_points[1].y(), self.measure_points[2].x() - \
                 self.measure_points[1].x()) - math.atan2(self.measure_points[0].y() - \
                 self.measure_points[1].y(), self.measure_points[0].x() - \
                 self.measure_points[1].x()))
            self.scene().update()

    def store_coord(self, position_x, position_y):
        if len(self.measure_points) == 4:
            self.measure_points = []
            self.measure_points.append(QtCore.QPoint(position_x, position_y))        
        self.measure_points.append(QtCore.QPoint(position_x, position_y))

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
        self.current_point = QtCore.QPoint(0, 0)
        self.min_max_coord = None

    def paint(self, painter, option, widget):
        self.custom_pen.setStyle(SOLID_LINE_STYLE)
        self.custom_pen.setColor(SELECTED_COLOR)
        painter.setPen(self.custom_pen)
        painter.setBrush(self.custom_brush)

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
                             
    def set_start_position(self, pos_x, pos_y):
        self.min_max_coord = None
        self.measured_area = 0
        self.measure_polygon.clear()
        self.measure_polygon.append(QtCore.QPoint(pos_x, pos_y))
        self.current_point = QtCore.QPoint(pos_x, pos_y)

    def set_coord(self, coord):
        if not self.last_point_set:
            self.current_point.setX(coord[0])
            self.current_point.setY(coord[1])
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
        if self.measure_polygon.count() > 2:
            self.measured_area = 0
            for point_index in range(self.measure_polygon.count() - 1):
                self.measured_area += self.measure_polygon.value(point_index).x() * \
                                      self.measure_polygon.value(point_index + 1).y()
                self.measured_area -= self.measure_polygon.value(point_index + 1).x() * \
                                      self.measure_polygon.value(point_index).y()
            self.measured_area += self.measure_polygon.value(len(self.measure_polygon) - 1).x() * \
                                  self.measure_polygon.value(0).y()
            self.measured_area -= self.measure_polygon.value(0).x() * \
                                  self.measure_polygon.value(len(self.measure_polygon) - 1).y()
            self.measured_area = abs(self.measured_area / (2 * self.pixels_per_mm[0] * \
                                 self.pixels_per_mm[1]) * 1e6)
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
        self.mouseMovedSignal.emit(event.x(), event.y())
        self.update()
 
    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):  
            self.keyPressedSignal.emit("Delete")
        elif event.key() == QtCore.Qt.Key_Escape:
            self.keyPressedSignal.emit("Escape")

    def toggle_scrollbars_enable(self, state):
        if state:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)


class GraphicsScene(QtGui.QGraphicsScene):
    """
    Implemented signals:
    - mouseClickedSignal (pos_x, pos_y, is left key)
    - mouseDoubleClickedSignal (pos_x, pos_y)
    - mouseReleasedSignal (pos_x, pos_y)
    - itemDoubleClickedSignal (GraphicsItem)
    - itemClickedSignal (GraphicsItem, isSelected)
    """

    mouseClickedSignal = QtCore.pyqtSignal(int, int, bool)
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
        self.scene().mouseClickedSignal.emit(position.x(), position.y(), 
             event.button() == QtCore.Qt.LeftButton)
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
