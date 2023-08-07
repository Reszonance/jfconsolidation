"""
For autofilling. Assumes IDs of html elements remain the same.



"""

def assign_customer_info(customer, data):
    """
    Updates customer information from a form request (data).
    Assumes name attributes of the input fields.

    Parameters:
    ----------
    customer: Customer
    data: form data sent as dict

    Returns
    ----------
    customer
    """
    customer.name = data['shipper_name']
    customer.email = data['shipper_email']
    customer.phone = data['shipper_phone']
    customer.address = data['shipper_address']
    customer.city = data['shipper_city']
    customer.state = data['shipper_state']
    customer.zip_code = data['shipper_zip']
    return customer

def assign_consignee_info(consignee, data):
    """
    Updates consignee information from a form request (data).
    Assumes name attributes of the input fields.

    Parameters:
    ----------
    consignee: Consignee
    data: form data sent as dict

    Returns
    ----------
    consignee
    """
    consignee.name = data['consignee_name']
    consignee.email = data['consignee_email']
    consignee.phone = data['consignee_phone']
    consignee.address = data['consignee_address']
    consignee.city = data['consignee_city']
    consignee.state = data['consignee_state']
    consignee.zip_code = data['consignee_zip']
    return consignee

def update_order_details(order, data):
    """
    Updates order details from a form request (data).
    Assumes name attributes of the input fields.

    Parameters:
    ----------
    order: CustomerOrder
    data: form data sent as dict

    Returns
    ----------
    order
    """
    if data.get('delivery-method') == 'office-office' or data.get('delivery-method') == 'office-door':
        office_dropoff = True
    else:
        office_dropoff = False
        order.pickup_address = data.get('pickup-address')
    # delivery address is consignee address by default
    office_pickup = data.get('delivery-method') == 'door-office' or data.get('delivery-method') == 'office-office'
    
    order.office_dropoff = office_dropoff
    order.office_pickup = office_pickup
    order.insurance = data.get('insurance') == 'on'
    order.notes = data.get('order-notes')
    return order

def assign_package_info(package, data):
    """
    Updates package information from a form request (data).
    Assumes name attributes of the input fields.

    Parameters:
    ----------
    package: Package
    data: form data sent as dict

    Returns
    ----------
    package
    """
    package.has_batteries = 'lithium_batteries' in data
    package.fragile = 'is_fragile' in data
    package.set_dimensions(
        length=float(data['length']),
        width=float(data['width']),
        height=float(data['height'])
    )
    package.dim_units = data['units']
    package.weight = float(data['weight'])
    package.description = data['package_description']
    return package


def get_autofill_dict(customer=None, consignee=None, order=None, debugging_data=False, no_data=False):
    """
    Returns data (dict) for the HTML template to use.
    order cannot be None if debugging_data and no_data are false.
    debugging_data and no_data autofill the data with preset
    values (testing and blank values respectively).

    Parameters:
    ----------
    package: Package
    data: form data sent as dict

    Returns
    ----------
    package
    """
    if debugging_data:
      autofill_dict = {
        'shipper_name': 'John Doe',
        'shipper_address': '123 street',
        'shipper_city': 'Johns city',
        'shipper_state': 'Johns state',
        'shipper_zip': 'zip code',
        'shipper_phone': '2983748932',
        'shipper_email': 'john@gmail.com',
        'consignee_name': 'somebody',
        'consignee_address': 'address',
        'consignee_city': 'sombody city',
        'consignee_state': 'somebody state',
        'consignee_zip': 'somebody zip',
        'consignee_phone': '4873983',
        'consignee_email': '',
        'office_dropoff': False,
        'office_pickup': False,
        'insurance': True,
        'box_num': 2,
        'boxes': {
            '1': {
                'length': 2,
                'width': 10,
                'height': 3,
                'units': 'INCH',
                'weight': 234,
                'description': 'contains items',
                'batteries': True,
                'fragile': False,
            },
            '2': {
                'length': 4,
                'width': 10,
                'height': 12,
                'units': 'INCH',
                'weight': 14.5,
                'description': 'contains items',
                'batteries': True,
                'fragile': True,
            }
        }
    }
      return autofill_dict
    elif no_data:
      blank_dict = {
          'shipper_name': '',
          'shipper_address': '',
          'shipper_city': '',
          'shipper_state': '',
          'shipper_zip': '',
          'shipper_phone': '',
          'shipper_email': '',
          'consignee_name': '',
          'consignee_address': '',
          'consignee_city': '',
          'consignee_state': '',
          'consignee_zip': '',
          'consignee_phone': '',
          'consignee_email': '',
          'office_dropoff': "",
          'office_pickup': "",
          'insurance': "",
          'box_num': "",
          'boxes': {
              'length': "",
              'width': "",
              'height': "",
              'units': '',
              'weight': "",
              'description': '',
              'batteries': "",    # make this required in the html template
              'fragile': "",
          }
      }
      return blank_dict
    
    if order is None:
       raise AssertionError("Order cannot be None for autofill data.")
    data = {}
    data_list = []

    if customer is not None:
      customer_dict = {
          'shipper_name': customer.name,
          'shipper_address': customer.address,
          'shipper_city': customer.city,
          'shipper_state': customer.state,
          'shipper_zip': customer.zip_code,
          'shipper_phone': customer.phone,
          'shipper_email': customer.email,
      }
      data_list.append(customer_dict)

    if consignee is not None:
      consignee_dict = {
          'consignee_name': consignee.name,
          'consignee_address': consignee.address,
          'consignee_city': consignee.city,
          'consignee_state': consignee.state,
          'consignee_zip': consignee.zip_code,
          'consignee_phone': consignee.phone,
          'consignee_email': consignee.email,
      }
      data_list.append(consignee_dict)

    order_dict = {
        'office_dropoff': order.delivery_option[0],
        'office_pickup': order.delivery_option[1],
        'insurance': order.insurance,
        'box_num': len(order.packages),
        'boxes': {
            'length': "",
            'width': "",
            'height': "",
            'units': "",
            'weight': "",
            'description': "",
            'batteries': "",
            'fragile': "",
        }
        #'boxes': {}
    }
    data_list.append(order_dict)
    """
    # currently no option to autofill package information
    for pk in order.packages:
        pk_dict = {
            'length': pk.dimensions[0],
            'width': pk.dimensions[1],
            'height': pk.dimensions[2],
            'units': pk.dim_units,
            'weight': pk.weight,
            'description': pk.description,
            'batteries': pk.has_batteries,
            'fragile': pk.fragile
        }
        order_dict["boxes"] = pk_dict
    """
    for d in data_list:
       data.update(d)
    return data