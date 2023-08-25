import datetime, pytz, pickle, os, numbers, shutil
import backend.excelthings as xl

#from datetime import datetime

# MEASUREMENTS ARE DEFINED IN INCHES, KG
# fixme create unique code for package
# PACKAGES MUST BELONG TO A CUSTOMER
# therefore belongs to a shipment
# do individual packages need insurance or jsut whole orders?
class Package:
    def __init__(self, dimensions: iter, dim_units: str, weight: float,
                 customer_order, shipper, consignee,
                 description: str, has_batteries: bool, fragile: bool=False, consolidated=False):
        
        # sender/receiver details
        # customer has to exist
        if not isinstance(customer_order, CustomerOrder):
            raise ValueError("Customer order does not exist")
        
        self.customer_order = customer_order
        self._shipper = shipper
        self._consignee = consignee

        self.dim_units = dim_units  # string: INCH or CM
        self._dimensions = []
        self.set_dimensions(new_dimensions=dimensions)
        #self.dim_units = dim_units

        
        self.weight = weight
        self.description = description
        self.has_batteries = has_batteries
        self.fragile = fragile
        self.insurance = customer_order.insurance
        self._consolidated = consolidated
        self.parent_package = None

        self._package_id = -1;   # fixme
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
    def package_id(self):
        return self._package_id
    @package_id.setter
    def package_id(self, new_value):
        self._package_id = str(new_value)
        return self._package_id
    
    @property
    def consolidated(self):
        return self._consolidated
    @consolidated.setter
    def consolidated(self, new_value):
        try:
            cons, parent_package = new_value
        except ValueError:
            raise ValueError("Pass an iterable with two items")
        
        if cons == True:
            self.parent_package = parent_package
        elif self._consolidated:
            # remove from consolidated package
            # do not add this back in
            # causes problems during loops
            try:
                self.parent_package.packages.remove(self)
            except ValueError as e:
                print(f"Error: package not found in consolidated package list when trying to remove—{e}")
            self.parent_package.generate_ids()
            self.parent_package = None
        self._consolidated = cons
        return parent_package

    @property
    def dimensions(self):
        return self._dimensions
    
    @property
    def dim_units(self):
        return self._dim_units
    
    @dim_units.setter
    def dim_units(self, new_units):
        if new_units != 'INCH' and new_units != 'CM':
            raise ValueError('New units must be INCH or CM.')
        
        # unit conversion
        if hasattr(self, '_dim_units'):
            self.convert_dimensions(self._dim_units, new_units)

        self._dim_units = new_units

    def convert_dimensions(self, units: str, new_units: str):
        if units == new_units:
            return
        if units == "INCH":
            if new_units == "CM":
                self.set_dimensions(length=self.dimensions[0]*2.54,
                               width=self.dimensions[1]*2.54,
                               height=self.dimensions[2]*2.54)
        elif units == "CM":
            if new_units == "INCH":
                self.set_dimensions(length=self.dimensions[0]/2.54,
                               width=self.dimensions[1]/2.54,
                               height=self.dimensions[2]/2.54)
                
    def set_dimensions(self, new_dimensions: iter=None, length: float=None, width: float=None, height: float=None):
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
        
    def view_dimensions(self):
        dimensions = "("
        for dim in self.dimensions:
            dimensions += str(dim) + ", "
        return dimensions[:-2] + ")"
    @property
    def cbm(self):
        # in CM
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
    
    def validate(self):
        """
        Check if dimensions and weight are all filled in.
        If any of the dimensions or weight is 0,
        return a list of missing details.
        Otherwise, return True
        """
        # might make dimensions a dict instead
        missing = []
        dim = self.dimensions
        for i, d in enumerate(dim):
            if d == 0:
                if i == 0:
                    missing.append("length")
                elif i == 1:
                    missing.append("width")
                elif i == 2:
                    missing.append("height")
        if self.weight == 0:
            missing.append("weight")
        
        if len(missing) > 0:
            return missing
        return True

    
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
            'consolidated boxes': self.consolidated
        }



class ConsolidatedPackage(Package):
    def generate_id(self, list_position):
        """
        list position: nth consolidated box
        """
        return f'CONS-{list_position}'
    def generate_sub_id(self, position=-1):
        if position == -1:
            position = len(self.packages)
        return self.package_id + f'-{position}'
    def generate_ids(self):
        for pk, i in zip(self.packages, range(1, len(self.packages)+1)):
            pk.package_id = self.generate_sub_id(position=i)
    def generate_default_description(self, shipment, packages):
        # describe as shipper name and # of boxes they are shipping
        description = ""
        cdict = {}
        for pk in packages:
            c = shipment.package(pk).customer
            cdict[c] = cdict.get(c, 0) + 1
        for c, num in cdict.items():
            description += f'{c}: {num}x, '
        description = description[:-2]

    def __init__(self, dimensions, dim_units, customer_order, description='default', package_list=[]):

        #if len(package_list) < 2:
        #    raise ValueError("ConsolidatedPackage must have at least 2 packages.")

        shipment = customer_order.shipment
        self.customer_order = customer_order
        self._shipper = None
        self._consignee = None

        self.packages = []  # package_list items are added via add_packages()
        self._consolidated = False
        self.parent_package = None
        self._dimensions = -1
        self.set_dimensions(new_dimensions=dimensions)
        self.weight = 0
        self._dim_units = dim_units  # string: INCH or CM
        if description == 'default':
            description = self.generate_default_description(shipment, package_list)

        self.description = description

        self.has_batteries = False
        self.fragile = False
        self.insurance = False
        #self.consolidated = (False, None)   # do not remove
        shipment = self.customer_order.shipment
        
        self.customer_order.add_package(self)
        self._package_id = self.generate_id(shipment.consolidated_num)
        self.consolidated = (False, None)   # do not remove
        self.add_packages(*package_list)

    def add_packages(self, *packages):
        """
        Adds packages to consolidated box and removes it from shipment. 
        ID is assigned based on position in consolidated box package list.

        Parameters:
        ----------
        *packages: list
            List of package ids.

        Returns
        ----------
        None
        """
        shipment = self.customer_order.shipment
        for pk, i in zip(packages, range(1, 10)):
            print(self.packages)
            
        for pk in packages:
            pk = shipment.package(pk)
            pk.consolidated = (True, self)    # setter takes consolidated ID as argument
            # assigns package_id = -1 within function below
            shipment.remove_from_shipment(pk)
            self.packages.append(pk)
            pk.package_id = self.generate_sub_id()
            
            self.weight += pk.weight
            if not self.has_batteries and pk.has_batteries:
                self.has_batteries = True
            if not self.fragile and pk.fragile:
                self.fragile = True
        
        return None

    def remove_packages(self, remove_all=False, delete_self=False, packages=None):
        """
        Removes a list of packages from a consolidated box.

        Parameters:
        ----------
        packages: list
            List of package ids.
        remove_all: bool
            If set to true, removes all packages.

        Returns
        ----------
        None
        """
        if packages is None:
            packages = []
        
        for pk in packages:
            print(f'should be removing {pk}')

        if delete_self:
                # do not retain package info after deletion
                return
        
        if remove_all:
            packages = []
            for pk in self.packages:
                packages.append(pk)
        
        for i in range(0, len(packages)):
            # PACKAGE_ID OF A CONSOLIDATED BOX IS NOT BASED ON ITS POSITION WITHIN THE SHIPMENT
            pk = packages[i]
            # if searching based on ID
            # similar to Shipment.package() function
            if not isinstance(pk, Package):
                print('not a package object, searching by ID:')
                for p in self.packages:
                    if p.package_id == pk:
                        print(f'found: {p}')
                        pk = p

            # add to shipment before setting consolidated = False
            # otherwise it won't work (by design)
            # MAKE SURE pk.consolidated == FALSE BEFORE
            # REASSIGNING PACKAGE IDs
            pk.consolidated = (False, None)
            self.shipment.assign_package_IDs()
            self.weight -= pk.weight
            
        self.generate_ids()
        

        # update batteries/fragile info for consolidated box
        self.has_batteries = False
        self.fragile = False
        self.description = ""
        for pk in self.packages:
            if not self.has_batteries and pk.has_batteries:
                self.has_batteries = True
            if not self.fragile and pk.fragile:
                self.fragile = True


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
# orders are assigned to shipments later
# package list not necessary in constrcutor
# when a new package is created it automatically gets assigned to the list
class CustomerOrder:
    def __init__(self, customer, description: str, office_dropoff: bool, office_pickup: bool, wants_insurance: bool, notes: str=""):

        self._customer = customer
        self._description = description
        self.delivery_option = (office_dropoff, office_pickup)
        self.pickup_address = ""
        self.insurance = wants_insurance
        self.notes = notes

        self._packages = []
        self._shipment = -1
        self._id = -1

    def __str__(self):
        return self.customer.name

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

    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, new_id):
        self._id = str(new_id)

    @property
    def office_dropoff(self):
        return self.delivery_option[0]
    
    @office_dropoff.setter
    def office_dropoff(self, new_value):
        ls = list(self.delivery_option)
        ls[0] = new_value
        self.delivery_option = tuple(ls)
        return self.delivery_option
    
    @property
    def office_pickup(self):
        return self.delivery_option[1]
    
    @office_pickup.setter
    def office_pickup(self, new_value):
        ls = list(self.delivery_option)
        ls[1] = new_value
        self.delivery_option = tuple(ls)
        return self.delivery_option

    
    def assign_shipment(self, shipment_inst):
        if self.shipment != -1:
            # remove self from customer list in shipment
            self.shipment.remove_from_shipment(self)
        self.shipment = shipment_inst
        if shipment_inst != -1:
            self.shipment.add_shipping_order(self)
    

    @property
    def customer(self):
        return self._customer
    
    @property
    def packages(self):
        return self._packages

    def add_package(self, package):
        self.packages.append(package)
        if self.shipment != -1:
            print('-----package added via customerorder')
            self.shipment.assign_package_IDs()

    # removes package from shipment AND order
    def remove_package(self, package):
        if self.package_by_id(package) is None:
            raise ValueError("Cannot remove nonexistent package from order.")
        try:
            print(f'removing {package} from customer order')
            self.packages.remove(package)
        except ValueError:
            print("Package not found in customer order list but still exists in shipment.")

        # remove from shipment too
        if self.shipment != -1:
            if not package.consolidated:
                # consolidated packages are already removed from shipment
                #self.shipment.packages.remove(package)
                pass
            else:
                print(f'removing {package} from consolidated box')
                package.parent_package.remove_packages(packages=[package])
            if isinstance(package, ConsolidatedPackage):
                # does not remove box from shipment or customer order
                print(f'REMOVING THESE PACKAGES FROM CONSOLIDATED BOX VIA CUSTOMER ORDER: {package.packages}')
                package.remove_packages(remove_all=True)
            # fixme once package id assignment is changed
            print('-----package removed via customerorder object')
            package.package_id = -1
            self.shipment.assign_package_IDs()

    def package_by_id(self, package):
        """
        Checks if a given package id belongs to an existing package.

        Parameters:
        ----------
        package: str or Package
            Can be a package ID or Package object.

        Returns
        ----------
        Package or None
            Returns None if no package in the customer order
            matches the given package ID/object
        """
        if not isinstance(package, Package):
            package_id = package
            for pk in self.packages:
                if pk.package_id == package_id:
                    return pk
        else:
            return package
        return None
        
    def get_delivery_method(self):
        return self.delivery_dict[self.delivery_option]
    
    def get_dict(self):
        return {
                **(self.customer.get_dict()),
            "Package Description": self.shipping_description,
            "Number of Boxes": len(self.packages),
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
        self._package_array = []
        self._id = -1
        self._shipment_order = customer_order   # not part of orders array
        customer_order.shipment = self

    # region properties
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, new_value):
        self._id = new_value
        return self._id
    
    # array of INDIVIDUAL PACKED BOXES
    # in shipment
    # consolidated box = 1 array entry
    @property
    def packages(self):
        # go through all customer orders
        # exclude packages that are consolidated
        packages = []
        for order in self.orders:
            for pk in order.packages:
                if not pk.consolidated:
                    packages.append(pk)
        
        # go through shipment_order too
        # this stores all consolidated boxes
        for pk in self.shipment_order.packages:
            if not pk.consolidated:
                packages.append(pk)
        #return self._package_array
        return packages
    
    @property
    def consolidated_num(self):
        num = 0
        for pk in self.packages:
            if isinstance(pk, ConsolidatedPackage):
                num += 1
        return num
    @property
    def package_id_list(self):
        ids = []
        for pk in self.packages:
            ids.append(pk.package_id)
        return ids

    @property
    def orders(self):
        return self._orders_array
    @property
    def customers(self):
        return [order.customer for order in self.orders]
    
    @property
    def shipment_order(self):
        return self._shipment_order

    # array of TOTAL BOXES SENT BY CUSTOMERS
    # != packages
    # package array is not dependent on customers
    # eg. consolidated package
    def get_customer_packages(self):
        package_list = []
        for c in self.customers:
            package_list.extend(c.packages)
        return package_list
    
    @property
    def battery_num(self):
        battery_num = 0
        for p in self.packages:
            if p.has_batteries:
                battery_num += 1
        return battery_num

    @property
    def gross_weight(self):
        gweight = 0
        for p in self.packages:
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
        pass
    
        # called on the class itself (not instance)
    @property
    def cost(self, kg, has_batteries):
        if has_batteries:
            return kg * Shipment.shipment_cost["has battery"]
        else:
            return kg * Shipment.shipment_cost["no battery"]
    @property
    def package_num(self):
        return len(self.packages)
    
    @property
    def battery_num(self):
        return sum(pk.has_batteries for pk in self.packages)
    @property
    def gross_weight(self):
        return sum(pk.weight for pk in self.packages)
    
    @property
    def volumetric_weight(self):
        return round(sum(pk.cbm for pk in self.packages), 2)
    
    def get_order(self, order_id):
        """
        Fetches CustomerOrder object matching order_id.
        """
        for o in self.orders:
            if o.id == order_id:
                return o
        raise ValueError(f"Order ID {order_id} not found.")

    # packages must belong to a customer
    # THERE SHOULD BE NO DUPLICATE IDS
    def assign_package_IDs(self):
        """
        Reassigns package IDs after change to package list.
        Order of packages in shipment is based on orders.
        accounts for consolidated package IDs
        """
        label = 0
        c_label = 0
        for pk in self.packages:
            if not isinstance(pk, ConsolidatedPackage):
                label += 1
                pk.package_id = label
            else:
                c_label += 1
                pk.package_id = pk.generate_id(c_label)
    
    def package(self, package_id):
        cons_list = []
        for pk in self.packages:
            if str(pk.package_id) == str(package_id):
                return pk
            elif isinstance(pk, ConsolidatedPackage):
                cons_list.append(pk)

        # check if package is consolidated
        for cons_pk in cons_list:
            for pk in cons_pk.packages:
                if str(pk.package_id) == str(package_id):
                    return pk

        return None
    
    def add_to_shipment(self, item):
        """
        Adds an order or consolidated package to the shipment. If adding a package, ID is assigned automatically.

        Parameters:
        ----------
        item: CustomerOrder or Package

        Returns
        ----------
        item
        """
        if isinstance(item, Package):
            # MUST BE FOR CONSOLIDATING PACKAGES
            # adding a non-consolidated package must be done from CustomerOrder
            package = item
            if not package.consolidated:
                raise ValueError("Cannot add package directly via Shipment unless consolidated.")
            else:
                # add_package assigns an ID
                # does not alter customer order
                # just adds it back to shipment
                
                #self.packages.append(package)
                # change this if a new package ID system
                #package.package_id = len(self.packages)
                self.shipment.assign_package_IDs()
                return package
            
        elif isinstance(item, CustomerOrder):
            customer_order = item
            self.orders.append(customer_order)
            self.shipment.assign_package_IDs()
            for pk in customer_order.packages:
                #self.packages.append(pk)
                #pk.package_id = len(self.packages)
                pass
                
            return customer_order

    def remove_from_shipment(self, item):
        if isinstance(item, Package):
            # MUST BE FOR CONSOLIDATING PACKAGES
            # wholly removing a package must be done from CustomerOrder
            package = item
            if not package.consolidated:
                raise ValueError("Cannot remove package directly via Shipment unless consolidated.")
            else:
                #self.packages.remove(package)
                package.package_id = -1
                return package
            
        elif isinstance(item, CustomerOrder):
            # removes all their packages permanently from the shipment
            # TODO: check if removed packages are part of consolidated boxes
            # remove packages and reassign IDs
            customer_order = item
            self.orders.remove(customer_order)
            customer_order.id = -1

            i = 1
            for o in self.orders:
                o.id = i
                i += 1
            for pk in customer_order.packages:
                #self.packages.remove(pk)    # removes from shipment
                pk.consolidated = (False, None)  # setter removes pk from consolidated list
                pk.package_id = -1
            return customer_order

    def add_shipping_order(self, customer_order):
        self.orders.append(customer_order)
        customer_order.id = len(self.orders)
        self.assign_package_IDs()
        for pk in customer_order.packages:
            #self.packages.append(pk)
            #pk.package_id = len(self.packages)
            pass

    # can be slow depending on # of packages
    # can optimize
    # takes a list of package IDs
    def consolidate(self, dimensions: iter, packages, description: str="default"):

        #if len(packages) < 2:
            #print('Need at least 2 packages to consolidate')

        print(f'FROM SHIPMENT CONSOLIDATE(): PACKAGE LIST = {packages}')
        cons = ConsolidatedPackage(
            dimensions=dimensions,
            dim_units='INCH',
            customer_order=self.shipment_order,
            description=description,
            package_list=packages
        )
        self.assign_package_IDs()

    def deconsolidate(self, package):
        if not isinstance(package, ConsolidatedPackage):
            raise ValueError("Cannot deconsolidate non-consolidated package.")
        
        package.remove_packages(remove_all=True)

    # for converting customer data to excel sheet
    # returns a list of dict representations of customers
    def get_customer_data(self):
        return [c.get_dict() for c in self.orders.customer]
    
    def get_package_data(self):
        return [p.get_dict() for p in self.packages]
    
    def generate_excel_data(self):
        """
        Defines what data is sent to exported excel sheet.
        Returns order information viewable by excel sheet.
        excelthings.py is for formatting the excel sheet.
        See customer_info_ideal_template for how excel sheet is presented.

        Parameters:
        ----------
        None

        Returns
        ----------
        Dict containing shipment data viewable by excel sheet.
        """
        data = {}
        box_num = 0
        print(f'ORDERS PASSED TO EXCEL EXPORT (via Shipment): {len(self.orders)}')

        for order in self.orders:
            print(order.customer.name)
            order_info = {}
            cs_info = {}
            cs_info["Name"] = order.customer.name
            cs_info["Email"] = order.customer.email
            cs_info["Cell Number"] = order.customer.phone
            cs_info["Delivery Option"] = order.delivery_dict[order.delivery_option]
            cs_info["Wants Insurance"] = order.insurance
            cs_info["Total Cost"] = "=SUM()"
            cs_info["Notes"] = order.notes
            order_info["Customer Info"] = cs_info

            # ASSUMES DIMENSIONS ARE IN INCHES
            # bold whichever dimension applies
            pk_info = {}
            for pk in order.packages:
                box_num += 1
                pk_details = {}
                pk_details["Units"] = pk.dim_units
                pk_details["Length"], pk_details["Width"], pk_details["Height"] = pk.dimensions
                pk_details["Gross Weight (kg)"] = pk.weight
                pk_details["CBM"] = "cbm" # calculate this from within spreadsheet
                pk_details["Has Batteries"] = pk.has_batteries

                # TODO: replace with box id instead
                pk_info[f"Box {box_num}"] = pk_details
            
            order_info["Packages"] = pk_info
            
            # note: will not work if 'Order' is not a hashable object
            data[order] = order_info
        
        return data # this is sent to populate_shipment in excelthings
    
    def export_excel(self, filename):
        data = self.generate_excel_data()
        file_path = xl.write_to_sheet(filename, data)
        return file_path

class Session:
    # stores all shipments
    # export this object as a file from SaveData
    def __init__(self, shipments=[], orders=[], customers=[]):
        self.shipments = shipments     # orders are stored in shipments
        self.orders = orders
        self.active_shipment = None
        self.customers = customers


# save file pickles Session object
class SaveData:
    def __new__(cls):
        # keep arguments consistent with __init__
        if not hasattr(cls, 'instance'):
            cls.instance = super(SaveData, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        root_folder = os.getcwd()  # Get the current working directory (root folder)
        save_folder = os.path.join(root_folder, "backend", "save_files")
        self.temp_folder = os.path.join(root_folder, "backend", "temp_files")
        self.save_folder = save_folder
        self.filename = self.get_session_name()
        self.old_filename = 'old_'+self.filename
        self.file_path = os.path.join(save_folder, self.filename)
        
        self.old_file_path = os.path.join(save_folder, self.old_filename)

        # erase temp files
        file_list = os.listdir(self.temp_folder)
        for f in file_list:
            file_path = os.path.join(self.temp_folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")


    def get_session_name(self):
        current_month = datetime.datetime.now().strftime('%B')
        current_day = datetime.datetime.now().day
        file_name = f"{current_month}{current_day}Session.jf"
        print(file_name)
        return file_name
    
    def load_data(self, debugging, restart_data=False):
        if restart_data or debugging:
            return self.initialize_default_data(debugging)
        
        try:
            with open(self.file_path, "rb") as file:
                session = pickle.load(file)
            return session
        except FileNotFoundError:
                print(f"The file path '{self.file_path}' does not exist. Initializing new data.")
                return self.initialize_default_data(debugging)

    def save_data(self, session, filename=""):
        """
        Saves Session as a pickle file in self.save_folder.
        Default filename is given by self.get_session_name().

        Parameters:
        ----------
        session: Session
            Session data to save.
        filename: str
            Overrides default filename.

        Returns
        ----------
        None
        """
        print("Saving session data in file.")
        """
        if os.path.exists(self.old_file_path):
            os.remove(self.old_file_path)
        if os.path.exists(self.file_path):
            os.rename(self.filename, self.old_filename)
            """
        if not isinstance(session, Session):
            raise AssertionError("save_data must take a Session object.")
        
        if filename == "":
            filename = self.get_session_name()
        filepath = os.path.join(self.save_folder, filename)
        with open(filepath, "wb") as file:
            pickle.dump(session, file)
    
    def export_data(self, session, filename="", export_current_data=False):
        """
        Returns a pickle file containing session data.

        Parameters:
        ----------
        filename: str
            Search save_files for this filename. If it doesn't exist,
            create a new one.
        session: Session
            Session data to export.

        Returns
        ----------
        filename: str
        """
        if export_current_data:
            print('getting default session name')
            filename = self.get_session_name()
            # overwrite existing data if present
            self.save_data(session, filename=filename)
        elif filename == "":
            print('getting default session name')
            filename = self.get_session_name()
            filepath = os.path.join(self.save_folder, filename)
            if os.path.exists(filepath):
                print(f"The file path '{filepath}' already exists. Exporting data from this filepath.")
        else:
            raise AssertionError("Please specify a filename to export data from.")
        
        filepath = os.path.join(self.save_folder, filename)

        with open(filepath, "wb") as file:
            pickle.dump(session, file)
        print(f'return data from {filepath}')
        return filepath

    def erase_data(self):
        file_list = os.listdir(self.save_folder)
        for f in file_list:
            file_path = os.path.join(self.save_folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")
    
    # replaces current save file with old one
    # in case of corruption
    def restore_data(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        try:
            shutil.copy2(self.old_file_path, self.file_path)
        except FileNotFoundError:
            print("Cannot find old data to restore.")
    
    # overwrites current data and replaces it with this default
    def initialize_default_data(self, debugging):
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
        shipment = Shipment(company_order)
        shipments = [shipment]
        customers = [company_customer]

        if debugging:
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
                    has_batteries=True,
                    fragile=True)

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

            customers.extend([customer1, customer2])
            customer_order1.id = 1
            customer_order2.id = 2

        session = Session(shipments=shipments, customers=customers)
        session.active_shipment = shipments[0]  # change once active shipment can be selected from homepage
        print('--------DONE INITIALIZING DATA')
        #print(f'number of orders: {len(session.active_shipment.orders)}')
        return session
        
