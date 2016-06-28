#coding=utf-8

import re
import requests
from lxml import etree
from lxml import html
import csv
import json

def findLinksToEstate(url):

	r = requests.get(url)

	htmlPage = r.text
	htmlElement = html.fromstring(htmlPage)

	area_paths = htmlElement.xpath('//*[@id="bar-left"]/div[6]/div/div/a')
	area_links = []
	area_codes = []

	for area_path in area_paths:
		link = area_path.get('href')
		#print link
		p = re.search("""code=([0-9]*)""", link)
		code = p.group(1)
		area_codes.append(code)
		area_link = 'http://hk.centadata.com/'+ link +'&ref=CD2_Detail_Nav'
		area_links.append(area_link)

	url_get_estate = 'http://hk.centadata.com/Ajax/AjaxServices.asmx/paddresssearch1'

	for area_code in area_codes:		

		page_index = 1
		is_bottom = False
		cblgcode_estates = []

		#print area_code

		while not is_bottom:
			postInfo = {}
			postInfo['type'] = 22
			postInfo['code'] = area_code
			postInfo['pageIndex'] = page_index
			postInfo['pageSize'] = 30
			postInfo['columnName'] = 'vol180'
			postInfo['order'] = 'desc'

			#print page_index

			r = requests.post(url_get_estate, data = postInfo)
			strings = r.text.encode('utf-8')
			xmlElement = etree.fromstring(strings)
			tmp_info = xmlElement.text
			estates_info = json.loads(tmp_info)

			if len(estates_info['d']) == 0:
				is_bottom = True
				break

			for estate_info in estates_info['d']:
				#print estate_info['code']
				cblgcode_estates.append(estate_info['code'])

			page_index += 1

	return cblgcode_estates


if __name__ == '__main__':
	url = 'http://hk.centadata.com/paddresssearch1.aspx?type=22&code=101&ref=CD2_Detail_Nav'
	findLinksToEstate(url)
