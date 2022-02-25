#!/bin/bash
#########################################################################
# Script for QC UHCW data
#########################################################################
python -m histoqc \
input_pattern /mnt/jalapeno_uhcw_bladder_wsi/*.jp2 \
-o results/uhcw_v2_config/ \
-c /home/robj/Projects/HistoQCFork/HistoQC/histoqc/config/config_v2.1.ini \
-n 16 \