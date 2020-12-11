import os
import boto3
from minerl.data.util.constants import BASE_DIR, DOWNLOAD_DIR, OUTPUT_DIR, BUCKET_NAME
from concurrent.futures import ThreadPoolExecutor

s3 = boto3.resource('s3')
bucket = s3.Bucket(BUCKET_NAME)

J = os.path.join

def partition_streams(rank, size):
    stream_list = list(set(get_stream_prefix(o.key) for o in bucket.objects.iterator()))
    stream_list.sort()
    my_streams = stream_list[rank:size:]
    return my_streams

def download_stream(stream_prefix):
    print(f"Downloading stream {stream_prefix}")
    client = boto3.client('s3')
    stream_pieces = bucket.objects.filter(Prefix=stream_prefix)
    for p in stream_pieces:
        file_path = key_to_local_path(p.key)
        os.mkdir(os.dirname(file_path), exists_ok=True)
        client.download_file(BUCKET_NAME, p.key, file_path)

def download_streams(stream_prefixes, n_workers=4):
    with ThreadPoolExecutor(max_workers=n_workers) as tpe:
        fs = [tpe.submit(download_stream, p) for p in stream_prefixes]
        for f in fs:
            f.result()
        
def get_stream_prefix(key):
    return '-'.join(key.split('-')[:2])

def get_stream_name(key):
    return get_stream_prefix(key).split('/')[-1]

def key_to_local_path(key):
    return J(DOWNLOAD_DIR, '/'.join(key.split('/')[1:]))


def download_partition():
    from mpi4py import MPI
    rank = MPI.COMM_WORLD.rank
    size = MPI.COMM_WORLD.size
    prefixes = partition_streams(rank, size)
    download_streams(prefixes)


if __name__ == '__main__':
    download_partition()
