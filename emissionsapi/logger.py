# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Module to get pre-configured logger objects
"""
import logging


def getLogger(name):
    """Get Logger with the default logging configuration for this projects

    :param name: name of the logging program
    :type name: string
    :return: logger
    :rtype: logging.Logger
    """
    # Logging Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Create logger stream handler for logging to stderr
    handler = logging.StreamHandler()
    # Use formatter for the new handler
    handler.setFormatter(formatter)
    # Get logger for name
    logger = logging.getLogger(name)
    # Add handler to logger
    logger.addHandler(handler)
    # Set logging level
    logger.setLevel(logging.INFO)
    # Return logger
    return logger
