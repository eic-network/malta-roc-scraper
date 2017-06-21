import json
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver import PhantomJS


# Set the base url
_BASE_URL = 'http://rocsupport.mfsa.com.mt/pages/SearchCompanyInformation.aspx'

# Start a global browser and set it's attributes
_BROWSER = PhantomJS()
_BROWSER.set_window_size(1920, 1080)


def generate_results_rows():
    """
    Go to the first page and extract the parameters then navigate to the first pages of
    results.

    :return: Yield rows of companies
    """

    # Get the page
    _BROWSER.get(_BASE_URL)

    # Find the letters
    _BROWSER.find_element_by_xpath('//input[@id="ctl00_cphMain_RadComboBoxFirstLetter_Input"]').click()
    time.sleep(1)

    letters_length = len(_BROWSER.find_elements_by_xpath('//ul[@class="rcbList"][1]//li'))+1
    letter_xpath_template = '//ul[@class="rcbList"][1]//li[{}]'

    # Iterate through all the letters
    pg_size_set = False
    for index in range(2, letters_length):

        # Build the letter xpath from the template
        letter_xpath = letter_xpath_template.format(index)
        _BROWSER.find_element_by_xpath('//input[@id="ctl00_cphMain_RadComboBoxFirstLetter_Input"]').click()
        time.sleep(1)
        _BROWSER.find_element_by_xpath(letter_xpath).click()
        letter_text = _BROWSER.find_element_by_xpath(letter_xpath)

        time.sleep(1)
        try:
            # If the page size is not set then set it
            if not pg_size_set:
                _BROWSER.find_element_by_xpath('//tr[@class="rgPager"]//input[@id="ctl00_cphMain_RadGrid1_ctl00_ctl03_ctl01_PageSizeComboBox_Input"]').click()
                _BROWSER.find_element_by_xpath('//ul[@class="rcbList"][1]//li[3]').click()
                pg_size_set = True
                time.sleep(1)

            # Make sure this is the first page by clicking the first page button
            _BROWSER.find_element_by_xpath('//input[@class="rgPageFirst"]').click()
            time.sleep(1)

            # Get the rows on this page and yield them
            soup = BeautifulSoup(_BROWSER.page_source, 'lxml')
            rows = soup.findAll('tr', {'id': re.compile('ctl00_cphMain_RadGrid1_ctl00__[0-9]+')})
            for row in rows:
                yield row
            # If there are more pages of results for this letter now that the page has changed
            # navigate to the next pages until the last one is reached
            # First off: Something fucked happens here. some cookies get carried over from one letter to another
            if soup.select('div.rgWrap.rgInfoPart'):
                last_page = soup.select('div.rgWrap.rgInfoPart strong')[1].get_text().strip()
                while soup.select('a.rgCurrentPage')[0].get_text().strip() != last_page:
                    # Go to the next page and extract the rows from it to be processed further
                    _BROWSER.find_element_by_xpath('//input[@class="rgPageNext"]').click()
                    time.sleep(2.5)
                    soup = BeautifulSoup(_BROWSER.page_source, 'lxml')
                    rows = soup.findAll('tr', {'id': re.compile('ctl00_cphMain_RadGrid1_ctl00__[0-9]+')})
                    for row in rows:
                        yield row

        except:
            # If there are no other pages even at minimum page length extract all the rows and yield them
            soup = BeautifulSoup(_BROWSER.page_source, 'lxml')
            rows = soup.findAll('tr', {'id': re.compile('ctl00_cphMain_RadGrid1_ctl00__[0-9]+')})
            for row in rows:
                yield row


def generate_extracted_data():
    """
    Parse each retrieved page and extract the data form it

    :return: Yield dictionary containing the extracted data
    """

    for row in generate_results_rows():

        entity = dict()
        data = row.select('td')

        # Extract the data from the row
        entity['name'] = data[0].get_text().strip()
        entity['company_id'] = data[1].get_text().strip()
        entity['address'] = data[2].get_text().strip()
        entity['locality'] = data[3].get_text().strip()
        entity['status'] = data[4].get_text().strip()

        # Yield the extracted data
        yield entity


def main():
    """
    Main function of the script. Handles the execution and output
    """

    try:
        entity_list = list()
        for entity in generate_extracted_data():
            entity_list.append(entity)

        with open('gather.json', 'wt') as gather:
            gather.write(json.dumps(entity_list))

        _BROWSER.close()
    except:
        _BROWSER.close()

if __name__ == '__main__':
    main()
