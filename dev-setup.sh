#!/usr/bin/env bash
# Simple setup script for development
set -e
python -m pip install --upgrade pip
pip install -e .[dev]
