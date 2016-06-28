from datetime import datetime
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

def get_districts():
    pass

def get_building_codes(district):
    pass

def get_building_details(base_cblgcode):
    params = { "type" : 2, "code" : base_cblgcode }
    url = "http://estate.centadata.com/pih09/pih09/estate.aspx"
    req = requests.get(url, params=params)
    if req.status_code != 200:
        raise Exception("Failed to load page: %s" % req.url)
    res = { "address" : None, "school_net" : None, "developer" : None, "start_date" : None, "tower_count" : None, "flat_count" : None }
    root = lxml.html.fromstring(req.text)
    tables = root.xpath("//table[@class='tableDesc1']")
    if len(tables) <= 0:
        return None
    table = tables[0]
    rows = table.xpath("tr")
    for row in rows:
        print(lxml.html.tostring(row))
        print(row.text_content())
        cols = row.xpath("td")
        tokens = [c.text_content().strip() for c in cols]
        if len(tokens) < 2:
            continue
        if tokens[0].startswith(u'地址'):
            res["address"] = tokens[1]
        elif tokens[0].startswith(u'所屬校網'):
            res["school_net"] = int(get_numeric(tokens[1]))
        elif tokens[0].startswith(u'發展商'):
            res["developer"] = tokens[1]
        elif tokens[0].startswith(u'入伙日期'):
            res["start_date"] = datetime.strftime(datetime.strptime(tokens[1], "%m-%Y"), "%Y-%m")
        elif tokens[0].startswith(u'物業座數'):
            res["tower_count"] = int(get_numeric(tokens[1]))
        elif tokens[0].startswith(u'單位總數'):
            res["flat_count"] = int(tokens[1])
    return res

def getHistoricalTransactionEstate(base_cblgcode):

    params = { "type" : 1, "code" : base_cblgcode }
    url = 'http://www1.centadata.com/tfs_centadata/Pih2Sln/TransactionHistory.aspx'
    r = requests.get(url, params=params)
    if r.status_code != 200:
        raise Exception("Failed to load page: %s" % r.url)

    htmlPage = r.text
    htmlElement = lxml.html.fromstring(htmlPage)

    # find block cblgcode <--

    cblgcodes_links = htmlElement.xpath('//table[@class="unitTran-left-a"]/tr/td/a')

    cblgcodes = []

    for link in cblgcodes_links:
        ahref = link.get('href')
        cblgcode = re.search('code=([A-Z]{10})',ahref).group(1)
        cblgcodes.append(cblgcode)

    url_get_transaction = 'http://www1.centadata.com/tfs_centadata/Pih2Sln/Ajax/AjaxServices.asmx/GenTransactionHistoryPinfo'

    historical_transactions = []

    for cblgcode in cblgcodes:
        params["code"] = cblgcode
        r = requests.get(url, params=params)

        htmlPage = r.text
        htmlElement = lxml.html.fromstring(htmlPage)
        acodes_links = htmlElement.xpath('//tr[@class="trHasTrans"]')

        # find floor and room acode <-- 

        acodes = [l.get('id') for l in acodes_links]

        for acode in acodes:
            postInfo = { "acode" : acode, "cblgcode" : cblgcode, "cci_price" : "", "cultureInfo" : "TraditionalChinese" }

            r = requests.post(url_get_transaction, data = postInfo)
            strings = r.text.encode('utf-8')
            tree = lxml.etree.fromstring(strings).text
            htmlElement = lxml.html.fromstring(tree)
            rows = htmlElement.xpath('//tr')

            flat_name = None
            net_area = None
            gross_area = None

            transaction_history = []
            is_transaction_history = False

            for r in rows:
                cols = r.xpath("td")
                tokens = [c.text_content().strip() for c in cols]
                if len(tokens) <= 0:
                    continue
                if len(tokens[0]) <= 0:
                    continue
                if tokens[0].startswith(u'屋苑名稱'):
                    flat_name = tokens[1]
                elif tokens[0].startswith(u'實用面積'):
                    try:
                        net_area = get_numeric(tokens[1])
                    except:
                        pass
                elif tokens[0].startswith(u'建築面積'):
                    try:
                        gross_area = get_numeric(tokens[1])
                    except:
                        pass
                elif tokens[0].startswith(u'過往成交紀錄'):
                    is_transaction_history = True
                elif tokens[0].startswith(u'筍盤推薦'):
                    is_transaction_history = False
                if is_transaction_history:
                    transaction = {}
                    transaction["flat_name"] = flat_name
                    transaction["net_area"] = net_area
                    transaction["gross_area"] = gross_area
                    if re.match("[0-9]{2}/[0-9]{2}/[0-9]{2}", tokens[0]):
                        transaction["date"] = datetime.strftime(datetime.strptime(tokens[0], "%d/%m/%y"), "%Y-%m-%d")
                        transaction["sale_price"] = get_numeric(tokens[1])
                        transaction["net_price"] = None
                        transaction["gross_price"] = None
                        for t in tokens[2:]:
                            if u'建' in t:
                                transaction["gross_price"] = get_numeric(t)
                            elif u'實' in t:
                                transaction["net_price"] = get_numeric(t)
                        transaction_history.append(transaction)
                    else:
                        continue

            historical_transactions += transaction_history

    return historical_transactions

# Orders on market

def get_page_count(posttype="S"):
    subparams = { "posttype" : posttype }
    count_suffix_url = "%s?%s" % (COUNT_SUFFIX_URL, urllib.parse.urlencode(subparams))
    count_params = { "chartType" : "price", "url" : count_suffix_url }
    req = requests.get(COUNT_URL, params=count_params)
    if req.status_code != 200:
        raise Exception("Cannot get count. Aborting ...")
    root = json.loads(req.text)
    count = sum([x["Cnt"] for x in root["ChartBars"]])
    n_pages = (count - 1) // 10 + 1
    return n_pages

def get_page(page, posttype="S"):
    subparams = { "posttype" : posttype, "limit" : -1, "currentpage" : page }
    suffix_url = "%s?%s" % (SUFFIX_URL, urllib.parse.urlencode(subparams))
    params = { "url" : suffix_url }
    req = requests.get(BASE_URL, params=params)
    if req.status_code != 200:
        raise Exception("Failed to load page. Aborting ...")
    root = json.loads(req.text)
    return root["post"]

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
        header = left.xpath(".//*[@class='ContentInfo_Header' and contains(@title, '')]")
        title = header[0].get("title").strip() if len(header) > 0 else None
        info["title"] = title
        ps = left.xpath("p")
        for x in ps:
            s = x.text_content()
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
                    area = get_numeric_part(s.text_content())
                    break
                prices = ps.xpath("div/div/span")
                ps = []
                for p in prices:
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
            details = "|".join([d.text_content().strip().replace("\n", "").replace("\r", "") for d in details])
            info["gross_area"] = gross_area
            info["net_area"] = net_area
            info["gross_price"] = gross_price
            info["net_price"] = net_price
            info["is_bo"] = is_bo
            info["details"] = details
            break
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

