"""
Steps through time windows, adjusting dynamically to fit within maximum results.
Inspired by PayPal's API being utter shit. Thanks, PayPal.
"""
import logging

logger = logging.getLogger('timestepper')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def set_log_level(level):
    logger.setLevel(level)
    ch.setLevel(level)

def do_window(start, delta, end, cap, margin_low, margin_high, acc, get):
    """
    Does a window.
    """
    if start + delta > end:
        delta = end - start
    logger.debug('Getting %s to %s (delta %s)' % (start, start+delta, delta))
    results = get(start, start + delta)
    if len(results) >= cap:
        logger.debug('Results capped, adjusting delta from %s to %s' % (delta, delta / 2))
        delta = delta / 2
        do_window(start, delta, end, cap, margin_low, margin_high, acc, get)
    else:
        acc += results
        start += delta
        if len(results) >= (cap * margin_high):
            logger.debug('Results above high margin, adjusting delta from %s to %s' % (delta, delta / 2))
            delta = delta / 2
        elif len(results) <= (cap * margin_low):
            logger.debug('Results below low margin, adjusting delta from %s to %s' % (delta, delta * 2))
            delta = delta * 2
        if start < end:
            do_window(start, delta, end, cap, margin_low, margin_high, acc, get)
    return acc
