from bs4 import BeautifulSoup
import requests
import ast
import csv

url = 'https://cstonelaw.harvestapp.com'
# Place headers copied from harvest here
headers = {}



def scrape_tables():

    tables_dict = {}
    for page_num in range(1, 19):
        r = requests.get(url + '/retainers?page=' + str(page_num), headers=headers)
        tables = BeautifulSoup(r.text, 'html.parser').find_all('table')

        for table in tables:
            client_info = {}
            for tr in table.find_all('tr'):
                if tr.td is not None and tr.contents is not None:
                    # If we are at the first table on the first page of the retainers page
                    if 'id' in table.attrs and table.attrs['id'] == 'retainers-ongoing':
                        client = tr.contents[1].contents[1].text
                        project = tr.contents[3].contents[1].text
                        uninvoiced_amount = tr.contents[5].contents[1].previous.strip().replace('\n','')
                        # If we're at the end of the table
                        if client == 'Total' and uninvoiced_amount == '':
                            break
                        retainer_balance = tr.contents[7].contents[1].text
                        link = tr.contents[5].contents[1].get('href')

                        client_info[len(client_info)] = {
                            'client': client,
                            'project': project,
                            'uninvoiced_amount': uninvoiced_amount,
                            'retainer_balance': retainer_balance,
                            'link': link
                        }
                    else:
                        # First column
                        client = tr.contents[1].contents[1].previous.strip().replace('\n','')
                        # Second column
                        project = tr.contents[3].contents[1].text
                        # Third column
                        drawn_balance = tr.contents[7].contents[1].previous.strip().replace('\n','')
                        link = tr.contents[7].contents[1].get('href')

                        client_info[len(client_info)] = {
                            'client': client,
                            'project': project,
                            'drawn_balance': drawn_balance,
                            'link': link
                        }

            tables_dict[len(tables_dict)] = client_info

    return tables_dict

def scrape_invoice_tables(client_table_result):
    invoice_dict = {}
    for table_num in client_table_result:
        for client in client_table_result[table_num]:
            page = client_table_result[table_num][client]['link']
            r = requests.get(url + page, headers=headers)
            tbody = BeautifulSoup(r.text, 'html.parser').find('tbody')
            if tbody is not None: 
                invoice_info = {}
                for tr in tbody.find_all('tr'):
                    if tr.td is not None and tr.contents is not None:
                        activity = tr.contents[1].contents[1].text.strip().replace('\n','')
                        date = tr.contents[3].text.strip().replace('\n','')
                        invoice_id = tr.contents[5].contents[1].text
                        amount = tr.contents[7].text.strip().replace('\n','')
                        link = tr.contents[7].contents[3].get('href')

                        invoice_info[len(invoice_info)] = {
                            'activity': activity,
                            'date': date,
                            'invoice_id': invoice_id,
                            'amount': amount,
                            'link': link
                        }
                client_table_result[table_num][client]['invoices'] = invoice_info
    return client_table_result

def scrape_invoice_page(invoice_results):
    row_dict = {}
    for table_page in invoice_results:
        for client_index in invoice_results[table_page]:
            if 'invoices' in invoice_results[table_page][client_index]:
                for invoice_index in invoice_results[table_page][client_index]['invoices']:
                    page = invoice_results[table_page][client_index]['invoices'][invoice_index]['link']
                    r = requests.get(url + page, headers=headers)
                    table = BeautifulSoup(r.text, 'html.parser').find_all('table')[2]
                    invoice_info = {}
                    for tr in table.find_all('tr'):
                            if tr.td is not None and tr.contents is not None:
                                if tr.contents[1].text.strip().replace('\n','') == '':
                                    user = 'not available'
                                else:
                                    user = tr.contents[1].contents[1].attrs['alt']
                                message = tr.contents[3].contents[1].text.strip().replace('\n','')
                                if message == 'Invoice updated.' or message == 'Invoice created.':
                                    continue
                                date = tr.contents[3].text.strip().replace('\n','')
                                if tr.contents[5].text == '\n':
                                    amount = ''
                                else:
                                    amount = tr.contents[5].contents[1].text.strip().replace('\n','')

                                invoice_info[len(invoice_info)] = {
                                    'icon_alt': user,
                                    'history_note': date,
                                    'message': message,
                                    'amount': amount
                                }

                    invoice_results[table_page][client_index]['invoices'][invoice_index]['invoice_info'] = invoice_info

    return invoice_results

def write_invoices():
    # Scrape data from /retainers?page=x
    client_table_result = scrape_tables()
    # Scrape data from /retainers/xxxxxx (client page)
    invoice_results = scrape_invoice_tables(client_table_result)
    # Scrape final data from each /invoices page
    invoices = scrape_invoice_page(invoice_results)

    # Write results to a file
    f = open("invoices.txt", "a")
    f.write(str(invoices))
    f.close()

def dict_to_csv():
    
    f = open("invoices.txt", 'r')
    invoice_results = ast.literal_eval(f.read())
    flattened = {}
    for index in invoice_results:
        if index != 0:
            for row in invoice_results[index]:
                flattened[len(flattened)] = invoice_results[index][row]

    with open('scraped.csv', 'w') as f:
        f.write('client|project|drawn_balance|retainer_link|activity|date|invoice_id|invoice_amount|invoice_link|icon_alt|history_note|message|invoice_row_amount\n')
    f.close

    for client_index in flattened:
        for project_index in flattened[client_index]['invoices']:
            for invoice_index in flattened[client_index]['invoices'][project_index]['invoice_info']:
                with open('scraped.csv', 'a') as f:
                    a = str(flattened[client_index]['client'])
                    b = str(flattened[client_index]['project'])
                    c = str(flattened[client_index]['drawn_balance'])
                    d = str(flattened[client_index]['link'])

                    e = str(flattened[client_index]['invoices'][project_index]['activity'])
                    g = str(flattened[client_index]['invoices'][project_index]['date'])
                    h = str(flattened[client_index]['invoices'][project_index]['invoice_id'])
                    i = str(flattened[client_index]['invoices'][project_index]['amount'])
                    j = str(flattened[client_index]['invoices'][project_index]['link'])

                    k = str(flattened[client_index]['invoices'][project_index]['invoice_info'][invoice_index]['icon_alt'])
                    l = str(flattened[client_index]['invoices'][project_index]['invoice_info'][invoice_index]['history_note']).strip().replace('\n','').replace('\r','').strip().replace('\r\n','')
                    m = str(flattened[client_index]['invoices'][project_index]['invoice_info'][invoice_index]['message']).strip().replace('\n','').replace('\r','').strip().replace('\r\n','')
                    n = str(flattened[client_index]['invoices'][project_index]['invoice_info'][invoice_index]['amount'])
                    f.write(a+'|'+b+'|'+c+'|'+d+'|'+e+'|'+g+'|'+h+'|'+i+'|'+j+'|'+k+'|'+l+'|'+m+'|'+n+'\n')
                
    

if __name__ == "__main__":
    # Write invoices.txt
    write_invoices()
    # Convert invoices.txt (results from every client and every invoice) to scraped.csv
    dict_to_csv()