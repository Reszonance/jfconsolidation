import datetime, pytz, pickle, os, numbers, shutil
import backend.excelthings as xl

# MEASUREMENTS ARE DEFINED IN INCHES, KG
# fixme create unique code for package
# PACKAGES MUST BELONG TO A CUSTOMER
# therefore belongs to a shipment
# do individual packages need insurance or jsut whole orders?
class Package:
    def __init__(self, dimensions: iter, dim_units: str, weight: float,
                 customer_order: Shipment, shipper: Shipper, consignee: Consignee,
                 description, has_batteries: bool, fragile: bool=False):
        
        # sender/receiver details
        # customer has to exist
        if not isinstance(customer_order, CustomerOrder):
            raise ValueError("Customer order does not exist")
        
        self.customer_order = customer_order
        self._shipper = shipper
        self._consignee = consignee

        # package details
        # consolidated_boxes is empty if not a
        # consolidated package
        self._dimensions = -1
        self.set_dimensions(new_dimensions=dimensions)
        self._dim_units = dim_units  # string: INCH or CM
        self.weight = weight
        self.description = description
        self.has_batteries = has_batteries
        self.fragile = fragile
        self.insurance = customer_order.insurance
        self.consolidated_boxes = []

        self.package_id = -1;   # fixme
        self.customer_order.add_package(self)
    
    def __repr__(self):
        return str(self.package_id)
    
    # override equality comparison
    def __eq__(self, other):
        if isinstance(other, Package):
            return (
                self.package_id == other.package_id and
                self.weight == other.weight
            )
        return False
    
    @property
    def id(self):
        return self.package_id
    @property
    def dimensions(self):
        # check if dimensions are blank if initializing without dimensions
        # to set dimension, do we need a setter too
        return self._dimensions
    @property 
    def dim_units(self):
        self._dim_units
    @dim_units.setter
    def dim_units(self, new_units):
        if new_units != 'INCH' and new_units != 'CM':
            raise ValueError('New units must be \'INCH\' or \'CM\'.')
    
    def set_dimensions(self, new_dimensions=None, length=None, width=None, height=None):
        if new_dimensions is not None:
            if not hasattr(new_dimensions, '__iter__'):
                raise ValueError("Dimensions must be an iterable.")
            if len(new_dimensions) == 3:
                self._dimensions = list(new_dimensions)
        else:
            if length is not None:
                if isinstance(length, numbers.Number):
                    self._dimensions[0] = length
                else:
                    raise ValueError("Length must be a number.")
            if width is not None:
                if isinstance(width, numbers.Number):
                    self._dimensions[1] = width
                else:
                        raise ValueError("Width must be a number.")
            if height is not None:
                if isinstance(height, numbers.Number):
                    self._dimensions[2] = height
                else:
                    raise ValueError("Height must be a number.")
        # in CM
    
    @property
    def cbm(self):
        multiplier = 1
        if self.dim_units.lower() == "inch":
            return (self.dimensions[0]*2.54 *
                    self.dimensions[1]*2.54 *
                    self.dimensions[2]*2.54
                    /6000
            )
        elif self.dim_units.lower() == "cm":
            multiplier = 1
        else:
            return ValueError(f"Cannot calculate CBM of unknown measurement ({self.dim_units.lower()})")
        return (self.dimensions[0]*multiplier *
                    self.dimensions[1]*multiplier *
                    self.dimensions[2]*multiplier
                    /6000
        )

    @property
    def shipment(self):
        return self.customer_order.shipment
    @property
    def customer(self):
        return self.customer_order.customer
    
    @property
    def shipper(self):
        return self._shipper
    @property
    def consignee(self):
        return self._consignee
    
    def get_dict(self):
        # returns a dict representation of package attributes
        # for writing to excel sheet
        return {
            'ID': self.package_id,
            'customer': self.customer_order.customer,
            'length': self.dimensions[0],
            'width': self.dimensions[1],
            'height': self.dimensions[2],
            'weight': self.weight,
            'shipper': self._shipper,
            'consignee': self._consignee,
            'description': self.description,
            'has batteries': self.has_batteries,
            'consolidated boxes': "None" if len(self.consolidated_boxes) > 0 else self.consolidated_boxes
        }
    
    def assign_id(self, id):
        self.package_id = id
    def get_id(self):
        return self.package_id

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

class ConsolidatedPackage(Package):
    def __init__(self, dimensions, dim_units, customer_order, description='Consolidated', package_list=[]):
        
        self.customer_order = None
        self._shipper = None
        self._consignee = None

        self._dimensions = -1
        self.set_dimensions(new_dimensions=dimensions)
        self.dim_units = dim_units  # string: INCH or CM
        self.description = description
        if len(package_list) < 2:
            raise ValueError("ConsolidatedPackage must have at least 2 packages.")
        
        consolidated_label = '-CONS'
        self.has_batteries = False
        self.fragile = False
        self.insurance = False

        self.package_id = len(self.consolidated_packages) + consolidated_label
        for pk, i in zip(package_list, range(1, len(package_list))):
            pk.id = self.package_id + f'-{i}'
            self.weight += pk.weight
            if not self.has_batteries and pk.has_batteries:
                self.has_batteries = True
            if not self.fragile and pk.fragile:
                self.fragile = True
            if not self.insurance and pk.customer_order.insurance:
                self.insurance = pk.customer_order.insurance
                
        
        self.customer_order.add_package(self)


class Person:
    def __init__(self, name: str, address: str, city: str, state: str, zip_code: str, phone: str, email: str):
        self.name = name
        self.address = address
        self.city = city
        self.state = state
        self.zip_code= zip_code
        self.phone = phone
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
            "Province": self.state,
            "Zip Code": self.zip_code,
            "Cell Number": self.phone,
            "email": self.email,
        }

#region PEOPLE
# the one who requests the shipment
# delivery option is a boolean tuple (send to calgary office, office pickup)
class Customer(Person):
    def __init__(self, name, address, city, state, zip_code, phone, email):
        super().__init__(name, address, city, state, zip_code, phone, email)

        # fixme customer id generating is handled by customer list
        self.customer_id = -1

# the one who is shipping the package
class Shipper(Person):
    pass

# the one receiving the package
# makes zip_code and email optional
class Consignee(Person):
    #  zip_code/email is either None or "" if no data
    def __init__(self, name, address, city, state, phone, zip_code=None, email=None):
        super().__init__(name, address, city, state, zip_code, phone, email)

#endregion

class CustomerDatabase:
    def __init__(self):
        # use a dict
        # will be looking up customers more often than
        # creating new ones
        self.customer_list = {}

    # CLASS ATTRIBUTE
    time_format = "%Y%m%d%H"
    
    # note: consider allowing an array of customers added
    def create_customer(self, name, address, city, state, zip_code, phone, email):
        new_customer = Customer(name, address, city, state, zip_code, phone, email)
        new_customer.customer_id = len(self.customer_list)
        self.customer_list.append(new_customer)

    # note: find a faster way to do this
    def generate_customer_id(self, customer):
        # assuming id is generated BEFORE customer is added to database
        pass
        # region old customer id assignment
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
        #endregion
        

# THIS CLASS HAS MOST POWER OVER OTHERS
# handle most things using this class
# note: make ID for each order?
# orders are assigned to shipments later
# package list not necessary in constrcutor
# when a new package is created it automatically gets assigned to the list
class CustomerOrder:
    def __init__(self, customer: Customer, description: str, office_dropoff: bool, office_pickup: bool, wants_insurance: bool):

        self._customer = customer
        self._description = description
        self.delivery_option = (office_dropoff, office_pickup)
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
    
    @shipment.setter
    def shipment(self, shipment_inst):
        self._shipment = shipment_inst
    
    # clearer to assign shipments via nameable function instead of setter
    def assign_shipment(self, shipment_inst):
        if self.shipment != -1:
            # TODO: update remove_order to remove packages too
            # remove self from customer list in shipment
            self.shipment.remove_shipping_order(self)
        self.shipment = shipment_inst
        if shipment_inst != -1:
            self.shipment.add_shipping_order(self)

    @property
    def customer(self):
        return self._customer
    
    @property
    def package_list(self):
        return self._package_list

    def add_package(self, package):
        self._package_list.append(package)
        if self.shipment != -1:
            packages = self.shipment._package_array
            packages.append(package)
            # fixme once package id assignment is better
            print('-----package added via customerorder')
            package.package_id = len(packages)

    # removes package from shipment AND order
    # change once order system is in place
    def remove_package(self, package):
        self._package_list.remove(package)
        if self.shipment != -1:
            packages = self.shipment._package_array
            packages.remove(package)
            # fixme once package id assignment is better
            print('-----package removed via customerorder object')
            package.package_id = -1
            self.shipment.assign_package_IDs()



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
    def __init__(self, customer_order):
        # gross weight and battery num are defined as property methods
        self._orders_array = []
        self._customer_array = []
        self._package_array = []
        self._consolidated_packages = []
        self._id = -1

    # region properties
    @property
    def id(self):
        return self._id
    
    # array of INDIVIDUAL PACKED BOXES
    # in shipment
    # consolidated box = 1 array entry
    @property
    def package_array(self):
        return self._package_array
    @property
    def consolidated_packages(self):
        return self._consolidated_packages
    @property
    def package_id_list(self):
        ids = []
        for pk in self.package_array:
            ids.append(pk.id)
        return ids

    @property
    def orders(self):
        return self._orders_array
    @property
    def customers(self):
        return self._customer_array

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

        # cost per kg
    shipment_cost = {
        "no battery": 13,
        "has battery": 14
    }
    # necessary for consolidating boxes
    company = None

    @property
    def company_order():

    
        # called on the class itself (not instance)
    @property
    def cost(self, kg, has_batteries):
        if has_batteries:
            return kg * Shipment.shipment_cost["has battery"]
        else:
            return kg * Shipment.shipment_cost["no battery"]
    @property
    def package_num(self):
        return len(self._package_array)
    
    @property
    def battery_num(self):
        return sum(
            pk.has_batteries for pk in self._package_array
        )
    @property
    def gross_weight(self):
        return sum(
            pk.weight for pk in self._package_array
        )
    
    @property
    def volumetric_weight(self):
        return round(
            sum(pk.cbm for pk in self._package_array), 2
            )

    # packages must belong to a customer
    # THERE SHOULD BE NO DUPLICATE IDS
    def assign_package_IDs(self):
        label = 0
        for pk in self.package_array:
            label += 1
            pk.assign_id(label)
    
    def package(self, package_id):
        package_id = int(package_id)    #fixme change later
        for pk in self.package_array:
            if pk.package_id is package_id:
                return pk
        return None
    
    def remove_package_from_shipment(self, package_id):
        print('removing '+str(package_id))
        package_id = int(package_id)    #fixme change later
        pk = self.package(package_id)
        if pk is None:
            raise ValueError("Cannot remove nonexistent package")
        else:
            self.package_array.remove(pk)
            # fixme once package id assignment is better
            pk.package_id = -1
            self.assign_package_IDs()   # reassign IDs for rest
            return pk

    def remove_shipping_order(self, customer_order):
        # fixme check if removed packages are part of consolidated boxes
        # remove packages and reassign IDs
        self.orders.remove(customer_order)
        self.customers.remove(customer_order.customer)
        for pk in customer_order.package_list:
            self.package_array.remove(pk)

    def add_shipping_order(self, customer_order):
        self.orders.append(customer_order)
        self.customers.append(customer_order.customer)
        for pk in customer_order.package_list:
            self.package_array.append(pk)
            pk.assign_id(len(self.package_array))

    # can be slow depending on # of packages
    # can optimize
    def consolidate(self, packages=[]):
        if len(packages) < 2:
            print('Need at least 2 packages to consolidate')
        else:
            # create a new box
            for pk in packages:
                print(f'----adding box {pk} to consolidated box')

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

        for order in self._orders_array:
            order_info = {}
            cs_info = {}
            cs_info["Name"] = order.customer.name
            cs_info["Email"] = order.customer.email
            cs_info["Cell Number"] = order.customer.phone
            cs_info["Delivery Option"] = order.delivery_dict[order.delivery_option]
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
        
        return data # this is sent to populate_shipment in excelthings
    
    def export_excel(self, filename):
        print(self.generate_excel_data())
        # name = "shipment_data.xlsx"
        xl.write_to_sheet(filename, self)
        return filename


# only saves data for one shipment for now
# TODO: save file now stores ALL shipments and customers, not just one shipment
# save file pickles Save_Data object
class Save_Data:
    _instance = None
    def __new__(cls, filename):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, filename="pickle_data.json"):
        if hasattr(self, 'initialized'):
            raise ValueError("Another instance of Save_Data cannot be created.")
        self.initialized = True
        root_folder = os.getcwd()  # Get the current working directory (root folder)
        save_folder = os.path.join(root_folder, "backend", "save_files")
        self.filename = filename
        self.file_path = os.path.join(save_folder, filename)
        self.old_file_path = os.path.join(save_folder, 'old_'+filename)

        self.shipments = []     # orders are stored in shipments
        self.customers = []

    def load_data(self, restart_data=False):
        try:
            with open(self.file_path, "rb") as file:
                shipment = pickle.load(file)
            return shipment
        except FileNotFoundError:
            print(f"The file '{self.file_path}' does not exist. Making new one.")
            if restart_data:
                return self.initialize_default_data()
            return None

    def save_data(self, shipment):
        if os.path.exists(self.old_file_path):
            os.remove(self.old_file_path)
        os.rename(self.filename, 'old_'+self.filename)
        with open(self.file_path, "wb") as file:
            pickle.dump(shipment, file)

    def erase_data(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            os.remove(self.old_file_path)
        else:
            print("Nothing to erase")
    
    # replaces current save file with old one
    # in case of corruption
    def restore_data(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        if os.path.exists(self.old_file_path):
            shutil.copy2(self.old_file_path, self.file_path)
        else:
            ValueError("Cannot find old data to restore.")
    
    # overwrites current data and replaces it with this default
    def initialize_default_data(self):
        print('--------INITIALIZING DATA')
        self.erase_data()
        company_customer = Customer(
            name="Jenik Freight",
            address='3571 52 St. SE, 1st Floor',
            city='Calgary',
            state='Alberta',
            zip_code='T2B 3R3',
            phone='(403)-402-0949',
            email='customerservice@jenikservices.ca'
        )
        company_order = CustomerOrder(
            customer=company_customer,
            description="defines origin and destination of shipment",
            office_dropoff=True,
            office_pickup=True,
            wants_insurance=False
        )
        shipment.company_order = company_order
        shipment = Shipment(company_order)
        customer1 = Customer(
                        name="Justice Oladeji", 
                        address="1164 Brightoncrest Green St SE", 
                        city="Calgary", 
                        state="Alberta", 
                        zip_code="T2Z 1G9", 
                        phone="4039035399", 
                        email="justice.oladeji@gmail.com")
        consignee = Consignee(
                        name="Mr Ben Oguh", 
                        address="Number 9 Olajide Esan Close Egeda Lagos", 
                        city="Lagos", 
                        state="Nigeria",
                        phone="456463534")
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
        print('--------DONE')
        return shipment
        
