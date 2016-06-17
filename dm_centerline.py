import requests
import json
from lxml import html

def recursivePrint(nodes):
	info = []
	if nodes.getchildren():
		for n in nodes:	
			info = info + recursivePrint(n) 
		return info
	else:
		s = nodes.text_content().strip()
		if s != "":
			info.append(s)
		return info

url = 'http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx?url=http%3A%2F%2Fhk.centanet.com%2Ffindproperty%2Fzh-HK%2FHome%2FSearchResult%2F%3Fscopeid%3D203%26minprice%3D%26maxprice%3D%26minarea%3D%26maxarea%3D%26areatype%3DN%26posttype%3DS%26src%3DF%26sortcolumn%3D%26sorttype%3D%26limit%3D100%26currentpage%3D2'
text = requests.get(url).text
j = json.loads(text)
LargeString
f = open('centerline2.txt', 'w')
tobeprint = j['post'].encode('utf-8')
f.write(tobeprint)
f.close()

tree = html.fromstring(j['post'])

# propertyName = tree.xpath('//span[@class="ContentInfo_Header"]')
# netsize = tree.xpath('//div[@class="price_size"]/p/span[@class="LargeString"]')
# size = tree.xpath('//div[@class="price_size"]')
# room = tree.xpath('//p[@class="ContentInfo_DetailStr_Lf fLeft OneRow"]')
# price = tree.xpath('//div[@class="ContentInfo_Right fRight"]')

propertiesInfo = tree.xpath('//div[@class="SearchResult_Row"]')

properties = []

for index, pInfo in enumerate(propertiesInfo):
	propertyInfo = []
	SearchResult_Row = pInfo.getchildren()
	print index
	for child in SearchResult_Row :
		#print child, child.get('class')
		if child.get('class') == 'ContentInfo_Left fLeft':
			ContentInfo_Left_fLeft = child.getchildren()
			for child in ContentInfo_Left_fLeft:
				#print  " - "
				if child.tag == 'p':
					s = child.text_content()
					propertyInfo.append(s)
					print s
				else:
					#print child, child.get('class')
					if child.get('class') == 'ContentInfo_HeaderWrapper':
						propertyNames = child.getchildren()
						s = propertyNames[0].get('title').strip()
						propertyInfo.append(s)
						print s
						#print propertyNames[0].text_content().strip()
					if child.get('class') == 'ContentInfo_SubInfo':
						prices_sizes = child.getchildren()
						for price_size in prices_sizes:
							#print "--", price_size, price_size.get('class')
							if price_size.get('class') == 'price_size':
								pricesizeInfo = []
								s = price_size.text_content().split("\n")
								# propertyInfo.append(s)
								for ss in s:
									if ss.strip() != "":
										pricesizeInfo.append(ss.strip())
										print ss.strip()
								propertyInfo.append(pricesizeInfo)
							if price_size.get('class') == 'ContentInfo_DetailStr_Lf fLeft OneRow':
								s = price_size.text_content().strip().replace(" ", "").replace("\n", "")
								t = price_size.getnext().text_content().strip().replace(" ", "").replace("\n", "")
								u = price_size.getnext().getnext().text_content().strip().replace(" ", "").replace("\n", "")
								propertyInfo.append(s)
								propertyInfo.append(t)
								propertyInfo.append(u)
								print s,t,u
		if child.get('class') == 'ContentInfo_Right fRight':
			text = child.xpath("/text")
			s = recursivePrint(child)
			propertyInfo.append(s)


	properties.append(propertyInfo)		


for index, p in enumerate(properties):
	print index
	for info in p:
		if type(info) == list:
			for i in info:
				print i
		else:
			print info

# for divs in propertyName:
# 	s = divs.text_content().replace(" ", "").replace("\n","").strip()
# 	print s

# for index, divs in enumerate(netsize):
# 	s = divs.text_content().replace(" ", "").replace("\n","").strip()
# 	print index, s

# for index, divs in enumerate(size):
# 	s = divs.get('class')
# 	print index, s
# 	children =  divs.getchildren()
# 	print children[0].text_content()

# for index, divs in enumerate(room):
# 	s = divs.text_content().replace(" ", "").replace("\n","").strip()
# 	print index, s
# 	print divs.getnext().text_content()
# 	print divs.getnext().getnext().text_content()

# for index, divs in enumerate(price):
# 	children = divs.getchildren()
# 	print index
# 	for child in children:
# 		print child.text_content().replace(" ", "").replace("\n","").strip()

# for d in price:
# 	print d


# for d in size:
# 	print d
	#print d.decode('unicode-escape')



