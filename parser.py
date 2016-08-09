import urllib.request
from bs4 import  BeautifulSoup
import time
import sys
import json


cookieProcessor = urllib.request.HTTPCookieProcessor()
opener = urllib.request.build_opener(cookieProcessor)
#This stores the set of all the ngos with their date_of_reg in the format name-date_of_reg
#so if there is any repetation of NGO then we can easily detect it

#Stores the soup to handle http://ngo.india.gov.in/sector_ngolist_ngo.php?page=1&psid=&records=200
url = "http://ngo.india.gov.in/sector_ngolist_ngo.php?page=1&psid=&records=200"
content=urllib.request.urlopen(url).read()
soup = BeautifulSoup(content,'lxml')
start_page, pages = 1, 359
#Gets in the entry you got an error on.
entry = int(sys.argv[1])
file_start = entry - entry % 1000
file_end = file_start + 1000

#Search for the number of total items
#on the first page and then compute the number of
#pages based on the number of items
pointer_to_td = soup.find('td', class_='hm_section_head_bg1')
nums = pointer_to_td.strong.string[pointer_to_td.strong.string.find('(')+1:pointer_to_td.strong.string.find(')')]
pages = int(nums) / 200
start_page = file_start // 200

#Just a temporary workaround
if file_start == 0:
    file_start, file_end, start_page = 1, 1000, 1

file_name = 'ngo_list_%d-%d.json'  % (file_start,file_end)
f = open(file_name, 'w')
print("Starting again from file : %s" %(file_name))

def a_tags_parser(page):
    '''
    Returns all the anchor tags of intrest so that you can parse out all the JS calls made by the anchor tag
    '''
    global soup
    url = "http://ngo.india.gov.in/sector_ngolist_ngo.php?page=%s&psid=&records=200" % (str(page))
    content=urllib.request.urlopen(url).read()
    soup = BeautifulSoup(content,'lxml')
    tr = soup.find('tr', "hm_section_head_bg1")
    tr_ke_bhai = tr.find_next_siblings()
    a_tags = [ele.a for idx, ele in enumerate(tr_ke_bhai) if idx % 2 == 0]
    return a_tags

def js_parser(a_tag,page):
    func_call = a_tag['href']
    a, b, c, d = func_call[21:func_call[21:].find("'")+21], 200 , page , func_call[::-1][2:func_call[::-1].find("'")+2][::-1]
    return a,b,c,d

def get_doc(a, b, c, d):
    return {'ngo_id': a, 'records_no': b, 'page_no': c,'page_val': '1', 'issue_id':'', 'ngo_black':d, 'records_no':'' }


print ('Number of pages to parse: ' + str(pages))

for page in range(int(start_page), int(pages)+1):
    print("Page number: "+ str(page) + ' / ' + str(pages))
    #If entry has reached multiple of 1000 make a new file
    if page*200 % 1000 == 0:
        file_name = 'ngo_list_%d-%d.json'  % (page*200,page*200+1000)
        f = open(file_name, 'w')



    #Fetches all the important anchor tags from that page
    a_tags = a_tags_parser(page)

    for a_tag in a_tags:
        strt = time.time()
        #Fetch value for a, b, c, d for a_tag
        a, b, c, d = js_parser(a_tag,page)

        # Encode it to send it along with the soup
        data = urllib.parse.urlencode(get_doc(a,b,c,d)).encode()
        soup = BeautifulSoup(opener.open('http://ngo.india.gov.in/view_ngo_details_ngo.php', data), "lxml")

        # We start with the first tag with class hm_section_head_bg1
        start = soup.find_all(class_='hm_section_head_bg1')[0]
        name = start.text[10:].strip()
        # Then we go to it's Parent and while it has siblings continue
        tr = start.parent
        entry = {}
        for tr_sibling in tr.find_next_siblings()[:len(tr.find_next_siblings())-1]:
            td = tr_sibling.find_all('td')
            if len(td) == 4:
                if td[1].string == None or td[3].string == None:
                    continue
                else:
                    key = td[1].string.strip()

                value = td[3].string.strip()
                entry[key] = value



        print(json.dumps(entry, sort_keys=True, indent=4))
        f.write(',\n' + json.dumps(entry, sort_keys=True, indent=4))
        stop = time.time()
        print("\n\n=============================================================== \n \n")
        print("Time taken for computation of this entry: %.4f Seconds" % (stop-strt))
