#!/usr/bin/env bash
# Rebuild the report with only D+ stocks, sorted by analyst recommendation
./venv/bin/python data_pipeline/create_report.py -cv classification:D+ -s recommendationKey
