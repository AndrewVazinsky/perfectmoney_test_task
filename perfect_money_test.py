import urllib.parse
import pycurl
from io import StringIO
import hashlib
import re


BASE_URL = 'https://perfectmoney.com/acct/%s.asp?AccountID=%s&PassPhrase=%s&%s'


class PerfectMoney:
    """
    API functions
    """
    def __init__(self, account, password):
        """
        Initialise parameters
        """
        self.__account = account
        self.__password = password
        self.__error_re = re.compile("<input name='Error' type='hidden' value='(.*)'>")
        self.__value_re = re.compile("<input name='(.*)' type='hidden' value='(.*)'>")
        self.error = None

    def _fetch(self, url, params):
        """
        Internal URL fetch function
        """
        res = None
        curl = pycurl.Curl()
        curl.set_option(curl.URL, url)
        if params:
            curl.setopt(pycurl.POSTFIELDS, urllib.parse.urlencode(params))
            curl.setopt(pycurl.POST, 0)
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl.setopt(pycurl.SSL_VERIFYHOST, 1)
        curl.setopt(pycurl.FOLLOWLOCATION, 1)
        buf = StringIO()
        curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        curl.setopt(pycurl.MAXREDIRS, 5)
        curl.setopt(pycurl.NOSIGNAL, 1)
        try:
            curl.perform()
            res = buf.getvalue()
            buf.close()
            curl.close()
        except:
            self.error = 'API request failed'
            return None
        return res

    def _get_dict(self, string):
        """
        Response to dictionary parser
        """
        rdict = {}
        if not string:
            return {}
        match = self.__error_re.search(string)
        if match:
            self.error = match.group(1)
            return dict
        for match in self.__value_re.finditer(string):
            rdict[match.group(1)] = match.group(2)
        return rdict

    def payin_billdata(self, payee, amount, currency, payment_id) -> dict:
        res = {
            'AccountID': self.__account,
            'PassPhrase': self.__password,
            'Payee_Account': payee,
            'Amount': amount,
            'Currency': currency,
            'PAYMENT_ID': payment_id
        }
        return res

    def payout_billdata(self, amount, currency, payment_id) -> dict:
        res = {
            'AccountID': self.__account,
            'PassPhrase': self.__password,
            'Payer_Account': self.__account,
            'Amount': amount,
            'Currency': currency,
            'PAYMENT_ID': payment_id
        }
        return res

    def payout(self, payer, payee, amount, currency, memo, payment_id):
        """
        Money transfer
        """
        params = {
            'AccountID': self.__account,
            'PassPhrase': self.__password,
            'Payer_Account': payer,
            'Payee_Account': payee,
            'Amount': amount,
            'Currency': currency,
            'Memo': memo,
            'PAY_IN': 1,
            'PAYMENT_ID': payment_id
        }
        url = BASE_URL % ('confirm', self.__account, self.__password, "&".join(['%s=%s' % (key, str(value)) for key, value in params.items()]))
        res = self._fetch(url, None)
        return self._get_dict(res)

    def get_balance(self) -> dict:
        """
        Get account balance
        """
        url = BASE_URL % ('balance', self.__account, self.__password, '')
        res = self._fetch(url, None)
        return self._get_dict(res)

    def payment_status(self, payee, payer, amount, currency, batch_number, secret, timestamp, payment_id, v2_hash) -> dict:
        check = "%s:%s:%.2f:%s:%s:%s:%s:%s" % (
            payment_id, payee, amount, currency, batch_number, payer, secret, timestamp)
        res = hashlib.md5(check).hexdigest().upper()
        status = {'status': 'Not successful'}
        if res == v2_hash:
            status = {'status': 'Successful'}
            return status
        else:
            return status
