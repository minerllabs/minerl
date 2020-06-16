import os
import logging

SHOULD_ASSERT = bool(os.environ.get('MINERL_TESTING', False)) or 'PYTEST_CURRENT_TEST' in os.environ
