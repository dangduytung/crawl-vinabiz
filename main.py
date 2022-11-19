import sys
import os
import requests
import logging
from datetime import datetime
import time
from bs4 import BeautifulSoup
import argparse
import urllib.parse
import xlsxwriter

from company import Company

FOLDER_SAVE_DATA = 'data'
FOLDER_SAVE_lOGS = 'logs'
TIME_SLEEP_CRAWL = 0  # Seconds
WEB_URL_ROOT = 'https://vinabiz.us'
PARAM_CRAWL = '/company'

cookie = ''


"""
======================= START CHECK SAVING FOLDERS
"""
# Folder save data crawled files
if not os.path.exists(FOLDER_SAVE_DATA):
    os.mkdir(FOLDER_SAVE_DATA)

# Folder save log files
if not os.path.exists(FOLDER_SAVE_lOGS):
    os.mkdir(FOLDER_SAVE_lOGS)
"""
======================= END CHECK SAVING FOLDERS
"""


"""
======================= START CONFIG LOG
"""
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Setting INFO for deploy PRODUCT
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                              '%m-%d-%Y %H:%M:%S')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler(FOLDER_SAVE_lOGS + '\\' +
                                   'log_{:%Y-%m-%d}.log'.format(datetime.now()), encoding="UTF-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)
"""
======================= END CONFIG LOG
"""

"""
======================= START ADD ARGUMENTS
"""
parser = argparse.ArgumentParser(
    description='A program crawl company info at ' + WEB_URL_ROOT + PARAM_CRAWL)
parser.add_argument("--start", "-s", help="start page",
                    type=int, required=True)
parser.add_argument("--end", "-e", help="end page", type=int, required=True)
parser.add_argument("--out", "-o", help="output file")
args = parser.parse_args()
"""
======================= END ADD ARGUMENTS
"""


def is_blank(s):
    return not (s and s.strip())


def is_not_blank(s):
    return bool(s and s.strip())


def int2hex(i):
    return f'{i:02x}'


def hex2int(data, idx):
    _ret = data[idx:idx+2]
    return int(_ret, base=16)


def encode(key, data):
    _data_encode = ''
    _key_encode = int2hex(ord(key))
    _data_encode += _key_encode
    for x in data:
        _x_encode = int2hex(ord(key) ^ ord(x))
        _data_encode += _x_encode
    return _data_encode


def decode(n, c):
    o = ''
    a = hex2int(n, c)
    logger.info('_key_email: ' + chr(a))
    i = c + 2
    xs = i
    for x in range(i, len(n)):
        if xs in range(i, len(n)):
            l = hex2int(n, xs) ^ a
            o += chr(l)
            xs = xs + 2
        else:
            break
    try:
        o = urllib.parse.unquote(urllib.parse.quote(o))
        logger.info('_email: ' + o)
        return o
    except Exception as e:
        logger.error(str(e))


def extract_domain(url):
    # scheme://netloc/path;parameters?query#fragment
    parsed_domain = urllib.parse.urlparse(url)

    # Just in case, for urls without scheme
    domain = parsed_domain.netloc or parsed_domain.path
    domain_parts = domain.split('.')
    if len(domain_parts) > 2:
        domain = '.'.join(domain_parts[-(2 if domain_parts[-1] in {
            'com', 'net', 'org', 'io', 'ly', 'me', 'sh', 'fm', 'us'} else 3): ])
    return parsed_domain.scheme + '://' + domain


def check_input():
    if args.start is None:
        logger.error('Please enter start page')
    if int(args.start) <= 0:
        logger.error('Please enter start page > 0')
        sys.exit(0)
    if args.end is None:
        logger.error('Please enter end page')
        sys.exit(0)
    if int(args.start) > int(args.end):
        logger.error('Please enter start page < end page')
        sys.exit(0)
    if args.out is None:
        args.out = get_name_file_by_url()
        logger.info('Auto create name file: ' + args.out)
    logger.debug('Args: ' + str(args))


def get_url_by_page(page):
    url = WEB_URL_ROOT + PARAM_CRAWL
    # page 1 doesn't need concatenate
    if int(page) > 1:
        url += '/' + str(page)
    return url


def request_list_company(page):
    url = get_url_by_page(page)
    logger.info("Getting list of company in page " +
                str(page) + " ~ url: " + url)
    company_url_list = []

    if is_blank(cookie):
        response = requests.get(url)
    else:
        response = requests.get(url, headers={'Cookie': cookie})

    soup = BeautifulSoup(response.content, 'html.parser')
    list_of_company_div = soup.find('div', {"id": "content"}).find(
        'div', class_="well").find_all("div", class_="row")
    for company_div in list_of_company_div:
        _ = company_div.find('a')['href']
        if _:
            company_url_list.append(_)
    logger.info('Get total ' + str(len(company_url_list)) + ' company url')
    return company_url_list


def get_company_details(url):
    url = WEB_URL_ROOT + url
    logger.info('Get company details in ' + url)

    if is_blank(cookie):
        response = requests.get(url)
    else:
        response = requests.get(url, headers={'Cookie': cookie})

    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.find('div', {'id': 'content'}).find(
        'table', class_='table').find_all('tr')

    # Parse info
    company = parse_company_detail(rows)
    company.url = url
    logger.info(company)
    return company


def parse_company_detail(rows):
    _email_encode = None
    company = Company()

    # THÔNG TIN ĐĂNG KÝ DOANH NGHIỆP
    company.official_name = rows[1].find_all('td')[1].get_text().strip()
    company.trading_name = rows[1].find_all('td')[3].get_text().strip()
    company.bussiness_code = rows[2].find_all('td')[1].get_text().strip()
    company.date_of_license = rows[2].find_all('td')[3].get_text().strip()
    company.administration_tax_agency = rows[1].find_all('td')[
        3].get_text().strip()
    company.start_working_date = rows[3].find_all('td')[3].get_text().strip()
    company.status = rows[4].find_all('td')[1].find_all(
        'div', class_='alert alert-success fade in')[0].get_text().strip()

    # THÔNG TIN LIÊN HỆ
    company.address = rows[7].find_all('td')[1].get_text().strip()
    company.phone = rows[8].find_all('td')[1].get_text().strip()
    company.fax = rows[8].find_all('td')[3].get_text().strip()

    # Decode email
    logger.info('email-data: ' + str(rows[9].find_all('td')[1]))

    if rows[9].find_all('td')[1].find('span', class_='__cf_email__'):
        _email_encode = rows[9].find_all('td')[1].find(
            'span', class_='__cf_email__')['data-cfemail']
    if _email_encode is not None:
        company.email = decode(_email_encode, 0)
    else:
        company.email = ''

    company.web = rows[9].find_all('td')[3].get_text().strip()
    company.representative = rows[10].find_all('td')[1].get_text().strip()
    company.representative_phone = rows[10].find_all('td')[
        3].get_text().strip()
    company.representative_address = rows[11].find_all('td')[
        1].get_text().strip()
    company.director = rows[12].find_all('td')[1].get_text().strip()
    company.director_phone = rows[12].find_all('td')[3].get_text().strip()
    company.director_address = rows[13].find_all('td')[1].get_text().strip()
    company.accountant = rows[14].find_all('td')[1].get_text().strip()
    company.accountant_phone = rows[14].find_all('td')[3].get_text().strip()
    company.accountant_address = rows[15].find_all('td')[1].get_text().strip()

    # THÔNG TIN NGÀNH NGHỀ, LĨNH VỰC HOẠT ĐỘNG
    company.main_job = rows[18].find_all('td')[1].get_text().strip()
    company.economic_field = rows[18].find_all('td')[3].get_text().strip()
    company.economic_type = rows[19].find_all('td')[1].get_text().strip()
    company.organization_type = rows[19].find_all('td')[3].get_text().strip()
    company.chapter_level = rows[20].find_all('td')[1].get_text().strip()
    company.economic_type_child = rows[20].find_all('td')[3].get_text().strip()

    return company


def get_name_file_by_url():
    parsed_domain = urllib.parse.urlparse(WEB_URL_ROOT)
    return 'Data_' + parsed_domain.netloc + '_' + datetime.now().strftime("%Y%m%d_%H%M%S")


def write_sheet_header(sheet):
    sheet_header = ['Tên chính thức', 'Tên giao dịch', 'Mã doanh nghiệp', 'Ngày cấp', 'Cơ quan thuế quản lý', 'Ngày bắt đầu hoạt động',
                    'Trạng thái', 'Địa chỉ trụ sở', 'Điện thoại', 'Fax', 'Email', 'Website', 'Người đại diện', 'SĐT người đại diện', 'Địa chỉ người đại diện', 'Giám đốc', 'SĐT giám đốc',
                    'Địa chỉ giám đốc', 'Kế toán', 'SĐT kế toán', 'Địa chỉ kế toán', 'Ngành nghề chính', 'Lĩnh vực kinh tế', 'Loại hình kinh tế', 'Loại hình tổ chức',
                    'Cấp chương', 'Loại khoản']
    for header in sheet_header:
        sheet.write(0, sheet_header.index(header), header)


def write_sheet_data(data):
    # Create a new workbook and add a worksheet
    _file_save = FOLDER_SAVE_DATA + '\\' + args.out + '.xlsx'
    wb = xlsxwriter.Workbook(_file_save)
    ws = wb.add_worksheet('Data')

    # Format the first column
    ws.set_column('A:A', 25)

    # Write headers
    write_sheet_header(ws)

    # Set row index start write data
    _row_idx = 1

    # Write data
    for company in data:
        attributes_arr = list(company.__dict__.keys())
        for att in attributes_arr:
            if (att == 'url'):
                continue
            _col_idx = attributes_arr.index(att)
            if (0 == _col_idx and company.url != ''):
                ws.write_url(_row_idx, _col_idx, url=company.url,
                             string=str(getattr(company, att)))
            else:
                ws.write(_row_idx, _col_idx, str(getattr(company, att)))
        _row_idx += 1

    wb.close()
    logger.info('Saved file: ' + _file_save)


def crawl():

    logger.info('<===> Crawl start')

    _company_arr = []
    _company_count = 0

    for i in range(int(args.start), int(args.end) + 1):
        
        # Get list company by page
        company_url_list = request_list_company(i)

        # Crawl info company one by one
        for company_url in company_url_list:
            try:
                _company_count += 1
                logger.info('count: ' + str(_company_count))

                # Get info
                _company = get_company_details(company_url)
                _company_arr.append(_company)

                # Sleep after crawl one
                if (TIME_SLEEP_CRAWL > 0):
                    time.sleep(TIME_SLEEP_CRAWL)
            except Exception as e:
                logger.error('url: ' + company_url)
                logger.error(str(e))

        # Write data excel
        write_sheet_data(_company_arr)

    logger.info('<===> Crawl end ~ Get information of total ' +
                str(len(_company_arr)) + ' companies')


def main():
    logger.info('====================================================')

    check_input()
    crawl()

    logger.info('====================================================')
    logger.info('')


if __name__ == '__main__':
    main()
