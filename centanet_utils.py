import urllib
import requests
import json
import lxml
import lxml.html
import re

### Utility Functions ###

def get_numeric_part(s):
    return float("".join([x for x in s if x.isdigit() or x == '.']))

def get_unit(s):
    if s == u'億':
        return 1e8
    elif s == u'萬':
        return 1e4
    else:
        return 1

def get_numeric(s):
    return get_numeric_part(s) * get_unit(s[-1])

### Centanet ###

# Constants

BASE_URL = "http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx"
SUFFIX_URL = "http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/"
COUNT_URL = "http://hk.centanet.com/findproperty/zh-HK/Service/GetBarChartAjax"
COUNT_SUFFIX_URL = "http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/"

# Historical transactions

def get_districts(big_district=None):
    big_districts = [big_district]
    if big_district is None:
        big_districts = ['HK', 'KL', 'NE', 'NW']
    res = []
    for bd in big_districts:
        params = { "type" : "district16", "code" : bd }
        req = requests.get("http://www1.centadata.com/paddresssearch1.aspx", params=params)
        if req.status_code != 200:
            continue
        root = lxml.html.fromstring(req.text)
        tables = root.xpath("table[@class='tbreg1']")
        for table in tables:
            print(table.text_content())

# Orders on market

def get_page(page, posttype="S"):
    subparams = { "maxprice" : 2000000, "posttype" : posttype, "limit" : -1, "currentpage" : page }
    suffix_url = "%s?%s" % (SUFFIX_URL, urllib.parse.urlencode(subparams))
    params = { "url" : suffix_url }
    req = requests.get(BASE_URL, params=params)
    if req.status_code != 200:
        raise Exception("Failed to load page. Aborting ...")
    root = json.loads(req.text)
    return root["post"]

def get_pages(posttype="S"):
    subparams = { "posttype" : posttype }
    count_suffix_url = "%s?%s" % (COUNT_SUFFIX_URL, urllib.parse.urlencode(subparams))
    count_params = { "chartType" : "price", "url" : count_suffix_url }
    req = requests.get(COUNT_URL, params=count_params)
    if req.status_code != 200:
        raise Exception("Cannot get count. Aborting ...")
    root = json.loads(req.text)
    count = sum([x["Cnt"] for x in root["ChartBars"]])
    n_pages = (count - 1) // 10 + 1
    divs = []
    for i in range(0, n_pages):
        try:
            divs.append(get_page(i + 1, posttype))
        except:
            continue
    return divs

def parse_page_content(content):
    tree = lxml.html.fromstring(content)
    properties = tree.xpath('//div[@class="SearchResult_Row"]')
    res = []
    for p in properties:
        info = {}
        left = p.xpath("*[@class='ContentInfo_Left fLeft']")
        if len(left) > 0:
            left = left[0]
        else:
            continue
        right = p.xpath("*[@class='ContentInfo_Right fRight']")
        if len(right) > 0:
            right = right[0]
        else:
            continue
        header = left.xpath("//*[@class='ContentInfo_Header' and contains(@title, '')]")
        title = header[0].get("title") if len(header) > 0 else None
        info["title"] = title
        ps = left.xpath("p")
        for p in ps:
            s = p.text_content()
            info["district"] = s
            break
        sale_price = right.xpath("p/span/span")
        sale_price = get_numeric(sale_price[0].text_content().strip()) if len(sale_price) > 0 else None
        info["sale_price"] = sale_price
        subinfo = left.xpath("*[@class='ContentInfo_SubInfo']")
        for i in subinfo:
            gross_area = None
            net_area = None
            gross_price = None
            net_price = None
            is_bo = False
            price_sizes = i.xpath("*[@class='price_size']")
            for ps in price_sizes:
                sizes = ps.xpath("p")
                for s in sizes:
                    print(lxml.html.tostring(s))
                    print(s.text_content())
                    area = get_numeric_part(s.text_content())
                    break
                prices = ps.xpath("div/div/span")
                ps = []
                for p in prices:
                    print(lxml.html.tostring(p))
                    print(p.text_content())
                    try:
                         ps.append(get_numeric_part(p.text_content()))
                    except:
                         is_bo = True
                try:
                    price = max(ps)
                except:
                    continue
                if net_area is None or net_price is None:
                    net_area = area
                    net_price = price
                else:
                    if area < net_area:
                        gross_area = net_area
                        gross_price = net_price
                        net_area = area
                        net_price = price
                    else:
                        gross_area = area
                        gross_price = price
            details = i.xpath("*[contains(@class, 'ContentInfo_DetailStr_Lf')]")
            details = "|".join([d.text_content().strip() for d in details])
            info["gross_area"] = gross_area
            info["net_area"] = net_area
            info["gross_price"] = gross_price
            info["net_price"] = net_price
            info["is_bo"] = is_bo
            info["details"] = details
            break
        print(info)
        res.append(info)
    return res

# Unused

def get_midland_page(page, tx_type="S"):
    params = { "estate_name" : "", "priceFrom" : None, "priceTo" : None, "areaFrom" : None, "areaTo" : None, "bedroom" : "", "tx_type" : tx_type, "area_type" : "net_area", "is_hos" : False, "autocompleteString" : "", "districtIds" : "", "estIds" : "", "latLngBounds" : "22.261965,113.92932,22.484834,114.290496" , "page" : page, "sort" : "", "bldgIds" : "", "feature" : "", "is_random" : False }
    postdata = json.dumps(params)
    req = requests.post(MIDLAND_URL, data=postdata)
    if req.status_code != 200:
        raise Exception("Failed to load page. Aborting ...")
    root = json.loads(req.text)
    return root

