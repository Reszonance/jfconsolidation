from .shipping_objects import *
from .excelthings import *

# do packages have to have a shipment defined??
# check if shipment exists for consolidating package
# obsolete for initializing data
# see save_data object in shipping_objects.py

saver = Save_Data()
shipment = saver.load_data()
if shipment is None:
  shipment = Shipment()
  customer1 = Customer(
                name="Justice Oladeji", 
                address="1164 Brightoncrest Green St SE", city="Calgary", 
                province="Alberta", 
                zip_code="T2Z 1G9", 
                cellnum="4039035399", 
                email="justice.oladeji@gmail.com")
  consignee = Consignee(
                name="Mr Ben Oguh", 
                address="Number 9 Olajide Esan Close Egeda Lagos", 
                city="Lagos", 
                province="Nigeria",
                cellnum="456463534")
  customer_order1 = CustomerOrder(
                      customer=customer1, 
                      description="cellphones", 
                      office_dropoff=True, 
                      office_pickup=True, 
                      wants_insurance=False)
  p1 = Package(
        dimensions=(23, 33, 16), 
        dim_units="INCH", 
        weight=7.7, 
        customer_order=customer_order1, 
        shipper=customer1, 
        consignee=consignee, 
        description="Cellphones", 
        has_batteries=True)
  customer_order1.assign_shipment(shipment)

  customer2 = Customer("Uzoma Emah", "5493 Crabapple Loop SW", "Calgary", "Alberta", 
                      "T6X 1S5", "780-802-4712", "info@ozone-concepts.com")
  consignee = Consignee("Azeez", "3a, Moses Emeiya close, Abule Egba (off Social Club)", "Lagos", "Nigeria", 
                        "None", "+234 809 899 1920")
  customer_order2 = CustomerOrder(customer2, "baby stuff", False, False, False)
  p1 = Package((20, 20, 20), "INCH", 2.0, customer_order2, customer2, consignee, "crib", False)
  p2 = Package((30, 30, 30), "INCH", 3.0, customer_order2, customer2, consignee, "baby monitor", True)
  p3 = Package((16, 23.5, 16), "CM", 4, customer_order2, customer2, consignee, "diapers", False)
  customer_order2.assign_shipment(shipment)
print('------DONE')