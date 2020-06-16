gsutil cp gs://wguss-rcall/results/$1.zip .
unzip $1.zip
cp $1/* ../minerl/herobraine/env_specs/obfuscators/comp/v3