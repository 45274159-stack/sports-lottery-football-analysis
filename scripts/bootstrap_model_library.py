"""Load reviewed JSON catalog into a new or existing registry."""
import argparse,json
from pathlib import Path
from sports_lottery.model_library import connect,register_model,add_evaluation

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--catalog",default="data/models/catalog.json")
parser.add_argument("--db",default="data/models/model_library.sqlite3")
args=parser.parse_args()
catalog=json.loads(Path(args.catalog).read_text(encoding="utf-8"))
Path(args.db).parent.mkdir(parents=True,exist_ok=True)
db=connect(args.db)
try:
 for entry in catalog["models"]:
  model_id=entry["model"]["model_id"]
  if db.execute("SELECT 1 FROM models WHERE model_id=?",(model_id,)).fetchone():
   print(f"skip existing {model_id}")
   continue
  register_model(db,entry["model"])
  add_evaluation(db,model_id,entry["evaluation"])
  print(f"registered candidate {model_id}")
finally:
 db.close()
