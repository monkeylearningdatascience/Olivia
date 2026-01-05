from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Receiving, ReceivingItem, Supplier, Category, Location, MaterialRequisition, MaterialRequisitionItem, Product
from utils.excel_exporter import export_to_excel
import json
from datetime import datetime


@require_http_methods(["GET"])
def api_receiving_list(request):
    """Get all receiving records with pagination"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 100))  # Default 100 records per page
        
        # Get all receivings ordered by date
        receivings = Receiving.objects.all().select_related('supplier').order_by('-date')
        
        # Get total count
        total_count = receivings.count()
        
        # Calculate pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Get paginated receivings
        paginated_receivings = receivings[start_index:end_index]
        
        data = []
        
        for receiving in paginated_receivings:
            # Get supplier name - handle both FK and text field
            supplier_name = ''
            if hasattr(receiving, 'supplier') and receiving.supplier:
                if isinstance(receiving.supplier, Supplier):
                    supplier_name = receiving.supplier.name
                else:
                    supplier_name = str(receiving.supplier)
            
            receiving_data = {
                'id': receiving.id,
                'date': receiving.date.strftime('%Y-%m-%d') if receiving.date else None,
                'pr_number': receiving.pr_number,
                'po_number': receiving.po_number,
                'po_date': receiving.po_date.strftime('%Y-%m-%d') if receiving.po_date else None,
                'grn_number': receiving.grn_number,
                'invoice_number': receiving.invoice_number,
                'supplier_name': supplier_name,
                'purchase_type': receiving.purchase_type,
                'department': receiving.department,
                'status': receiving.status,
                'remarks': receiving.remarks,
                'items': []
            }
            
            # Get items if they exist
            items = receiving.receivingitem_set.all()
            for item in items:
                item_data = {
                    'id': item.id,
                    'product_name': item.product.name if item.product else None,
                    'category_name': item.category.name if item.category else None,
                    'item_code': item.item_code,
                    'item_description': item.item_description,
                    'model_number': item.model_number,
                    'serial_number': item.serial_number,
                    'country_of_origin': item.country_of_origin,
                    'uom': item.uom,
                    'location': item.location.name if item.location else None,
                    'unit': item.product.unit.abbreviation if item.product and item.product.unit else None,
                    'quantity': float(item.quantity) if item.quantity else 0,
                    'unit_price': float(item.unit_price) if item.unit_price else 0,
                    'subtotal': float(item.subtotal) if hasattr(item, 'subtotal') else 0,
                    'vat_percentage': float(item.vat_percentage) if item.vat_percentage else 0,
                    'vat_amount': float(item.vat_amount) if hasattr(item, 'vat_amount') else 0,
                    'production_date': item.production_date.strftime('%Y-%m-%d') if item.production_date else None,
                    'expiry_date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else None,
                    'product_life': item.product_life if hasattr(item, 'product_life') else None,
                    'product_status': 'Active' if item.expiry_date and item.expiry_date > datetime.now().date() else 'Expired' if item.expiry_date else 'N/A'
                }
                receiving_data['items'].append(item_data)
            
            data.append(receiving_data)
        
        # Return paginated response
        response = {
            'data': data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
        
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_receiving_create(request):
    """Create a new receiving record with multiple items"""
    try:
        data = json.loads(request.body)
        
        # Get or create supplier
        supplier_value = data.get('supplier')
        supplier_obj = None
        
        if supplier_value:
            # Try to get existing supplier by name or create new
            try:
                supplier_obj = Supplier.objects.filter(name__iexact=supplier_value).first()
                if not supplier_obj:
                    # Create new supplier with basic info
                    supplier_obj = Supplier.objects.create(
                        name=supplier_value,
                        contact_person='N/A',
                        email='',
                        phone='',
                        address=''
                    )
            except Exception as e:
                print(f"Supplier error: {e}")
                pass
        
        # Get items data
        items_data = data.get('items', [])
        
        if not items_data or len(items_data) == 0:
            return JsonResponse({'error': 'At least one item is required'}, status=400)
        
        from .models import Category, Location, Product
        from decimal import Decimal
        
        # Get or create default location
        location_obj, _ = Location.objects.get_or_create(
            name='Default Warehouse',
            defaults={'code': 'DEF', 'description': 'Default warehouse location'}
        )
        
        # Create multiple receiving records (one per item) with same header info
        created_count = 0
        for item_data in items_data:
            # Create receiving record for each item
            receiving = Receiving.objects.create(
                date=data.get('date'),
                pr_number=data.get('pr_number', ''),
                po_number=data.get('po_number', ''),
                po_date=data.get('po_date') if data.get('po_date') else None,
                grn_number=data.get('grn_number'),
                invoice_number=data.get('invoice_number', ''),
                supplier=supplier_obj,
                purchase_type=data.get('purchase_type', 'LOCAL'),
                department=data.get('department', ''),
                status=data.get('status', 'PENDING'),
                remarks=data.get('remarks', ''),
                created_by=request.user if request.user.is_authenticated else None
            )
            
            # Get or create category
            category_obj = None
            if item_data.get('category'):
                category_obj, _ = Category.objects.get_or_create(name=item_data.get('category'))
            
            # Get or create product if needed
            product_obj = None
            if item_data.get('item_description'):
                product_obj = Product.objects.filter(name=item_data.get('item_description')).first()
            
            # Create receiving item
            ReceivingItem.objects.create(
                receiving=receiving,
                product=product_obj,
                category=category_obj,
                location=location_obj,
                item_code=item_data.get('item_code', ''),
                item_description=item_data.get('item_description', ''),
                model_number=item_data.get('model_number', ''),
                serial_number=item_data.get('serial_number', ''),
                country_of_origin=item_data.get('country_of_origin', ''),
                uom=item_data.get('uom', ''),
                quantity=Decimal(str(item_data.get('quantity', 0))),
                unit_price=Decimal(str(item_data.get('unit_price', 0))),
                vat_percentage=Decimal(str(item_data.get('vat_percentage', 0))),
                production_date=item_data.get('production_date') if item_data.get('production_date') else None,
                expiry_date=item_data.get('expiry_date') if item_data.get('expiry_date') else None
            )
            created_count += 1
        
        return JsonResponse({
            'message': f'{created_count} item(s) saved successfully under GRN {data.get("grn_number")}'
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_receiving_detail(request, pk):
    """Get a single receiving record by ID"""
    try:
        receiving = get_object_or_404(Receiving, pk=pk)
        
        supplier_name = ''
        if receiving.supplier:
            if isinstance(receiving.supplier, Supplier):
                supplier_name = receiving.supplier.name
            else:
                supplier_name = str(receiving.supplier)
        
        data = {
            'id': receiving.id,
            'date': receiving.date.strftime('%Y-%m-%d') if receiving.date else None,
            'pr_number': receiving.pr_number,
            'po_number': receiving.po_number,
            'po_date': receiving.po_date.strftime('%Y-%m-%d') if receiving.po_date else None,
            'grn_number': receiving.grn_number,
            'invoice_number': receiving.invoice_number,
            'supplier': supplier_name,
            'purchase_type': receiving.purchase_type,
            'department': receiving.department,
            'status': receiving.status,
            'remarks': receiving.remarks,
            'item': None
        }
        
        # Get first item if exists
        item = receiving.receivingitem_set.first()
        if item:
            data['item'] = {
                'category': item.category.name if item.category else '',
                'item_code': item.item_code,
                'item_description': item.item_description,
                'model_number': item.model_number,
                'serial_number': item.serial_number,
                'country_of_origin': item.country_of_origin,
                'uom': item.uom,
                'quantity': float(item.quantity) if item.quantity else 0,
                'unit_price': float(item.unit_price) if item.unit_price else 0,
                'vat_percentage': float(item.vat_percentage) if item.vat_percentage else 0,
                'production_date': item.production_date.strftime('%Y-%m-%d') if item.production_date else None,
                'expiry_date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else None
            }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
def api_receiving_update(request, pk):
    """Update an existing receiving record"""
    try:
        receiving = get_object_or_404(Receiving, pk=pk)
        data = json.loads(request.body)
        
        # Update supplier
        supplier_value = data.get('supplier')
        if supplier_value:
            supplier_obj = Supplier.objects.filter(name__iexact=supplier_value).first()
            if not supplier_obj:
                supplier_obj = Supplier.objects.create(
                    name=supplier_value,
                    contact_person='N/A',
                    email='',
                    phone='',
                    address=''
                )
            receiving.supplier = supplier_obj
        
        # Update fields
        receiving.date = data.get('date', receiving.date)
        receiving.pr_number = data.get('pr_number', receiving.pr_number)
        receiving.po_number = data.get('po_number', receiving.po_number)
        receiving.po_date = data.get('po_date') if data.get('po_date') else receiving.po_date
        receiving.grn_number = data.get('grn_number', receiving.grn_number)
        receiving.invoice_number = data.get('invoice_number', receiving.invoice_number)
        receiving.purchase_type = data.get('purchase_type', receiving.purchase_type)
        receiving.department = data.get('department', receiving.department)
        receiving.status = data.get('status', receiving.status)
        receiving.remarks = data.get('remarks', receiving.remarks)
        receiving.modified_by = request.user if request.user.is_authenticated else None
        
        receiving.save()
        
        # Update or create receiving item if item data is provided
        if any([data.get('item_code'), data.get('item_description'), data.get('quantity')]):
            from .models import Category, Location, Product, UnitOfMeasure
            from decimal import Decimal
            
            # Get or create category
            category_obj = None
            if data.get('category'):
                category_obj, _ = Category.objects.get_or_create(name=data.get('category'))
            
            # Get or create default location
            location_obj, _ = Location.objects.get_or_create(
                name='Default Warehouse',
                defaults={'description': 'Default warehouse location'}
            )
            
            # Get or create product if needed
            product_obj = None
            if data.get('item_description'):
                product_obj = Product.objects.filter(name=data.get('item_description')).first()
            
            # Get existing item or create new
            item = receiving.receivingitem_set.first()
            if item:
                # Update existing item
                item.category = category_obj
                item.location = location_obj
                item.product = product_obj
                item.item_code = data.get('item_code', item.item_code)
                item.item_description = data.get('item_description', item.item_description)
                item.model_number = data.get('model_number', item.model_number)
                item.serial_number = data.get('serial_number', item.serial_number)
                item.country_of_origin = data.get('country_of_origin', item.country_of_origin)
                item.uom = data.get('uom', item.uom)
                item.quantity = Decimal(str(data.get('quantity', 0)))
                item.unit_price = Decimal(str(data.get('unit_price', 0)))
                item.vat_percentage = Decimal(str(data.get('vat_percentage', 0)))
                item.production_date = data.get('production_date') if data.get('production_date') else item.production_date
                item.expiry_date = data.get('expiry_date') if data.get('expiry_date') else item.expiry_date
                item.save()
            else:
                # Create new item
                ReceivingItem.objects.create(
                    receiving=receiving,
                    product=product_obj,
                    category=category_obj,
                    location=location_obj,
                    item_code=data.get('item_code', ''),
                    item_description=data.get('item_description', ''),
                    model_number=data.get('model_number', ''),
                    serial_number=data.get('serial_number', ''),
                    country_of_origin=data.get('country_of_origin', ''),
                    uom=data.get('uom', ''),
                    quantity=Decimal(str(data.get('quantity', 0))),
                    unit_price=Decimal(str(data.get('unit_price', 0))),
                    vat_percentage=Decimal(str(data.get('vat_percentage', 0))),
                    production_date=data.get('production_date') if data.get('production_date') else None,
                    expiry_date=data.get('expiry_date') if data.get('expiry_date') else None
                )
        
        return JsonResponse({
            'id': receiving.id,
            'message': 'Receiving updated successfully'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def api_receiving_delete(request):
    """Delete one or more receiving records"""
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({'error': 'No IDs provided'}, status=400)
        
        deleted_count = Receiving.objects.filter(id__in=ids).delete()[0]
        
        return JsonResponse({
            'message': f'{deleted_count} receiving record(s) deleted successfully',
            'count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_receiving_import(request):
    """Import receiving records from Excel/CSV"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        file = request.FILES['file']
        
        # Check file extension
        if not (file.name.endswith('.xlsx') or file.name.endswith('.xls') or file.name.endswith('.csv')):
            return JsonResponse({'error': 'Invalid file format. Please upload Excel (.xlsx, .xls) or CSV file.'}, status=400)
        
        # Read the file using pandas
        import pandas as pd
        from datetime import datetime as dt
        from decimal import Decimal
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        except Exception as e:
            return JsonResponse({'error': f'Failed to read file: {str(e)}'}, status=400)
        
        # Expected columns mapping
        expected_columns = {
            'Receive Date': 'date',
            'PR No': 'pr_number',
            'PO No': 'po_number',
            'PO Date': 'po_date',
            'Reference No': 'grn_number',  # GRN Number
            'Invoice No': 'invoice_number',
            'Category': 'category',
            'Item code': 'item_code',
            'Item Description': 'item_description',
            'Model Number': 'model_number',
            'Serial Number': 'serial_number',
            'Country of origin': 'country_of_origin',
            'UOM': 'uom',
            'Quantity': 'quantity',
            'Unit Price': 'unit_price',
            'VAT': 'vat_percentage',
            'Supplier': 'supplier',
            'Purchase': 'purchase_type',
            'Dept': 'department',
            'Production Date': 'production_date',
            'Expiry Date': 'expiry_date',
        }
        
        # Validate columns
        missing_cols = []
        for col in expected_columns.keys():
            if col not in df.columns:
                missing_cols.append(col)
        
        if missing_cols:
            return JsonResponse({
                'error': f'Missing required columns: {", ".join(missing_cols)}'
            }, status=400)
        
        # Process each row
        success_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row['Receive Date']) or pd.isna(row['Reference No']):
                    continue
                
                # Parse dates
                try:
                    receive_date = pd.to_datetime(row['Receive Date']).date()
                except:
                    receive_date = dt.strptime(str(row['Receive Date']), '%Y-%m-%d').date()
                
                po_date = None
                if not pd.isna(row['PO Date']):
                    try:
                        po_date = pd.to_datetime(row['PO Date']).date()
                    except:
                        po_date = dt.strptime(str(row['PO Date']), '%Y-%m-%d').date()
                
                production_date = None
                if not pd.isna(row['Production Date']):
                    try:
                        production_date = pd.to_datetime(row['Production Date']).date()
                    except:
                        pass
                
                expiry_date = None
                if not pd.isna(row['Expiry Date']):
                    try:
                        expiry_date = pd.to_datetime(row['Expiry Date']).date()
                    except:
                        pass
                
                # Get or create supplier
                supplier_name = str(row['Supplier']).strip()
                supplier, created = Supplier.objects.get_or_create(
                    name=supplier_name,
                    defaults={
                        'contact_person': '',
                        'email': f'{supplier_name.lower().replace(" ", "")}@supplier.com',
                        'phone': '',
                        'address': ''
                    }
                )
                
                # Get or create category
                category_name = str(row['Category']).strip() if not pd.isna(row['Category']) else 'General'
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description': ''}
                )
                
                # Determine purchase type
                purchase_type = 'LOCAL'
                if not pd.isna(row['Purchase']):
                    if 'head' in str(row['Purchase']).lower() or 'hq' in str(row['Purchase']).lower():
                        purchase_type = 'HQ'
                
                # Get department
                department = ''
                if not pd.isna(row['Dept']):
                    dept_value = str(row['Dept']).strip().upper()
                    # Map to valid department choices
                    dept_map = {
                        'SOFT SERVICE': 'SOFT SERVICE',
                        'HARD SERVICE': 'HARD SERVICE',
                        'ICT': 'ICT',
                        'FLS': 'FLS',
                    }
                    department = dept_map.get(dept_value, '')
                
                # Create Receiving record
                receiving = Receiving.objects.create(
                    date=receive_date,
                    pr_number=str(row['PR No']) if not pd.isna(row['PR No']) else '',
                    po_number=str(row['PO No']) if not pd.isna(row['PO No']) else '',
                    po_date=po_date,
                    grn_number=str(row['Reference No']),
                    invoice_number=str(row['Invoice No']) if not pd.isna(row['Invoice No']) else '',
                    supplier=supplier,
                    purchase_type=purchase_type,
                    department=department,
                    status='COMPLETED',
                    created_by=request.user if request.user.is_authenticated else None
                )
                
                # Get default location
                location, created = Location.objects.get_or_create(
                    code='DEFAULT',
                    defaults={'name': 'Default Location', 'description': 'Default storage location'}
                )
                
                # Create ReceivingItem
                quantity = Decimal(str(row['Quantity'])) if not pd.isna(row['Quantity']) else Decimal('0')
                unit_price = Decimal(str(row['Unit Price'])) if not pd.isna(row['Unit Price']) else Decimal('0')
                vat_percentage = Decimal(str(row['VAT'])) if not pd.isna(row['VAT']) else Decimal('0')
                
                ReceivingItem.objects.create(
                    receiving=receiving,
                    category=category,
                    item_code=str(row['Item code']) if not pd.isna(row['Item code']) else '',
                    item_description=str(row['Item Description']) if not pd.isna(row['Item Description']) else '',
                    model_number=str(row['Model Number']) if not pd.isna(row['Model Number']) else '',
                    serial_number=str(row['Serial Number']) if not pd.isna(row['Serial Number']) else '',
                    country_of_origin=str(row['Country of origin']) if not pd.isna(row['Country of origin']) else '',
                    uom=str(row['UOM']) if not pd.isna(row['UOM']) else '',
                    location=location,
                    quantity=quantity,
                    unit_price=unit_price,
                    vat_percentage=vat_percentage,
                    production_date=production_date,
                    expiry_date=expiry_date,
                    created_by=request.user if request.user.is_authenticated else None
                )
                
                success_count += 1
                
            except Exception as e:
                errors.append(f'Row {index + 2}: {str(e)}')
                continue
        
        if errors:
            error_summary = '\n'.join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_summary += f'\n... and {len(errors) - 5} more errors'
            
            return JsonResponse({
                'message': f'Imported {success_count} record(s) with {len(errors)} error(s)',
                'count': success_count,
                'errors': error_summary
            }, status=200)
        
        return JsonResponse({
            'message': f'Successfully imported {success_count} receiving record(s)',
            'count': success_count
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': f'Import failed: {str(e)}'}, status=400)


@require_http_methods(["GET"])
def api_receiving_export(request):
    """Export receiving records to Excel"""
    try:
        # Get all receiving records with items
        from django.db.models import Prefetch
        
        receivings = Receiving.objects.all().select_related('supplier').prefetch_related(
            Prefetch('receivingitem_set', queryset=ReceivingItem.objects.select_related('category', 'product__unit', 'location'))
        ).order_by('-date')
        
        # Flatten the data: create one row per item
        flat_data = []
        for receiving in receivings:
            # Get supplier name
            supplier_name = ''
            if receiving.supplier:
                if isinstance(receiving.supplier, Supplier):
                    supplier_name = receiving.supplier.name
                else:
                    supplier_name = str(receiving.supplier)
            
            purchase_type_label = 'Local Purchase' if receiving.purchase_type == 'LOCAL' else 'Head Quarters'
            
            items = receiving.receivingitem_set.all()
            if items.exists():
                for item in items:
                    flat_data.append({
                        'receiving': receiving,
                        'item': item,
                        'supplier_name': supplier_name,
                        'purchase_type_label': purchase_type_label
                    })
            else:
                # No items, add receiving header only
                flat_data.append({
                    'receiving': receiving,
                    'item': None,
                    'supplier_name': supplier_name,
                    'purchase_type_label': purchase_type_label
                })
        
        # Define headers
        headers = [
            "Receive Date", "PR No", "PO No", "PO Date", "Reference No", 
            "Invoice No", "Category", "Item code", "Item Description", 
            "Model Number", "Serial Number", "Country of origin", "UOM", 
            "Quantity", "Unit Price", "VAT", "Total", "Supplier", 
            "Purchase", "Dept", "Production Date", "Expiry Date", 
            "Life of the Product"
        ]
        
        # Define row data function
        def row_data(data):
            receiving = data['receiving']
            item = data['item']
            supplier_name = data['supplier_name']
            purchase_type_label = data['purchase_type_label']
            
            if item:
                # Calculate totals
                subtotal = float(item.quantity * item.unit_price) if item.quantity and item.unit_price else 0
                vat_amount = subtotal * (float(item.vat_percentage) / 100) if item.vat_percentage else 0
                total = subtotal + vat_amount
                
                # Calculate product life in days
                product_life = ''
                if item.production_date:
                    from datetime import date
                    delta = date.today() - item.production_date
                    product_life = delta.days
                
                return [
                    receiving.date.strftime('%Y-%m-%d') if receiving.date else '',
                    receiving.pr_number or '',
                    receiving.po_number or '',
                    receiving.po_date.strftime('%Y-%m-%d') if receiving.po_date else '',
                    receiving.grn_number or '',
                    receiving.invoice_number or '',
                    item.category.name if item.category else '',
                    item.item_code or '',
                    item.item_description or '',
                    item.model_number or '',
                    item.serial_number or '',
                    item.country_of_origin or '',
                    item.product.unit.abbreviation if item.product and item.product.unit else '',
                    float(item.quantity) if item.quantity else '',
                    float(item.unit_price) if item.unit_price else '',
                    float(item.vat_percentage) if item.vat_percentage else 0,
                    total,
                    supplier_name,
                    purchase_type_label,
                    receiving.department or '',
                    item.production_date.strftime('%Y-%m-%d') if item.production_date else '',
                    item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else '',
                    product_life
                ]
            else:
                # No item data
                return [
                    receiving.date.strftime('%Y-%m-%d') if receiving.date else '',
                    receiving.pr_number or '',
                    receiving.po_number or '',
                    receiving.po_date.strftime('%Y-%m-%d') if receiving.po_date else '',
                    receiving.grn_number or '',
                    receiving.invoice_number or '',
                    '', '', '', '', '', '', '', '', '', '', '',
                    supplier_name,
                    purchase_type_label,
                    receiving.department or '',
                    '', '', ''
                ]
        
        return export_to_excel(flat_data, headers, row_data, file_prefix="receiving")
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =======================================================
# MATERIAL REQUISITION API ENDPOINTS
# =======================================================

@require_http_methods(["GET"])
def api_requisition_list(request):
    """Get all material requisition records"""
    try:
        requisitions = MaterialRequisition.objects.all().select_related('requested_by', 'approved_by').prefetch_related('materialrequisitionitem_set__product').order_by('-date')
        data = []
        
        for req in requisitions:
            items_count = req.materialrequisitionitem_set.count()
            
            data.append({
                'id': req.id,
                'mr_number': req.mr_number,
                'date': req.date.strftime('%Y-%m-%d') if req.date else None,
                'department': req.department,
                'requested_by': req.requested_by.get_full_name() or req.requested_by.username if req.requested_by else '',
                'status': req.status,
                'status_display': req.get_status_display(),
                'items_count': items_count,
                'remarks': req.remarks,
                'approved_by': req.approved_by.get_full_name() or req.approved_by.username if req.approved_by else '',
                'approved_date': req.approved_date.strftime('%Y-%m-%d') if req.approved_date else None,
            })
        
        return JsonResponse({'data': data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_requisition_create(request):
    """Create new material requisition with items"""
    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        
        if not items_data or len(items_data) == 0:
            return JsonResponse({'error': 'At least one item is required'}, status=400)
        
        # Create Material Requisition
        requisition = MaterialRequisition.objects.create(
            mr_number=data['mr_number'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            department=data.get('department', ''),
            requested_by=request.user if request.user.is_authenticated else None,
            status=data.get('status', 'PENDING'),
            remarks=data.get('remarks', ''),
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Create items
        for item_data in items_data:
            product = get_object_or_404(Product, id=item_data['product_id'])
            
            MaterialRequisitionItem.objects.create(
                requisition=requisition,
                product=product,
                requested_quantity=item_data['requested_quantity'],
                issued_quantity=item_data.get('issued_quantity', 0),
                remarks=item_data.get('remarks', ''),
                created_by=request.user if request.user.is_authenticated else None
            )
        
        return JsonResponse({
            'message': 'Material requisition created successfully',
            'id': requisition.id
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_requisition_detail(request, pk):
    """Get material requisition detail with items"""
    try:
        requisition = get_object_or_404(MaterialRequisition.objects.select_related('requested_by', 'approved_by'), pk=pk)
        items = requisition.materialrequisitionitem_set.select_related('product').all()
        
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_code': item.product.code,
                'product_name': item.product.name,
                'requested_quantity': str(item.requested_quantity),
                'issued_quantity': str(item.issued_quantity),
                'remarks': item.remarks
            })
        
        data = {
            'id': requisition.id,
            'mr_number': requisition.mr_number,
            'date': requisition.date.strftime('%Y-%m-%d'),
            'department': requisition.department,
            'requested_by': requisition.requested_by.get_full_name() or requisition.requested_by.username if requisition.requested_by else '',
            'requested_by_id': requisition.requested_by.id if requisition.requested_by else None,
            'status': requisition.status,
            'remarks': requisition.remarks,
            'approved_by': requisition.approved_by.get_full_name() or requisition.approved_by.username if requisition.approved_by else '',
            'approved_date': requisition.approved_date.strftime('%Y-%m-%d') if requisition.approved_date else None,
            'items': items_data
        }
        
        return JsonResponse(data, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT"])
def api_requisition_update(request, pk):
    """Update material requisition"""
    try:
        requisition = get_object_or_404(MaterialRequisition, pk=pk)
        data = json.loads(request.body)
        
        # Update requisition fields
        requisition.mr_number = data.get('mr_number', requisition.mr_number)
        requisition.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if 'date' in data else requisition.date
        requisition.department = data.get('department', requisition.department)
        requisition.status = data.get('status', requisition.status)
        requisition.remarks = data.get('remarks', requisition.remarks)
        requisition.modified_by = request.user if request.user.is_authenticated else None
        requisition.save()
        
        # Update items if provided
        if 'items' in data:
            # Delete existing items
            requisition.materialrequisitionitem_set.all().delete()
            
            # Create new items
            for item_data in data['items']:
                product = get_object_or_404(Product, id=item_data['product_id'])
                
                MaterialRequisitionItem.objects.create(
                    requisition=requisition,
                    product=product,
                    requested_quantity=item_data['requested_quantity'],
                    issued_quantity=item_data.get('issued_quantity', 0),
                    remarks=item_data.get('remarks', ''),
                    created_by=request.user if request.user.is_authenticated else None
                )
        
        return JsonResponse({'message': 'Material requisition updated successfully'}, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_requisition_delete(request):
    """Delete material requisition records"""
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({'error': 'No IDs provided'}, status=400)
        
        count = MaterialRequisition.objects.filter(id__in=ids).delete()[0]
        
        return JsonResponse({
            'message': f'Successfully deleted {count} requisition(s)',
            'count': count
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_requisition_export(request):
    """Export material requisition records to Excel"""
    try:
        requisitions = MaterialRequisition.objects.all().select_related('requested_by', 'approved_by').prefetch_related('materialrequisitionitem_set__product').order_by('-date')
        
        # Flatten the data
        flat_data = []
        for req in requisitions:
            requested_by = req.requested_by.get_full_name() or req.requested_by.username if req.requested_by else ''
            approved_by = req.approved_by.get_full_name() or req.approved_by.username if req.approved_by else ''
            status_display = req.get_status_display()
            
            items = req.materialrequisitionitem_set.all()
            if items.exists():
                for item in items:
                    flat_data.append({
                        'requisition': req,
                        'item': item,
                        'requested_by': requested_by,
                        'approved_by': approved_by,
                        'status_display': status_display
                    })
            else:
                flat_data.append({
                    'requisition': req,
                    'item': None,
                    'requested_by': requested_by,
                    'approved_by': approved_by,
                    'status_display': status_display
                })
        
        # Define headers
        headers = [
            "MR No", "Date", "Department", "Requested By", 
            "Product Code", "Product Name", "Requested Quantity", 
            "Issued Quantity", "Status", "Approved By", "Approved Date", "Remarks"
        ]
        
        # Define row data function
        def row_data(data):
            req = data['requisition']
            item = data['item']
            requested_by = data['requested_by']
            approved_by = data['approved_by']
            status_display = data['status_display']
            
            if item:
                return [
                    req.mr_number,
                    req.date.strftime('%Y-%m-%d') if req.date else '',
                    req.department,
                    requested_by,
                    item.product.code if item.product else '',
                    item.product.name if item.product else '',
                    str(item.requested_quantity),
                    str(item.issued_quantity),
                    status_display,
                    approved_by,
                    req.approved_date.strftime('%Y-%m-%d') if req.approved_date else '',
                    req.remarks or ''
                ]
            else:
                return [
                    req.mr_number,
                    req.date.strftime('%Y-%m-%d') if req.date else '',
                    req.department,
                    requested_by,
                    '', '', '', '',
                    status_display,
                    approved_by,
                    req.approved_date.strftime('%Y-%m-%d') if req.approved_date else '',
                    req.remarks or ''
                ]
        
        return export_to_excel(flat_data, headers, row_data, file_prefix="material_requisition")
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_products_list(request):
    """Get all products for dropdown"""
    try:
        products = Product.objects.filter(is_active=True).select_related('category', 'unit').order_by('code')
        data = []
        
        for product in products:
            data.append({
                'id': product.id,
                'code': product.code,
                'name': product.name,
                'category': product.category.name if product.category else '',
                'unit': product.unit.name if product.unit else '',
                'current_stock': float(product.current_stock) if hasattr(product, 'current_stock') else 0
            })
        
        return JsonResponse({'data': data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
