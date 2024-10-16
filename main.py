import requests
import pytest

class DogAPI:
    BASE_URL = "https://dog.ceo/api"

    @staticmethod
    def get_sub_breeds(breed):
        res = requests.get(f"{DogAPI.BASE_URL}/breed/{breed}/list")
        res.raise_for_status()
        return res.json().get('message', [])

    @staticmethod
    def get_random_image(breed, sub_breed=None):
        if sub_breed:
            res = requests.get(f"{DogAPI.BASE_URL}/breed/{breed}/{sub_breed}/images/random")
        else:
            res = requests.get(f"{DogAPI.BASE_URL}/breed/{breed}/images/random")
        res.raise_for_status()
        return res.json().get('message')


def get_urls(breed, sub_breeds):
    url_images = []
    if sub_breeds:
        for sub_breed in sub_breeds:
            url_images.append(DogAPI.get_random_image(breed, sub_breed))
    else:
        url_images.append(DogAPI.get_random_image(breed))
    return url_images


class YaUploader:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'OAuth {self.token}'
        }
        self.url_create = 'https://cloud-api.yandex.net/v1/disk/resources'

    def create_folder(self, folder_name):
        res = requests.put(f'{self.url_create}?path={folder_name}', headers=self.headers)
        if res.status_code != 201:
            raise Exception("Folder creation failed")

    def upload_photos_to_yd(self, folder_name, name):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        params = {"path": f'/{folder_name}/{name}', 'url': url, "overwrite": "true"}
        response = requests.post(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


@pytest.mark.parametrize('breed', ['doberman', 'bulldog', 'collie'])
def test_proverka_upload_dog(ya_uploader, breed):
    folder_name = 'test_folder'
    ya_uploader.create_folder(folder_name)
    sub_breeds = DogAPI.get_sub_breeds(breed)
    urls = get_urls(breed, sub_breeds)

    for url in urls:
        part_name = url.split('/')
        name = '_'.join([part_name[-2], part_name[-1]])
        ya_uploader.upload_photos_to_yd(folder_name, name)

    response = requests.get(f'{ya_uploader.url_create}?path=/{folder_name}', headers=ya_uploader.headers)
    assert response.json()['type'] == "dir"
    assert response.json()['name'] == folder_name
    items = response.json().get('_embedded', {}).get('items', [])
    assert len(items) == len(urls)
    for item in items:
        assert item['type'] == 'file'
        assert item['name'].startswith(breed)
