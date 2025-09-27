# core/services/onvif_client.py
from onvif import ONVIFCamera
from typing import Optional

class OnvifClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.camera = ONVIFCamera(host, port, user, password)
        self.media = self.camera.create_media_service()
        self.profiles = self.media.GetProfiles()
        self.ptz = self.camera.create_ptz_service()

    def get_device_info(self) -> dict:
        info = self.camera.devicemgmt.GetDeviceInformation()
        return {
            "Manufacturer": info.Manufacturer,
            "Model": info.Model,
            "FirmwareVersion": info.FirmwareVersion,
            "SerialNumber": info.SerialNumber,
        }

    def get_rtsp_url(self, profile_token: Optional[str] = None) -> str:
        token = profile_token or self.profiles[0].token
        uri = self.media.GetStreamUri({
            "StreamSetup": {"Stream": "RTP-Unicast", "Transport": {"Protocol": "RTSP"}},
            "ProfileToken": token,
        })
        return uri.Uri

    def move(self, x: float, y: float, zoom: float = 0.0, profile_token: Optional[str] = None):
        token = profile_token or self.profiles[0].token
        self.ptz.ContinuousMove({
            "ProfileToken": token,
            "Velocity": {"PanTilt": {"x": x, "y": y}, "Zoom": {"x": zoom}},
        })

    def stop(self, profile_token: Optional[str] = None):
        token = profile_token or self.profiles[0].token
        self.ptz.Stop({"ProfileToken": token})
