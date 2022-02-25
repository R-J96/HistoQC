#!/bin/bash
#########################################################################
# Script for QC BC2001 data
#########################################################################
python -m histoqc \
input_pattern file_lists/bc2001_files filtered.tsv \
-o results/bc2001_2.1/ \
-c /home/robj/Projects/HistoQCFork/HistoQC/histoqc/config/config_first.ini \
-n 4 \
--force \