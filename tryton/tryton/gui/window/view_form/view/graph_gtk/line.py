#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
#This code is inspired by the pycha project (http://www.lorenzogil.com/projects/pycha/)
from graph import Graph
from tryton.common import hex2rgb, float_time_to_text, safe_eval
import locale
import math
import cairo
import tryton.rpc as rpc


class Line(Graph):

    def updateGraph(self):

        yfield2attrs = {}
        for yfield in self.yfields:
            yfield2attrs[yfield.get('key', yfield['name'])] = yfield

        self.points = []
        i = 0
        keys = self.datas.keys()
        keys.sort()
        for xfield in keys:
            j = 0
            for yfield in self.datas[xfield]:
                xval = i
                yval = self.datas[xfield][yfield]

                x = (xval - self.minxval) * self.xscale
                y = 1.0 - (yval - self.minyval) * self.yscale

                if self.xrange == 0:
                    x = 1.0

                if not bool(safe_eval(yfield2attrs[yfield].get('empty', '1'))) \
                        and yval == 0:
                    continue

                point = Point(x, y, xval, yval, xfield, yfield)
                if (0.0 <= point.x <= 1.0) and (0.0 <= point.y <= 1.0):
                    self.points.append(point)

                j += 1
            i += 1

    def drawGraph(self, cr, width, height):
        key2fill = {}
        for yfield in self.yfields:
            key2fill[yfield.get('key', yfield['name'])] = \
                    bool(safe_eval(yfield.get('fill', '0')))

        def preparePath(key):
            cr.new_path()
            cr.move_to(self.area.x, self.area.y + self.area.h)
            for point in self.points:
                if point.yname == key:
                    cr.line_to(point.x * self.area.w + self.area.x,
                            point.y * self.area.h + self.area.y)
            cr.line_to(self.area.x + self.area.w, self.area.y + self.area.h)
            cr.move_to(self.area.x, self.area.y + self.area.h)

            if key2fill[key]:
                cr.close_path()
            else:
                cr.set_source_rgb(*self.colorScheme[key])
                cr.stroke()

        cr.save()
        cr.set_line_width(2)
        for key in self._getDatasKeys():
            if key2fill[key]:
                cr.save()
                cr.set_source_rgba(0, 0, 0, 0.15)
                cr.translate(2, -2)
                preparePath(key)
                cr.fill()
                cr.restore()

                r, g, b = self.colorScheme[key]
                linear = cairo.LinearGradient(width / 2, 0, width / 2, height)
                linear.add_color_stop_rgb(0,
                        3.5 * r / 5.0, 3.5 * g / 5.0, 3.5 * b / 5.0)
                linear.add_color_stop_rgb(1, r, g, b)
                cr.set_source(linear)
                preparePath(key)
                cr.fill()
            else:
                preparePath(key)

        for point in self.points:
            if key2fill[point.yname]:
                continue
            cr.set_source_rgb(*self.colorScheme[point.yname])
            cr.move_to(point.x * self.area.w + self.area.x,
                    point.y * self.area.h + self.area.y)
            cr.arc(point.x * self.area.w + self.area.x,
                    point.y * self.area.h + self.area.y,
                    3, 0, 2 * math.pi)
            cr.fill()

        cr.restore()

    def drawLegend(self, cr, widht, height):
        super(Line, self).drawLegend(cr, widht, height)
        cr.save()
        for point in self.points:
            if point.highlight:
                cr.set_line_width(2)
                cr.set_source_rgb(*hex2rgb('#000000'))
                cr.move_to(point.x * self.area.w + self.area.x,
                        point.y * self.area.h + self.area.y)
                cr.arc(point.x * self.area.w + self.area.x,
                        point.y * self.area.h + self.area.y,
                        3, 0, 2 * math.pi)
                cr.stroke()
                cr.set_source_rgb(*self.colorScheme['__highlight'])
                cr.arc(point.x * self.area.w + self.area.x,
                        point.y * self.area.h + self.area.y,
                        3, 0, 2 * math.pi)
                cr.fill()
        cr.restore()

    def motion(self, widget, event):
        if not getattr(self, 'area', None):
            return

        nearest = None
        for point in self.points:
            x = point.x * self.area.w + self.area.x
            y = point.y * self.area.h + self.area.y

            l = (event.x - x) ** 2 + (event.y - y) ** 2

            if not nearest or l < nearest[1]:
                nearest = (point, l)

        dia = self.area.w ** 2 + self.area.h ** 2

        keys2txt = {}
        for yfield in self.yfields:
            keys2txt[yfield.get('key', yfield['name'])] = yfield['string']

        highlight = False
        draw_points = []
        yfields_float_time = dict([(x.get('key', x['name']), x.get('float_time'))
            for x in self.yfields if x.get('widget')])
        for point in self.points:
            if point == nearest[0] and nearest[1] < dia / 100:
                if not point.highlight:
                    point.highlight = True
                    label = keys2txt[point.yname]
                    label += '\n'
                    if point.yname in yfields_float_time:
                        conv = None
                        if yfields_float_time[point.yname]:
                            conv = rpc.CONTEXT.get(
                                    yfields_float_time[point.yname])
                        label += float_time_to_text(point.yval, conv)
                    else:
                        label += locale.format('%.2f', point.yval, True)
                    label += '\n'
                    label += str(self.labels[point.xname])
                    self.popup.set_text(label)
                    draw_points.append(point)
            else:
                if point.highlight:
                    point.highlight = False
                    draw_points.append(point)
            if point.highlight:
                self.popup.set_position(self,
                        point.x * self.area.w + self.area.x,
                        point.y * self.area.h + self.area.y)
                highlight = True
        if highlight:
            self.popup.show()
        else:
            self.popup.hide()

        if draw_points:
            minx = self.area.w + self.area.x
            miny = self.area.h + self.area.y
            maxx = maxy = 0.0
            for point in draw_points:
                x = self.area.w * point.x + self.area.x
                y = self.area.h * point.y + self.area.y
                minx = min(x - 5, minx)
                miny = min(y - 5, miny)
                maxx = max(x + 5, maxx)
                maxy = max(y + 5, maxy)
            self.queue_draw_area(int(minx - 1), int(miny - 1),
                    int(maxx - minx + 1), int(maxy - miny + 1))

    def updateXY(self):
        super(Line, self).updateXY()
        if self.xrange != 0:
            self.xrange -= 1
            if self.xrange == 0:
                self.xscale = 1.0
            else:
                self.xscale = 1.0 / self.xrange

    def drawAxis(self, cr, width, height):
        super(Line, self).drawAxis(cr, width, height)
        self.drawLine(cr, 1.0, 0)

    def action(self):
        super(Line, self).action()
        for point in self.points:
            if point.highlight:
                ids = self.ids[point.xname]
                self.action_keyword(ids)

    def YLabels(self):
        ylabels = super(Line, self).YLabels()
        if len([x.get('key', x['name']) for x in self.yfields
            if x.get('widget')]) == len(self.yfields):
            conv = None
            float_time = reduce(lambda x, y: x == y and x or False,
                    [x.get('float_time') for x in self.yfields])
            if float_time:
                conv = rpc.CONTEXT.get(float_time)
            return [(x[0], float_time_to_text(locale.atof(x[1]), conv))
                    for x in ylabels]
        return ylabels


class Point(object):

    def __init__(self, x, y, xval, yval, xname, yname):
        self.x, self.y = x, y
        self.xval, self.yval = xval, yval
        self.xname = xname
        self.yname = yname
        self.highlight = False
