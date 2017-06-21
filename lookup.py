import json
import os
import re
import time
import requests

from random import randint
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError


_INDEX_URL = 'http://registry.mfsa.com.mt/index.jsp'
_LOGIN_URL = 'https://registry.mfsa.com.mt/login.do'
_LOGON_URL = 'https://registry.mfsa.com.mt/logon.do'
_SEARCH_PAGE_URL = 'https://registry.mfsa.com.mt/companySearch.do?action=companyDetails'
_SEARCH_URL = 'https://registry.mfsa.com.mt/companiesReport.do?action=companyDetails'
_INVOLVED_PARTIES_URL = 'https://registry.mfsa.com.mt/companyDetailsRO.do?action=involvementList'
_AUTHORISED_CAPITAL_URL = 'https://registry.mfsa.com.mt/companyDetailsRO.do?action=authorisedCapital'
_DOCUMENTS_URL_TEMPLATE = 'https://registry.mfsa.com.mt/documentsList.do?action=companyDetails&companyId={}'
_DOCUMENTS_URL_PAGED_TEMPLATE = (
                                    'http://registry.mfsa.com.mt/documentsList'
                                    '.do?action=companyDetails&companyId={}&pager.offset={}'
                                )

_LOGIN_DATA = {
    'username': 'username',
    'password': 'password',
}

_HEADERS = {'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'User-Agent': (
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ' (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
            )
            }

_SESSION = requests.Session()

_MAX_REQUESTS = 1000

_PROXIES = {
    'https': ''
}

_LIST_START = 0

def set_list_start(value):
    global _LIST_START
    _LIST_START = value


def get_proxy():
    proxy_list = eval(open('proxy_list.txt').read())
    proxy_index = eval(open('proxy_index.txt').read())
    while proxy_index < len(proxy_list):
        if proxy_list[proxy_index]['active']:
            break
        if proxy_index + 1 < len(proxy_list):
            proxy_index += 1
        else:
            proxy_index = 0

    with open('proxy_index.txt', 'wt') as proxy_index_file:
        if proxy_index + 1 < len(proxy_list):
            proxy_index_file.write(str(proxy_index + 1))
        else:
            proxy_index_file.write('0')

    proxy = proxy_list[proxy_index]
    return proxy['string']


def relogin():
    """
    Self explanatory
    """
    global _SESSION

    _PROXIES['https'] = get_proxy()

    _SESSION.close()
    time.sleep(2)
    _SESSION = requests.Session()
    _SESSION.headers.update(_HEADERS)
    _SESSION.get(_INDEX_URL, timeout=3.0, proxies=_PROXIES)

    # Perform login
    response = _SESSION.get(_LOGIN_URL, timeout=3.0, proxies=_PROXIES)
    soup = BeautifulSoup(response.text, 'lxml')

    # Instantiate a params dict and add the token, login data, and mouse position on the logon button
    params = dict()
    params['token'] = soup.find('input', {'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
    params.update(_LOGIN_DATA)
    params['logon.x'] = '45'
    params['logon.y'] = '10'

    _SESSION.post(_LOGON_URL, data=params, proxies=_PROXIES)


def session_request(url, entity=None, get_response=True, rtype=None, params=None):
    global _MAX_REQUESTS, _SESSION

    def request(url, get_response=True, rtype=None, params=None):

        response = None
        retry = 0
        while retry < 5:
            try:
                if rtype == 'post' and params:
                    response = _SESSION.post(url, data=params, timeout=3.0, proxies=_PROXIES)

                elif not params and rtype == 'post':
                    raise ValueError('params argument must be provided when performing a post request')

                elif not rtype:
                    response = _SESSION.get(url, timeout=3.0, proxies=_PROXIES)

                break
            except (ConnectionError):
                retry += 1
                time.sleep(1)

        if get_response:
            return response

    if _MAX_REQUESTS:
        _MAX_REQUESTS -= 1
        return request(url, get_response=get_response, rtype=rtype, params=params)
    else:
        time.sleep(2)
        relogin()
        if not request(_SEARCH_URL):
            return None

        params = dict()
        params['companyId'] = entity['company_id']
        params['companyName'] = ''
        params['companyNameComplexCombination'] = 'on'
        params['search.x'] = str(randint(10, 81))
        params['search.y'] = str(randint(4, 15))
        if not request(_SEARCH_URL, rtype='post', params=params):
            return None
        response = request(url, get_response=get_response, rtype=rtype, params=params)
        if get_response:
            return response


def generate_lookup_data():
    """
    Login and go to the search page. There perform the search based on the company id.
    For each company gather the
    :return:
    """

    _SESSION.headers.update(_HEADERS)
    session_request(_INDEX_URL, get_response=False)

    # Perform login
    response = session_request(_LOGIN_URL)
    soup = BeautifulSoup(response.text, 'lxml')

    # Instantiate a params dict and add the token, login data, and mouse position on the logon
    params = dict()
    params['token'] = soup.find('input', {'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
    params.update(_LOGIN_DATA)
    params['logon.x'] = '45'
    params['logon.y'] = '10'

    session_request(_LOGON_URL, get_response=False, rtype='post', params=params)

    entity_list = open('gather.json2', 'r').read()
    entity_list = eval(entity_list)

    # Navigate to the search url and
    for entity in entity_list[_LIST_START:]:
        # print(entity['company_id'])
        # Perform the search for this entity
        session_request(_SEARCH_URL, entity=entity)
        params = dict()
        params['companyId'] = entity['company_id']
        params['companyName'] = ''
        params['companyNameComplexCombination'] = 'on'
        params['search.x'] = str(randint(10, 81))
        params['search.y'] = str(randint(4, 15))

        response = session_request(_SEARCH_URL, entity=entity, rtype='post', params=params)

        if not response:
            continue

        soup = BeautifulSoup(response.text, 'lxml')
        entity['registration_date'] = 'unknown'
        if soup.find('td', text=re.compile('.*Registration Date.*')):
            entity['registration_date'] = soup.find(
                'td',
                text=re.compile('.*Registration Date.*')
                ).findNextSibling('td').get_text().strip()


        if soup.find('a', text=re.compile('.*Authorised Shares.*')):

            response = session_request(_AUTHORISED_CAPITAL_URL, entity=entity)
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract general data about the issued and authorised shares
            entity['authorised_shares'] = list()
            entity['total_authorised_shares'] = soup.find('td', text=re.compile('.*Total No\. of Authorised Shares.*'))
            entity['total_authorised_shares'] = entity['total_authorised_shares'].findNextSibling(
                'td').get_text().strip()
            entity['total_authorised_shares'] = re.sub('\s+|\n', ' ', entity['total_authorised_shares']).strip()
            entity['total_authorised_shares'] = re.sub(',', '', entity['total_authorised_shares']).strip()
            entity['total_authorised_shares_value'] = re.match('.*\(.*?([0-9\.]+).*\).*',
                                                               entity['total_authorised_shares'])
            entity['total_authorised_shares_value'] = eval(entity['total_authorised_shares_value'].groups()[0].strip())
            entity['total_authorised_shares'] = eval(re.sub('\(.*\).*', '', entity['total_authorised_shares']))
            entity['total_issued_shares'] = soup.find('td', text=re.compile('.*Total No\. of Issued Shares.*'))
            entity['total_issued_shares'] = entity['total_issued_shares'].findNextSibling('td').get_text().strip()
            entity['total_issued_shares'] = re.sub('\s+|\n', ' ', entity['total_issued_shares']).strip()
            entity['total_issued_shares'] = re.sub(',', '', entity['total_issued_shares']).strip()
            entity['total_issued_shares_value'] = re.match('.*\(.*?([0-9\.]+).*\).*', entity['total_issued_shares'])
            entity['total_issued_shares_value'] = eval(entity['total_issued_shares_value'].groups()[0].strip())
            entity['total_issued_shares'] = eval(re.sub('\(.*\).*', '', entity['total_issued_shares']))
            entity['authorised_shares'] = list()
            table_rows = soup.find('td', text=re.compile('.*Nominal Value Per Share in .*'))
            currency = re.match('.*Nominal Value Per Share in (.*)', table_rows.get_text().strip())
            currency = currency.groups()[0].strip()
            entity['shares_currency'] = currency

            table_rows = table_rows.findParent('table').findAll('tr')

            # If there is info about the issued shares extract each line and add it to the list
            if len(table_rows) > 1:
                for row in table_rows[1:]:
                    row_data = row.select('td')
                    share = dict()
                    share['authorised_share_capital'] = re.sub(',', '', row_data[0].get_text().strip())
                    share['authorised_share_capital'] = eval(share['authorised_share_capital'])
                    share['type'] = re.sub('\s*', '', row_data[1].get_text().strip())
                    share['nominal_value_per_share'] = eval(row_data[2].get_text().strip())
                    share['issued_shares'] = re.sub(',', '', row_data[3].get_text().strip())
                    share['issued_shares'] = eval(share['issued_shares'])
                    entity['authorised_shares'].append(share)

        # Load the involved parties page
        response = session_request(_INVOLVED_PARTIES_URL, entity=entity)

        if response:
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract the data about the involved parties
            entity['involved_parties'] = dict()
            tables = soup.findAll('td', {'class': 'tableheadDark', 'colspan': '3'})

            # Separate the big table into definite sections
            sections = dict()
            for table in tables:
                section = re.match('\s*(.*?)\(.*\).*', table.get_text().strip()).groups()[0]
                entity['involved_parties'][section] = list()
                sections[section] = list()
                table = table.findParent('tr')

                for party in table.findNextSiblings():
                    if party.find('hr'):
                        break

                    sections[section].append(party)

            # Extract the data from each section
            for section, involved_parties in sections.items():
                for party in involved_parties:
                    # If the row is empty skip it
                    if not party.get_text().strip():
                        continue

                    # If this is a table head also skip it
                    if party.find('td', {'class': 'tablehead'}):
                        continue

                    if party.find('tr', {'onmouseout': "this.className='pNormal'"}):
                        party_dict = dict()
                        party_data = party.findAll('td')
                        party_dict['name'] = party_data[0].get_text().strip()
                        party_dict['name'] = re.split('\n', party_dict['name'])
                        if len(party_dict['name']) > 1:
                            party_dict['name'], party_dict['party_id'] = party_dict['name'][0], party_dict['name'][1]
                        elif len(party_dict['name']) == 1:
                            party_dict['name'] = party_dict['name'][0]
                            party_dict['party_id'] = ''
                        else:
                            party_dict['name'] = ''
                            party_dict['party_id'] = ''

                        party_dict['address'] = re.sub('\r|\s*', '', party_data[1].get_text().strip())
                        party_dict['nationality'] = party_data[2].get_text().strip()

                        # If this party is a shareholder add the details about the shares they hold
                        if section.lower() == 'shareholders':
                            party_dict['shares'] = dict()
                            shares_data = party.findNext('td', text=re.compile('.*Shares.*'),
                                                         attrs={'class': 'tableHeadDark'})
                            shares_data = shares_data.findNext('td', {'class': 'tablehead'}).findParent(
                                'tr').findNextSibling('tr')
                            shares_data = shares_data.findAll('td')
                            party_dict['shares']['type'] = shares_data[0].get_text().strip()
                            party_dict['shares']['class'] = shares_data[1].get_text().strip()
                            party_dict['shares']['issued_shares'] = re.sub(',', '',
                                                                           shares_data[2].get_text().strip()).strip()
                            party_dict['shares']['issued_shares'] = eval(party_dict['shares']['issued_shares'])
                            party_dict['shares']['paid_up_%'] = eval(shares_data[3].get_text().strip())
                            party_dict['shares']['nominal_value_per_share'] = eval(shares_data[4].get_text().strip())

                        entity['involved_parties'][section].append(party_dict)

        # # Gather the data about all the documents
        # entity['documents'] = list()
        #
        # documents_url = _DOCUMENTS_URL_TEMPLATE.format(entity['company_id'])
        # response = session_request(documents_url, entity=entity)
        # if not response:
        #     yield entity
        #     continue
        #
        # soup = BeautifulSoup(response.text, 'lxml')
        #
        # # Extract the data from the current first
        # document_rows = soup.find('td', text=re.compile('Document In File'), attrs={'class': 'tablehead'})
        #
        #
        # if not document_rows:
        #     yield entity
        #     continue
        #
        # document_rows = document_rows.findParent('tr').findNextSiblings('tr',
        #                                                                 {'onmouseout': "this.className='pNormal'"})
        # for row in document_rows:
        #     row_data = row.findAll('td')
        #     row_dict = dict()
        #     row_dict['preview'] = row_data[0].find('a')['href']
        #     row_dict['preview'] = urljoin(_INDEX_URL, row_dict['preview'])
        #     row_dict['date'] = row_data[1].get_text().strip()
        #     row_dict['archived'] = row_data[2].get_text().strip()
        #     row_dict['document_in_file'] = row_data[3].get_text().strip()
        #
        #     if row_dict['document_in_file'] == 'NA':
        #         row_dict['document_in_file'] = None
        #     else:
        #         row_dict['document_in_file'] = eval(row_dict['document_in_file'])
        #
        #     row_dict['year'] = row_data[4].get_text().strip()
        #     row_dict['comments'] = row_data[5].get_text().strip()
        #     row_dict['was_paid'] = row_data[6].get_text().strip()
        #     row_dict['purchase__link'] = row_data[1].get_text().strip()
        #
        #     entity['documents'].append(row_dict)
        #
        # if soup.find('b', text=re.compile('.*Last Page.*\(.*\).*')):
        #     pages = soup.find('b', text=re.compile('.*Last Page.*\(.*\).*')).get_text().strip()
        #     pages = eval(re.match('.*\((.*)\).*', pages).groups()[0])
        # else:
        #     continue
        #
        # for index in range(1, pages):
        #     offset = 20 * index
        #     documents_url = _DOCUMENTS_URL_PAGED_TEMPLATE.format(entity['company_id'], offset)
        #
        #     document_rows = None
        #     retry = 0
        #     while retry < 5:
        #         response = session_request(documents_url, entity=entity)
        #         soup = BeautifulSoup(response.text, 'lxml')
        #
        #         # Extract the data from the current page
        #         document_rows = soup.find('td', text=re.compile('Document In File'), attrs={'class': 'tablehead'})
        #         retry += 1
        #         if document_rows:
        #             break
        #
        #     if not document_rows:
        #         break
        #
        #     document_rows = document_rows.findParent('tr').findNextSiblings('tr',
        #                                                                     {'onmouseout': "this.className='pNormal'"})
        #     for row in document_rows:
        #
        #         row_data = row.findAll('td')
        #         row_dict = dict()
        #         row_dict['preview'] = row_data[0].find('a')['href']
        #         row_dict['preview'] = urljoin(_INDEX_URL, row_dict['preview'])
        #         row_dict['date'] = row_data[1].get_text().strip()
        #         row_dict['archived'] = row_data[2].get_text().strip()
        #         row_dict['document_in_file'] = row_data[3].get_text().strip()
        #         if row_dict['document_in_file'] == 'NA':
        #             row_dict['document_in_file'] = None
        #         else:
        #             row_dict['document_in_file'] = eval(row_dict['document_in_file'])
        #
        #         row_dict['year'] = row_data[4].get_text().strip()
        #         row_dict['comments'] = row_data[5].get_text().strip()
        #         row_dict['was_paid'] = row_data[6].get_text().strip()
        #         row_dict['purchase__link'] = row_data[1].get_text().strip()
        #
        #         entity['documents'].append(row_dict)

        yield entity


def main():

    for entity in generate_lookup_data():
        _id = ''.join(s.title() for s in re.findall('[A-Za-z0-9]+', entity['company_id']))
        file_name = 'output/{}.json'.format(_id)
        with open(file_name, 'wt') as jfile:
            jfile.write(json.dumps(entity))


if __name__ == '__main__':
    gather = len(os.listdir('output'))
    set_list_start(gather)
    main()
