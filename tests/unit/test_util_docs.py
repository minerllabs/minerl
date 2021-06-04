from minerl.utils import docs
from minerl.herobraine import envs


def test_docs_smoke():
    for env_spec in envs.ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)
