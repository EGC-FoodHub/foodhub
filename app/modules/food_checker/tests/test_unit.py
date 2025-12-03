import pytest
from unittest.mock import MagicMock, patch
from app.modules.food_checker.services import FoodCheckerService
from app.modules.food_checker.forms import FoodCheckerForm


# Service Tests
def test_parse_food_content_valid():
    service = FoodCheckerService()
    content = """
name: Apple
calories: 52
type: Fruit
"""
    result = service._parse_food_content(content)
    assert result["valid"] is True
    assert result["valid"] is True

    content = """
info:
  author: John
  version: 1.0
name: Apple
calories: 52
type: Fruit
"""
    result = service._parse_food_content(content)
    assert result["valid"] is True
    assert result["data"]["info"]["author"] == "John"
    assert result["data"]["name"] == "Apple"


def test_parse_food_content_invalid_calories():
    service = FoodCheckerService()
    content = """
name: Apple
calories: not_a_number
type: Fruit
"""
    result = service._parse_food_content(content)
    assert result["valid"] is True
    result = service._parse_food_content(content)
    assert result["valid"] is True


def test_parse_food_content_invalid_syntax():
    service = FoodCheckerService()
    content = """
    name: Apple
    calories: 52
    type: Fruit
    invalid_line_without_colon
    """
    content = """
    name: Apple
    calories: 52
    type: Fruit
    invalid_line_without_colon
    """

    content = """
    name: Apple
    """
    result = service._parse_food_content(content)
    assert result["valid"] is False
    result = service._parse_food_content(content)
    assert result["valid"] is False
    assert result["error"] is None


def test_parse_food_content_syntax_error():
    service = FoodCheckerService()
    result = service._parse_food_content(123)  # Not a string
    assert result["valid"] is False
    assert "Syntax error" in result["error"]


def test_check_file_path_exists(tmp_path):
    service = FoodCheckerService()
    f = tmp_path / "test.food"
    f.write_text("name: Banana\ncalories: 89\ntype: Fruit", encoding="utf-8")

    result = service.check_file_path(str(f))
    assert result["valid"] is True
    assert result["data"]["name"] == "Banana"


def test_check_file_path_not_found():
    service = FoodCheckerService()
    result = service.check_file_path("/non/existent/path.food")
    assert result["valid"] is False


def test_check_file_path_read_error():
    service = FoodCheckerService()
    with patch("builtins.open", side_effect=Exception("Read failed")), patch("os.path.exists", return_value=True):
        result = service.check_file_path("somepath")
        assert result["valid"] is False
        assert "Read error" in result["error"]


def test_check_hubfile():
    service = FoodCheckerService()
    mock_hubfile = MagicMock()
    mock_hubfile.id = 1

    service.hubfile_service.get_or_404 = MagicMock(return_value=mock_hubfile)
    service.hubfile_service.get_path_by_hubfile = MagicMock(return_value="/path/to/file")

    service.hubfile_service.get_or_404 = MagicMock(return_value=mock_hubfile)
    service.hubfile_service.get_path_by_hubfile = MagicMock(return_value="/path/to/file")

    service.check_file_path = MagicMock(return_value={"valid": True})

    result = service.check_hubfile(1)
    assert result["valid"] is True
    service.hubfile_service.get_or_404.assert_called_with(1)
    service.hubfile_service.get_path_by_hubfile.assert_called_with(mock_hubfile)
    service.check_file_path.assert_called_with("/path/to/file")


def test_check_dataset():
    service = FoodCheckerService()
    mock_dataset = MagicMock()

    mock_file1 = MagicMock()
    mock_file1.id = 1
    mock_file1.name = "apple.food"

    mock_file2 = MagicMock()
    mock_file2.id = 2
    mock_file2.name = "burger.food"

    mock_food_model = MagicMock()
    mock_food_model.files = [mock_file1, mock_file2]
    mock_dataset.files = [mock_food_model]

    def side_effect(file_id):
        if file_id == 1:
            return {"valid": True, "data": {"calories": "50 cal"}}
        else:
            return {"valid": False, "error": "Bad format"}

    service.check_hubfile = MagicMock(side_effect=side_effect)

    summary = service.check_dataset(mock_dataset)

    assert summary["total_files"] == 2
    assert summary["valid_files"] == 1
    assert summary["total_calories"] == 50
    assert len(summary["details"]) == 2
    assert summary["details"][0]["filename"] == "apple.food"
    assert summary["details"][0]["valid"] is True
    assert summary["details"][1]["filename"] == "burger.food"
    assert summary["details"][1]["valid"] is False


def test_check_dataset_calorie_exception():
    service = FoodCheckerService()
    mock_dataset = MagicMock()
    mock_file = MagicMock()
    mock_file.id = 1
    mock_food_model = MagicMock()
    mock_food_model.files = [mock_file]
    mock_dataset.files = [mock_food_model]

    # Mock check_hubfile to return valid data but invalid calorie string
    service.check_hubfile = MagicMock(return_value={"valid": True, "data": {"calories": "not_an_int"}})

    summary = service.check_dataset(mock_dataset)

    # Total calories should remain 0 because of exception
    assert summary["total_calories"] == 0
    assert summary["valid_files"] == 1


def test_food_checker_model():
    from app.modules.food_checker.models import FoodChecker

    model = FoodChecker()
    model.id = 1
    assert repr(model) == "FoodChecker<1>"


def test_food_checker_repository():
    from app.modules.food_checker.repositories import FoodCheckerRepository

    repo = FoodCheckerRepository()
    assert repo.model is not None


# Route Tests
def test_check_temp_file(test_client):

    with (
        patch("app.modules.food_checker.routes.checker_service") as mock_service,
        patch("app.modules.food_checker.routes.current_user") as mock_user,
    ):

        mock_user.temp_folder.return_value = "/tmp/user/1"
        mock_service.check_file_path.return_value = {"valid": True, "data": {"name": "Test"}}

    # Test invalid calories in check_dataset
    def side_effect_invalid_cal(file_id):
        return {"valid": True, "data": {"calories": "invalid"}}

    service.check_hubfile = MagicMock(side_effect=side_effect_invalid_cal)
    summary = service.check_dataset(mock_dataset)
    assert summary["total_calories"] == 0


# Route Tests
def test_check_temp_file(test_client):
    from app.modules.auth.models import User
    from app import db

    user = User.query.filter_by(email="test@example.com").first()
    if user:
        user.is_email_verified = True
        db.session.commit()

    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)

    with (
        patch("app.modules.food_checker.routes.checker_service") as mock_service,
        patch("app.modules.food_checker.routes.current_user") as mock_user,
    ):
        mock_user.temp_folder = MagicMock(return_value="/tmp/user/1")
        mock_user.is_authenticated = True
        mock_service.check_file_path.return_value = {"valid": True, "data": {"name": "Test"}}

        response = test_client.post("/api/food_checker/check/temp", json={"filename": "test.food"})

        assert response.status_code == 200
        assert response.json["valid"] is True


def test_check_file_route(test_client):
    with patch("app.modules.food_checker.routes.checker_service") as mock_service:
        mock_service.check_hubfile.return_value = {"valid": True}
        response = test_client.get("/api/food_checker/check/file/1")
        assert response.status_code == 200
        assert response.json == {"valid": True}
        mock_service.check_hubfile.assert_called_with(1)


def test_check_dataset_route(test_client):
    with (
        patch("app.modules.food_checker.routes.checker_service") as mock_service,
        patch("app.modules.food_checker.routes.dataset_service") as mock_dataset_service,
    ):

        mock_dataset = MagicMock()
        mock_dataset_service.get_by_id.return_value = mock_dataset
        mock_service.check_dataset.return_value = {"summary": "ok"}

        response = test_client.get("/api/food_checker/check/dataset/1")
        assert response.status_code == 200
        assert response.json == {"summary": "ok"}

        mock_dataset_service.get_by_id.assert_called_with(1)
        mock_service.check_dataset.assert_called_with(mock_dataset)


def test_check_dataset_route_404(test_client):
    with patch("app.modules.food_checker.routes.dataset_service") as mock_dataset_service:
        mock_dataset_service.get_by_id.return_value = None
        response = test_client.get("/api/food_checker/check/dataset/999")
        assert response.status_code == 404


# Form Tests
def test_food_checker_form(test_client):
    with test_client.application.app_context():
        form = FoodCheckerForm()
        assert form.submit.label.text == "Save food_checker"
