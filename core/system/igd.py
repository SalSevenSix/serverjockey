import logging
import typing
import asyncio
import upnpy
# ALLOW util.* msg.* context.* http.* system.svrabc
from core.util import util, funcutil, sysutil
from core.msg import msgabc, msgftr


TCP, UDP = 'TCP', 'UDP'
_VALID_PROTOCALS = TCP, UDP


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(IgdService())
    mailer.post('core.system.idg.initialise()', IgdService.DISCOVER)


def add_port_mapping(mailer: msgabc.Mailer, source: typing.Any, port: int, protocal: str, description: str):
    assert protocal in _VALID_PROTOCALS
    mailer.post(source, IgdService.ADD_PORT_MAPPING, {'port': port, 'protocal': protocal, 'description': description})


def delete_port_mapping(mailer: msgabc.Mailer, source: typing.Any, port: int, protocal: str, sync: bool = False):
    assert protocal in _VALID_PROTOCALS
    mailer.post(source, IgdService.DELETE_PORT_MAPPING, {'port': port, 'protocal': protocal, 'sync': sync})


class IgdService(msgabc.AbcSubscriber):
    DISCOVER = 'IgdService.Discover'
    ADD_PORT_MAPPING = 'IgdService.AddPortMapping'
    DELETE_PORT_MAPPING = 'IgdService.DeletePortMapping'
    FILTER = msgftr.NameIn((ADD_PORT_MAPPING, DELETE_PORT_MAPPING))

    def __init__(self):
        super().__init__(msgftr.NameIn((
            IgdService.DISCOVER,
            IgdService.ADD_PORT_MAPPING,
            IgdService.DELETE_PORT_MAPPING)))
        self._upnp = upnpy.UPnP()
        self._service = None

    async def handle(self, message):
        action, data = message.name(), message.data()
        try:
            return await self._handle(action, data)
        except Exception as e:
            logging.warning('Error handling ' + action + ': ' + repr(e))
        return False

    async def _handle(self, action, data):
        if action is IgdService.DISCOVER:
            self._service = await asyncio.wait_for(_get_mapping_service(self._upnp), 20.0)
            return None if self._service else False
        if not self._service:
            return False
        if action is IgdService.ADD_PORT_MAPPING:
            local_ip = await sysutil.get_local_ip()
            port, protocal = util.get('port', data), util.get('protocal', data)
            description = util.get('description', data)
            await asyncio.wait_for(_add_port_mapping(self._service, local_ip, port, protocal, description), 4.0)
            return None
        if action is IgdService.DELETE_PORT_MAPPING:
            sync, port, protocal = util.get('sync', data, False), util.get('port', data), util.get('protocal', data)
            if sync:  # Allowing sync option because aiohttp aggressively kills tasks upon shutdown
                _sync_delete_port_mapping(self._service, port, protocal)
            else:
                await asyncio.wait_for(_delete_port_mapping(self._service, port, protocal), 4.0)
            return None
        return None


def _sync_get_mapping_service(upnp):
    try:
        logging.debug('Discovering UPnP devices.')
        for device in upnp.discover(delay=3):
            for service in device.get_services():
                for action in service.get_actions():
                    if action.name == 'AddPortMapping':
                        logging.debug('Found port mapping service: ' + repr(service))
                        return service
        logging.debug('No IGD port mapping service found.')
    except Exception as e:
        logging.debug('UPnP discovery error: ' + repr(e))
    return None


def _sync_add_port_mapping(service, local_ip: str, port: int, protocal: str, description: str):
    try:
        logging.debug('Opening port ' + local_ip + ':' + str(port) + ' for ' + protocal)
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
        logging.debug('Add port mapping error: ' + repr(e))


def _sync_delete_port_mapping(service, port: int, protocal: str):
    try:
        logging.debug('Closing port ' + str(port) + ' for ' + protocal)
        service.DeletePortMapping(NewRemoteHost='', NewExternalPort=port, NewProtocol=protocal)
    except Exception as e:
        logging.debug('Delete port mapping error: ' + repr(e))


_get_mapping_service = funcutil.to_async(_sync_get_mapping_service)
_add_port_mapping = funcutil.to_async(_sync_add_port_mapping)
_delete_port_mapping = funcutil.to_async(_sync_delete_port_mapping)
