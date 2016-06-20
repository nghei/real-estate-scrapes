import re
import requests
from lxml import etree
from lxml import html

url = 'http://www1.centadata.com/tfs_centadata/Pih2Sln/Ajax/AjaxServices.asmx/GenTransactionHistoryPinfo'

postInfo = {}
postInfo['acode'] = 'TNNZIMHVTXXH'
postInfo['cblgcode'] = 'TNTLTHHXHX'
postInfo['cci_price'] = ''
postInfo['cultureInfo'] = 'TraditionalChinese'

# r = requests.post(url, data = postInfo)

# with open('historical.txt', 'w') as f:
# 	f.write(r.text.encode('utf-8'))

strings = ""

with open('historical.txt', 'r') as f:
	strings = f.read()

# for string in strings.split(";"):
# 	print string

tree = etree.fromstring(strings).text

print type(tree)

htmlElement = html.fromstring(tree)

print (etree.tostring(htmlElement, encoding='utf-8', pretty_print=True))

infos = htmlElement.xpath('//tr')

for index, info in enumerate(infos):
	tds = info.xpath('td')
	if len(tds) == 0:
		continue
	if not re.match("[0-9]{2}/[0-9]{2}/[0-9]{2}", tds[0].text_content()):
		continue
	print info.text_content()
	# for td in tds: 
	#  	print td.text_content()
	# if info.tag == 'tr':	
	# 	print index
	# 	print "<-------------START----------------->"
	# 	print info.tag
	# 	print info.text_content()
	# 	print info.getchildren()
	# 	print "<----------------END-------------->"



# for node in nodes:
# 	print node.getchildren()
# 	print
# 	print node.getchildren().text_content()


