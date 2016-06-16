import urllib
import requests
import json

BASE_URL = "http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx"
SUFFIX_URL = "http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/"
COUNT_URL = "http://hk.centanet.com/findproperty/zh-HK/Service/GetBarChartAjax"
COUNT_SUFFIX_URL = "http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/"

def get_page(page, posttype="S"):
    subparams = { "posttype" : posttype, "limit" : -1, "currentpage" : page }
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

