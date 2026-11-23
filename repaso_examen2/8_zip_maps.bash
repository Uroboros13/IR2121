#!/bin/bash
rm -f maps.zip
zip -r maps.zip maps -i '*.pgm' '*.yaml'
