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

	for index, info in enumerate(infos):
		if len(info.text_content()) == 0:
			continue
		historical_transaction.append(info.text_content())

	historical_transactions.append(historical_transaction)	

for historical_transaction in historical_transactions:
	for item in historical_transaction:
		print item,
	print

print historical_transactions
print type(historical_transactions)

f = open("historical_transactions_in_NanFungSunChuen.csv", "w")
for historical_transaction in historical_transactions:
	print >> f, historical_transaction


fr = open("historical_transactions_in_NanFungSunChuen.csv", "r")
text = fr.read()


# with open("historical_transactions_in_NanFungSunChuen.csv", "wb") as f:
# 	writer = csv.writer(f)
# 	for historical_transaction in historical_transactions:
# 		writer.writerows(historical_transaction)




		
