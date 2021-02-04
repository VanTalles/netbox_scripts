from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from tenancy.models import Tenant
from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, Rack, Interface
from ipam.models import Aggregate, IPAddress, Prefix, RIR, Role, RouteTarget, Service, VLAN, VLANGroup, VRF
from extras.scripts import *
from extras.models import CustomField
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
        field_order = ['site','rack','sw_name','sw_int_name','sw_int_ip']

    SERVICESLIST = (
        ('s2','SSHv2'),
        ('s1','SSHv1'),
        ('t','Telnet'),
        ('y','YANG'),
        ('r','REST'),
    )

    dev_name = StringVar(
        description = 'Switch name'
    )

    dev_serial = StringVar(
        description = 'Serial number'
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

    monitoring = BooleanVar(
        description = 'Set to monitoring'
    )

    backup = BooleanVar(
        description = 'Set to backup'
    )

    services = MultiChoiceVar(choices=SERVICESLIST)


    def run(self,data,commit):

        services_list = [
            {'id_s':'s2','port':22,'name':'SSHv2','protocol':'tcp'},
            {'id_s':'s1','port':22,'name':'SSHv1','protocol':'tcp'},
            {'id_s':'t','port':23,'name':'Telnet','protocol':'tcp'},
            {'id_s':'y','port':443,'name':'YANG','protocol':'tcp'},
            {'id_s':'r','port':443,'name':'REST','protocol':'tcp'},
        ]


        dev_role = DeviceRole.objects.get(slug = 'access-switch')
        device_new = Device(
            name = data['dev_name'],
            device_type = data['dev_model'],
            site = data['site'],
            rack = data['rack'],
            position = data['position'],
            device_role = dev_role,
            serial = data['dev_serial'],
        )
        device_new.save()

        device_new.custom_field_data['fMonitoring'] = data['monitoring']
        device_new.custom_field_data['fBackup'] = data['backup']
        device_new.save()

        output = []
        for iServ in data['services']:
            output.append(iServ)
            print(output)
            res = [row for row in services_list if row['id_s'] == iServ]
            s1 = Service(
                device = device_new,
                name = res[0]['name'],
                ports = [res[0]['port']],
                protocol = res[0]['protocol'],
            )
            s1.save()


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
        return ''.join(output)
