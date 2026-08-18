import unittest

from backend.app.main import app


class TestMLJobsSetup(unittest.TestCase):
    def test_ml_jobs_router_is_registered(self):
        routes = {route.path for route in app.routes}
        self.assertIn("/api/ml/jobs", routes)
