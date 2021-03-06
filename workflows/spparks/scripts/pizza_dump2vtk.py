#!/usr/bin/env python
""" convert a SPPARKS multi-timestep dump file to single-timestep vtks with pizza.py """
import sys
import os
import dump # pizza.py module
import vtk  # pizza.py module

infile = ""
try:
  infile = sys.argv[1]
except:
  sys.exit("Please supply the filename of a valid SPPARKS dump file.")

print("loading dump file timestep:")
d = dump.dump(infile)
v = vtk.vtk(d)
print("writing vtk file for timestep:")
if not os.path.exists("workflows/spparks/vtk"):
    os.makedirs("workflows/spparks/vtk")
v.one("workflows/spparks/vtk/potts")
