"""
Test fixtures for `dlgr.memoryexp` module.
"""
import pytest
from dallinger import models
from dallinger import networks
from dallinger import nodes


@pytest.fixture(scope='module', autouse=True)
def reset_config():
    yield

    # Make sure dallinger_experiment module isn't kept between tests
    import sys
    if 'dallinger_experiment' in sys.modules:
        del sys.modules['dallinger_experiment']

    # Make sure extra parameters aren't kept between tests
    from dallinger.config import get_config
    config = get_config()
    config._reset(register_defaults=True)


@pytest.fixture
def stub_config():
    """Builds a standardized Configuration object and returns it, but does
    not load it as the active configuration returned by
    dallinger.config.get_config()
    """
    defaults = {
        u'aws_region': u'us-east-1',
        u'base_port': 5000,
        u'clock_on': True,
        u'dallinger_email_address': u'test@example.com',
        u'database_url': u'postgresql://postgres@localhost/dallinger',
        u'dyno_type': u'standard-2x',
        u'heroku_team': u'dallinger',
        u'host': u'localhost',
        u'logfile': u'server.log',
        u'loglevel': 0,
        u'mode': u'debug',
        u'num_dynos_web': 2,
        u'num_dynos_worker': 2,
        u'threads': u'1',
        u'whimsical': True
    }
    from dallinger.config import default_keys
    from dallinger.config import Configuration
    config = Configuration()
    for key in default_keys:
        config.register(*key)
    config.extend(defaults.copy())
    config.ready = True

    return config


@pytest.fixture
def active_config(stub_config):
    """Loads the standard config as the active configuration returned by
    dallinger.config.get_config() and returns it.
    """
    from dallinger.config import get_config
    config = get_config()
    config.data = stub_config.data
    config.ready = True
    return config


@pytest.fixture
def db_session():
    import dallinger.db
    # The drop_all call can hang without this; see:
    # https://stackoverflow.com/questions/13882407/sqlalchemy-blocked-on-dropping-tables
    dallinger.db.session.close()
    session = dallinger.db.init_db(drop_all=True)
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def exp_klass(db_session, active_config):
    import dallinger.experiment
    klass = dallinger.experiment.load()

    yield klass


@pytest.fixture
def exp_module(active_config, exp_klass):
    from dallinger_experiment import experiment
    try:
        experiment.extra_parameters()
    except KeyError:
        pass

    yield experiment


@pytest.fixture
def dbview():
    """A class for performing DB queries"""

    class Query(object):

        def partner_indexes(self, node):
            agents = nodes.Agent.query.all()
            node_index = agents.index(node)
            neighbors = agents[node_index].neighbors()
            return [agents.index(n) for n in neighbors]

        def participant_vectors(self):
            vectors = [
                (v.origin.id, v.destination.id)
                for v in models.Vector.query.all()
                if v.origin.participant_id is not None
            ]

            return sorted(vectors)

        def unique_participant_vectors(self):
            vectors = self.participant_vectors()
            ordered = [tuple(sorted(pair)) for pair in vectors]
            deduped = sorted(list(set(sorted(ordered))))

            return deduped

    return Query()


@pytest.fixture
def a(db_session):
    """ Provides a standard way of building model objects in tests.

        def test_using_all_defaults(self, a):
            participant = a.participant(worker_id=42)
    """
    class ModelFactory(object):

        def __init__(self, db):
            self.db = db

        def participant(self, **kw):
            defaults = {
                'recruiter_id': 'hotair',
                'worker_id': '1',
                'assignment_id': '1',
                'hit_id': '1',
                'mode': 'test'
            }
            defaults.update(kw)
            return self._build(models.Participant, defaults)

        def network(self, **kw):
            defaults = {}
            defaults.update(kw)
            return self._build(models.Network, defaults)

        def empty(self, **kw):
            defaults = {}
            defaults.update(kw)
            return self._build(networks.Empty, defaults)

        def fully_connected(self, **kw):
            defaults = {}
            defaults.update(kw)
            return self._build(networks.FullyConnected, defaults)

        def node(self, **kw):
            defaults = {
                'network': self.empty
            }
            defaults.update(kw)
            return self._build(nodes.Agent, defaults)

        def _build(self, klass, attrs):
            # Some of our default values are factories:
            for k, v in attrs.items():
                if callable(v):
                    attrs[k] = v()

            obj = klass(**attrs)
            self._insert(obj)
            return obj

        def _insert(self, thing):
            db_session.add(thing)
            db_session.flush()  # This gets us an ID and sets relationships

    return ModelFactory(db_session)
