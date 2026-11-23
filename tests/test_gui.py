import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt5.QtCore import QThreadPool, qInstallMessageHandler  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

from crypto_core import hashing  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def qt_messages():
    messages = []
    previous = qInstallMessageHandler(lambda mode, ctx, msg: messages.append(msg))
    yield messages
    qInstallMessageHandler(previous)


@pytest.fixture
def window(app, qt_messages):
    from gui.main_window import MainWindow
    from gui.theme import apply_theme

    apply_theme(app)
    win = MainWindow()
    win.show()
    app.processEvents()
    yield win
    win.close()


def wait_tasks(app):
    QThreadPool.globalInstance().waitForDone(30000)
    app.processEvents()


def test_stylesheet_parses_without_warnings(window, qt_messages):
    problems = [m for m in qt_messages if "stylesheet" in m.lower() or "unknown property" in m.lower()]
    assert problems == []


def test_sidebar_switches_every_page(app, window):
    assert list(window.pages) == ["aes", "rsa", "ecc", "sha256", "bcrypt", "base64"]
    assert window.stack.count() == 6
    for index in range(6):
        window.sidebar.select(index)
        app.processEvents()
        assert window.stack.currentIndex() == index


def test_base64_page_round_trip(app, window):
    page = window.pages["base64"]
    page.input_panel.set_text("你好 Base64")
    page.encode_btn.click()
    assert page.output_panel.text() == "5L2g5aW9IEJhc2U2NA=="
    page.swap_btn.click()
    page.decode_btn.click()
    assert page.output_panel.text() == "你好 Base64"


def test_base64_page_url_safe_and_charset_options(app, window):
    page = window.pages["base64"]
    page.url_safe_check.setChecked(True)
    page.input_panel.set_text("???")
    page.encode_btn.click()
    assert page.output_panel.text() == "Pz8_"

    page.url_safe_check.setChecked(False)
    page.charset_combo.setCurrentText("GBK")
    page.input_panel.set_text("中文")
    page.encode_btn.click()
    assert page.output_panel.text() == "1tDOxA=="


def test_base64_page_invalid_input_shows_error_toast(app, window):
    page = window.pages["base64"]
    page.input_panel.set_text("abc$")
    page.decode_btn.click()
    assert window.toast.isVisible()
    assert window.toast.property("kind") == "error"


def test_aes_page_round_trip(app, window):
    page = window.pages["aes"]
    page.password.setText("pw")
    page.input_panel.set_text("hello 世界")
    page.encrypt_btn.click()
    wait_tasks(app)
    assert page.output_panel.text()
    page.swap_btn.click()
    page.decrypt_btn.click()
    wait_tasks(app)
    assert page.output_panel.text() == "hello 世界"


def test_aes_wrong_password_shows_error_toast(app, window):
    page = window.pages["aes"]
    page.password.setText("pw")
    page.input_panel.set_text("x")
    page.encrypt_btn.click()
    wait_tasks(app)
    page.swap_btn.click()
    page.password.setText("wrong")
    page.decrypt_btn.click()
    wait_tasks(app)
    assert window.toast.isVisible()
    assert window.toast.property("kind") == "error"


@pytest.mark.parametrize("name", ["rsa", "ecc"])
def test_asymmetric_page_round_trip(app, window, name):
    page = window.pages[name]
    page.generate_btn.click()
    wait_tasks(app)
    assert "BEGIN PUBLIC KEY" in page.public_panel.text()
    assert "BEGIN PRIVATE KEY" in page.private_panel.text()
    page.input_panel.set_text("非对称 round trip")
    page.encrypt_btn.click()
    wait_tasks(app)
    page.swap_btn.click()
    page.decrypt_btn.click()
    wait_tasks(app)
    assert page.output_panel.text() == "非对称 round trip"


def test_encrypted_private_key_prompts_for_password_on_decrypt(app, window, monkeypatch):
    import gui.pages.asymmetric_page as page_module
    from crypto_core import keys, rsa_cipher

    page = window.pages["rsa"]
    private_pem, public_pem = rsa_cipher.generate_keypair("2048")
    page.public_panel.set_text(public_pem)
    page.private_panel.set_text(keys.protect_private_pem(private_pem, "kp", "RSA"))
    prompts = []
    monkeypatch.setattr(page_module, "ask_password", lambda *args: prompts.append(args) or "kp")

    page.input_panel.set_text("locked message")
    page.encrypt_btn.click()
    wait_tasks(app)
    page.swap_btn.click()
    page.decrypt_btn.click()
    wait_tasks(app)  # 第一次失败 → 弹密码框 → 用密码重试
    wait_tasks(app)
    assert len(prompts) == 1
    assert page.output_panel.text() == "locked message"


def test_private_key_export_with_password_then_import(app, window, monkeypatch, tmp_path):
    import gui.pages.asymmetric_page as page_module

    page = window.pages["ecc"]
    page.generate_btn.click()
    wait_tasks(app)
    original = page.private_panel.text()
    target = tmp_path / "ecc_private.pem"
    monkeypatch.setattr(page_module, "ask_password", lambda *args: "kp")
    monkeypatch.setattr(page_module.QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(target), "")))
    monkeypatch.setattr(page_module.QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(target), "")))

    page.export_priv_btn.click()
    assert "ENCRYPTED PRIVATE KEY" in target.read_text(encoding="utf-8")

    page.private_panel.clear()
    page.import_priv_btn.click()
    assert page.private_panel.text() == original


def test_derive_public_button_fills_public_panel(app, window):
    page = window.pages["rsa"]
    page.generate_btn.click()
    wait_tasks(app)
    expected = page.public_panel.text()
    page.public_panel.clear()
    page.derive_pub_btn.click()
    assert page.public_panel.text() == expected


def test_derive_public_from_encrypted_private_prompts_for_password(app, window, monkeypatch):
    import gui.pages.asymmetric_page as page_module
    from crypto_core import keys

    page = window.pages["ecc"]
    page.generate_btn.click()
    wait_tasks(app)
    expected = page.public_panel.text()
    page.private_panel.set_text(keys.protect_private_pem(page.private_panel.text(), "kp", "ECC"))
    page.public_panel.clear()
    monkeypatch.setattr(page_module, "ask_password", lambda *args: "kp")
    page.derive_pub_btn.click()
    assert page.public_panel.text() == expected


def _patch_open_dialog(monkeypatch, path):
    import gui.pages.asymmetric_page as page_module

    monkeypatch.setattr(page_module.QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(path), "")))


def test_import_public_from_private_key_file_extracts_public_key(app, window, monkeypatch, tmp_path):
    page = window.pages["rsa"]
    page.generate_btn.click()
    wait_tasks(app)
    expected = page.public_panel.text()
    key_file = tmp_path / "id_rsa.pem"
    key_file.write_text(page.private_panel.text(), encoding="utf-8")
    page.public_panel.clear()
    _patch_open_dialog(monkeypatch, key_file)
    page.import_pub_btn.click()
    assert page.public_panel.text() == expected


def test_import_public_from_binary_der_file(app, window, monkeypatch, tmp_path):
    import base64

    page = window.pages["rsa"]
    page.generate_btn.click()
    wait_tasks(app)
    expected = page.public_panel.text()
    body = "".join(expected.splitlines()[1:-1])
    der_file = tmp_path / "public.der"
    der_file.write_bytes(base64.b64decode(body))
    page.public_panel.clear()
    _patch_open_dialog(monkeypatch, der_file)
    page.import_pub_btn.click()
    assert page.public_panel.text() == expected


def test_sha256_page_updates_live(app, window):
    page = window.pages["sha256"]
    page.input_panel.set_text("abc")
    assert page.output.text() == hashing.sha256_hex("abc")
    page.upper_check.setChecked(True)
    assert page.output.text() == hashing.sha256_hex("abc", upper=True)
    page.input_panel.set_text("")
    assert page.output.text() == ""


def test_bcrypt_page_hash_and_verify(app, window):
    page = window.pages["bcrypt"]
    page.cost_slider.setValue(4)
    page.hash_password.setText("pw")
    page.hash_btn.click()
    wait_tasks(app)
    hashed = page.hash_output.text()
    assert hashed.startswith("$2b$04$")

    page.use_hash_btn.click()
    assert page.verify_hash.text() == hashed

    page.verify_password.setText("pw")
    page.verify_btn.click()
    wait_tasks(app)
    assert page.result_badge.property("state") == "match"

    page.verify_password.setText("nope")
    page.verify_btn.click()
    wait_tasks(app)
    assert page.result_badge.property("state") == "mismatch"
