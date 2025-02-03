from .check_device import router as check_device_router
from .ddm_check import router as ddm_router
from .device_command import router as device_command_router
from .device_port_check import router as device_port_router
from .vlan_show import router as vlan_router
from  .lldp_show import router as lldp_router
from .show_macs import router as mac_router

__all__ = ["check_device_router", "device_command_router", "device_port_router", "vlan_router", "ddm_router","lldp_router","mac_router"]
