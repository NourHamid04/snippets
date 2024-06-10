
#----------------------------------------------------------------
            #starting a new project with django-ninja#
#----------------------------------------------------------------
#  python -m venv venv

#  .\venv\Scripts\activate

#  pip install django djangoninja     
#                                                 #commands#
#  django-admin startproject myproject

#  cd myproject

# python manage.py startapp myapp

#----------------------------------------------------------------
#SETTINGS.JSON:

#INSTALLED_APPS = [
#    ...
#   'myapp',
#    'ninja',  # Add this line
#]
#----------------------------------------------------------------
                        #api.py:





from ninja import NinjaAPI

from django.shortcuts import get_object_or_404
from .schemas import (SortingSchema)
from typing import List,Optional
from pydantic import BaseModel, ValidationError
from django.db.models import Sum, Avg
from django.db.models import Count
from ninja.errors import HttpError
from django.db.models import F
from django.db.models import Max
from django.db.models import FloatField
from django.db.models import ExpressionWrapper
from datetime import datetime
from ninja import Schema,Query
from .utils import generate_barcode, generate_label
from django.http import FileResponse
import base64
import random,time
import uuid
from ninja.pagination import paginate, PageNumberPagination
from .permissions import permission_required
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from ninja.security import HttpBearer
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
import datetime
from datetime import date, timedelta


api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return {"message": "Hello, world!"}
#----------------------------------------------------------------
                        #urls.py

            #from django.contrib import admin
            #from django.urls import path
            #from myapp.api import api

#urlpatterns = [
  #  path('admin/', admin.site.urls),
  #  path('api/', api.urls),  # Add this line
#]

#-----------------------------------------------------------------
                #python manage.py runserver


#-----------------------------------------------------------------
                        #migrations:

            #python manage.py makemigrations
            #python manage.py migrate



#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
                                                    #Error Handling


from ninja.errors import HttpError
from pydantic import ValidationError

def bad_request(request, exc):
    return api.create_response(request, {"detail": str(exc)}, status=400)

def not_found(request, exc):
    return api.create_response(request, {"detail": "The requested resource was not found."}, status=404)

def internal_server_error(request, exc):
    return api.create_response(request, {"detail": "Internal server error, please try again later."}, status=500)

def validation_error(request, exc):
    return api.create_response(request, {"detail": str(exc)}, status=422)

api.add_exception_handler(HttpError, bad_request)
api.add_exception_handler(ValidationError, validation_error)
api.add_exception_handler(Exception, internal_server_error)


#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

                                            #Authentication and Permissions


from ninja.security import HttpBearer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            token_obj = Token.objects.get(key=token)
            return token_obj.user
        except Token.DoesNotExist:
            return None

api = NinjaAPI(auth=GlobalAuth())

def permission_required(permission):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not request.auth.has_perm(permission):
                raise HttpError(403, "Permission denied")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
                                            #Pagination and Sorting


from ninja.pagination import paginate, PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

class SortingSchema(Schema):
    sort_by: Optional[str] = None
    sort_order: Optional[str] = 'asc'


#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
                                            #Filtering and pagination for get with (schemas.py) AND CRUD methods

from ninja import ModelSchema
from typing import List
from pydantic import BaseModel
from typing import Optional
from ninja import Schema,FilterSchema,Field
from datetime import datetime
from .models import Product




class ProductSchema(ModelSchema):
    class Config:
        model = Product
        model_fields = ['id', 'name', 'cost', 'description']


class ProductFilterSchema(FilterSchema):
    name: Optional[str] = None
    cost: Optional[float] = None


class SortingSchema(Schema):
    sort_by: Optional[str] = None
    sort_order: Optional[str] = 'asc'



@api.post("/products", response=ProductSchema)
def create_product(request, payload: ProductSchema):
    product = Product.objects.create(**payload.dict())
    return product




@api.get("/products", response=List[ProductSchema])
@paginate(CustomPagination)
def list_products(request, filters: ProductFilterSchema = Query(...), sorting: SortingSchema = Query(...)):
    products = Product.objects.all()
    products = filters.filter(products)
    
    if sorting.sort_by:
        sort_order = '' if sorting.sort_order == 'asc' else '-'
        products = products.order_by(f'{sort_order}{sorting.sort_by}')
    
    return products


@api.put("/products/{id}", response=ProductSchema)
def update_product(request, id: int, payload: ProductSchema):
    product = get_object_or_404(Product, id=id)
    for attr, value in payload.dict().items():
        setattr(product, attr, value)
    product.save()
    return product


@api.delete("/products/{id}")
def delete_product(request, id: int):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return {"success": True}



                    #Packaging_Materials CRUD methods 

# @api.post("/packaging_materials", response=PackagingMaterialsSchema)
# @permission_required('inventory.add_packagingmaterials')
# def create_packaging_material(request, payload: PackagingMaterialsSchema):
#     try:
#         packaging_material = PackagingMaterials.objects.create(**payload.dict())
#         return PackagingMaterialsSchema.from_orm(packaging_material)
#     except ValidationError as e:
#         raise HttpError(400, str(e))





# @api.put("/packaging_materials/{id}", response=PackagingMaterialsSchema)
# @permission_required('inventory.change_packagingmaterials')
# def update_packaging_material(request, id: int, payload: PackagingMaterialsSchema):
#     try:
#         packaging_material = get_object_or_404(PackagingMaterials, id=id)
#         for attr, value in payload.dict().items():
#             setattr(packaging_material, attr, value)
#         packaging_material.save()
#         return PackagingMaterialsSchema.from_orm(packaging_material)
#     except ValidationError as e:
#         raise HttpError(400, str(e))



# @api.delete("/packaging_materials/{id}")
# @permission_required('inventory.delete_packagingmaterials')
# def delete_packaging_material(request, id: int):
#     try:
#         packaging_material = get_object_or_404(PackagingMaterials, id=id)
#         packaging_material.delete()
#         return {"success": True}
#     except ValidationError as e:
#         raise HttpError(400, str(e))









# from ninja import Query

# class PackagingMaterialsFilterSchema(FilterSchema):
#     name: Optional[str] = None
#     cost: Optional[float] = None
#     description: Optional[str] = None

# @api.get("/packaging_materials", response=List[PackagingMaterialsSchema])
# @paginate(CustomPagination)
# @permission_required('inventory.view_packagingmaterials')
# def get_packaging_materials(request, filters: PackagingMaterialsFilterSchema = Query(...), sorting: SortingSchema = Query(...)):
#     try:
#         packaging_materials = PackagingMaterials.objects.all()
#         packaging_materials = filters.filter(packaging_materials)
        
#         if sorting.sort_by:
#             sort_order = '' if sorting.sort_order == 'asc' else '-'
#             packaging_materials = packaging_materials.order_by(f'{sort_order}{sorting.sort_by}')

#         return packaging_materials
#     except Exception as e:
#         print(f"Error: {e}")
#         raise HttpError(500, "Internal server error, please try again later.")



#----------------------------------------------------------------------------------------------------------------#
                #Parcode

# @api.post("/generate_barcode", response=BarcodeAndLabelResponseSchema)
# @permission_required('inventory.generate_barcode')
# def generate_barcode(request, packaging_type_id: int):
#     packaging_type = get_object_or_404(PackagingTypes, id=packaging_type_id)
#     barcode_number = generate_barcode(packaging_type)
#     label = generate_label(packaging_type, barcode_number)
#     return {"barcode_number": barcode_number, "label": label}

# @api.post("/validate_barcode", response=ValidateBarcodeResponseSchema)
# @permission_required('inventory.validate_barcode')
# def validate_barcode(request, payload: ValidateBarcodeRequestSchema):
#     try:
#         packaging_type = PackagingTypes.objects.get(id=payload.barcode_number[:6])
#         return {"valid": True, "packaging_type_info": PackagingTypesSchema.from_orm(packaging_type)}
#     except PackagingTypes.DoesNotExist:
#         return {"valid": False, "packaging_type_info": None}




#-------------------------------------------------------------------------------    ----------------------------------------------------------------
                                                    #Handling Foriegn KEYS WITH CRUD :

#model:
#-------------------------------------------------------------------------------
# from django.db import models

# WAREHOUSE_TYPES = [(1, 'Type1'), (2, 'Type2')]

# class Warehouse(models.Model):
#     code = models.CharField(max_length=50)
#     name = models.CharField(max_length=50)
#     warehouse_type = models.IntegerField(choices=WAREHOUSE_TYPES)
#     description = models.TextField(blank=True)
#     total_capacity = models.IntegerField()
#     available_capacity = models.IntegerField()
#     packaging_materials = models.ForeignKey('PackagingMaterials', on_delete=models.CASCADE, null=True, blank=True)
#     packaging_types = models.ForeignKey('PackagingTypes', on_delete=models.CASCADE, null=True, blank=True)

#     class Meta:
#         permissions = [
#             ("can_create_warehouse", "Can create warehouse"),
#             ("can_view_warehouse", "Can view warehouse"),
#             ("can_update_warehouse", "Can update warehouse"),
#             ("can_delete_warehouse", "Can delete warehouse"),
#         ]

#     def __str__(self):
#         return self.name


#----------------------------------------------------------------
#SCHEMA_VERSION:

# from ninja import ModelSchema, Schema
# from typing import Optional

# class WarehouseSchema(ModelSchema):
#     class Config:
#         model = Warehouse
#         model_fields = ['id', 'code', 'name', 'warehouse_type', 'description', 'total_capacity', 'available_capacity', 'packaging_materials', 'packaging_types']

#----------------------------------------------------------------------------------------

#CREATE WITH FORIEGN KEY
# import logging

# logger = logging.getLogger(__name__)

# @api.post("/packaging_types", response=PackagingTypesSchema)
# @permission_required('inventory.add_packagingtypes')
# def create_packaging_type(request, payload: PackagingTypesSchema):
#     try:
#         material_id = payload.material.id
#         material = get_object_or_404(PackagingMaterials, id=material_id)
        
#         if material.available_quantity < payload.quantity:
#             raise HttpError(400, "Not enough material available")

#         packaging_type_data = payload.dict()
#         packaging_type_data['material'] = material
        
#         packaging_type = PackagingTypes.objects.create(**packaging_type_data)
#         return PackagingTypesSchema.from_orm(packaging_type)
#     except ValidationError as e:
#         logger.error(f"Validation error: {str(e)}")
#         raise HttpError(422, str(e))
#     except PackagingMaterials.DoesNotExist:
#         logger.error("Packaging material does not exist")
#         raise HttpError(400, "Packaging material does not exist")
#     except Exception as e:
#         logger.error(f"Internal server error: {str(e)}")
#         raise HttpError(500, "Internal server error, please try again later.")


#----------------------------------------------------------------------------------------

#ASSIGN THING
# @api.put("/packaging_types/{packaging_type_id}/assign_parent", response=PackagingTypesSchema)
# @permission_required('inventory.change_packagingtypes')
# def assign_parent(request, packaging_type_id: int, payload: ParentAssignmentSchema):
#     try:
#         packaging_type = get_object_or_404(PackagingTypes, id=packaging_type_id)
#         parent = get_object_or_404(PackagingTypes, id=payload.parent_id)

#         packaging_type.parent = parent
#         packaging_type.save()
#         return PackagingTypesSchema.from_orm(packaging_type)
#     except PackagingTypes.DoesNotExist:
#         logger.error("Packaging type or parent does not exist")
#         raise HttpError(400, "Packaging type or parent does not exist")
#     except Exception as e:
#         logger.error(f"Internal server error: {str(e)}")
#         raise HttpError(500, "Internal server error, please try again later.")
#--------------------------------------------------------------------------------------------------------------------------------
# ADVANCED MODEL


from django.db import models
from django.utils import timezone
from tinymce.models import HTMLField

# class PackagingTypes(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     weight = models.FloatField()
#     volume = models.FloatField()
#     length = models.FloatField()
#     width = models.FloatField()
#     height = models.FloatField()
#     material = models.ForeignKey(PackagingMaterials, on_delete=models.CASCADE)
#     cost = models.FloatField()
#     quantity = models.DecimalField(max_digits=10, decimal_places=2)
#     level = models.CharField(max_length=100, choices=LEVEL_OPTIONS)
#     created_at = models.DateTimeField(default=timezone.now)
#     updated_at = models.DateTimeField(auto_now=True)
#     parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)  # Add this line

#     class Meta:
#         permissions = [
#             ("can_create_packaging_type", "Can create packaging type"),
#             ("can_view_packaging_type", "Can view packaging type"),
#             ("can_update_packaging_type", "Can update packaging type"),
#             ("can_delete_packaging_type", "Can delete packaging type"),
#         ]

#     def __str__(self):
#         return self.name


#--------------------------------------------------------------------------------------------------------

#UPDATE ADVANCE

# @api.put("/packaging_types/{packaging_type_id}", response=PackagingTypesSchema)
# @permission_required('inventory.change_packagingtypes')
# def update_packaging_type(request, packaging_type_id: int, payload: PackagingTypesSchema):
#     try:
#         packaging_type = get_object_or_404(PackagingTypes, id=packaging_type_id)
#         material_id = payload.material.id
#         material = get_object_or_404(PackagingMaterials, id=material_id)

#         if material.available_quantity < payload.quantity:
#             raise HttpError(400, "Not enough material available")

#         for attr, value in payload.dict().items():
#             if attr == "material":
#                 setattr(packaging_type, attr, material)
#             elif attr == "parent":
#                 if value is not None:
#                     parent_id = value['id']
#                     parent = get_object_or_404(PackagingTypes, id=parent_id)
#                     setattr(packaging_type, attr, parent)
#                 else:
#                     setattr(packaging_type, attr, None)
#             else:
#                 setattr(packaging_type, attr, value)

#         packaging_type.save()
#         return PackagingTypesSchema.from_orm(packaging_type)
#     except ValidationError as e:
#         logger.error(f"Validation error: {str(e)}")
#         raise HttpError(422, str(e))
#     except PackagingMaterials.DoesNotExist:
#         logger.error("Packaging material does not exist")
#         raise HttpError(400, "Packaging material does not exist")
#     except PackagingTypes.DoesNotExist:
#         logger.error("Parent packaging type does not exist")
#         raise HttpError(400, "Parent packaging type does not exist")
#     except Exception as e:
#         logger.error(f"Internal server error: {str(e)}")
#         raise HttpError(500, "Internal server error, please try again later.")




#--------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------



#HELPFUL FUNCTIONS:

#1) OPTIMIZATION:

# @api.post("/packaging_optimization", response=OptimizationOutputSchema)
# @permission_required('inventory.optimize_packaging')
# def optimize_packaging(request, length: float, width: float, height: float, max_weight: float, max_cost: float):
#     try:
#         optimal_material = PackagingMaterials.objects.filter(
#             packagingtypes__length__lte=length,
#             packagingtypes__width__lte=width,
#             packagingtypes__height__lte=height,
#             packagingtypes__weight__lte=max_weight,
#             packagingtypes__cost__lte=max_cost
#         ).annotate(
#             total_cost=Sum('packagingtypes__cost'),
#             total_weight=Sum('packagingtypes__weight')
#         ).order_by('total_cost').first()

#         if not optimal_material:
#             raise HttpError(404, "No suitable material found")

#         return {
#             "material_id": optimal_material.id,
#             "material_name": optimal_material.name,
#             "total_cost": optimal_material.total_cost,
#             "total_weight": optimal_material.total_weight
#         }
#     except ValidationError as e:
#         raise HttpError(400, str(e))
#     except Exception as e:
#         raise HttpError(500, "Internal server error, please try again later.")


#Rearoder Alert:

# @api.get("/reorder_alerts", response=List[ItemsSchema])
# @permission_required('inventory.view_reorder_alerts')
# def get_reorder_alerts(request):
#     try:
#         items = Items.objects.filter(stock_quantity__lte=F('reorder_level'))
#         return items
#     except ValidationError as e:
#         raise HttpError(400, str(e))
#     except Exception as e:
#         raise HttpError(500, "Internal server error, please try again later.")


#------------------------------------------------------------------------------------------------

#allocate materials:


# @api.post("/allocate_materials", response=dict)
# @permission_required('inventory.allocate_materials')
# def allocate_materials(request, warehouse_id: int, material_id: int, quantity: float):
#     try:
#         warehouse = get_object_or_404(Warehouse, id=warehouse_id)
#         material = get_object_or_404(PackagingMaterials, id=material_id)

#         if warehouse.available_capacity < quantity:
#             raise HttpError(400, "Not enough available capacity in the warehouse.")

#         if material.available_quantity < quantity:
#             raise HttpError(400, "Not enough material available.")

#         material.available_quantity -= quantity
#         material.save()

#         warehouse.available_capacity -= quantity
#         warehouse.save()

#         return {
#             "message": "Materials allocated successfully",
#             "remaining_material_quantity": material.available_quantity,
#             "remaining_warehouse_capacity": warehouse.available_capacity,
#         }
#     except ValidationError as e:
#         raise HttpError(400, str(e))
#     except Exception as e:
#         raise HttpError(500, "Internal server error, please try again later.")

#------------------------------------------------------------------------------------------------

  # Suggest Packaging:

# @api.post("/suggest_packaging", response=PackagingTypesSchema)
# @permission_required('inventory.suggest_packaging')
# def suggest_packaging(request, item_id: int):
#     item = get_object_or_404(Items, id=item_id)
#     suitable_packaging = PackagingTypes.objects.filter(
#         length__gte=item.length,
#         width__gte=item.width,
#         height__gte=item.height,
#         weight__gte=item.weight
#     ).order_by('cost').first()

#     if not suitable_packaging:
#         raise HttpError(404, "No suitable packaging type found.")

#     return suitable_packaging 

#__________________________________________

#Request Materials:

# @api.post("/request-materials", response={200: dict})
# @permission_required('supply_chain.request_materials')
# def request_materials_from_supplier(request, payload: MaterialRequestSchema):
#     try:
#         supplier = get_object_or_404(Supplier, id=payload.supplier_id)
#         material_requests = payload.material_requests
#         response_data = []

#         for request_item in material_requests:
#             material = get_object_or_404(PackagingMaterials, id=request_item.material_id)

#             # Check if supplier has the requested material
#             if material in supplier.packaging_materials.all():
#                 # Assume the supplier can fulfill the request. You can add more logic here if needed.
#                 response_data.append({
#                     "material_id": material.id,
#                     "material_name": material.name,
#                     "requested_quantity": request_item.quantity,
#                     "available_quantity": material.available_quantity,  # Example of useful information
#                     "supplier_name": supplier.name
#                 })
#             else:
#                 response_data.append({
#                     "material_id": material.id,
#                     "material_name": material.name,
#                     "requested_quantity": request_item.quantity,
#                     "available_quantity": 0,
#                     "supplier_name": supplier.name,
#                     "message": "Supplier does not have the requested material"
#                 })

#         return {"message": "Material request processed successfully", "data": response_data}

#     except Exception as e:
#         print(f"Error: {e}")
#         raise HttpError(500, "Internal server error, please try again later.")



#--------------------------------------------------------------------------------------------------------------------------------
#Patch cost update request

# @api.patch("/integration/finance/costs/packaging/", response={200: dict})
# @permission_required('finance.track_packaging_costs')
# def track_packaging_costs(request, payload: PackagingCostUpdateSchema):
#     try:
#         packaging_type = get_object_or_404(PackagingTypes, id=payload.packaging_type_id)
#         packaging_type.cost = payload.cost
#         packaging_type.save()
#         return {"message": "Packaging costs updated successfully", "packaging_type_id": packaging_type.id, "new_cost": packaging_type.cost}
#     except Exception as e:
#         print(f"Error: {e}")
#         raise HttpError(500, "Internal server error, please try again later.")




#-------------------------------------------------------------------------------------------------------

#order status:


#@api.get("/customer/order-status", response={200: dict})
# @permission_required('sales.view_order_status')
# def order_status(request, order_id: int):
#     try:
#         sales_order = get_object_or_404(SalesOrder1, id=order_id)
#         return {
#             "order_id": sales_order.id,
#             "order_number": sales_order.order_number,
#             "customer_name": sales_order.customer.name,
#             "order_date": sales_order.order_date,
#             "status": sales_order.status,
#             "packaging_types": [pt.name for pt in sales_order.packaging_types.all()]
#         }
#     except Exception as e:
#         print(f"Error: {e}")
#         raise HttpError(500, "Internal server error, please try again later.")
#------------------------------------------------------------------------------------------------------------------------

#count and get childern packages

# @api.get("/packaging_types/{parent_id}/children_count", response=dict)
# @permission_required('inventory.view_packagingtypes')
# def count_children_packages(request, parent_id: int):
#     try:
#         parent = get_object_or_404(PackagingTypes, id=parent_id)
#         count = PackagingTypes.objects.filter(parent=parent).count()
#         return {"parent_id": parent_id, "children_count": count}
#     except PackagingTypes.DoesNotExist:
#         logger.error("Parent packaging type does not exist")
#         raise HttpError(400, "Parent packaging type does not exist")
#     except Exception as e:
#         logger.error(f"Internal server error: {str(e)}")
#         raise HttpError(500, "Internal server error, please try again later.")
    


# @api.get("/packaging_types/{parent_id}/children", response=List[PackagingTypesSchema])
# @permission_required('inventory.view_packagingtypes')
# def get_children_packages(request, parent_id: int):
#     try:
#         parent = get_object_or_404(PackagingTypes, id=parent_id)
#         children = PackagingTypes.objects.filter(parent=parent)
#         return [PackagingTypesSchema.from_orm(child) for child in children]
#     except PackagingTypes.DoesNotExist:
#         logger.error("Parent packaging type does not exist")
#         raise HttpError(400, "Parent packaging type does not exist")
#     except Exception as e:
#         logger.error(f"Internal server error: {str(e)}")
#         raise HttpError(500, "Internal server error, please try again later.")
    
#--------------------------------------------------------------------------------------------------------------------------------
#UNIT TESTING


# import pytest
# import json
# from rest_framework.test import APIClient
# from inventory.models import PackagingMaterials, PackagingTypes, UnitsOfMeasurement, Warehouse, Items, PackagingInstructions, BillOfMaterials, WorkOrders
# from django.utils import timezone
# from inventory.schemas import PackagingLevel
# from django.test import TestCase, Client
# @pytest.fixture
# def client():
#     return APIClient()

# @pytest.mark.django_db
# def test_get_units_of_measurement(client):
#     UnitsOfMeasurement.objects.create(name="Kilogram", abbreviation="kg")
#     UnitsOfMeasurement.objects.create(name="Liter", abbreviation="L")
#     url = "/api/units_of_measurement"
#     response = client.get(url)
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) == 2



# @pytest.mark.django_db
# def test_get_packaging_types(client):
#     material = PackagingMaterials.objects.create(
#         name="Plastic",
#         description="Durable plastic",
#         cost=1.5,
#         available_quantity=200.0,
#         created_at=timezone.now()
#     )
#     PackagingTypes.objects.create(
#         name="Box",
#         description="Plastic box",
#         weight=0.5,
#         volume=1.0,
#         length=30.0,
#         width=30.0,
#         height=30.0,
#         material=material,
#         cost=1.0,
#         quantity=50,
#         level=PackagingLevel.PRIMARY,
#         created_at=timezone.now()
#     )
#     url = "/api/packaging_types"
#     response = client.get(url)
#     assert response.status_code == 200, response.json()
#     data = response.json()
#     assert len(data) == 1
#     assert data[0]['name'] == "Box"
#     assert data[0]['description'] == "Plastic box"



#--------------------------------------------------------------------------------------------------------------------------------
#SETTING.JSON

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
    'ninja',
    'tinymce',
    'rest_framework',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
   
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
