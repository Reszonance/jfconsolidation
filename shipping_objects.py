import datetime
import pytz

# MEASUREMENTS ARE DEFINED IN INCHES, KG
# fixme create unique code for package
# PACKAGES MUST BELONG TO A CUSTOMER
# therefore belongs to a shipment
class Package:
    def __init__(self, dimensions, dim_units, weight,
                 customer_order, shipper, consignee,
                 description, has_batteries):
        
        # sender/receiver details
        # customer has to exist
        if customer_order is None or not isinstance(customer_order, CustomerOrder):
            raise ValueError("Customer order does not exist")
        
        self.customer_order = customer_order
        self.customer_order.add_package(self)
        self.shipper = shipper
        self.consignee = consignee


        # package details
        # consolidated_boxes is empty if not a
        # consolidated package
        self._dimensions = dimensions
        self.dim_units = dim_units
        self.weight = weight
        self.description = description
        self.has_batteries = has_batteries
        self.consolidated_boxes = []

        self.package_id = 0;   # fixme
    
    def __repr__(self):
        return str(self.package_id)
    
    @property
    def dimensions(self):
        # check if dimensions are blank if initializing without dimensions
        # to set dimension, do we need a setter too
        return self._dimensions
    
    @property
    def shipment(self):
        return self.customer_order.shipment
    
    def get_dict(self):
        # returns a dict representation of package attributes
        # for writing to excel sheet
        return {
            'ID': self.package_id,
            'customer': self.customer_order.customer,
            'length': self.dimension[0],
            'width': self.dimension[1],
            'height': self.dimension[2],
            'weight': self.weight,
            'shipper': self.shipper,
            'consignee': self.consignee,
            'description': self.description,
            'has batteries': self.has_batteries,
            'consolidated boxes': "None" if len(self.consolidated_boxes) > 0 else self.consolidated_boxes
        }
    
    # fixme check if correct
    def consolidate_package(self, *args):
        # failsafe in case package does not belong to a shipment yet
        if shipment is None:
            raise ValueError("No shipment exists for this package's customer order")
        
        # update package list
        # note: this assumes the customer belongs to a shipment
        shipment = self.customer_order.shipment
        for box in args:
            self.consolidated_boxes.append(box)
            # fixme change from array to dict for faster removal
            shipment.package_array = [p for p in shipment.package_array if p not in args]
        return self.consolidated_boxes
    


class Person:
    def __init__(self, name, address, city, province, zip_code, cellnum, email):
        self.name = name
        self.address = address
        self.city = city
        self.province = province
        self.zip_code= zip_code
        self.cellnum = cellnum
        self.email = email
    
    # will return person's name when referenced
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def get_dict(self):
        return {
            "Name": self.name,
            "Address": self.address,
            "City": self.city,
            "Province": self.province,
            "Zip Code": self.zip_code,
            "Cell Number": self.cellnum,
            "email": self.email,
        }

#region PEOPLE
# the one who requests the shipment
# delivery option is a boolean tuple (send to calgary office, office pickup)
class Customer(Person):
    def __init__(self, name, address, city, province, zip_code, cellnum, email):
        super().__init__(name, address, city, province, zip_code, cellnum, email)
        # fixme customer id generating is handled by customer list
        #self.customer_id = self.generate_customer_id()


# the one who is shipping the package
class Shipper(Person):
    pass

# the one receiving the package
class Consignee(Person):
    pass

#endregion

class CustomerList:
    def __init__(self):
        # use a dict
        # will be looking up customers more often than
        # creating new ones
        self.customer_list = {}

    # CLASS ATTRIBUTE
    time_format = "%Y%m%d%H"
    
    # note: consider allowing an array of customers added
    def add_customer(self, customer):
        cid = self.generate_customer_id(customer)
        self.customer_list[cid] = customer

    # note: find a faster way to do this
    def generate_customer_id(self, customer):
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        time_str = utc_now.strftime("C-"+self.time_format)
        # check if there is a customer matching this time_str
        # most recent customer, most recent time
        mr_customer = None
        mr_time = datetime.datetime.min

        for cid in self.customer_list:
            # extract creation time from customer ID
            ct_str = cid.split('-')[1]
            creation_time = datetime.datetime.strptime(ct_str, self.time_format)

            if creation_time > mr_time:
                mr_customer = self.customer_list[cid]
                #fixme do later


        
        return self.customer_id

        

# THIS CLASS HAS MOST POWER OVER OTHERS
# handle most things using this class
# note: make ID for each order?
# orders are assigned to shipments later
# package list not necessary in constrcutor
# when a new package is created it automatically gets assigned to the list
class CustomerOrder:
    def __init__(self, customer, shipping_description, send_to_calgary_office, office_pickup, wants_insurance):

        self._customer = customer
        self._description = shipping_description
        self.delivery_option = (send_to_calgary_office, office_pickup)
        self.insurance = wants_insurance

        self._package_list = []
        self._shipment = -1

    # class attribute
    delivery_dict = {
            (True, True): "Office to Office",
            (True, False): "Office to Door",
            (False, True): "Door to Office",
            (False, False): "Door to Door"
        }
    
    @property
    def shipment(self):
        return self._shipment
    
    # returns True if order has already been assigned to shipment
    def assign_shipment(self, shipment_inst):
        if self._shipment != -1:
            self._shipment = shipment_inst
            return True
        else:
            self._shipment = shipment_inst
            return False
    
    @property
    def customer(self):
        return self._customer
    
    @property
    def package_list(self):
        return self._package_list

    def add_package(self, package):
        self._package_list.append(package)
    
    # fixme 
    # check if package exists in array
    def remove_package(self, package):
        pass

    def get_delivery_method(self):
        return self.delivery_dict[self.delivery_option]
    
    def get_dict(self):
        return {
            **(self.customer.get_dict()),
            "Package Description": self.shipping_description,
            "Number of Boxes": len(self._package_list),
            "Delivery Option": self.get_delivery_method(),
            "Insurance": "Yes" if self.insurance else "No",
        }


# holds all data for a single shipment
# includes all customers, packages, etc for a shipment
# this would be an excel sheet
# find way to make id
# must access customer data through orders array
class Shipment:
    def __init__(self):
        # gross weight and battery num are defined as property methods
        self._orders_array = []
        self._customer_array = []
        self._package_array = []
        self._id = -1

    # region random
    @property
    def id(self):
        return self._id
    
    # for debugging
    # packages must belong to a customer
    def assign_package_IDs(self):
        pass
    
    # array of INDIVIDUAL PACKED BOXES
    # in shipment
    # consolidated box = 1 array entry
    @property
    def package_array(self):
        return self._package_array

    # array of TOTAL BOXES SENT BY CUSTOMERS
    # != package_array
    # package array is not dependent on customers
    # eg. consolidated package
    def get_customer_packages(self):
        package_list = []
        for c in self._customer_array:
            package_list.extend(c.package_array)
        return package_list
    
    @property
    def battery_num(self):
        battery_num = 0
        package_list = self.get_package_array()
        for p in package_list:
            if p.has_batteries:
                battery_num += 1
        return battery_num

    @property
    def gross_weight(self):
        gweight = 0
        package_list = self.get_package_array()
        for p in package_list:
            gweight += p.weight
        return gweight

    #endregion

        # class attributes
        # cost per kg
    shipment_cost = {
        "no battery": 13,
        "has battery": 14
    }
        # called on the class itself (not instance)
    @property
    def cost(self, kg, has_battery):
        if has_battery:
            return kg * Shipment.shipment_cost["has battery"]
        else:
            return kg * Shipment.shipment_cost["no battery"]
        

    def add_package(self, package):
        self._package_array.append(package)

    def remove_package(self, package):
        self._package_array.remove(package)

    def add_order(self, order):
        self._orders_array.append(order)

    def remove_order(self, order):
        # fixme add some checking here
        self._orders_array.remove(order)

    # for converting customer data to excel sheet
    # returns a list of dict representations of customers
    def get_customer_data(self):
        return [c.get_dict() for c in self._orders_array.customer]
    
    def get_package_data(self):
        return [p.get_dict() for p in self.package_array]
    
        # need some things
        # returns a nested dict of customer orders
        # DEFINES HOW DATA APPEARS IN EXCEL SHEET (ie. which data to show)
        # look at example customer info sheet to view structure
    def generate_excel_data(self):
        data = {}
        box_num = 0

            # how will data be presented for every order
        for order in self._orders_array:
            order_info = {}
            cs_info = {}
            cs_info["Name"] = order.customer.name
            cs_info["Email"] = order.customer.email
            cs_info["Cell Number"] = order.customer.cellnum
            cs_info["Delivery Option"] = order.delivery_dict[order.delivery_option] # boolean tuple
            cs_info["Wants Insurance"] = order.insurance
            cs_info["Total Cost"] = "=SUM()"
            cs_info["Notes"] = ""
            order_info["Customer Info"] = cs_info

                # ASSUMES DIMENSIONS ARE IN INCHES
                # bold whichever dimension applies
            pk_info = {}
            for pk in order.package_list:
                box_num += 1
                pk_details = {}
                pk_details["Units"] = pk.dim_units
                pk_details["Length"], pk_details["Width"], pk_details["Height"] = pk.dimensions
                pk_details["Gross Weight (kg)"] = pk.weight
                pk_details["CBM"] = "cbm" # calculate this from within spreadsheet
                pk_details["Has Batteries"] = pk.has_batteries

                pk_info[f"Box {box_num}"] = pk_details
            
            order_info["Packages"] = pk_info
            
            # note: will not work if 'Order' is not a hashable object
            data[order] = order_info
        
        return data

