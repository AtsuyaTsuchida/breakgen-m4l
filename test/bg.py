# Set BreakGen device params by name: python3 test/bg.py '{"Fetch":1}'
import json, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from live import q
def track(name="BreakGen"):
    n = q("get_session_info")["result"]["track_count"]
    for i in range(n):
        if q("get_track_info", {"track_index": i})["result"]["name"] == name: return i
if __name__ == "__main__":
    t = track()
    vals = json.loads(sys.argv[1])
    buttons = {k: 0 for k in vals if k in ("Fetch", "Generate", "Tempo")}
    if buttons:   # momentary buttons stay at 1 when set through the API
        q("set_device_parameter_ex", {"track_index": t, "device_index": 0, "values": buttons})
    print(q("set_device_parameter_ex", {"track_index": t, "device_index": 0, "values": vals})["result"])
