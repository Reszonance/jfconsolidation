# stores standard routes for website
# ie. where users can go to 
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Note
from . import db, form_autofill
import json, os

from backend.shipping_objects import *
saver = SaveData(filename="pickle_data.json")
session = saver.load_data(restart_data=True)
shipment = session.active_shipment

print('---------RESTARTING VIEWS')
# blueprint defines a bunch of URLs
# naming it 'views' is optional but simplifies things
views = Blueprint('views', __name__)

# define route for homepage
# home() will run whenever user goes to homepage
# (ie. root directory '/')
# view orders from here
@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        pass
    # applies html template to homepage
    # passes user as a variable to be used in template
    return render_template("home.html", shipment=shipment, package_num=shipment.package_num)

@views.route('/upload', methods=['GET', 'POST'])
def upload_data():
    global session
    global shipment
    if request.method == 'POST':
        # Check if a file was submitted
        if 'file' not in request.files:
            print('NO FILE PART FOUND')
            return "No file part found", 400
        
        file = request.files['file']

        if file.filename == '':
            print('NO SELECTED FILE')
            return "No selected file", 400
        
        #if file and file.filename:
        try:
            # Unpickle the file and check if it is a valid Shipment object
            session = pickle.load(file)
            shipment = session.active_shipment

            flash('Session data uploaded', category='success')
            return redirect(url_for('views.home'))

        except pickle.UnpicklingError:
            return "Error unpickling the file. File upload failed."

        return "No file selected. File upload failed."
    elif request.method == 'GET':
        return render_template("upload.html")

@views.route('/export-data', methods=['GET'])
def export_data():
    current_date = datetime.now()
    filename = 'session' + current_date.strftime("%d%m%Y") + '.jf'
    #file_path = os.path.join(os.path.dirname(__file__), filename)
    current_directory = os.path.abspath(os.path.dirname(__file__))
    parent_directory = os.path.abspath(os.path.join(current_directory, ".."))
    file_path = os.path.join(parent_directory, filename)
    saver.export_data(session, filename)
    return send_file(file_path, as_attachment=True)

@views.route('/delete-package', methods=['POST'])
def delete_package():
    # request is sent as data parameter of request object (not form)
    # request.data is json string sent from index.js
    pk_object = json.loads(request.data)    # js object defined in index.js
    print(f'----------PK OBJECT FROM DELETE: {pk_object}')
    pk_id = pk_object['pk_id']
    delete_type = pk_object['delete_type']
    
    if delete_type == 'from_box':
        for cons_pk in shipment.packages:
            if isinstance(cons_pk, ConsolidatedPackage):
                for pkkk in cons_pk.packages:
                    if str(pkkk.package_id) == str(pk_id):
                        pk = pkkk
                        cons_pk.remove_packages(False, False, pk)
                        break

    else:
        print(f'REMOVE PERMANENTLY FROM SHIPMENT: {pk_id}')
        pk = shipment.package(pk_id)    # retrieves package based on id
        pk.customer_order.remove_package(pk)
    saver.save_data(shipment)

    return jsonify({})  # jsonify empty python dictionary

@views.route('/consolidate-packages', methods=['POST'])
def consolidate():
    # request is sent as data parameter of request object (not form)
    # request.data is json string sent from index.js
    pk_ids = json.loads(request.data)    # js object defined in index.js
    shipment.consolidate([0, 0, 0], pk_ids)
    #saver.save_data(shipment)
    return jsonify({})

# VIEW/EDIT PACKAGE INFO HERE
# consignee/consignee info: name, email, phone, address
# additional info: has batteries, wants insurance
@views.route('/pkg/<string:pk_id>', methods=['GET', 'POST'])
def pk_details(pk_id):
    # pk_id is passed as a string
    package = shipment.package(pk_id)
    if request.method == 'POST':
        form_data = request.form
            # ASSUMES THAT SHIPPER == CUSTOMER
        if form_data['save_btn'] == 'shipper-info':
            form_autofill.assign_customer_info(package.customer, form_data)
        elif form_data['save_btn'] == 'consignee-info':
            form_autofill.assign_consignee_info(package.consignee, form_data)
        elif form_data['save_btn'] == 'additional-info':
            form_autofill.assign_package_info(package, form_data)
            saver.save_data(shipment)
            return redirect(url_for('views.home'))
        else:
            raise ValueError("Do not recognize save button value, check pk_details.html")

    cons_packages = []
    if isinstance(package, ConsolidatedPackage):
        for pk in package.packages:
            cons_packages.append(pk)

    return render_template('pk_details.html', pk=package, cons_packages=cons_packages)

@views.route('/view-order', methods=['GET', 'POST'])
def view_order():
    #print(f'order_id: {request.args["order_id"]}')
    order_id = request.args['order_id']
    order = None
    for o in shipment.orders:
        if o.id == order_id:
            order = o
            break
    else:
        raise ValueError(f"Order ID {order_id} not found.")
    
    if request.method == 'POST':
        form_data = request.form
        print(form_data)
        if form_data['save_btn'] == 'order-info':
            form_autofill.assign_customer_info(order.customer, form_data)
            form_autofill.update_order_details(order, form_data)
        elif form_data['save_btn'] == 'delete-order':
            print('deleting order')
            shipment.remove_from_shipment(order)
            return render_template("home.html", shipment=shipment, package_num=shipment.package_num)
        
    data = form_autofill.get_autofill_dict(order=order)
    return render_template('view_order.html', order=order, data=data)

@views.route('/add-order', methods=['GET', 'POST'])
def add_order():
    global shipment
    if request.method == 'POST':
        form_data = request.form
        action = form_data.get('action')

        customer = None
        package = None
        # NOTE: 
        # default unit for weight is kg
        # delivery address == consignee address
        # fragile option doesn't do anything; need to add to shipping_objects
        if action == 'add':
            # assumes shipper = customer
            customer = Customer(
                name=form_data['shipper-name'], 
                address=form_data['shipper-address'], 
                city=form_data['shipper-city'], 
                state=form_data['shipper-state'], 
                zip_code=form_data['shipper-zip'], 
                phone=form_data['shipper-phone'], 
                email=form_data['shipper-email'])
            shipper = Shipper(
                name=form_data['shipper-name'], 
                address=form_data['shipper-address'], 
                city=form_data['shipper-city'], 
                state=form_data['shipper-state'], 
                zip_code=form_data['shipper-zip'], 
                phone=form_data['shipper-phone'], 
                email=form_data['shipper-email'])
            consignee = Consignee(
                name=form_data['consignee-name'], 
                address=form_data['consignee-address'], 
                city=form_data['consignee-city'], 
                state=form_data['consignee-state'], 
                zip_code=form_data['consignee-zip'], # returns blank string if nothing there
                phone=form_data['consignee-phone'], 
                email=form_data['consignee-email'])
            
            pickup_address = None
            if form_data.get('office-drop-off') == 'drop-off':
                office_dropoff = True
            else:
                office_dropoff = False
                pickup_address = form_data.get('pickup-address')
            # delivery address is consignee address by default
            office_pickup = form_data.get('office-pickup') == 'pick-up'
            insurance = form_data.get('insurance') == 'on' 
            order = CustomerOrder(customer, "", office_dropoff, office_pickup, insurance)
            order.pickup_address = pickup_address
            order.assign_shipment(shipment)

            # region BOXES
            box_num = form_data.get('box-count')
            if box_num is None or int(box_num) == 0:
                error_message = "Please enter a valid number of boxes (greater than 0)."
                print("-------------------Please enter a valid number of boxes (greater than 0).")
                # FIXME error message does not work
                # do error checking from within the template instead of here
                # caused an error where site was redirecting to add order page upon submit
                # without knowing why
                return render_template('add_order.html', error=error_message)
            
            box_num = int(box_num)
            for i in range(1, box_num+1):
                dim = (float(form_data.get(f'length-{i}')),
                       float(form_data.get(f'width-{i}')),
                       float(form_data.get(f'height-{i}')))
                units = form_data.get(f'units-{i}')
                weight = float(form_data[f'weight-{i}'])
                desc = form_data[f'box-cargo-description-{i}']
                batteries = form_data.get(f'box-lithium-batteries-{i}') == 'on' 
                fragile = form_data.get(f'box-fragile-{i}') == 'on'
                pk = Package(dim, units, weight, order, shipper, consignee, desc, batteries)
                print(f"----------UNITS {units}")
            # endregion
            """
            {% if not data %}
                {% set data = {'boxes':{}} %}
            {% endif %}
            """
            print('-----------------SHIPMENT')
            print(shipment.packages)
            print(order)
            flash('Order added', category='success')
            autofill_dict = {'boxes':{}}
            
            saver.save_data(shipment)
            #return render_template('add_order.html', data=autofill_dict)
            return redirect(url_for('views.home'))
        elif action == 'cancel':
            return redirect(url_for('views.home'))

    data = form_autofill.get_autofill_dict(debugging_data=True)
    
    return render_template('add_order.html', data=data)

@views.route("/ajaxlivesearch", methods=['POST', 'GET'])
def ajaxlivesearch():
    if request.method == 'POST':
        search_word = request.form['query']
        print(search_word)
    return jsonify('success')

@views.route('/download-excel', methods=['GET'])
def download_excel():
    filename = 'exported_data.xlsx'
    #file_path = os.path.join(os.path.dirname(__file__), filename)
    shipment.export_excel(filename)
    return send_file(filename, as_attachment=True)


#TODO:
# find a way to view customer orders
# do customer database system