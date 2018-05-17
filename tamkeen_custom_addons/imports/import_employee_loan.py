import xmlrpclib
import csv

username = "admin"
pwd = "ERP@DEV2017"
dbname = "tamkeen_march27"

sock_common = xmlrpclib.ServerProxy ('http://10.60.74.42:8069/xmlrpc/common',
                                     allow_none=True)
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy('http://10.60.74.42:8069/xmlrpc/object', allow_none=True)

reader = csv.reader(open('/home/bista/Desktop/new_employee_loan.csv','rb'))

count = 0
for row in reader:
    print "row", count
    if count == 0:
        count+=1
        continue
    count +=1

    sale_id = False
    sale_order_exist = False
    line_exist =False

    loan_id = sock.execute(dbname, uid, pwd, 'hr.employee.loan', 'search',
                           [('name', '=', str(row[0]))])
    print "LOAN Request:::", loan_id
    if loan_id:
        sock.execute(dbname, uid, pwd, 'hr.employee.loan', 'write', loan_id,
                     {'loan_amount': float(row[1])})

