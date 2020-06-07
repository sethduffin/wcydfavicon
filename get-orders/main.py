from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import extensions
import os,sys,time,pyperclip,signal,string
import local

driver = webdriver.Chrome()
action = ActionChains(driver)
driver.implicitly_wait(3)

extensions.set_driver(driver,action)

orders = []
all_products = []

def signal_handler(sig, frame):
    error("Manual Exit",False)

signal.signal(signal.SIGINT, signal_handler)

def error(e="Unkown",pause=True):
	try:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error: %s (%s %s)" % (e,fname,exc_tb.tb_lineno))
	except:
		pass
	if pause:
		input("-- Enter to Quit -- ")
	driver.quit()
	time.sleep(1)
	quit()

class Order:
	def __init__(self): 
		pass


def run():
	driver.get("https://my.ecwid.com/store/28113010#orders")
	driver.find("name","email")[0].send(local.email)
	driver.find("name","password")[0].send(local.password)
	driver.find("id","SIF.sIB").click()
	time.sleep(6)
	order_count = int(driver.find("class","order__number",True)[0].text)
	get_orders(order_count)
	write_csv()

def get_orders(count):
	try:
		done = False
		index = 0
		if local.start_order:
			index = local.start_order-1
		while not done:
			num = index+1
			if num <= count:
				driver.get("https://my.ecwid.com/store/28113010#order:id="+str(num)+"&return=orders")

				wait = 0
				while wait < 5:
					key = driver.find("id","XG",True)
					if len(key) > 0:
						if key[0].text == str(num):
							break
					time.sleep(.1)
					wait += 0.1
				else:
					error("Couldn't get order #%s" % (num))


				order = Order()
				orders.append(order)
				
				order.number = '=HYPERLINK("https://my.ecwid.com/store/28113010#order:id=%s&return=orders","%s")' % (num,num)
				order.date = driver.find("class","order-details__date").text
				order.customer = driver.find("id","1W").text
				order.email = driver.find("id","rG").text
				order.phone = driver.find("id","7Q").text
				
				p = driver.find('id','aJ').find("class","ecwid-Person").find("tag","div")
				order.address1 = p[1].text
				order.city = p[2].text.split(',')[0]
				s = p[2].text.split(',')[1].split(' ')
				order.state = s[1]
				order.zip = s[2]
				order.country = p[3].text

				order.delivery = driver.find("class","order-details__shipping").find("tag","strong").find("class","gwt-InlineLabel")[0].text
				if order.delivery == "Cache Valley Deliver":
					order.delivery = "CVD"
				if order.delivery == "U.S.P.S. Priority Mail":
					order.delivery = "USPS"
				order.payment = driver.find("class","order-details__payment").find("tag","strong")[0].find("class","gwt-InlineLabel").text
				if order.payment == "Credit or debit card":
					order.payment = "Card"
				order.item_total = driver.find("id","NO").text
				order.shipping_total = driver.find("id","vx").text
				order.tax_total = driver.find("class","order-detailed-taxes").up().find('class','gwt-Label')[1].text
				order.total = driver.find('id',"Bo").text
				order.products = get_products()
			else:
				done = True
			index += 1
	except Exception as e:
			error(e)

def get_products():
	try:
		Product = {
			"S":"",
			"M":"",
			"L":"",
			"XL":"",
			"XXL":""
		}
		products = {}
		for web_product in driver.find("class","order-details-products-list__product",True):
			class product:
				name = web_product.find("class","order-details-product__name").text.replace("WCYD ","")
				size = web_product.find("text~","Size:").up().find("class","product-attribute__value").text
				quantity = web_product.find("class","product-cost__multiplier").text
			if not product.name in all_products:
				all_products.append(product.name)
			if not product.name in products.keys():
				products[product.name] = Product.copy()
			if product.quantity:
				products[product.name][product.size] = product.quantity
			else:
				products[product.name][product.size] = "1"
		return products
	except Exception as e:
		error(e)

def write_csv():
	try:
		row1 = ["","Info","","","","","","","","","","","Cost","","",""]
		for product in all_products:
			row1 += [product,"","","",""]
		row2 = ["#","Date","Customer","Email","Phone","Address 1","City","State","Zip","Country","Delivery","Payment","Items","Shipping","Tax","Total"]
		for product in all_products:
			row2 += ["S","M","L","XL","XXL"]
		rows = [row1,row2]
		for order in orders:
			the_order = [
				order.number,
				order.date,
				order.customer,
				order.email,
				"\'"+order.phone,
				order.address1,
				order.city,
				order.state,
				order.zip,
				order.country,
				order.delivery,
				order.payment,
				order.item_total,
				order.shipping_total,
				order.tax_total,
				order.total
			]
			for product in all_products:
				if product in order.products:
					the_order.append(order.products[product]["S"])
					the_order.append(order.products[product]["M"])
					the_order.append(order.products[product]["L"])
					the_order.append(order.products[product]["XL"])
					the_order.append(order.products[product]["XXL"])
				else:
					the_order.append("")
					the_order.append("")
					the_order.append("")
					the_order.append("")
					the_order.append("")

			rows.append(the_order)
		
		rows.append([""])

		totals = []
		for i,label in enumerate(row2,1):
			if i == 3:
				totals.append("Totals")
			elif i <= 12:
				totals.append("")
			else:
				if i > 26:
					letter = "A"+string.ascii_uppercase[i-27] 
				else:
					letter = string.ascii_uppercase[i-1]
				formula = 'SUM(%s3:%s%s)' % (letter,letter,len(orders)+2)
				totals.append('=IF(%s<>0,%s,"")' % (formula,formula))
				
				
		rows.append(totals)

		csv = ""
		for row in rows:
			csv += "	".join(row)+"\n"
		pyperclip.copy(csv)
	except Exception as e:
			error(e)

try:
	run()
except Exception as e:
	error(e)
else:
	driver.quit()