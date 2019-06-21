import os.path
import json
from calval.satellites.srf import (
    SRF, Sentinel2Blue, Sentinel2Green, Sentinel2Red)

datadir = os.path.dirname(__file__)


class MultiBandSRF:
    def __init__(self, band_srfs):
        self.srfs = band_srfs
        self.by_band = {srf.band: srf for srf in band_srfs}


class Sentinel2SRF(MultiBandSRF):
    def __init__(self):
        super().__init__([
            Sentinel2Blue(), Sentinel2Green(), Sentinel2Red()
        ])


class Newsat3HyperSpectralSRF(MultiBandSRF):
    def __init__(self):
        with open(os.path.join(datadir, 'Newsat3_Hyperspectral_SRF.json'), 'rt') as f:
            data = json.load(f)
        super().__init__([SRF(**chan) for chan in data])
