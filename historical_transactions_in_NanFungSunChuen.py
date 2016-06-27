#coding=utf-8

import re
import requests
from lxml import etree
from lxml import html
import csv

url = 'http://www1.centadata.com/tfs_centadata/Pih2Sln/TransactionHistory.aspx?type=1&code=TNNZIHHVHX'

r = requests.get(url)

htmlPage = r.text
htmlElement = html.fromstring(htmlPage)

# find floor and room acode <-- 

links = htmlElement.xpath('//tr[@class="trHasTrans"]')

acodes = []

for link in links:
	acode = link.get('id')
	acodes.append(acode)

url_get_transaction = 'http://www1.centadata.com/tfs_centadata/Pih2Sln/Ajax/AjaxServices.asmx/GenTransactionHistoryPinfo'

historical_transactions = []
historical_transactions_dict = []

for acode in acodes[:10]:
	postInfo = {}
	postInfo['acode'] = acode
	postInfo['cblgcode'] = 'TNTLTHHXHX'
	postInfo['cci_price'] = ''
	postInfo['cultureInfo'] = 'TraditionalChinese'

	r = requests.post(url_get_transaction, data = postInfo)
	strings = r.text.encode('utf-8')
	tree = etree.fromstring(strings).text
	htmlElement = html.fromstring(tree)
	infos = htmlElement.xpath('//tr/td')

	historical_transaction = []
	historical_transaction_dict = {}

	transaction_history = []
	is_transaction_history = False

	for index, info in enumerate(infos):

		if len(info.text_content()) == 0:
			continue
		if unicode(info.text_content()) == u'\u5c4b\u82d1\u540d\u7a31: ':
			# 屋苑名稱: 
			historical_transaction_dict['name'] = infos[index+1].text_content()
		elif unicode(info.text_content()) == u'\u5be6\u7528\u9762\u7a4d: ':
			# 實用面積:
			historical_transaction_dict['netarea'] = infos[index+1].text_content()
		elif unicode(info.text_content()) == u'\u5efa\u7bc9\u9762\u7a4d: ':
			# 建築面積:
			historical_transaction_dict['grossarea'] = infos[index+1].text_content()
		elif unicode(info.text_content()) == u'\u904e\u5f80\u6210\u4ea4\u7d00\u9304':
			# 過往成交紀錄:
			is_transaction_history = True
		elif unicode(info.text_content()) == u'\u7b4d\u76e4\u63a8\u85a6':
			# 筍盤推薦
			is_transaction_history = False
			historical_transaction_dict['history'] = transaction_history 
		else:	
			historical_transaction.append(info.text_content())

		if is_transaction_history:
			transaction_history.append(info.text_content())

	historical_transactions.append(historical_transaction)	
	historical_transactions_dict.append(historical_transaction_dict)	

for historical_transaction in historical_transactions_dict:
	for item in historical_transaction.values():
		print item, " | "
	print

with open("historical_transactions_in_NanFungSunChuen.csv", "wb") as f:
	writer = csv.writer(f)
	for historical_transaction in historical_transactions:
		line = [item.encode("utf-8") for item in historical_transaction]
		print line
		writer.writerows([line])




		
