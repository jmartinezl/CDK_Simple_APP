#!/usr/bin/env python3

from aws_cdk import core

from cloud101.cloud101_stack import Cloud101Stack


app = core.App()
Cloud101Stack(app, "cloud101")

app.synth()
