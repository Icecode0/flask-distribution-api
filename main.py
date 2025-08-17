from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from waitress import serve
import mysql.connector
import requests
import json
import logging
from datetime import datetime

logging.basicConfig(filename='apilog.log', level=logging.DEBUG)
logging.info('This will get logged')
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

conn_params = {
    "user": "OMITTED",
    "password": "OMITTED",
    "host": "OMITTED",
    "database": "OMITTED",
}

#Generate token 
def getToken():
    #API Call
    tokenUrl = 'https://orders.OMITTED.biz/cgi-bin/tnet/GenerateToken.p'
    headers = {"Content-type": "application/json"}
    data= '{"Authorization":[{"username":"OMITTED",,"password":"OMITTED",}]}'
    uriResponse = requests.get(tokenUrl,headers=headers,data=data)
    
    #Parsing Token Data to get Token
    tokenData = json.loads(uriResponse.text)
    token = tokenData['wToken'][0]['TOKEN']

    logging.info(token)
    
    #Send Token
    return token




#Customer Master       
@app.route('/api/V2/CustomerMaster', methods=['GET'])
@cross_origin()
def get_custMasterv2():
    hCust = request.args.get('hCustomer') or ''
    hSalesrep = request.args.get('hSalesrep') or ''
    
    # Connect to the database
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    # Prepare the SQL query to find customers
    query = """
    SELECT * FROM customers
    WHERE  (%s = '' OR CUSTOMER = %s) AND (%s = '' OR SALESREP = %s)
    """
    cursor.execute(query, ( hCust, hCust, hSalesrep, hSalesrep))

    # Fetch all matching records
    customers = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert the records to JSON
    customers_json = []
    columns = ["CO", "CUSTOMER", "NAME", "ADDRESS1", "ADDRESS2", "ADDRESS3", "CITY", "STATE", "ZIP", "PHONE1", 
               "PHONE2", "SALESREP", "SALESREPNAME", "CHAIN", "TERMS", "AGEDAYS1", "AGEDAYS2", "AGEDAYS3", 
               "AGEDAYS4", "CREDITHOLD", "ARCURR", "ARTOT", "EMAIL", "CREATEDATE", "EDITDATE", "SHIPSUN", 
               "SHIPMON", "SHIPTUE", "SHIPWED", "SHIPTHU", "SHIPFRI", "SHIPSAT", "ERROR"]

    for customer in customers:
        customer_dict = dict(zip(columns, customer))
        customers_json.append(customer_dict)

    return jsonify(customers_json)
    


#Item Master            
@app.route('/api/V2/ItemMaster', methods=['GET'])
@cross_origin()
def get_itemsAllv2():
    # Connect to the database
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    # Prepare the SQL query to fetch all items
    query = """
    SELECT * FROM items WHERE HIDDEN = FALSE
    """
    cursor.execute(query)

    # Fetch all matching records
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert the records to JSON
    items_json = []
    columns = ["CO", "ITEM", "DESCRIPTION", "BRAND", "RW", "STOCKSTATUS", "PRODUCTLINE", "MAJORCATEGORY", 
               "MINORCATEGORY", "CREATEDATE", "EDITDATE", "DELETEDATE", "TEMPZONE", "VENDORITEM", "MFGITEM", 
               "WORDS", "UNIT1", "UNIT2", "UNIT3", "PACK1", "PACK2", "PACK3", "GTIN1", "GTIN2", "GTIN3", 
               "BARCODE1", "BARCODE2", "BARCODE3", "SLSCOST1", "SLSCOST2", "SLSCOST3", "ONHAND", "ONORDER", 
               "RCVDT", "RAWONHAND", "SIZE1", "SIZE2", "SIZE3", "ERROR", "IMAGEURL", "IMAGECOUNT", 
               "WEIGHT1", "WEIGHT2", "WEIGHT3"]

    for item in items:
        item_dict = dict(zip(columns, item))
        items_json.append(item_dict)

    return jsonify(items_json)



#Order Guide Master      
@app.route('/api/V2/OrderGuideMaster', methods=['GET'])
@cross_origin()
def get_custOrderGuidev2():
    # Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCust')
    
    # Connect to the database
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    # SQL query to find order guides
    query_orderguides = """
    SELECT ORDERGUIDE, CUSTOMER, TITLE, DESCRIPTION, TEMPZONE FROM orderguides
    WHERE CUSTOMER = %s
    """
    cursor.execute(query_orderguides, (hCust,))

    order_guides = cursor.fetchall()

    query_items = """
    SELECT ogitems.ITEM, ogitems.CORD, ogitems.UNIT, items.DESCRIPTION, items.BRAND, items.RW, 
           items.STOCKSTATUS, items.IMAGEURL, items.IMAGECOUNT,
           items.UNIT1, items.PACK1, items.SLSCOST1, items.WEIGHT1,
           items.UNIT2, items.PACK2, items.SLSCOST2, items.WEIGHT2,
           items.UNIT3, items.PACK3, items.SLSCOST3, items.WEIGHT3
    FROM ogitems
    INNER JOIN items ON ogitems.ITEM = items.ITEM
    WHERE ogitems.ORDERGUIDE = %s
    """

    order_guides_json = []
    for order_guide in order_guides:
        order_guide_dict = {
            "ORDERGUIDE": order_guide[0],
            "CUSTOMER": order_guide[1],
            "TITLE": order_guide[2],
            "DESCRIPTION": order_guide[3],
            "TEMPZONE": order_guide[4],
            "ITEMS": []
        }

        cursor.execute(query_items, (order_guide[0],))
        items = cursor.fetchall()

        for item in items:
            unit_og = item[2]
            unit1, unit2, unit3 = item[9], item[12], item[15]
            pack, price, weight = '', '', ''

            if unit_og == unit1:
                pack, price, weight = item[10], item[11], item[12]
            elif unit_og == unit2:
                pack, price, weight = item[13], item[14], item[16]
            elif unit_og == unit3:
                pack, price, weight = item[17], item[18], item[19]

            item_dict = {
                "ITEM": item[0],
                "CORD": item[1],
                "UNIT": unit_og,
                "ITEMDESC": item[3],
                "BRAND": item[4],
                "RW": item[5],
                "STOCKSTATUS": item[6],
                "PHOTOURL": item[7],
                "IMAGECOUNT": item[8],
                "PACK": pack,
                "PRICE": price,
                "WEIGHT": weight  # Added weight
            }
            order_guide_dict["ITEMS"].append(item_dict)

        order_guides_json.append(order_guide_dict)

    cursor.close()
    conn.close()

    return jsonify(order_guides_json)



#Order Guide Post 
@app.route('/api/V2/OrderGuidePost', methods=['POST'])
@cross_origin()
def post_OrderGuidev2():
    #Getting Params
    data = json.loads(request.data)
    hCo = request.args.get('hCo')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/OrderGuidePost.p' + '?hCo=' + hCo + '&hUserName=OMITTED' + '&hToken=' + token
    
    logging.debug(url)
    headers = {"Content-type": "application/json"}
    uriResponse = requests.post(url,headers=headers,data=json.dumps(data))

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response



#ITEM BY KEYWORD     
@app.route('/api/V2/ItembyKeyword', methods=['GET'])
@cross_origin()
def get_itemKeywordv2():
    # Getting the keyword parameter from the search bar
    keyword = request.args.get('keyword')
    single_item = request.args.get('SingleItem', 'false').lower() == 'true'

    # Connect to the database
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()
    
    items_json = []
    
    columns = ["CO", "ITEM", "DESCRIPTION", "BRAND", "RW", "STOCKSTATUS", "PRODUCTLINE", "MAJORCATEGORY", 
               "MINORCATEGORY", "CREATEDATE", "EDITDATE", "DELETEDATE", "TEMPZONE", "VENDORITEM", "MFGITEM", 
               "WORDS", "UNIT1", "UNIT2", "UNIT3", "PACK1", "PACK2", "PACK3", "GTIN1", "GTIN2", "GTIN3", 
               "BARCODE1", "BARCODE2", "BARCODE3", "SLSCOST1", "SLSCOST2", "SLSCOST3", "ONHAND", "ONORDER", 
               "RCVDT", "RAWONHAND", "SIZE1", "SIZE2", "SIZE3", "ERROR", "IMAGEURL", "IMAGECOUNT",
               "WEIGHT1", "WEIGHT2", "WEIGHT3"]



    if single_item:
        # Fetch the item that exactly matches the keyword
        query = "SELECT * FROM items WHERE ITEM = %s AND HIDDEN = FALSE"
        cursor.execute(query, (keyword,))
        
         # Fetch all matching records
        items = cursor.fetchall()
        cursor.close()
        conn.close()
    
        # Convert the records to JSON
        
        
        for item in items:
            item_dict = dict(zip(columns, item))
            items_json.append(item_dict)
    else:
        # Split the keyword into individual words for multi-item search
        keywords = keyword.split('|')

        # Using CONCAT to ensure we match whole words in the comma-separated list
        like_clauses = " OR ".join(["WORDS LIKE CONCAT('%,', %s, ',%')" for _ in keywords])
        query = f"""
        SELECT * FROM items
        WHERE ({like_clauses}) AND HIDDEN = FALSE
        """
        query_params = tuple(keywords)
        cursor.execute(query, query_params)
        
        items = cursor.fetchall()
        cursor.close()
        conn.close()
    
        # Convert the records to JSON
        
        
        for item in items:
            item_dict = dict(zip(columns, item))
            items_json.append(item_dict)
            
        def count_matching_keywords(item):
            # Convert both item words and keywords to lower case for case-insensitive comparison
            item_words = set(word.lower() for word in item['WORDS'].split(','))
            lower_keywords = [keyword.lower() for keyword in keywords]

            # Count the number of keywords present in the item's words
            matching_count = sum(keyword in item_words for keyword in lower_keywords)
            return matching_count

        # Sort the items based on the number of matching keywords, in descending order
        items_json.sort(key=count_matching_keywords, reverse=True)


    return jsonify(items_json)



# CUSTOMER ITEM PRICING  
@app.route('/api/V2/CustomerItemPricing', methods=['GET'])
@cross_origin()
def get_custItemPricingv2():
    #Getting Params
    hCo = request.args.get('hCo')
    hCustomer = request.args.get('hCustomer')
    hItemList = request.args.get('hItemList')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerItemPricing.p' + '?hCo=' + hCo + '&hCustomer=' + hCustomer + '&hItemList=' + hItemList + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response



# CUSTOMER VELOCITY      
@app.route('/api/V2/CustomerVelocity', methods=['GET'])
@cross_origin()
def get_custVelocityv2():
    #Getting Params
    hCo = request.args.get('hCo')
    hCustomer = request.args.get('hCustomer')
    hBegDt = request.args.get('hBegDt')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerVelocity.p' + '?hCo=' + hCo + '&hCustomer=' + hCustomer + '&hBegDt=' + hBegDt + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response



# CUSTOMER ORDER POST 
@app.route('/api/V2/CustomerOrderPost', methods=['POST'])
@cross_origin()
#Path Function
def post_custOrderv2():
    # Getting Params
    data = json.loads(request.data)
    hCo = request.args.get('hCo')

    # Generate Token 
    token = getToken()

    # API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerOrderPost.p' + '?hCo=' + hCo + '&hUserName=OMITTED' + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.post(url, headers=headers, data=json.dumps(data))

    # Database insertion
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    # Get today's date in the same format as SHIPDATE
    today_date = datetime.now().strftime("%m/%d/%y")

    for order in data['Orders']:
        item_count = len(order.get('lines', []))
        query = """
        INSERT INTO orders (CO, CUSTOMER, ORDERNUM, STATUS_, ORDERDATE, SHIPDATE, TYPE_, PO, SHIPVIA, STAMP_OP, TTL_LN, TTL_PCS, TTL_EXT, FREIGHT, TTL_TAX, TTL_ADF, ITEMCNT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (hCo, order.get('customer'), '', '', today_date, order.get('shipdt'), '', order.get('po'), '', '', '', '', '', '', '', '', item_count))

    conn.commit()
    cursor.close()
    conn.close()

    # Return the response from the API call
    return app.response_class(
        response=uriResponse.content,
        status=uriResponse.status_code,
        mimetype='application/json'
    )



# DELETE ORDER
@app.route('/api/V2/DeleteOrder', methods=['GET'])
@cross_origin()
#Path Function
def get_delOrderv2():
    #Getting Params
    hCo = request.args.get('hCo')
    hOrder = request.args.get('hOrder')
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/DeleteOrder.p' + '?hCo=' + hCo + '&hOrder=' + hOrder + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response



# CUSTOMER ORDERS
@app.route('/api/V2/CustomerOrders', methods=['GET'])
@cross_origin()
def get_custOrdersv2():
    # Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCust')
    hBegDt = request.args.get('hBegDt')
    
    
    logging.info(f"hCo: {hCo}, hCust: {hCust}, hBegDt: {hBegDt}")
    
    
    # Connect to the database
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    # Prepare the SQL query to find customer orders
    query = """
    SELECT * FROM orders
    WHERE CO = %s AND CUSTOMER = %s
    """
    cursor.execute(query, (hCo, hCust))

    # Fetch all matching records
    all_orders = cursor.fetchall()
    
    logging.info(f"Number of records fetched: {len(all_orders)}")
    
    
    
    cursor.close()
    conn.close()

    # Define the columns list
    columns = ["CO", "CUSTOMER", "ORDERNUM", "STATUS_", "ORDERDATE", "SHIPDATE", "TYPE_", "PO",
               "SHIPVIA", "STAMP_OP", "TTL_LN", "TTL_PCS", "TTL_EXT", "FREIGHT", "TTL_TAX",
               "TTL_ADF", "ITEMCNT"]

    # Adjust the format of the date from the app
    app_date_format = '%m/%d/%y'
    _beginDate = datetime.strptime(hBegDt, app_date_format).strftime('%Y-%m-%d')

    # Filter orders based on the adjusted date
    filtered_orders = [order for order in all_orders if datetime.strptime(order[columns.index('ORDERDATE')], '%m/%d/%Y') >= datetime.strptime(_beginDate, '%Y-%m-%d')]

    # Sort orders by date
    sorted_orders = sorted(filtered_orders, key=lambda x: datetime.strptime(x[columns.index('ORDERDATE')], '%m/%d/%Y'))

    # Convert the sorted records to JSON
    orders_json = []

    for order in sorted_orders:
        order_dict = dict(zip(columns, order))
        orders_json.append(order_dict)
        
        

    return jsonify(orders_json)



# Order Status
@app.route('/api/V2/OrderStatus', methods=['GET'])
@cross_origin()
def get_orderStatusv2():
    #Getting Params
    hCo = request.args.get('hCo')
    hOrder = request.args.get('hOrder')
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders. OMITTED.biz:40443/cgi-bin/tnet/OrderStatus.p' + '?hCo=' + hCo + '&hOrder=' + hOrder + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response



#Customer AR 
@app.route('/api/V2/CustomerAR', methods=['GET'])
@cross_origin()
def get_custARv2():
    # Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCust')
    
    # Connect to the database
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    # Prepare the SQL query to find customer AR records
    query = """
    SELECT CO, CUSTOMER, INVOICE, INVOICEDT, DESCRIPTION, TYPE, DAYS, DISCOUNT, AMOUNT, BALANCE, DUEDT, TERMS, ARTOT, AR_30, AR_45, AR_60, AR_90
    FROM customer_ar
    WHERE CO = %s AND CUSTOMER = %s
    """
    cursor.execute(query, (hCo, hCust))

    # Fetch all matching records
    customer_ars = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert the records to JSON
    customer_ars_json = []
    columns = ["CO", "CUSTOMER", "INVOICE", "INVOICEDT", "DESCRIPTION", "TYPE", "DAYS", "DISCOUNT", "AMOUNT", "BALANCE", "DUEDT", "TERMS", "ARTOT", "AR_30", "AR_45", "AR_60", "AR_90"]

    for ar in customer_ars:
        ar_dict = dict(zip(columns, ar))
        customer_ars_json.append(ar_dict)

    return jsonify(customer_ars_json)


#Log Search 

@app.route('/api/V2/LogSearch', methods=['POST'])
@cross_origin()
def log_searchv2():
    # Getting Params
    cust = request.args.get('cust')
    search = request.args.get('search')
    selected = request.args.get('selected')

    # Get the current date and time
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Date and time in datetime format
    current_time = datetime.now().strftime("%H:%M")  # Time in 24-hour format

    # Database insertion
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()

    query = """
    INSERT INTO searches (CUSTOMER, SEARCH, DATE, TIME, SELECTED)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (cust, search, current_date, current_time, selected))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success", "message": "Search logged successfully"})

    
 
@app.route('/api/CustomerMaster', methods=['GET'])
@cross_origin()
#Path Function
def get_custMaster():
    #Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCustomer')
    hSalesrep = request.args.get('hSalesrep')
    
    #NullCheck
    if hCust==None:
        hCust=''
    if hSalesrep==None:
        hSalesrep=''
    
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz:40443/cgi-bin/tnet/CustomerMaster.p' + '?hCo=' + hCo + '&hCustomer=' + hCust + '&hSalesrep=' + hSalesrep + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response
    
@app.route('/api/ItemMaster', methods=['GET'])
@cross_origin()
#Path Function
def get_itemsAll():
    #Getting Params
    hCo = '1'
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz:40443/cgi-bin/tnet/ItemMaster.p' + '?hCo=' + hCo + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response

 
@app.route('/api/OrderGuideMaster', methods=['GET'])
@cross_origin()
#Path Function
def get_custOrderGuide():
    #Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCust')
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz:40443/cgi-bin/tnet/OrderGuideMaster.p' + '?hCo=' + hCo + '&hCust=' + hCust + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response

 
@app.route('/api/OrderGuidePost', methods=['POST'])
@cross_origin()
#Path Function
def post_OrderGuide():
    #Getting Params
    data = json.loads(request.data)
    hCo = request.args.get('hCo')
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz:40443/cgi-bin/tnet/OrderGuidePost.p' + '?hCo=' + hCo + '&hUserName=octopi' + '&hToken=' + token
    
    logging.debug(url)
    headers = {"Content-type": "application/json"}
    uriResponse = requests.post(url,headers=headers,data=json.dumps(data))

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response

 
@app.route('/api/ItembyKeyword', methods=['GET'])
@cross_origin()
#Path Function
def get_itemKeyword():
    #Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCust')
    hKeyword = request.args.get('hKeyword')
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz:40443/cgi-bin/tnet/ItembyKeyword.p' + '?hCo=' + hCo + '&hCust=' + hCust + '&hKeyword=' + hKeyword + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response

 
@app.route('/api/ItemOnhand', methods=['GET'])
@cross_origin()
#Path Function
def get_itemOnHand():
    #Getting Params
    hCo = request.args.get('hCo')
    hItemList = request.args.get('hItemList')
    
    #Generate Token 
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz:40443/cgi-bin/tnet/ItemOnhand.p' + '?hCo=' + hCo + '&hItemList=' + hItemList + '&hToken=' + token
    
    
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response

 
@app.route('/api/CustomerItemPricing', methods=['GET'])
@cross_origin()
#Path Function
def get_custItemPricing():
    #Getting Params
    hCo = request.args.get('hCo')
    hCustomer = request.args.get('hCustomer')
    hItemList = request.args.get('hItemList')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerItemPricing.p' + '?hCo=' + hCo + '&hCustomer=' + hCustomer + '&hItemList=' + hItemList + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response


@app.route('/api/CustomerVelocity', methods=['GET'])
@cross_origin()
#Path Function
def get_custVelocity():
    #Getting Params
    hCo = request.args.get('hCo')
    hCustomer = request.args.get('hCustomer')
    hBegDt = request.args.get('hBegDt')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerVelocity.p' + '?hCo=' + hCo + '&hCustomer=' + hCustomer + '&hBegDt=' + hBegDt + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response


@app.route('/api/CustomerOrderPost', methods=['POST'])
@cross_origin()
#Path Function
def post_custOrder():
    #Getting Params
    data = json.loads(request.data)
    hCo = request.args.get('hCo')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerOrderPost.p' + '?hCo=' + hCo + '&hUserName=octopi' + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers,data=json.dumps(data))
    
    print(uriResponse._content.decode('utf-8'))

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response


@app.route('/api/DeleteOrder', methods=['GET'])
@cross_origin()
#Path Function
def get_delOrder():
    #Getting Params
    hCo = request.args.get('hCo')
    hOrder = request.args.get('hOrder')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/DeleteOrder.p' + '?hCo=' + hCo + '&hOrder=' + hOrder + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response


@app.route('/api/CustomerOrders', methods=['GET'])
@cross_origin()
#Path Function
def get_custOrders():
    #Getting Params
    hCo = request.args.get('hCo')
    hCust = request.args.get('hCust')
    hBegDt = request.args.get('hBegDt')
    
    #Generate Token
    token = getToken()


    logging.info(hCo)
    logging.info(hCust)
    logging.info(hBegDt)

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/CustomerOrders.p' + '?hCo=' + hCo + '&hCust=' + hCust + '&hBegDt=' + hBegDt + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response


@app.route('/api/OrderStatus', methods=['GET'])
@cross_origin()
#Path Function
def get_orderStatus():
    #Getting Params
    hCo = request.args.get('hCo')
    hOrder = request.args.get('hOrder')
    
    #Generate Token
    token = getToken()

    #API Call
    url = 'https://orders.OMITTED.biz/cgi-bin/tnet/OrderStatus.p' + '?hCo=' + hCo + '&hOrder=' + hOrder + '&hToken=' + token
    headers = {"Content-type": "application/json"}
    uriResponse = requests.get(url,headers=headers)

    # Return the JSON response
    response = app.response_class(
        response=uriResponse._content.decode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    
    return response



if __name__ == '__main__':
    serve(app, host='0.0.0.0', threads= 10)