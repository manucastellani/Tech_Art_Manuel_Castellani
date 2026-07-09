"""
UE_Production_Toolkit.py  --  Version de ARCHIVO UNICO (Maya -> Unreal).

COMO USAR (simple y directo):
    1. Arrastra este archivo al Script Editor de Maya
       (o abri Script Editor > pestana Python y pega su contenido).
    2. Dale Play (Ejecutar).
    3. Se abre la ventana de la herramienta. Listo.

Todo esta en este unico archivo: no hay que instalar nada ni tocar rutas.

Autor: Manuel Castellani
Version: 1.2.0
Compatible: Maya 2022 - 2027 (elige PySide6 o PySide2 automaticamente).
"""

from __future__ import annotations

import datetime
import re
from contextlib import contextmanager

import maya.cmds as cmds
import maya.OpenMayaUI as omui

# --- Seleccion automatica del binding Qt ----------------------------------
# Maya 2025+ usa PySide6 (Qt6); Maya 2022-2024 usa PySide2 (Qt5).
try:
    from PySide6 import QtCore, QtGui, QtWidgets     # type: ignore
    from shiboken6 import wrapInstance               # type: ignore
    QT_BINDING = "PySide6"
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets     # type: ignore
    from shiboken2 import wrapInstance               # type: ignore
    QT_BINDING = "PySide2"


# ==========================================================================
#  1) LOGICA (sin interfaz)
# ==========================================================================

# Prefijos que ya usa el estudio: se detectan para no duplicarlos.
KNOWN_PREFIXES = ("SM_", "SK_", "M_", "T_", "MI_", "FX_", "JNT_")
MESH_PREFIXES = ("SM_", "SK_")
DEFAULT_CAMERAS = ("persp", "top", "front", "side")

_RE_LOD = re.compile(r"_LOD\d+$")           # _LOD0, _LOD12...
_RE_VARIATION = re.compile(r"_[A-Z]$")      # _A, _B (variantes)
_RE_VERSION = re.compile(r"_v\d+$")         # _v01, _v3
_RE_LEADING_ALPHA = re.compile(r"^[^0-9]+")


@contextmanager
def undo_chunk():
    """Agrupa toda la operacion en un solo paso de undo (un Ctrl+Z revierte todo)."""
    cmds.undoInfo(openChunk=True)
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


def _short_name(node):
    return node.rsplit("|", 1)[-1]


def _base_key(node):
    short = _short_name(node)
    match = _RE_LEADING_ALPHA.match(short)
    return match.group(0) if match else short


def _has_skin_cluster(transform):
    history = cmds.listHistory(transform) or []
    return any(cmds.nodeType(node) == "skinCluster" for node in history)


def _mesh_shape(transform):
    shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
    for shape in shapes:
        if cmds.nodeType(shape) == "mesh":
            return shape
    return None


def get_smart_name(obj, index, total_count):
    """Construye el nombre UE-ready: PREFIX_nombre[_variante][_NN][_LOD]."""
    name = _short_name(obj)

    lod = _RE_LOD.search(name)
    lod_suffix = lod.group(0) if lod else ""
    var = _RE_VARIATION.search(name)
    var_suffix = var.group(0) if var else ""

    base = name
    if lod_suffix:
        base = base[: -len(lod_suffix)]
    if var_suffix:
        base = base[: -len(var_suffix)]

    base = base.replace("_final", "")
    base = _RE_VERSION.sub("", base)          # quita _v01, _v3...

    # Quitar token de tipo si viene como prefijo (SM_Asset) o sufijo (root_JNT).
    for prefix in KNOWN_PREFIXES:
        token = prefix.rstrip("_")
        if base.startswith(prefix):
            base = base[len(prefix):]
            break
        if base.endswith("_" + token):
            base = base[: -(len(token) + 1)]
            break

    pure = _RE_LEADING_ALPHA.match(base)
    pure_base = (pure.group(0) if pure else base).rstrip("_")

    prefix = ""
    if cmds.nodeType(obj) == "joint":
        prefix = "JNT"
    elif _mesh_shape(obj) is not None:
        prefix = "SK" if _has_skin_cluster(obj) else "SM"

    final = "{}_{}".format(prefix, pure_base) if prefix else pure_base
    if var_suffix:
        final += var_suffix
    if total_count > 1:
        final += "_{:02d}".format(index)
    if lod_suffix:
        final += lod_suffix
    return final


def plan_rename(selection):
    """Calcula los renombres SIN aplicarlos (dry-run).

    Devuelve una lista de tuplas (full_path, nombre_viejo, nombre_nuevo),
    ordenada de mas profundo a menos profundo para que aplicar el rename no
    invalide los DAG paths de los hijos.
    """
    counts = {}
    for obj in selection:
        key = _base_key(obj)
        counts[key] = counts.get(key, 0) + 1

    running = {}
    decisions = []
    for obj in selection:
        key = _base_key(obj)
        running[key] = running.get(key, 0) + 1
        new_name = get_smart_name(obj, running[key], counts[key])
        decisions.append((obj, _short_name(obj), new_name))

    decisions.sort(key=lambda d: d[0].count("|"), reverse=True)
    return decisions


def apply_rename(decisions):
    """Aplica una lista de decisiones de plan_rename(). Devuelve nombres nuevos."""
    renamed = []
    for full_path, old_short, new_name in decisions:
        if old_short == new_name:
            continue
        actual = cmds.rename(full_path, new_name)
        renamed.append((old_short, _short_name(actual)))
    return renamed


def finalize_meshes(selection):
    """Delete history + freeze + center pivot. OMITE mallas skinneadas (rigs)."""
    cleaned, skipped_skinned, skipped_non_mesh = [], [], []
    for obj in selection:
        if _mesh_shape(obj) is None:
            skipped_non_mesh.append(_short_name(obj))
            continue
        if _has_skin_cluster(obj):
            skipped_skinned.append(_short_name(obj))
            continue
        cmds.delete(obj, constructionHistory=True)
        cmds.makeIdentity(obj, apply=True, translate=True, rotate=True,
                          scale=True, normal=0, preserveNormals=True)
        cmds.xform(obj, centerPivots=True)
        cleaned.append(_short_name(obj))
    return {"cleaned": cleaned, "skipped_skinned": skipped_skinned,
            "skipped_non_mesh": skipped_non_mesh}


def audit_naming():
    """Mallas de la escena sin prefijo SM_/SK_. No modifica nada."""
    broken = []
    for transform in cmds.ls(type="transform") or []:
        if transform in DEFAULT_CAMERAS:
            continue
        if _mesh_shape(transform) is None:
            continue
        if not _short_name(transform).startswith(MESH_PREFIXES):
            broken.append(transform)
    return broken


def check_duplicates():
    """Nodos con nombre corto no unico (rompen la exportacion a Unreal)."""
    all_nodes = cmds.ls(long=True, type=("transform", "mesh")) or []
    counts = {}
    for node in all_nodes:
        short = _short_name(node)
        counts[short] = counts.get(short, 0) + 1
    return [node for node in all_nodes if counts[_short_name(node)] > 1]


# ==========================================================================
#  2) INTERFAZ (PySide)
# ==========================================================================

WINDOW_OBJECT_NAME = "UEProductionToolkitWindow"
WINDOW_TITLE = "UE Production Toolkit"

_COLOR_AUDIT = "#5a2626"
_COLOR_DUPES = "#73501a"
_COLOR_RENAME = "#335a73"
_COLOR_FINALIZE = "#404040"
_COLOR_UNDO = "#3d3d3d"
_COLOR_NEW_NAME = "#7ec27e"   # verde para el nombre nuevo en el preview


def maya_main_window():
    """Ventana principal de Maya como QWidget (para parentear la herramienta)."""
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def _button(label, color, tooltip, height=40):
    btn = QtWidgets.QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setMinimumHeight(height)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    btn.setStyleSheet(
        "QPushButton {"
        "  background-color: %s; color: #f0f0f0; border: none;"
        "  border-radius: 4px; font-weight: bold; padding: 4px; }"
        "QPushButton:hover { border: 1px solid #8ab4d8; }"
        "QPushButton:pressed { background-color: #222222; }" % color
    )
    return btn


def _section_label(text):
    label = QtWidgets.QLabel(text)
    label.setStyleSheet("color: #9a9a9a; font-size: 10px; font-weight: bold;")
    return label


class RenamePreviewDialog(QtWidgets.QDialog):
    """Muestra los renombres propuestos y pide confirmacion antes de aplicar.

    El nombre nuevo se puede editar a mano con doble clic; al aplicar se usa
    lo que quedo en la tabla.
    """

    def __init__(self, changes, parent=None):
        super(RenamePreviewDialog, self).__init__(parent)
        self.setWindowTitle("Smart Rename  -  Preview")
        self.setMinimumSize(560, 420)
        self.resize(680, 520)

        self._rows = list(changes)  # (full_path, old, new) en orden de aplicacion

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info = QtWidgets.QLabel(
            "Se renombraran <b>{}</b> objetos. "
            "Doble clic en <b>Nombre nuevo</b> para editarlo a mano."
            .format(len(changes)))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QtWidgets.QTableWidget(len(changes), 2)
        self.table.setHorizontalHeaderLabels(["Nombre actual", "Nombre nuevo"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.DoubleClicked
            | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        for row, (_full, old, new) in enumerate(changes):
            old_item = QtWidgets.QTableWidgetItem(old)
            old_item.setFlags(old_item.flags() & ~QtCore.Qt.ItemIsEditable)
            old_item.setForeground(QtGui.QColor("#9a9a9a"))
            self.table.setItem(row, 0, old_item)

            new_item = QtWidgets.QTableWidgetItem(new)
            new_item.setForeground(QtGui.QColor(_COLOR_NEW_NAME))
            new_item.setToolTip("Doble clic para editar este nombre.")
            self.table.setItem(row, 1, new_item)
        layout.addWidget(self.table)

        buttons = QtWidgets.QDialogButtonBox()
        apply_btn = buttons.addButton("Aplicar", QtWidgets.QDialogButtonBox.AcceptRole)
        apply_btn.setStyleSheet(
            "background-color: %s; color: #f0f0f0; font-weight: bold; padding: 6px 16px;"
            % _COLOR_RENAME)
        buttons.addButton("Cancelar", QtWidgets.QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._commit_edits_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _commit_edits_and_accept(self):
        """Cierra cualquier editor abierto antes de aceptar y confirma."""
        self.table.setCurrentCell(-1, -1)  # fuerza a soltar el editor activo
        self.accept()

    def get_results(self):
        """Devuelve (full_path, old, nombre_final_editado) leido de la tabla."""
        results = []
        for row in range(self.table.rowCount()):
            full_path, old = self._rows[row][0], self._rows[row][1]
            new = self.table.item(row, 1).text().strip()
            results.append((full_path, old, new))
        return results


class UEToolkitWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(UEToolkitWindow, self).__init__(parent or maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setMinimumSize(480, 640)
        self._build_ui()
        self.resize(600, 760)   # tamano comodo por defecto (sin agrandar a mano)

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        title = QtWidgets.QLabel("UE PIPELINE MANAGER")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 6px;")
        root.addWidget(title)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #555;")
        root.addWidget(line)

        root.addWidget(_section_label("SCENE AUDIT"))
        b1 = _button("CHECK NAMING CONVENTIONS", _COLOR_AUDIT,
                     "Busca mallas sin prefijo SM_ o SK_ y las selecciona.")
        b1.clicked.connect(self._on_audit)
        root.addWidget(b1)

        b2 = _button("CHECK DUPLICATE NAMES", _COLOR_DUPES,
                     "Busca nombres no unicos que rompen la exportacion a Unreal.")
        b2.clicked.connect(self._on_duplicates)
        root.addWidget(b2)

        root.addSpacing(4)
        root.addWidget(_section_label("ORGANIZATION"))
        b3 = _button("SMART RENAME (AUTO-PREFIX)", _COLOR_RENAME,
                     "Muestra un preview y renombra con prefijos e indices automaticos.",
                     height=50)
        b3.clicked.connect(self._on_rename)
        root.addWidget(b3)

        root.addSpacing(4)
        root.addWidget(_section_label("OPTIMIZATION"))
        b4 = _button("FINALIZE MESH (DEL/FREEZE)", _COLOR_FINALIZE,
                     "Delete History, Freeze Transforms y Center Pivot. "
                     "Omite mallas skinneadas para no romper rigs.")
        b4.clicked.connect(self._on_finalize)
        root.addWidget(b4)

        # -- Log + Undo --
        root.addSpacing(4)
        log_header = QtWidgets.QHBoxLayout()
        log_header.addWidget(_section_label("LOG"))
        log_header.addStretch(1)
        clear_btn = QtWidgets.QPushButton("Limpiar")
        clear_btn.setToolTip("Vacia el log.")
        clear_btn.setMinimumHeight(30)
        clear_btn.setCursor(QtCore.Qt.PointingHandCursor)
        clear_btn.setStyleSheet(
            "QPushButton { background-color: #3d3d3d; color: #d0d0d0; border: none;"
            "  border-radius: 3px; font-size: 12px; padding: 4px 18px; }"
            "QPushButton:hover { background-color: #4a4a4a; }")
        clear_btn.clicked.connect(lambda: self.log_widget.clear())
        log_header.addWidget(clear_btn)
        root.addLayout(log_header)

        self.log_widget = QtWidgets.QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMinimumHeight(200)
        self.log_widget.setPlaceholderText("Las acciones apareceran aca...")
        self.log_widget.setStyleSheet(
            "background-color: #1e1e1e; color: #d6d6d6;"
            "font-family: Consolas, monospace; font-size: 14px; border: 1px solid #3a3a3a;")
        root.addWidget(self.log_widget)

        undo_btn = _button("UNDO  (deshacer ultima accion)", _COLOR_UNDO,
                           "Deshace la ultima operacion (equivale a Ctrl+Z en Maya).",
                           height=34)
        undo_btn.clicked.connect(self._on_undo)
        root.addWidget(undo_btn)

        footer = QtWidgets.QLabel("v1.2.0  |  Manuel Castellani")
        footer.setAlignment(QtCore.Qt.AlignCenter)
        footer.setStyleSheet("color: #777; font-size: 9px;")
        root.addWidget(footer)

    # -- log --
    def _log(self, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_widget.appendPlainText("[{}] {}".format(ts, message))

    # -- callbacks --
    def _selection(self):
        return cmds.ls(selection=True, long=True) or []

    def _on_rename(self):
        selection = self._selection()
        if not selection:
            self._log("Smart Rename: seleccion vacia. Elegi objetos y reintenta.")
            return

        decisions = plan_rename(selection)
        changes = [d for d in decisions if d[1] != d[2]]
        if not changes:
            self._log("Smart Rename: los {} objetos ya tienen el nombre correcto."
                      .format(len(selection)))
            return

        dialog = RenamePreviewDialog(changes, self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            self._log("Smart Rename: cancelado por el usuario (no se cambio nada).")
            return

        # Usar los nombres finales de la tabla (pueden estar editados a mano).
        final = [(f, o, n) for (f, o, n) in dialog.get_results() if n and n != o]
        if not final:
            self._log("Smart Rename: no quedaron cambios para aplicar.")
            return

        with undo_chunk():
            renamed = apply_rename(final)
        self._log("Smart Rename: {} objetos renombrados.".format(len(renamed)))
        for old, new in renamed[:15]:
            self._log("    {}  ->  {}".format(old, new))
        if len(renamed) > 15:
            self._log("    ... (+{} mas)".format(len(renamed) - 15))

    def _on_finalize(self):
        selection = self._selection()
        if not selection:
            self._log("Finalize: seleccion vacia. Elegi mallas y reintenta.")
            return
        with undo_chunk():
            report = finalize_meshes(selection)
        self._log("Finalize: {} mallas limpiadas (history / freeze / pivot)."
                  .format(len(report["cleaned"])))
        if report["skipped_skinned"]:
            self._log("    OMITIDAS (skinneadas, no se congelaron): {}"
                      .format(", ".join(report["skipped_skinned"])))
        if report["skipped_non_mesh"]:
            self._log("    Ignoradas (no eran mallas): {}"
                      .format(", ".join(report["skipped_non_mesh"])))

    def _on_audit(self):
        broken = audit_naming()
        if broken:
            cmds.select(broken, replace=True)
            self._log("Auditor: {} objetos no cumplen el naming SM_/SK_ "
                      "(quedaron seleccionados).".format(len(broken)))
        else:
            self._log("Auditor: escena limpia, todas las mallas cumplen el naming.")

    def _on_duplicates(self):
        dupes = check_duplicates()
        if dupes:
            cmds.select(dupes, replace=True)
            self._log("Duplicados: {} nodos con nombre no unico (quedaron "
                      "seleccionados). Renombralos antes de exportar a UE."
                      .format(len(dupes)))
        else:
            self._log("Duplicados: ninguno. Todos los nombres son unicos y UE-safe.")

    def _on_undo(self):
        try:
            cmds.undo()
            self._log("Undo: se revirtio la ultima accion.")
        except RuntimeError:
            self._log("Undo: no hay nada mas para deshacer.")


# Referencia global para que el garbage collector no cierre la ventana.
_window_instance = None


def show():
    """Crea (o reusa) y muestra la ventana."""
    global _window_instance
    if _window_instance is not None:
        try:
            _window_instance.close()
            _window_instance.deleteLater()
        except RuntimeError:
            pass
    _window_instance = UEToolkitWindow()
    _window_instance.show()
    return _window_instance


# --- Al ejecutar el archivo, abre la ventana directamente -----------------
show()
