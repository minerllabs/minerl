# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import pyglet
import minerl
import sys
import os
import random


class Rect:
    def __init__(self, x, y, w, h, color=None):
        color = (255, 255, 255) if color is None else color
        self.set(x, y, w, h, color)

    def draw(self):
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, self._quad, self._color_str)

    def set(self, x=None, y=None, w=None, h=None, color=None):
        self._x = self._x if x is None else x
        self._y = self._y if y is None else y
        self._w = self._w if w is None else w
        self._h = self._h if h is None else h
        self._color = self._color if color is None else color
        self._quad = ('v2f', (self._x, self._y,
                              self._x + self._w, self._y,
                              self._x + self._w, self._y + self._h,
                              self._x, self._y + self._h))
        self._color_str = ['c3B', self._color + self._color + self._color + self._color]

    @property
    def center(self):
        return self._x + self._w // 2, self._y + self._h // 2

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def height(self):
        return self._h

    @property
    def width(self):
        return self._w


class Point:
    def __init__(self, x, y, radius, color=None):
        color = (255, 255, 255) if color is None else color
        self.set(x, y, radius, color)

    def draw(self):
        pyglet.graphics.draw_indexed(3, pyglet.gl.GL_TRIANGLES,
                                     [0, 1, 2],
                                     self._vertex,
                                     self._color_str)

        # pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, self._quad, self._color_str)

    def set(self, x=None, y=None, radius=None, color=None):
        self._x = self._x if x is None else x
        self._y = self._y if y is None else y
        self._radius = self._radius if radius is None else radius
        self._color = self._color if color is None else color

        height = self._radius / 0.57735026919
        # TODO THIS IS INCORRECT LOL :) It's not a true radius.
        self._vertex = ('v2f', (self._x - self._radius, self._y - height / 2,
                                self._x + self._radius, self._y - height / 2,
                                self._x, self._y + height / 2))
        self._color_str = ['c3B', self._color + self._color + self._color]
