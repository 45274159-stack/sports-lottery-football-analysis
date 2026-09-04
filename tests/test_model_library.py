import tempfile,unittest
from pathlib import Path
from sports_lottery.model_library import connect,register_model,add_evaluation,activate,select_model,data_fingerprint,change_status

SPEC=dict(model_id="m1",family="venue-poisson",version="1",competition="L",markets=["result","score","total_goals"],trained_through="2024-06-30",training_data_hash="abc",parameters={"window":500},code_ref="commit:test",created_at="2024-07-01T00:00:00Z",status="accepted",notes="test")
EVAL=dict(split_name="rolling-2024",start_date="2024-07-01",end_date="2024-12-31",matches=100,metrics={"log_loss":1.0,"accuracy":.5},is_prospective=False)

class ModelLibraryTests(unittest.TestCase):
 def test_registry_lifecycle_and_cutoff(self):
  db=connect(":memory:");register_model(db,SPEC);add_evaluation(db,"m1",EVAL);activate(db,"m1","L","result","2025-01-01T00:00:00Z")
  self.assertEqual(select_model(db,"L","result","2025-01-02T10:00:00Z")["model_id"],"m1")
  with self.assertRaises(ValueError):select_model(db,"L","result","2024-06-30T10:00:00Z")
  with self.assertRaises(Exception):register_model(db,SPEC)
 def test_candidate_cannot_activate(self):
  db=connect(":memory:");register_model(db,dict(SPEC,model_id="c",status="candidate"));add_evaluation(db,"c",EVAL)
  with self.assertRaises(ValueError):activate(db,"c","L","result","2025-01-01T00:00:00Z")
  with self.assertRaises(ValueError):change_status(db,"c","accepted")
  add_evaluation(db,"c",dict(EVAL,split_name="prospective",matches=100,is_prospective=True))
  change_status(db,"c","accepted");activate(db,"c","L","result","2025-01-01T00:00:00Z")
  change_status(db,"c","retired")
  with self.assertRaises(ValueError):select_model(db,"L","result","2025-02-01T00:00:00Z")
 def test_scope(self):
  db=connect(":memory:");register_model(db,SPEC);add_evaluation(db,"m1",EVAL)
  with self.assertRaises(ValueError):activate(db,"m1","OTHER","result","2025-01-01T00:00:00Z")
 def test_fingerprint_is_order_independent(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/"a",Path(d)/"b";a.write_text("a");b.write_text("b")
   self.assertEqual(data_fingerprint([a,b]),data_fingerprint([b,a]))
