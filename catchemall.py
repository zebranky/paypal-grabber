#!/usr/bin/env python

import requests
import credentials
import timestepper
import urlparse
import logging
import datetime
import argparse

def get_shit(start, end):
    payload = {
        'METHOD': 'TransactionSearch',
        'STARTDATE': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'ENDDATE': end.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'USER': credentials.api_user,
        'PWD': credentials.api_passwd,
        'SIGNATURE': credentials.api_sig,
        'VERSION': '119.0'
    }

    r = requests.post('https://api-3t.paypal.com/nvp', data=payload)
    resp = parse_response(r.text)
    for txn in resp:
        txn.extra = get_details(txn.transactionid)
    return resp

def get_details(txnid):
    payload = {
        'METHOD': 'GetTransactionDetails',
        'TRANSACTIONID': txnid,
        'USER': credentials.api_user,
        'PWD': credentials.api_passwd,
        'SIGNATURE': credentials.api_sig,
        'VERSION': '119.0'
    }

    logging.debug('Getting details for %s' % txnid)
    r = requests.post('https://api-3t.paypal.com/nvp', data=payload)
    return r.text

class Transaction():
    def __init__(self, timestamp, timezone, type_, email, name,
                 transactionid, status, amt, currencycode, feeamt, netamt):
        self.timestamp = timestamp
        self.timezone = timezone
        self.type = type_
        self.email = email
        self.name = name
        self.transactionid = transactionid
        self.status = status
        self.amt = amt
        self.currencycode = currencycode
        self.feeamt = feeamt
        self.netamt = netamt
        self.extra = ''

    def __str__(self):
        return '\t'.join(str(x) for x in
                        (self.timestamp,
                         self.timezone,
                         self.type,
                         self.email,
                         self.name,
                         self.transactionid,
                         self.status,
                         self.amt,
                         self.currencycode,
                         self.feeamt,
                         self.netamt,
                         self.extra))

def parse_response(raw):
    d = urlparse.parse_qs(raw, keep_blank_values=True)
    results = []
    for i in range(100):
        if 'L_TIMESTAMP%s' % i in d:
            results.append(Transaction(d['L_TIMESTAMP%s' % i][0] if 'L_TIMESTAMP%s' % i else '',
                                       d['L_TIMEZONE%s' % i][0] if 'L_TIMEZONE%s' % i in d else '',
                                       d['L_TYPE%s' % i][0] if 'L_TYPE%s' % i in d else '',
                                       d['L_EMAIL%s' % i][0] if 'L_EMAIL%s' % i in d else '',
                                       d['L_NAME%s' % i][0] if 'L_NAME%s' % i in d else '',
                                       d['L_TRANSACTIONID%s' % i][0] if 'L_TRANSACTIONID%s' % i in d else '',
                                       d['L_STATUS%s' % i][0] if 'L_STATUS%s' % i in d else '',
                                       d['L_AMT%s' % i][0] if 'L_AMT%s' % i in d else '',
                                       d['L_CURRENCYCODE%s' % i][0] if 'L_CURRENCYCODE%s' % i in d else '',
                                       d['L_FEEAMT%s' % i][0] if 'L_FEEAMT%s' % i in d else '',
                                       d['L_NETAMT%s' % i][0] if 'L_NETAMT%s' % i in d else ''))
    logging.debug('Got %s results' % len(results))
    return results

def main():
    parser = argparse.ArgumentParser(description='Pull PayPal history for specified time window as (moderately gross) TSV.')
    parser.add_argument('start_date',
                        help='start date (inclusive) in ISO format (yyyy-mm-dd)',
                        type=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    parser.add_argument('end_date',
                        help='end date (exclusive) in ISO format (yyyy-mm-dd)',
                        type=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    parser.add_argument('-v', help='show verbose debugging output', action='store_true')
    args = parser.parse_args()
    level = logging.DEBUG if args.v else logging.WARN
    logging.basicConfig(level=level,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='[%H:%M:%S]')
    timestepper.set_log_level(level)
    results = timestepper.do_window(args.start_date,
                                    datetime.timedelta(14),
                                    args.end_date,
                                    100,
                                    0.2,
                                    0.8,
                                    [],
                                    get_shit)
    for r in results:
        print str(r)

if __name__ == '__main__':
    main()
