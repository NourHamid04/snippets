from django.shortcuts import render

# Create packaging type:

@router.post("/", response={201: MessageResponse, 400: ErrorMessages, 403: MessageResponse, 500: MessageResponse},tags=["PackagingTypes"])
def create_packaging_type(request, payload: PackagingTypesSchema):
    """
    Endpoint to create a packaging type.
    Possible Responses:
    - 201:
        - packagingTypeCreated
    - 400:
        - nameConflict
    - 403:
        - permissionDenied
    - 500:
        - internalServerError
    """
    try:
        if not request.auth.has_perm("packaging.add_packagingtypes"):
            return 403, {"message": "Permission denied", "code": "permissionDenied"}
        
        payload_dict = payload.dict()
        payload_dict['created_by'] = request.auth.id
        
        serializer = PackagingTypesSerializer(data=payload_dict)
        if serializer.is_valid():
            packaging_type = serializer.save()
            return 201, {"message": "Packaging type created successfully", "code": "packagingTypeCreated", "id": str(packaging_type.id)}
        else:
            errors = format_dynamic_serializer_errors(serializer.errors)
            return 400, {"errors": errors}
    
    except Exception as e:
        return 500, {"message": str(e), "code": "internalServerError"}

#update a packaging type
@router.patch("/{id}/Types/", response={200: PatchPackagingTypesSchema, 400: ErrorMessages, 403: MessageResponse, 404: MessageResponse, 500: MessageResponse}, tags=["PackagingTypes"])
def update_packaging_type(request, id: UUID, payload: PatchPackagingTypesSchema):
    """
    Endpoint to update a packaging type.
    Possible Responses:
    - 200:
        - packagingTypeUpdated
    - 400:
        - nameConflict
        - noChangesDetected
    - 403:
        - permissionDenied
    - 404:
        - packagingTypeDoesNotExist
    - 500:
        - internalServerError
    """
    try:
        if not request.auth.has_perm("packaging.change_packagingtypes"):
            return 403, {"message": messages.permission_denied, 'code': 'permissionDenied'}
        
        update_data = payload.dict(exclude_unset=True)
        if not update_data:
            error = create_error_response(
                code="noChangesDetected",
                message=messages.no_changes_detected,
            )
            return 400, {"errors": error}
        
        try:
            packaging_type = PackagingTypes.objects.get(id=id)
        except PackagingTypes.DoesNotExist:
            return 404, {"message": "Packaging type does not exist", 'id': id}
        
        update_data['modified_by'] = request.auth.id
        serializer = PatchPackagingTypesSerializer(packaging_type, data=update_data, partial=True)

        if serializer.is_valid():
            packaging_type = serializer.save()
            return 200, PatchPackagingTypesSchema.from_orm(packaging_type)
        else:
            errors = format_dynamic_serializer_errors(serializer.errors)
            return 400, {"errors": errors}
    except Exception as e:
        return 500, {"message": str(e), 'code': 'internalServerError'}


#list packaging type:
@router.get("/", response={200: ListPackagingTypes, 400: ErrorMessages, 403: MessageResponse, 500: MessageResponse}, tags=["PackagingTypes"])
def list_packaging_types(request,
                         page: int = Query(None, description="Page number"),
                         name: str = Query(None, description="Name filter"),
                         barcode: str = Query(None, description="Barcode filter"),
                         pageSize: int = Query(None, description="Page size")
                         ):
    """
    Endpoint for listing packaging types
    - 200:
        - success
    - 400:
        - invalidFilterFormat
        - paginationError
    - 403:
        - permissionDenied
    - 500:
        - internalServerError
    """
    try:
        if not request.auth.has_perm("packaging.view_packagingtypes"):
            return 403, {"message": messages.permission_denied, 'code': 'permissionDenied'}

        queryset = PackagingTypes.objects.all().order_by('-date_created')

        if name:
            queryset = queryset.filter(name__icontains=name)

        if barcode:
            try:
                barcode_number_base = barcode[:12]
                uuid_int = int(barcode_number_base)
                possible_packages = PackagingTypes.objects.all()
                matched_packages = [
                    package for package in possible_packages if str(package.id.int)[:12] == barcode_number_base
                ]
                if matched_packages:
                    queryset = queryset.filter(id__in=[package.id for package in matched_packages])
                else:
                    return 404, {"message": "No packages found for the given barcode", "code": "noPackagesFound"}
            except ValueError:
                return 400, {"message": "Invalid barcode format", "code": "invalidBarcodeFormat"}

        queryset, error = apply_filters_to_queryset(queryset, request)
        if error:
            errors = create_error_response(
                code="invalidFilterFormat",
                message=error,
            )
            return 400, {"errors": errors}

        paginated_query = custom_paginate_queryset(queryset, request)
        if 'error' in paginated_query.data:
            errors = create_error_response(
                code="paginationError",
                message=paginated_query.data['error'],
            )
            return 400, {"errors": errors}

        data = paginated_query.data['results']

        response_data = {
            "info": paginated_query.data['info'],
            "results": data,
        }
        return 200, response_data
    except Exception as e:
        return 500, {"message": str(e), 'code': 'internalServerError'}


#delete packaging type:
@router.delete("/{id}/", response={204: None, 404: MessageResponse, 403: MessageResponse, 400: ErrorMessages, 500: MessageResponse},tags=["PackagingTypes"])
def delete_packaging_type(request, id: UUID):
    """
    Endpoint to delete a packaging type.
    - 404: 
        - packagingTypeDoesNotExist
    - 403: 
        - permissionDenied
    - 400: 
        - cantBeDeleted
    - 500: 
        - internalServerError
    """
    try:
        if not request.auth.has_perm("packaging.delete_packagingtypes"):
            return 403, {"message": messages.permission_denied, 'code': 'permissionDenied'}
        try:
            packaging_type = PackagingTypes.objects.get(id=id)
        except PackagingTypes.DoesNotExist:
            return 404, {"message": "Packaging type " + messages.doesnt_exist, 'code': 'packagingTypeDoesNotExist', 'id': id}

        for rel in packaging_type._meta.related_objects:
            related = rel.related_model.objects.filter(
                **{rel.field.name: packaging_type})
            if related.exists():
                error = create_error_response(
                    code="cantBeDeleted",
                    message="Can't delete object referenced by other objects",
                )
                return 400, {"errors": error}
        packaging_type.delete()
        return 204,None
    except Exception as e:
        return 500,  {"message": str(e), 'code': 'internalServerError'}



#Some schemas:

class PackagingTypesListSchema(ActivitySchema):
    id :UUID
    name : str
    level: PackagingLevel
    weight : float
    volume : float
    length : float
    width : float
    height : float
    material: PackagingMaterialsSchema
    parent: Optional[ParentPackagingTypeSchema] = None
    capacity : float

class AssignItemToPackageResponseSchema(BaseModel):
    message: str
    quantity_assigned: int
    used_capacity: int
    remaining_capacity: int

#models:


class PackagingTypes(Activity):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    weight = models.FloatField()
    volume = models.FloatField()
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    level = models.CharField(max_length=100, choices=LEVEL_OPTIONS)
    capacity = models.IntegerField(default=0) 
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,blank=True, 
        help_text="Selling price of the packaging type"
        )
    
    material = models.ForeignKey(
        PackagingMaterials,
        on_delete=models.CASCADE
        )

    instructions = models.ForeignKey(
        PackagingInstructions, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        help_text="Packaging instructions associated with this packaging type")

    parent = models.ForeignKey(
        'self',
         null=True, blank=True,
         related_name='children', 
         on_delete=models.CASCADE
         )  

urls:

from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from inventory.api import router as inventory_router
from inventory.packaging.views import router as packaging_router
from ninja.security import django_auth
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework.authtoken.views import obtain_auth_token
from ninja.security import HttpBearer
from rest_framework.authtoken.models import Token

class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            token_obj = Token.objects.get(key=token)
            return token_obj.user
        except Token.DoesNotExist:
            return None

api = NinjaAPI(auth=GlobalAuth(),title="PackagingERP API")


api.add_router('/inventory/packaging', inventory_router)
api.add_router('/packaging/', packaging_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),  
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]



















#PAGINATION/COMMON/SERVICE.PY:

def custom_paginate_queryset(queryset, request):
    page_size = min(int(request.GET.get('pageSize', 20)), 500)
    page_number = int(request.GET.get('page', 1))
    paginator = Paginator(queryset, page_size)

    try:
        page = paginator.page(page_number)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

    base_url = request.build_absolute_uri(request.path)
    next_page = page.number + 1 if page.has_next() else None
    prev_page = page.number - 1 if page.has_previous() else None
    # Construct next and previous page URLs
    next_url = f"{base_url}?{urlencode({'page': next_page, 'pageSize': page_size})}" if next_page else None
    prev_url = f"{base_url}?{urlencode({'page': prev_page, 'pageSize': page_size})}" if prev_page else None

    return Response({
        'info': {
            'count': paginator.count,
            'pages': paginator.num_pages,
            'next': next_url,
            'prev': prev_url
        },
        # Assuming the object_list can be serialized to JSON
        'results': list(page.object_list),
    })


def apply_filters_to_queryset(queryset, request):
    """
    Apply filters to the given queryset based on the provided filters string.
    """
    try:
        base_url = request.build_absolute_uri(request.get_full_path())
        filter = parse_qs_dict(base_url)
        filters = custom_grid_filter(Q(), filter)
        return queryset.filter(filters), None

    except Exception as e:
        return None, f"Error in filtering: {str(e)}"


def snake_to_camel(snake_str):
    """
    Converts a snake_case string to camelCase.
    """
    components = snake_str.split('_')
    # Capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def camel_to_snake(name):
    """
    Convert camelCase string to snake_case.
    """
    name = name.replace('.', '__')
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def custom_grid_filter(q_filters, filter_options):
    if isinstance(filter_options, dict):
        filter_options = [filter_options]

    for obj in filter_options:
        field = obj.get('field', None)
        values = obj.get('value', [])
        operator = obj.get('operator', None)

        if field is not None:
            field = camel_to_snake(field)

        q_filter = None

        if operator in ['in', 'range']:
            if operator == 'range' and len(values) != 2:
                continue
            if isinstance(values[0], str) and re.match(r'\d{4}-\d{2}-\d{2}$', values[0]):
                field += '__date'
        else:
            value = values[0] if len(values) > 0 else None
            if isinstance(value, str) and re.match(r'\d{4}-\d{2}-\d{2}$', value) and operator in ['eq', 'neq', 'lt', 'lte', 'gt', 'gte']:
                field += '__date'

            q_filter = generate_q_filter(operator, field, value, values)

        if operator in ['or', 'and', 'not']:
            composite_filters = Q()
            for sub_filter in values:
                composite_filter = custom_grid_filter(Q(), [sub_filter])
                if operator == 'or':
                    composite_filters |= composite_filter
                elif operator == 'and':
                    composite_filters &= composite_filter
                elif operator == 'not':
                    composite_filters &= ~composite_filter
            q_filter = composite_filters

        if q_filter is not None:
            if operator == 'or':
                q_filters |= q_filter
            else:
                q_filters &= q_filter

    return q_filters


def generate_q_filter(operator, field, value, values):
    if operator == 'eq':
        return Q(**{f'{field}': value})
    elif operator == 'neq':
        return ~Q(**{f'{field}': value})
    elif operator == 'lt':
        return Q(**{f'{field}__lt': value})
    elif operator == 'lte':
        return Q(**{f'{field}__lte': value})
    elif operator == 'gt':
        return Q(**{f'{field}__gt': value})
    elif operator == 'gte':
        return Q(**{f'{field}__gte': value})
    elif operator == 'contains':
        return Q(**{f'{field}__icontains': value})
    elif operator == 'startswith':
        return Q(**{f'{field}__istartswith': value})
    elif operator == 'endswith':
        return Q(**{f'{field}__iendswith': value})
    elif operator == 'isnull':
        return Q(**{f'{field}__isnull': value})
    elif operator == 'in':
        return Q(**{f'{field}__in': values})
    elif operator == 'range':
        return Q(**{f'{field}__range': values})
    else:
        return None


def get_date_range(period_type):

    today = date.today()
    if period_type == 'thisMonth':
        start_date = today.replace(day=1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
    elif period_type == 'lastMonth':  # last_month
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
    elif period_type == 'thisYear':
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    elif period_type == 'lastYear':  # last_year
        start_date = date(today.year-1, 1, 1)
        end_date = date(today.year-1, 12, 31)
    else:
        return None, None
    return start_date, end_date


def format_dynamic_serializer_errors(serializer_errors, index=None, prefix=""):
    # Mapping of DRF error codes to human-readable strings and HTTP status codes
    error_code_map = {
        'required': ('IsRequired', 400),
        'blank': ('CannotBeBlank', 400),
        'invalid': ('IsInvalid', 400),
        'invalid_choice': ('InvalidChoice', 400),
        'null': ('CannotBeNull', 400),
        'max_length': ('MaxLengthExceeded', 400),
        'min_length': ('MinLengthNotReached', 400),
        'max_value': ('MaxValueExceeded', 400),
        'min_value': ('MinValueNotReached', 400),
        'max_digits': ('MaxDigitsExceeded', 400),
        'max_decimal_places': ('MaxDecimalPlacesExceeded', 400),
        'max_whole_digits': ('MaxWholeDigitsExceeded', 400),
        'unique': ('Conflict', 409),
        'does_not_exist': ('DoesNotExist', 404),
        'incorrect_type': ('IncorrectType', 400),
        'date': ('InvalidDate', 400),
        'datetime': ('InvalidDateTime', 400),
        'time': ('InvalidTime', 400),
        'email': ('InvalidEmail', 400),
        'url': ('InvalidURL', 400),
        'slug': ('InvalidSlug', 400),
        'uuid': ('InvalidUUID', 400),
        'unique_for_date': ('UniqueForDateViolation', 400),
    }

    errors_list = []  # Stores the formatted errors
    for field, errors in serializer_errors.items():
        field = snake_to_camel(field)
        for error in errors:
            # Extract the message from the ErrorDetail object
            message = str(error)

            # Default handling for the error code
            error_code, _ = error_code_map.get(error.code, ('Error', 400))
            code_suffix = error_code if error.code in error_code_map else 'Error'
            code = f"{field}{code_suffix}"

            # Detect and handle unique together constraint errors
            if 'unique' in message.lower():
                # Regex to extract field names from the error message
                match = re.search(
                    r"The fields (.+?) must .*?unique.*?(,|\.|$)", message
                )
                if match:
                    # Split the matched group by commas and 'and', then strip spaces
                    fields = [x.strip()
                              for x in re.split(r',| and ', match.group(1))]
                    fields = [snake_to_camel(field) for field in fields]
                    # Combine fields with plusses and capitalize
                    code = '+'.join(fields) + 'Conflict'

                    if prefix != "":
                        fields = [f"{prefix}.{field}" for field in fields]

                    error_details = fields
                else:
                    # Fallback to default field handling if regex match fails
                    if prefix == "":
                        error_details = {field}
                    else:
                        error_details = {
                            f"{prefix}.{field}"}
            else:
                # Default handling for errors not involving unique together constraints
                if prefix == "":
                    error_details = {field}
                else:
                    error_details = {
                        f"{prefix}.{field}"}

            # Construct and add the error dictionary
            error_dict = {
                "message": message,
                "code": code,
                "fields": error_details,
                "index": index
            }
            errors_list.append(error_dict)
    # Wrap the errors list in a dictionary under the 'errors' key
    return errors_list


def create_error_response(code="UndefinedError", message="Error Occurred", field=None, prefix=None, index=None, id=None):

    fields_elements = filter(None, [prefix, field])
    field = ".".join(fields_elements)
    error = []
    error.append({
        "id": id,
        "message": message,
        "code": code,
        "fields": [field] if field else [],
        "index": index
    })
    return error

