import logging
import typing
import asyncio
import upnpy
# ALLOW util.* msg*.* context.* http.*
from core.util import gc, util, funcutil, sysutil
from core.msg import msgabc, msgftr, msgext
from core.context import contextsvc


_VALID_PROTOCALS = gc.TCP, gc.UDP
_GET_STATUS, _SET_STATUS, _STATUS = 'IgdStatus.Get', 'IgdStatus.Set', 'IgdStatus.Status'


def initialise(context: contextsvc.Context, source: typing.Any):
    if context.config('noupnp'):
        return
    context.register(msgext.SetGetSubscriber(context, _GET_STATUS, _SET_STATUS, _STATUS, '...'))
    context.register(IgdService(context))
    context.post(source, IgdService.DISCOVER)


async def status(context: contextsvc.Context, source: typing.Any) -> str:
    if context.config('noupnp'):
        return 'Disabled'
    response = await msgext.SynchronousMessenger(context).request(source, _GET_STATUS)
    return response.data()


def add_port_mapping(mailer: msgabc.Mailer, source: typing.Any, port: int, protocal: str, description: str):
    assert protocal in _VALID_PROTOCALS
    mailer.post(source, IgdService.ADD_PORT_MAPPING, dict(port=port, protocal=protocal, description=description))


def delete_port_mapping(mailer: msgabc.Mailer, source: typing.Any, port: int, protocal: str):
    assert protocal in _VALID_PROTOCALS
    mailer.post(source, IgdService.DELETE_PORT_MAPPING, dict(port=port, protocal=protocal))


class IgdService(msgabc.AbcSubscriber):
    DISCOVER = 'IgdService.Discover'
    ADD_PORT_MAPPING, DELETE_PORT_MAPPING = 'IgdService.AddPortMapping', 'IgdService.DeletePortMapping'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.NameIn(
            IgdService.DISCOVER, IgdService.ADD_PORT_MAPPING, IgdService.DELETE_PORT_MAPPING))
        self._mailer, self._service = mailer, None

    async def handle(self, message):
        action, data = message.name(), message.data()
        try:
            return await self._handle(action, data)
        except Exception as e:
            logging.error('Error handling %s : %s', action, repr(e))
        return False

    async def _handle(self, action, data):
        if action is IgdService.DISCOVER:
            self._mailer.post(self, _SET_STATUS, 'discovery...')
            self._service = await _get_mapping_service()
            if self._service:
                self._mailer.post(self, _SET_STATUS, 'Active')
                return None
            self._mailer.post(self, _SET_STATUS, 'Unavailable')
        if not self._service:
            return False
        port, protocal = util.get('port', data), util.get('protocal', data)
        if action is IgdService.ADD_PORT_MAPPING:
            description = util.get('description', data)
            local_ip = await sysutil.local_ip()
            await asyncio.wait_for(_add_port_mapping(self._service, local_ip, port, protocal, description), 4.0)
            return None
        if action is IgdService.DELETE_PORT_MAPPING:
            await asyncio.wait_for(_delete_port_mapping(self._service, port, protocal), 4.0)
            return None
        return None


def _sort_device(device):
    value = repr(device)
    if value.find('IGD') > -1:
        return 0
    value = value.lower()
    if value.find('gateway') > -1 or value.find('router') > -1:
        return 0
    return 1


def _sync_get_mapping_service():
    try:
        logging.debug('Discovering UPnP devices')
        devices = list(upnpy.UPnP().discover(delay=3))
        devices.sort(key=_sort_device)
        for device in devices:
            device_repr = repr(device)
            logging.debug('net> discovered device: %s', device_repr)
            for service in device.get_services():
                service_repr = repr(service)
                logging.debug('net>  discovered service: %s', service_repr)
                for action in service.get_actions():
                    logging.debug('net>   discovered action: %s', repr(action))
                    if action.name == 'AddPortMapping':
                        logging.info('Found port mapping service: %s %s', device_repr, service_repr)
                        return service
        logging.info('No IGD port mapping service found')
    except Exception as e:
        logging.error('UPnP discovery error: %s', repr(e))
    return None


def _sync_add_port_mapping(service, local_ip: str, port: int, protocal: str, description: str):
    try:
        logging.debug('Opening port %s:%s for %s', local_ip, port, protocal)
        service.AddPortMapping(
            NewRemoteHost='',
            NewExternalPort=port,
            NewProtocol=protocal,
            NewInternalPort=port,
            NewInternalClient=local_ip,
            NewEnabled=1,
            NewPortMappingDescription=description,
            NewLeaseDuration=0)
    except Exception as e:
        logging.error('Add port mapping error: %s', repr(e))


def _sync_delete_port_mapping(service, port: int, protocal: str):
    try:
        logging.debug('Closing port %s for %s', port, protocal)
        service.DeletePortMapping(NewRemoteHost='', NewExternalPort=port, NewProtocol=protocal)
    except Exception as e:
        logging.error('Delete port mapping error: %s', repr(e))


_get_mapping_service = funcutil.to_async(_sync_get_mapping_service)
_add_port_mapping = funcutil.to_async(_sync_add_port_mapping)
_delete_port_mapping = funcutil.to_async(_sync_delete_port_mapping)
