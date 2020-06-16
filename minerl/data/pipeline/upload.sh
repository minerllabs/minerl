# Usage: MINERL_DATA_ROOT=<path to data root> ./upload.sh <version number>

aws s3 sync $MINERL_DATA_ROOT s3://minerl/v$1/  --acl public-read --exclude '*'  --include "*.tar"
aws s3 cp  $MINERL_DATA_ROOT/MD5SUMS  s3://minerl/v$1/ MD5SUMS --acl public-read
aws s3 cp  $MINERL_DATA_ROOT/SHA1SUMS   s3://minerl/v$1/ SHA1SUMS --acl public-read
aws s3 cp  $MINERL_DATA_ROOT/SHA256SUMS   s3://minerl/v$1/ SHA256SUMS --acl public-read
aws s3 cp  $MINERL_DATA_ROOT/VERSION   s3://minerl/v$1/ VERSION --acl public-read

