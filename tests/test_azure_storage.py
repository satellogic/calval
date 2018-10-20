import pytest
from testing_utils import config
from calval.azure_storage import AzureStorage

pytest.importorskip('azure.storage.blob')

account_cstring = (
    'DefaultEndpointsProtocol=https;'
    'AccountName=dummyaccount;'
    'AccountKey=dummy1/dummy2==;'
    'EndpointSuffix=core.windows.net')
sas_cstring = (
    'BlobEndpoint=https://dummyaccount.blob.core.windows.net;'
    'SharedAccessSignature=?st=2018-10-17T21%3A24%3A47Z&se=2020-10-18T21%3A24%3A00Z&sp=rl&sv=2018-03-28&sr=c&'
    'sig=dummy4%3D')


def test_cstring_parse():
    for cstring in [account_cstring, sas_cstring]:
        store = AzureStorage(cstring, 'cicd')
        assert store.endpoint == 'https://dummyaccount.blob.core.windows.net'


@pytest.mark.skipif('azure_cicd_connection' not in config,
                    reason='Azure connection string not configured')
def test_query():
    cstring = config['azure_cicd_connection']
    storage = AzureStorage(cstring, 'cicd', 'calval_test/')
    scenes = storage.query(satellite='LC08', product=['sr', 'toa'])
    assert len(scenes) == 3
    for s in scenes:
        assert s['satellite_class'] == 'landsat8'
    scenes = storage.query(satellite='LC08', product='toa', tag='1')
    assert len(scenes) == 0
    scenes = storage.query(satellite='LC08', product='toa', tag='0')
    assert len(scenes) == 2
