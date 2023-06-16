from shipping_objects import *
from excelthings import *

# do packages have to have a shipment defined??
# check if shipment exists for consolidating package

shipment = Shipment()

customer1 = Customer("Justice Oladeji", "1164 Brightoncrest Green St SE", "Calgary", "Alberta", 
                    "T2Z 1G9", "4039035399", "justice.oladeji@gmail.com")
consignee = Consignee("Mr Ben Oguh", "Number 9 Olajide Esan Close Egeda Lagos", "Lagos", "Nigeria", 
                      "None", "N/A", "N/A")
customer_order1 = CustomerOrder(customer1, "cellphones", True, True, False)
p1 = Package((23, 33, 16), "INCH", 7.7, customer_order1, customer1, consignee, "Cellphones", True)
shipment.add_order(customer_order1)

customer2 = Customer("Uzoma Emah", "5493 Crabapple Loop SW", "Calgary", "Alberta", 
                    "T6X 1S5", "780-802-4712", "info@ozone-concepts.com")
consignee = Consignee("Azeez", "3a, Moses Emeiya close, Abule Egba (off Social Club)", "Lagos", "Nigeria", 
                      "None", "+234 809 899 1920", "N/A")
customer_order2 = CustomerOrder(customer2, "baby stuff", False, False, False)
p1 = Package((20, 20, 20), "INCH", 2.0, customer_order2, customer2, consignee, "crib", False)
p2 = Package((30, 30, 30), "INCH", 3.0, customer_order2, customer2, consignee, "baby monitor", True)
p3 = Package((16, 23.5, 16), "CM", 4, customer_order2, customer2, consignee, "diapers", False)
shipment.add_order(customer_order2)


#print(shipment.generate_excel_data())
name = "cinfotesting.xlsx"
write_to_sheet(name, shipment)