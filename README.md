Ubiquiti mFi Controller
=======================
This repo contains a python implementation of a parser for the Ubiquiti Inform
Protocol. This protocol is used by Ubiquiti Unifi access points to communicate
with the controller for ongoing metrics collection and configuration. It's also
used in the Ubiquiti mFi products for command and control of light switches,
power outlets, mPorts and power strips.

The goal of this library is to build a fully functional replacement for the
abandoned Ubiquiti controller. A fully functional python library for inform
parsing and serialization exists in the python directory along with a sample
server that just sends NOOP packets to devices checking in. The python work is
considered finished and will be split into a new repo at some point. All
further work will go into a Go (golang) API on which the controller will be
built.
