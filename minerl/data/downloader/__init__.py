import requests
import tqdm


def download(directory, resolution='low', texturePack=0):

    url = '/'.join(["http://herobraine.com", resolution, texturePack])

    response = requests.get(url, stream=True)

    with open(directory, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)
    pass
