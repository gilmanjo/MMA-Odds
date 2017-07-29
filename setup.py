#!/usr/bin/env python

from setuptool import setup

with open("README", "r") as f:
	long_description = f.read()

setup(
	name="mma odds",
	version=0.01,
	description="Analysis of MMA sporting event stats",
	author="Jordan Gilman",
	author_email="gilmanjo@oregonstate.edu"
)