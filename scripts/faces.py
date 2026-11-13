#!/usr/bin/env python3
"""Face detection shared by render.py and track.py.

Uses YuNet (assets/face_detection_yunet_*.onnx, from OpenCV Zoo, MIT
licence) when this OpenCV build has cv2.FaceDetectorYN, and falls back to the
older Haar cascade otherwise. YuNet copes with side-on faces, glasses and
small faces far better, and also gives the mouth position.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
YUNET = os.path.join(ASSETS, "face_detection_yunet_2023mar.onnx")
YUNET_2026 = os.path.join(ASSETS, "face_detection_yunet_2026may.onnx")

_state = {"kind": None, "det": None}


def _load():
    if _state["kind"] is not None:
        return
    import cv2
    # OpenCV 5 prefers the 2026 export (dynamic input size); OpenCV 4 needs
    # the 2023 one. Try the better match first, then the other.
    models = [YUNET_2026, YUNET] if cv2.__version__.startswith("5") \
        else [YUNET, YUNET_2026]
    for model in models:
        if not (hasattr(cv2, "FaceDetectorYN") and os.path.exists(model)):
            continue
        try:
            _state["det"] = cv2.FaceDetectorYN.create(model, "", (320, 320),
                                                      0.6, 0.3, 50)
            _state["kind"] = "yunet"
            return
        except Exception:  # noqa: BLE001
            pass
    for xml in (os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""),
                             "haarcascade_frontalface_default.xml"),
                os.path.join(ASSETS, "haarcascade_frontalface_default.xml")):
        if os.path.exists(xml):
            c = cv2.CascadeClassifier(xml)
            if not c.empty():
                _state["det"], _state["kind"] = c, "haar"
                return
    _state["kind"] = "none"


def kind():
    _load()
    return _state["kind"]


def detect(frame, max_w=640):
    """Faces in one BGR frame, largest first. Each is a dict in source pixels:
    x, y, w, h, score, mouth (x, y) and eyes (x, y); mouth and eyes are
    estimated from the box when the detector does not give landmarks."""
    import cv2
    _load()
    if _state["kind"] == "none":
        return []
    H, W = frame.shape[:2]
    scale = min(max_w / W, 1.0)
    img = cv2.resize(frame, (int(W * scale), int(H * scale))) if scale < 1 else frame
    out = []
    if _state["kind"] == "yunet":
        det = _state["det"]
        det.setInputSize((img.shape[1], img.shape[0]))
        _, found = det.detect(img)
        for r in (found if found is not None else []):
            x, y, w, h = (float(v) / scale for v in r[:4])
            pts = [float(v) / scale for v in r[4:14]]
            out.append({"x": x, "y": y, "w": w, "h": h, "score": float(r[14]),
                        "eyes": ((pts[0] + pts[2]) / 2, (pts[1] + pts[3]) / 2),
                        "mouth": ((pts[6] + pts[8]) / 2, (pts[7] + pts[9]) / 2)})
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for (x, y, w, h) in _state["det"].detectMultiScale(gray, 1.1, 6,
                                                            minSize=(36, 36)):
            x, y, w, h = (float(v) / scale for v in (x, y, w, h))
            out.append({"x": x, "y": y, "w": w, "h": h, "score": 0.5,
                        "eyes": (x + w / 2, y + h * 0.38),
                        "mouth": (x + w / 2, y + h * 0.78)})
    out.sort(key=lambda f: -f["w"] * f["h"])
    return out
