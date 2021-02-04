from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from tenancy.models import Tenant
from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, Rack, Interface
from ipam.models import Aggregate, IPAddress, Prefix, RIR, Role, RouteTarget, Service, VLAN, VLANGroup, VRF
from extras.scripts import *

from utilities.forms import (
    APISelect, APISelectMultiple, add_blank_choice, BootstrapMixin, BulkEditForm, BulkEditNullBooleanSelect,
    ColorSelect, CommentField, CSVChoiceField, CSVContentTypeField, CSVModelChoiceField, CSVModelForm,
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, ExpandableNameField, form_from_model, JSONField,
    NumericArrayField, SelectWithPK, SmallTextarea, SlugField, StaticSelect2, StaticSelect2Multiple, TagFilterField,
    BOOLEAN_WITH_BLANK_CHOICES,
)


class createSGJuniperSwitch(Script):
    class Meta:
        name = 'Create switch for SG sites'
        description = 'test01'
        field_order = ['dev_name','dev_model','site']


    dev_name = StringVar(
        description = 'Switch name'
    )

    dev_model = ObjectVar(
        model = DeviceType,
        description = 'Device model',
        display_field = 'model',
        query_params = {
            'manufacturer_id' : '24'
        }
    )

    site = ObjectVar(
        model = Site,
        description = 'Site',
        display_field = 'name',
        query_params = {
            'tenant' : 'sg'
        }
    )

    rack = ObjectVar(
        model = Rack,
        description = 'Rack',
        display_field = 'name',
        query_params = {
            'site_id' : '$site'
        }
    )

    position = IntegerVar(
        description = 'Unit',
        widget=APISelect(
            api_url='/api/dcim/racks/{{rack}}/elevation/',
            attrs={
                'disabled-indicator': 'device',
                'data-query-param-face': "[\"$face\"]",
            }
        )

    )

    mgmt_int_name = StringVar(
        description = 'MGMT vlan name'
    )

    mgmt_int_ip = StringVar(
        description = 'MGMT ip'

    )

    def run(self,data,commit):
        dev_role = DeviceRole.objects.get(slug = 'access-switch')
        device_new = Device(
            name = data['dev_name'],
            device_type = data['dev_model'],
            site = data['site'],
            rack = data['rack'],
            position = data['position'],
            device_role = dev_role,
        )
        device_new.save()

        dev_mgmt_int = Interface(
            device = device_new,
            name = data['mgmt_int_name'],
            type = 'virtual',
        )
        dev_mgmt_int.save()

        ipa_type = ContentType.objects.get(app_label='dcim',model='interface')
        ipa = IPAddress(
            address = data['mgmt_int_ip'],
            assigned_object_id = dev_mgmt_int.id,
            assigned_object_type = ipa_type,
        )
        ipa.save()

        device_new.primary_ip4 = ipa

        device_new.save()

        self.log_success(f"Created new Juniper device: {device_new}")
        
