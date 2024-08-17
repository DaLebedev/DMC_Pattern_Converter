"""
***************************************************************
* Program Name: Thread.py
* Author: Daniel Lebedev
* Created : 7/31/2024
***************************************************************
"""


class Thread:
    def __init__(self, id, name, r, g, b):
        self.id = id
        self.name = name
        self.color = (int(r), int(g), int(b))

    def __str__(self):
        return f"ID: {self.id}, Name: {self.name}, RGB: {self.color}"
